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


class TestFeaturesV5:
    def test_alerta_infodengue_nunca_e_feature(self, mini_panel):
        p = mini_panel.assign(NIVEL_DENGUE=1.0, NIVEL_CHIKUNGUNYA=2.0, NIVEL_ZIKA=1.0)
        df = build_ml_features(p, doenca="dengue")
        for kw in ({}, {"clima": "parcimonioso", "suscetibilidade": True}):
            assert not any(c.startswith("NIVEL_") for c in get_feature_columns(df, doenca="dengue", **kw))

    def test_coluna_auxiliar_derivada_do_alvo_nunca_e_feature(self, mini_panel):
        # Regressão do bug da 1ª execução do teste de 2026: _incid (alvo / pop) entrou como feature
        df = build_ml_features(mini_panel, doenca="dengue").assign(_incid=lambda x: x["dengue_cases"] / x["populacao"])
        for kw in ({}, {"clima": "parcimonioso", "suscetibilidade": True}):
            assert not any(c.startswith("_") for c in get_feature_columns(df, doenca="dengue", **kw))

    @pytest.mark.parametrize("h", [1, 3])
    def test_suscetibilidade_usa_so_ate_t_menos_h(self, mini_panel, h):
        df = build_ml_features(mini_panel, doenca="dengue", horizonte=h)
        c = df[df["code"] == "100001"].sort_values(["year", "month"]).reset_index(drop=True)
        base = mini_panel[mini_panel["code"] == "100001"].sort_values(["year", "month"]).reset_index(drop=True)
        incid = base["dengue_cases"] / base["populacao"] * 1e5
        linha = c.iloc[-1]                                     # último mês (dez/2023)
        pos = len(base) - 1
        esperado = incid.iloc[pos - h - 11: pos - h + 1].sum()  # 12 meses terminando em t−h
        assert linha[f"dengue_susc_acum12_lag{h}"] == pytest.approx(esperado)

    def test_meses_desde_surto(self):
        from src.ml_pipeline.feature_engineering import LIMIAR_SURTO_100K
        rows = []
        for i in range(24):
            casos = 200 if i == 5 else 1          # surto só no mês 6 (incidência 200/100 mil)
            rows.append({"code": "A", "year": 2020 + i // 12, "month": i % 12 + 1, "dengue_cases": casos,
                         "chik_cases": 0, "populacao": 100_000})
        df = build_ml_features(pd.DataFrame(rows), doenca="dengue", horizonte=2)
        x = df.set_index(["year", "month"])["dengue_susc_meses_desde_surto_lag2"]
        assert LIMIAR_SURTO_100K < 200
        assert np.isnan(x.loc[(2020, 7)])          # em jul, o último mês conhecido (mai) é antes do surto
        assert x.loc[(2020, 8)] == 2               # em ago, o surto de jun é conhecido: 2 meses atrás
        assert x.loc[(2021, 6)] == 12

    def test_grupos_v5(self, mini_panel):
        from src.ml_pipeline.feature_engineering import grupos_de_features
        g = grupos_de_features(build_ml_features(mini_panel, doenca="dengue"), "dengue")
        assert sorted(g["clima_parcimonioso"]) == sorted(
            [f"temp_lag{k}" for k in (1, 2, 3)] + [f"prec_lag{k}" for k in (1, 2, 3)])
        assert len(g["suscetibilidade"]) == 4
        assert not any("enso" in c or "receptivo" in c for c in sum(g.values(), []))


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


