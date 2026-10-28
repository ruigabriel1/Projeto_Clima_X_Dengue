"""
Testes unitários para o pipeline ML v4 (multi-doença).
Testa a feature engineering e o treino em dados sintéticos,
garantindo ausência de vazamento e corretude das features.
"""
import numpy as np
import pandas as pd
import pytest

from src.ml_pipeline.feature_engineering import (
    build_ml_features,
    get_feature_columns,
    DOENCA_PARA_COL,
    PREFIXOS,
)
from src.ml_pipeline.model_training import clip_outliers_per_city, _expanding_window_splits
from src.ml_pipeline.baselines import PersistenciaBaseline, NaiveSazonalBaseline


# =============================================
# Fixture: painel sintético mínimo (multi-doença)
# =============================================
@pytest.fixture
def mini_panel():
    """Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças."""
    np.random.seed(42)
    rows = []
    for code in ["100001", "200002"]:
        for y in [2018, 2019, 2020, 2021, 2022, 2023]:
            for m in range(1, 13):
                rows.append({
                    "code": code,
                    "year": y,
                    "month": m,
                    "dengue_cases": np.random.poisson(50),
                    "chik_cases": np.random.poisson(10),
                    "zika_cases": np.random.poisson(3),
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
# Testes de Feature Engineering (multi-doença)
# =============================================
class TestFeatureEngineering:
    def test_output_has_no_target_leakage(self, mini_panel):
        """Garante que colunas proibidas não aparecem nas features."""
        df = build_ml_features(mini_panel, doenca="dengue")
        feat_cols = get_feature_columns(df, doenca="dengue")
        proibidas = {"dengue_cases", "chik_cases", "zika_cases", "code", "year", "month"}
        assert proibidas.isdisjoint(set(feat_cols)), f"Vazamento detectado: {proibidas & set(feat_cols)}"

    def test_lag_is_strictly_past(self, mini_panel):
        """Verifica que dengue_lag1 corresponde ao valor do mês anterior."""
        df = build_ml_features(mini_panel, doenca="dengue")
        city = df[df["code"] == "100001"].sort_values(["year", "month"]).reset_index(drop=True)
        for i in range(1, len(city)):
            lag_val = city.loc[i, "dengue_lag1"]
            prev_cases = city.loc[i - 1, "dengue_cases"]
            assert lag_val == prev_cases, f"Lag1 errado na linha {i}: esperado {prev_cases}, obtido {lag_val}"

    def test_rolling_12_does_not_include_current_month(self, mini_panel):
        """O rolling de memória epidêmica NÃO deve incluir o mês corrente."""
        df1 = build_ml_features(mini_panel, doenca="dengue")

        panel_mod = mini_panel.copy()
        mask = (panel_mod["code"] == "100001") & (panel_mod["year"] == 2022) & (panel_mod["month"] == 6)
        panel_mod.loc[mask, "dengue_cases"] = 99999

        df2 = build_ml_features(panel_mod, doenca="dengue")

        r1 = df1[(df1["code"] == "100001") & (df1["year"] == 2022) & (df1["month"] == 6)]["dengue_rolling_12"].values
        r2 = df2[(df2["code"] == "100001") & (df2["year"] == 2022) & (df2["month"] == 6)]["dengue_rolling_12"].values

        if len(r1) > 0 and len(r2) > 0:
            assert abs(r1[0] - r2[0]) < 1e-6, (
                f"Rolling inclui mês corrente! r1={r1[0]:.2f} vs r2={r2[0]:.2f}"
            )

    def test_output_shape(self, mini_panel):
        """Verifica que o output tem features e menos linhas que o input (warm-up)."""
        df = build_ml_features(mini_panel, doenca="dengue")
        assert len(df) < len(mini_panel), "Deveria ter removido linhas de warm-up"
        assert len(df.columns) > len(mini_panel.columns), "Deveria ter adicionado features"

    def test_get_feature_columns_excludes_meta(self, mini_panel):
        """Verifica que get_feature_columns exclui colunas de identificação."""
        df = build_ml_features(mini_panel, doenca="dengue")
        feat_cols = get_feature_columns(df, doenca="dengue")
        meta = {"code", "city_name", "year", "month", "dengue_cases", "populacao", "latitude", "longitude"}
        for col in meta:
            assert col not in feat_cols, f"Coluna meta {col} apareceu nas features!"

    def test_forecast_mode_excludes_current_month(self, mini_panel):
        """No modo forecast, nenhuma variável do mês-alvo pode ser feature."""
        df = build_ml_features(mini_panel, doenca="dengue")
        feat_fc = get_feature_columns(df, forecast=True, doenca="dengue")
        feat_all = get_feature_columns(df, forecast=False, doenca="dengue")
        for col in ["temp_media", "precipitacao", "umidmed", "enso", "receptivo_num"]:
            assert col not in feat_fc, f"{col} (mês corrente) vazou no modo forecast"
            assert col in feat_all
        assert "temp_lag1" in feat_fc and "enso_lag1" in feat_fc


# =============================================
# Testes Multi-Doença
# =============================================
class TestMultiDoenca:
    """Testa que o pipeline funciona para cada doença suportada."""

    @pytest.mark.parametrize("doenca", ["dengue", "chikungunya", "zika"])
    def test_build_features_per_disease(self, mini_panel, doenca):
        """build_ml_features roda sem erro para cada doença."""
        df = build_ml_features(mini_panel, doenca=doenca)
        target = DOENCA_PARA_COL[doenca]
        assert target in df.columns, f"Coluna-alvo {target} sumiu do DataFrame"
        assert len(df) > 0, f"DataFrame vazio para {doenca}"

    @pytest.mark.parametrize("doenca", ["dengue", "chikungunya", "zika"])
    def test_feature_cols_dont_include_other_target(self, mini_panel, doenca):
        """Features de uma doença NÃO devem incluir a coluna-alvo de outra."""
        df = build_ml_features(mini_panel, doenca=doenca)
        feat_cols = get_feature_columns(df, doenca=doenca)
        for nome, col in DOENCA_PARA_COL.items():
            assert col not in feat_cols, f"Coluna-alvo {col} ({nome}) vazou nas features de {doenca}"

    def test_chik_lag_exists(self, mini_panel):
        """Verifica que os lags de chikungunya são criados quando solicitado."""
        df = build_ml_features(mini_panel, doenca="chikungunya")
        assert "chik_lag1" in df.columns, "chik_lag1 não foi criado"
        assert "chik_rolling_3" in df.columns, "chik_rolling_3 não foi criado"

    def test_baselines_use_correct_lag(self, mini_panel):
        """Os baselines de persistência usam o lag da doença correta."""
        df = build_ml_features(mini_panel, doenca="chikungunya")

        persist = PersistenciaBaseline(target_col="chik_cases")
        assert persist.lag_col == "chik_lag1"

        sazonal = NaiveSazonalBaseline(target_col="chik_cases")
        assert sazonal.lag_col == "chik_lag12"


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
        max_a = clipped[df["code"] == "A"].max()
        max_b = clipped[df["code"] == "B"].max()
        assert max_a <= 100, f"Cidade A clipping falhou: max={max_a}"
        assert max_b <= 1000, f"Cidade B clipping falhou: max={max_b}"
        assert max_a != max_b, "Clipping parece ser global, não per-city"

    def test_expanding_window_splits(self):
        """Verifica que EW gera splits corretos."""
        years = pd.Series([2018, 2018, 2019, 2019, 2020, 2020, 2021, 2021, 2022, 2022])
        splits = list(_expanding_window_splits(years, min_train_years=3))

        assert len(splits) == 2, f"Esperado 2 splits, obtido {len(splits)}"
        assert splits[0][2] == 2021
        assert splits[1][2] == 2022

        for train_mask, test_mask, test_year in splits:
            train_years = set(years[train_mask].unique())
            assert test_year not in train_years, f"Vazamento temporal: {test_year} está no treino!"


# =============================================
# Teste de integração rápido (multi-doença)
# =============================================
class TestIntegration:
    @pytest.mark.parametrize("doenca", ["dengue", "chikungunya"])
    def test_pipeline_end_to_end(self, mini_panel, doenca):
        """Testa o fluxo completo: features → treino → predição, por doença."""
        from src.ml_pipeline.model_training import train_model

        target_col = DOENCA_PARA_COL[doenca]

        df = build_ml_features(mini_panel, doenca=doenca)
        feat_cols = get_feature_columns(df, doenca=doenca)

        # Mini panel tem 4 anos → deve gerar pelo menos 1 fold EW (min_train=3)
        df_train = df.dropna(subset=feat_cols + [target_col]).copy()

        model, metrics, fi = train_model(
            df=df_train,
            feature_cols=feat_cols,
            target_col=target_col,
        )
        assert model is not None, f"Modelo não treinado para {doenca}"
        assert len(metrics) >= 1, f"Deveria ter pelo menos 1 fold para {doenca}"
        assert len(fi) > 0, f"Feature importance vazia para {doenca}"
