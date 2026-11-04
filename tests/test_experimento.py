"""
Testes do experimento final (Fases 1–3): métricas, ausência de vazamento e travas do holdout.
Usa só dados sintéticos (fixture mini_panel, anos 2018–2023).
"""
import json
import re

import numpy as np
import pandas as pd
import pytest

from src.ml_pipeline.feature_engineering import build_ml_features, get_feature_columns, is_climate_feature
from src.ml_pipeline.metricas import avaliar_criterios, calcular_metricas
from src.ml_pipeline.model_training import (
    _expanding_window_splits, alvo_treino, limiares_por_cidade,
)


class TestMetricas:
    def test_previsao_perfeita(self):
        y = np.array([0, 1, 5, 10, 50, 100, 3, 0], float)
        m = calcular_metricas(y, y, np.roll(y, 1), np.full(len(y), 20.0), np.full(len(y), 4.0))
        assert m["mae"] == 0 and m["r2"] == 1
        assert m["skill_score"] == 1
        assert m["auc_risco_alto"] == 1
        assert m["n_surto"] == 2 and m["mae_surto"] == 0

    def test_skill_zero_para_a_propria_persistencia(self):
        y = np.array([1, 2, 3, 4, 5], float)
        p = np.array([0, 1, 2, 3, 4], float)
        m = calcular_metricas(y, p, p, np.full(5, 3.0), np.full(5, 2.0))
        assert m["skill_score"] == 0
        assert not avaliar_criterios(m, "dengue")["ok_skill"]

    def test_criterio_r2_so_vale_para_dengue(self):
        m = {"mae": 1, "mae_persistencia": 2, "mae_surto": 1, "pico_medio_surto": 10,
             "skill_score": 0.5, "auc_risco_alto": 0.9, "r2": 0.1}
        assert not avaliar_criterios(m, "dengue")["ok_r2"]
        assert avaliar_criterios(m, "chikungunya")["passa_todos"]


class TestSemVazamento:
    def test_limiares_usam_so_o_treino(self):
        tr = pd.DataFrame({"code": ["A"] * 4, "y": [0, 0, 10, 10]})
        lim = limiares_por_cidade(tr, pd.Series(["A", "B"]), "y", 0.5)
        assert lim[0] == 5.0
        assert lim[1] == 5.0   # cidade sem treino → quantil global do treino

    def test_corte_p99_calculado_no_treino(self):
        tr = pd.DataFrame({"code": ["A"] * 100, "y": list(range(100))})
        y = alvo_treino(tr, "y", 90)
        assert y.max() == pytest.approx(np.quantile(range(100), 0.9))
        assert (alvo_treino(tr, "y", None) == tr["y"].to_numpy()).all()

    def test_holdout_fora_dos_folds(self):
        years = pd.Series(range(2015, 2026)).repeat(2).reset_index(drop=True)
        anos = [a for _, _, a in _expanding_window_splits(years, 3, max_test_year=2024)]
        assert anos == list(range(2018, 2025))

    @pytest.mark.parametrize("h", [1, 2, 3])
    def test_features_respeitam_horizonte(self, mini_panel, h):
        df = build_ml_features(mini_panel, doenca="dengue", horizonte=h)
        feats = get_feature_columns(df, doenca="dengue")
        lags = [int(m.group(1)) for c in feats if (m := re.search(r"_lag(\d+)$", c))]
        assert min(lags) >= h, f"Feature com lag < h={h}"

    def test_sem_clima_remove_todas_as_climaticas(self, mini_panel):
        df = build_ml_features(mini_panel, doenca="dengue")
        com = get_feature_columns(df, doenca="dengue", usar_clima=True)
        sem = get_feature_columns(df, doenca="dengue", usar_clima=False)
        assert any(is_climate_feature(c) for c in com)
        assert not any(is_climate_feature(c) for c in sem)
        assert set(sem) < set(com)
        assert "dengue_lag1" in sem and "month_sin" in sem


class TestExperimentoPontaAPonta:
    def test_fases_1_e_2(self, mini_panel, tmp_path):
        from src.ml_pipeline.analise_experimento import run_analise
        from src.ml_pipeline.experimento_horizontes import run_experimento
        from src.ml_pipeline.teste_final import run_teste_final

        res = run_experimento(doencas=("dengue",), horizontes=(1, 2), out_dir=tmp_path, panel=mini_panel)
        assert len(res) == 12   # (4 configs + 2 baselines) × 2 horizontes
        assert set(res["modelo"]) >= {"persistencia", "sazonal", "xgb_clima_p99", "xgb_semclima_semcorte"}

        # persistência em h=2 é o valor de 2 meses antes (não o do mês anterior)
        oof = pd.read_csv(tmp_path / "oof_dengue_h2.csv.gz", dtype={"code": str})
        cidade = mini_panel[mini_panel["code"] == "100001"].set_index(["year", "month"])["dengue_cases"]
        linha = oof[(oof["code"] == "100001") & (oof["year"] == 2022) & (oof["month"] == 3)].iloc[0]
        assert linha["y_persistencia"] == cidade.loc[(2022, 1)]

        run_analise(out_dir=tmp_path, com_shap=False)
        cfg = json.loads((tmp_path / "config_escolhida.json").read_text(encoding="utf-8"))
        assert cfg["confirmado_pelo_usuario"] is False
        assert {"usar_clima", "corte_p99"} <= set(cfg["doencas"]["dengue"])
        assert (tmp_path / "analise.md").exists()

        # O teste final exige confirmação explícita
        with pytest.raises(PermissionError):
            run_teste_final(out_dir=tmp_path, panel=mini_panel)


class TestTravaHoldout:
    def test_trava_impede_reuso(self, tmp_path):
        from src.ml_pipeline.teste_final import LOCK_NAME, HoldoutJaUsado, run_teste_final

        (tmp_path / LOCK_NAME).write_text("2026-01-01", encoding="utf-8")
        with pytest.raises(HoldoutJaUsado):
            run_teste_final(out_dir=tmp_path, confirmar=True)