class TestExperimentoV5:
    def test_ponta_a_ponta_sem_2026(self, mini_panel, tmp_path):
        from src.ml_pipeline import experimento_v5 as v5

        ano_2026 = mini_panel[mini_panel["year"] == 2023].assign(year=2026, dengue_cases=10_000)
        panel = pd.concat([mini_panel, ano_2026], ignore_index=True)
        res, ef, dec = v5.run(panel=panel, out_dir=tmp_path, doencas=("dengue",), horizontes=(1, 2))

        for h in (1, 2):
            oof = pd.read_csv(tmp_path / f"oof_dengue_h{h}.csv.gz")
            assert oof["year"].max() <= 2025          # 2026 nunca entra
            assert oof["y_true"].max() < 10_000
        assert set(res["modelo"]) == {"semclima_semsusc", "clima_semsusc", "semclima_susc", "clima_susc", "persistencia"}
        assert {"auc", "brier_skill", "mae_incid_mediana_cidades", "skill"} <= set(res.columns)
        assert len(ef) == 4 and set(ef["grupo"]) == {"clima", "suscetibilidade"}
        assert dec["dengue"]["modelo"] in set(res["modelo"])

    def test_calibracao_so_usa_anos_anteriores(self):
        from src.ml_pipeline.experimento_v5 import calibrar_temporal
        oof = pd.DataFrame({"year": [2020] * 4 + [2021] * 4, "escore": [0, 1, 2, 3] * 2,
                            "risco_alto": [0, 0, 1, 1, 1, 1, 0, 0]})
        p = calibrar_temporal(oof, "escore")
        assert p[oof.year == 2020].isna().all()                 # 1º ano: sem passado para calibrar
        assert list(p[oof.year == 2021]) == [0, 0, 1, 1]        # aprendeu só com 2020


class TestCombinacao:
    def test_peso_escolhe_o_melhor_previsor(self):
        from src.ml_pipeline.combinacao import combinar, escolher_peso
        y = np.array([10, 20, 30, 40.0])
        assert escolher_peso(y, y, y * 0) == 1.0                    # modelo perfeito → só modelo
        assert escolher_peso(y, y * 0, y) == 0.0                    # persistência perfeita → só persistência
        assert list(combinar([10, 10], [np.nan, 20], 0.5)) == [5.0, 15.0]   # persistência ausente = 0

    def test_peso_do_ano_so_usa_anos_anteriores(self):
        from src.ml_pipeline.combinacao import pesos_cross_fit
        y = np.array([10.0, 20.0])
        # 2018–2019: persistência perfeita; 2020: modelo perfeito (não pode influenciar o peso de 2020)
        oof = pd.DataFrame({
            "year": [2018, 2018, 2019, 2019, 2020, 2020],
            "y_true": np.tile(y, 3),
            "pred": np.concatenate([y * 0, y * 0, y]),
            "y_persistencia": np.concatenate([y, y, y * 0]),
        })
        p = pesos_cross_fit(oof, "pred")
        assert p[2018] == 1.0          # sem passado: modelo puro
        assert p[2019] == 0.0 and p[2020] == 0.0


