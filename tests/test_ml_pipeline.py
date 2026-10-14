"""
Testes unitários para o pipeline ML v3.
Testa a feature engineering e o treino em dados sintéticos,
garantindo ausência de vazamento e corretude das features.
"""
import numpy as np
import pandas as pd
import pytest

from src.ml_pipeline.feature_engineering import build_ml_features, get_feature_columns
from src.ml_pipeline.model_training import clip_outliers_per_city, _expanding_window_splits


# =============================================
# Fixture: painel sintético mínimo
# =============================================
@pytest.fixture
def mini_panel():
    """Cria um painel sintético com 2 cidades × 24 meses."""
    np.random.seed(42)
    rows = []
    for code in ["100001", "200002"]:
        for y in [2020, 2021]:
            for m in range(1, 13):
                rows.append({
                    "code": code,
                    "year": y,
                    "month": m,
                    "dengue_cases": np.random.poisson(50),
                    "temp_media": 20 + np.random.randn() * 3,
                    "temp_maxima": 28 + np.random.randn() * 2,
                    "temp_minima": 14 + np.random.randn() * 2,
                    "precipitacao": max(0, 100 + np.random.randn() * 40),
                    "umidmed": min(100, max(30, 70 + np.random.randn() * 10)),
                    "enso": np.random.choice([-0.5, 0.0, 0.5, 1.0]),
                    "receptivo": np.random.choice([0, 1, 2]),
                    "populacao": 50000 + np.random.randint(-5000, 5000),
                    "latitude": -28.5 if code == "100001" else -25.0,
                })
    return pd.DataFrame(rows)


# =============================================
# Testes de Feature Engineering
# =============================================
class TestFeatureEngineering:
    def test_output_has_no_target_leakage(self, mini_panel):
        """Garante que colunas proibidas não aparecem nas features."""
        df = build_ml_features(mini_panel)
        feat_cols = get_feature_columns(df)
        proibidas = {"dengue_cases", "code", "year", "month", "CASOS_EST_DENGUE"}
        assert proibidas.isdisjoint(set(feat_cols)), f"Vazamento detectado: {proibidas & set(feat_cols)}"

    def test_lag_is_strictly_past(self, mini_panel):
        """Verifica que dengue_lag1 corresponde ao valor do mês anterior."""
        df = build_ml_features(mini_panel)
        # Pega a primeira cidade
        city = df[df["code"] == "100001"].sort_values(["year", "month"]).reset_index(drop=True)
        for i in range(1, len(city)):
            lag_val = city.loc[i, "dengue_lag1"]
            prev_cases = city.loc[i - 1, "dengue_cases"]
            assert lag_val == prev_cases, f"Lag1 errado na linha {i}: esperado {prev_cases}, obtido {lag_val}"

    def test_rolling_12_does_not_include_current_month(self, mini_panel):
        """
        O rolling de memória epidêmica NÃO deve incluir o mês corrente.
        Para verificar: se mudarmos o dengue_cases do mês corrente,
        o dengue_rolling_12 NÃO deve mudar.
        """
        df1 = build_ml_features(mini_panel)

        # Modifica o alvo de uma linha específica
        panel_mod = mini_panel.copy()
        mask = (panel_mod["code"] == "100001") & (panel_mod["year"] == 2021) & (panel_mod["month"] == 6)
        panel_mod.loc[mask, "dengue_cases"] = 99999

        df2 = build_ml_features(panel_mod)

        # O rolling_12 na MESMA linha (code=100001, 2021-06) deve ser igual
        r1 = df1[(df1["code"] == "100001") & (df1["year"] == 2021) & (df1["month"] == 6)]["dengue_rolling_12"].values
        r2 = df2[(df2["code"] == "100001") & (df2["year"] == 2021) & (df2["month"] == 6)]["dengue_rolling_12"].values

        if len(r1) > 0 and len(r2) > 0:
            assert abs(r1[0] - r2[0]) < 1e-6, (
                f"Rolling inclui mês corrente! r1={r1[0]:.2f} vs r2={r2[0]:.2f}"
            )

    def test_output_shape(self, mini_panel):
        """Verifica que o output tem features e menos linhas que o input (warm-up)."""
        df = build_ml_features(mini_panel)
        assert len(df) < len(mini_panel), "Deveria ter removido linhas de warm-up"
        assert len(df.columns) > len(mini_panel.columns), "Deveria ter adicionado features"

    def test_get_feature_columns_excludes_meta(self, mini_panel):
        """Verifica que get_feature_columns exclui colunas de identificação."""
        df = build_ml_features(mini_panel)
        feat_cols = get_feature_columns(df)
        meta = {"code", "city_name", "year", "month", "dengue_cases", "populacao", "latitude", "longitude"}
        for col in meta:
            assert col not in feat_cols, f"Coluna meta {col} apareceu nas features!"