@pytest.fixture
def painel_grade():
    """12 cidades numa grade de coordenadas × 4 anos (para os vizinhos do protocolo v6)."""
    rng = np.random.default_rng(0)
    linhas = []
    for i in range(12):
        code = f"4{i // 4 + 1}{i:04d}"           # UFs 41, 42, 43
        for y in range(2016, 2020):
            for m in range(1, 13):
                linhas.append({"code": code, "year": y, "month": m, "dengue_cases": int(rng.poisson(20 + 5 * i)),
                               "chik_cases": int(rng.poisson(3)), "populacao": 10_000 * (i + 1),
                               "latitude": -25.0 - (i % 4), "longitude": -50.0 - (i // 4), "temp_media": 20.0,
                               "precipitacao": 100.0})
    return pd.DataFrame(linhas)


class TestFeaturesV6:
    @pytest.mark.parametrize("h", [1, 3])
    def test_vizinhos_e_imunidade_nao_usam_o_futuro(self, painel_grade, h):
        df = build_ml_features(painel_grade, doenca="dengue", horizonte=h)
        alterado = painel_grade.copy()
        alvo_t = (alterado.year == 2019) & (alterado.month == 6)
        alterado.loc[alvo_t, "dengue_cases"] += 10_000               # muda o mês t de TODAS as cidades
        df2 = build_ml_features(alterado, doenca="dengue", horizonte=h)
        cols = [c for c in df.columns if "_viz_" in c or "_imun_" in c]
        assert len(cols) == 5
        linha = (df.year == 2019) & (df.month == 6)
        pd.testing.assert_frame_equal(df.loc[linha, cols].reset_index(drop=True), df2.loc[linha, cols].reset_index(drop=True))

    def test_vizinhos_agregam_as_8_mais_proximas(self, painel_grade):
        df = build_ml_features(painel_grade, doenca="dengue", horizonte=1)
        c0 = painel_grade.code.iloc[0]
        coords = painel_grade.groupby("code")[["latitude", "longitude"]].first()
        lat, lon = np.radians(coords["latitude"]), np.radians(coords["longitude"])
        a = (np.sin((lat - lat[c0]) / 2) ** 2 + np.cos(lat) * np.cos(lat[c0]) * np.sin((lon - lon[c0]) / 2) ** 2)
        viz = a.drop(c0).sort_values(kind="stable").index[:8]
        mes = painel_grade[(painel_grade.year == 2018) & (painel_grade.month == 5) & painel_grade.code.isin(viz)]
        esperado = mes.dengue_cases.sum() / mes.populacao.sum() * 1e5
        obtido = df[(df.code == c0) & (df.year == 2018) & (df.month == 6)]["dengue_viz_incid_lag1"].iloc[0]
        assert obtido == pytest.approx(esperado)

    def test_novas_features_desligadas_por_padrao(self, painel_grade):
        df = build_ml_features(painel_grade, doenca="dengue", horizonte=1)
        padrao = get_feature_columns(df, doenca="dengue", clima="parcimonioso", suscetibilidade=True)
        assert not any("_viz_" in c or "_imun_" in c for c in padrao)
        com = get_feature_columns(df, doenca="dengue", clima="parcimonioso", suscetibilidade=True,
                                  vizinhos=True, imunidade_longa=True)
        assert set(com) - set(padrao) == {c for c in df.columns if "_viz_" in c or "_imun_" in c}


class TestExperimentoV6:
    def test_offset_de_persistencia(self):
        from src.ml_pipeline.model_training import fit_predict_fold, margem_persistencia
        df = pd.DataFrame({"x": np.arange(200.0), "y": np.arange(200) % 7, "lag": [np.nan, 0.0, 4.0, 9.0] * 50,
                           "populacao": 1000})
        assert list(margem_persistencia(df.head(4), "lag")) == pytest.approx(np.log([1, 1, 5, 10]))
        _, pred = fit_predict_fold(df, df, ["x"], "y", offset_persistencia="lag")
        assert (pred >= 0).all() and len(pred) == 200

    def test_regra_sequencial(self):
        from src.ml_pipeline.experimento_v6 import decidir

        def ef(passos_sim):
            linhas = []
            for passo in ("A_vs_B0", "V_vs_B0", "L_vs_B0", "V_vs_A", "L_vs_A"):
                for h in (1, 2, 3):
                    linhas.append({"passo": passo, "horizonte": h, "reduz_erro": passo in passos_sim and h <= 2})
            return pd.DataFrame(linhas)
        assert decidir({"dengue": ef({"A_vs_B0", "V_vs_A"})})["dengue"]["modelo"] == "A_V"
        assert decidir({"dengue": ef({"V_vs_A", "L_vs_B0"})})["dengue"]["modelo"] == "B0_L"   # V só valeria sobre A
        d = decidir({"dengue": ef(set())})["dengue"]
        assert d["modelo"] == "B0" and d["offset"] == "pop"

    def test_ponta_a_ponta(self, mini_panel, tmp_path):
        from src.ml_pipeline import experimento_v6 as v6
        base = {"dengue": {"clima": "parcimonioso", "suscetibilidade": True}}
        res, ef, dec = v6.run(panel=mini_panel, out_dir=tmp_path, doencas=("dengue",), horizontes=(1, 2),
                              base=base, exigir_registro=False)
        assert set(res["modelo"]) == {*v6.VARIANTES, "persistencia"}
        assert set(ef["passo"]) == {"A_vs_B0", "V_vs_B0", "L_vs_B0", "V_vs_A", "L_vs_A"}
        assert dec["dengue"]["formulacao"] in ("A", "B0")
        oof = pd.read_csv(tmp_path / "oof_dengue_h1.csv.gz")
        assert oof["year"].min() >= v6.ANO_MIN_TESTE
        assert json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))["protocolo_commit"] is None

    def test_producao_e_preditor_com_offset_de_persistencia(self, mini_panel, tmp_path):
        from src.ml_pipeline import experimento_v6 as v6
        from src.prediction_service.data_fetcher import FonteDados
        from src.prediction_service.predictor import Preditor
        panel = mini_panel.assign(city_name="X")
        base = {"dengue": {"clima": "parcimonioso", "suscetibilidade": True}}
        v6.run(panel=panel, out_dir=tmp_path / "exp", doencas=("dengue",), horizontes=(1,), base=base,
               exigir_registro=False)
        (tmp_path / "exp" / "decisao.json").write_text(json.dumps({"dengue": {
            "formulacao": "A", "offset": "persistencia", "vizinhos": False, "imunidade_longa": True,
            "modelo": "A_L"}}), encoding="utf-8")
        meta = v6.treinar_producao(panel, exp_dir=tmp_path / "exp", out_dir=tmp_path / "mod", horizontes=(1,), base=base)
        assert meta["dengue"]["offset"] == "persistencia" and meta["dengue"]["horizontes"]["h1"]["calibracao_de"] == "A_L"
        lote = Preditor(model_dir=tmp_path / "mod", fonte=FonteDados(panel)).prever_lote("dengue", 1)
        assert len(lote) == 2 and (lote["casos_previstos"] >= 0).all()