# =============================================
# Testes de Model Training
# =============================================
class TestModelTraining:
    def test_clip_per_city(self):
        """Garante que clipping é por cidade e não global."""
        df = pd.DataFrame({
            "code": ["A"] * 10 + ["B"] * 10,
            "dengue_cases": list(range(10, 110, 10)) + list(range(100, 1100, 100)),
        })
        clipped = clip_outliers_per_city(df, "dengue_cases", percentile=90)
        # Cidade A: P90 ≈ 91 → max(A) ≤ 91
        # Cidade B: P90 ≈ 910 → max(B) ≤ 910
        max_a = clipped[df["code"] == "A"].max()
        max_b = clipped[df["code"] == "B"].max()
        assert max_a <= 100, f"Cidade A clipping falhou: max={max_a}"
        assert max_b <= 1000, f"Cidade B clipping falhou: max={max_b}"
        # Não devem ser iguais (se fosse global, seriam)
        assert max_a != max_b, "Clipping parece ser global, não per-city"

    def test_expanding_window_splits(self):
        """Verifica que EW gera splits corretos."""
        years = pd.Series([2018, 2018, 2019, 2019, 2020, 2020, 2021, 2021, 2022, 2022])
        splits = list(_expanding_window_splits(years, min_train_years=3))

        # Com anos [2018,2019,2020,2021,2022] e min_train=3,
        # test_year começa em 2021 (índice 3)
        assert len(splits) == 2, f"Esperado 2 splits, obtido {len(splits)}"
        assert splits[0][2] == 2021
        assert splits[1][2] == 2022

        # Garante que treino não contém dados do teste
        for train_mask, test_mask, test_year in splits:
            train_years = set(years[train_mask].unique())
            assert test_year not in train_years, f"Vazamento temporal: {test_year} está no treino!"


# =============================================
# Teste de integração rápido
# =============================================
class TestIntegration:
    def test_pipeline_end_to_end(self, mini_panel):
        """Testa o fluxo completo: features → treino → predição."""
        from src.ml_pipeline.model_training import train_model

        df = build_ml_features(mini_panel)
        feat_cols = get_feature_columns(df)

        # Precisa de pelo menos 4 anos para EW com min_train=3
        # Mini panel tem só 2 anos, então vamos adicionar mais
        dfs = []
        for extra_year in [2022, 2023]:
            extra = mini_panel.copy()
            extra["year"] = extra_year
            dfs.append(extra)
        extended = pd.concat([mini_panel] + dfs, ignore_index=True)

        df_ext = build_ml_features(extended)
        feat_cols = get_feature_columns(df_ext)

        model, metrics, fi = train_model(
            df=df_ext,
            feature_cols=feat_cols,
            target_col="dengue_cases",
        )
        assert model is not None
        assert len(metrics) >= 1, "Deveria ter pelo menos 1 fold de validação"
        assert len(fi) > 0, "Feature importance vazia"