class TestMonitoramentoPorModelo:
    def test_modelos_separados_e_registro_antigo(self, tmp_path):
        from src.prediction_service.monitoramento import avaliar, registrar
        arq = tmp_path / "p.csv"
        pd.DataFrame({"codigo_ibge": ["100001"], "mes_alvo": ["2024-01"], "casos_previstos": [5], "ic_lo": [0],
                      "ic_hi": [9], "probabilidade_risco_alto": [0.2], "casos_persistencia": [4.0],
                      "doenca": ["dengue"], "horizonte": [1], "emitido_em": ["x"]}).to_csv(arq, index=False)  # sem "modelo"
        lote = pd.DataFrame({"codigo_ibge": ["100001"], "mes_alvo": ["2024-01"], "casos_previstos": [7], "ic_lo": [1],
                             "ic_hi": [12], "probabilidade_risco_alto": [0.3], "casos_persistencia": [4.0]})
        assert registrar(lote, "dengue", 1, arq, modelo="v5.1") == 0        # já emitida pela v5.1
        assert registrar(lote, "dengue", 1, arq, modelo="v6") == 1
        panel = pd.DataFrame({"code": ["100001"], "year": [2024], "month": [1], "dengue_cases": [6]})
        res = {r["modelo"]: r for r in avaliar(panel, arq)}
        assert res["v5.1"]["casos_previstos"] == 5 and res["v6"]["casos_previstos"] == 7


class TestTravaHoldout:
    def test_trava_impede_reuso(self, tmp_path):
        from src.ml_pipeline.teste_final import LOCK_NAME, HoldoutJaUsado, run_teste_final

        (tmp_path / LOCK_NAME).write_text("2026-01-01", encoding="utf-8")
        with pytest.raises(HoldoutJaUsado):
            run_teste_final(out_dir=tmp_path, confirmar=True)
