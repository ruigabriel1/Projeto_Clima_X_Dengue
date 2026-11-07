"""Protocolo v7: features de Rt, nível regional (GLM + reconciliação), sorotipo, regra dupla. Dados sintéticos."""
import json

import numpy as np
import pandas as pd
import pytest

from src.ml_pipeline import nivel_regional as nr
from src.ml_pipeline.feature_engineering import build_ml_features, get_feature_columns


@pytest.fixture
def painel_v7():
    """9 cidades (3 por UF) × 2010–2020, sazonal, com Rt; chikungunya só a partir de 2015."""
    rng = np.random.default_rng(1)
    linhas = []
    for i in range(9):
        code = f"4{i // 3 + 1}{i:04d}"
        for y in range(2010, 2021):
            for m in range(1, 13):
                lam = (10 + 3 * i) * (1 + 0.8 * np.sin(2 * np.pi * (m - 1) / 12)) * (2.0 if y in (2013, 2016, 2019) else 1.0)
                linhas.append({"code": code, "year": y, "month": m, "dengue_cases": float(rng.poisson(lam)),
                               "chik_cases": float(rng.poisson(2)) if y >= 2015 else np.nan,
                               "populacao": 10_000 * (i + 1), "city_name": f"C{i}", "latitude": -25.0 - i % 3,
                               "longitude": -50.0 - i // 3, "temp_media": 20.0 + 5 * np.sin(m), "precipitacao": 100.0,
                               "dengue_rt_medio": 0.8 + 0.4 * rng.random(), "dengue_rt_ult": 1.0,
                               "dengue_prt1": rng.random(), "chik_rt_medio": 1.0, "chik_rt_ult": 1.0, "chik_prt1": 0.5})
    return pd.DataFrame(linhas)


@pytest.fixture
def sorotipo_sint():
    linhas = []
    for uf in nr.UFS:
        for y in range(2010, 2026):          # o portão olha 2015–2025
            for m in range(1, 13):
                dom = 1 if y < 2016 else 2                     # troca de sorotipo dominante em 2016
                linhas.append({"UF": uf, "ANO": y, "MES": m, "n_denv1": 20 if dom == 1 else 2,
                               "n_denv2": 2 if dom == 1 else 20, "n_denv3": 0, "n_denv4": 0})
    s = pd.DataFrame(linhas)
    return s.assign(n_testados=s[["n_denv1", "n_denv2", "n_denv3", "n_denv4"]].sum(axis=1))


class TestRt:
    @pytest.mark.parametrize("h", [1, 3])
    def test_rt_defasado_sem_vazamento(self, painel_v7, h):
        df = build_ml_features(painel_v7, doenca="dengue", horizonte=h)
        alt = painel_v7.copy()
        mes = (alt.year == 2018) & (alt.month == 6)
        alt.loc[mes, ["dengue_rt_medio", "dengue_rt_ult", "dengue_prt1"]] = 99.0
        df2 = build_ml_features(alt, doenca="dengue", horizonte=h)
        cols = [f"dengue_rt_medio_lag{h}", f"dengue_rt_ult_lag{h}", f"dengue_prt1_lag{h}", f"dengue_rt_uf_lag{h}"]
        linha = (df.year == 2018) & (df.month == 6)
        pd.testing.assert_frame_equal(df.loc[linha, cols].reset_index(drop=True), df2.loc[linha, cols].reset_index(drop=True))
        # o valor de t−h é o Rt do mês t−h
        c0 = painel_v7.code.iloc[0]
        t = pd.Timestamp(2018, 6, 1) - pd.DateOffset(months=h)
        esperado = painel_v7[(painel_v7.code == c0) & (painel_v7.year == t.year) & (painel_v7.month == t.month)]["dengue_rt_medio"].item()
        assert df[(df.code == c0) & linha][f"dengue_rt_medio_lag{h}"].item() == pytest.approx(esperado)

    def test_rt_uf_ponderado_pela_populacao(self, painel_v7):
        df = build_ml_features(painel_v7, doenca="dengue", horizonte=1)
        m = painel_v7[(painel_v7.year == 2017) & (painel_v7.month == 4) & painel_v7.code.str.startswith("42")]
        esperado = (m.dengue_rt_medio * m.populacao).sum() / m.populacao.sum()
        obtido = df[(df.year == 2017) & (df.month == 5) & df.code.str.startswith("42")]["dengue_rt_uf_lag1"]
        assert obtido.round(10).nunique() == 1 and obtido.iloc[0] == pytest.approx(esperado)

    def test_rt_fora_por_padrao_e_bruto_nunca(self, painel_v7):
        df = build_ml_features(painel_v7, doenca="dengue", horizonte=1)
        padrao = get_feature_columns(df, doenca="dengue", clima="parcimonioso", suscetibilidade=True)
        com = get_feature_columns(df, doenca="dengue", clima="parcimonioso", suscetibilidade=True, rt=True)
        assert not [c for c in padrao if "rt_" in c or "prt1" in c]
        assert set(com) - set(padrao) == {"dengue_rt_medio_lag1", "dengue_rt_ult_lag1", "dengue_prt1_lag1", "dengue_rt_uf_lag1"}
        assert not {"dengue_rt_medio", "dengue_rt_ult", "dengue_prt1", "chik_rt_medio"} & set(com)


class TestNivelRegional:
    def test_glm_recupera_coeficiente_conhecido(self):
        rng = np.random.default_rng(3)
        linhas = []
        for j, uf in enumerate(nr.UFS):
            T = 100.0
            for t in range(24_000, 24_000 + 120):
                m = t % 12 + 1
                mu = 1e6 / 1e5 * np.exp(1.0 + 0.2 * j + 0.5 * np.sin(2 * np.pi * m / 12) + 0.6 * np.log(T + 1) - 0.1)
                T = float(rng.poisson(mu))
                linhas.append({"uf": uf, "t": t, "T": T, "pop": 1e6, "rt_uf": 1.0})
        s = pd.DataFrame(linhas)
        s["rt_uf"] += rng.normal(0, 0.05, len(s))
        s["year"], s["month"] = s.t // 12, s.t % 12 + 1
        des = nr.desenho(s, 1)
        mod = nr.ajustar(des, np.ones(len(des), bool))
        coef = dict(zip(mod["nomes"], mod["coef"]))
        assert coef["x_logT"] == pytest.approx(0.6, abs=0.1)
        assert coef["s1"] == pytest.approx(0.5, abs=0.15)
        prev = nr.prever(mod, des)
        assert np.isnan(prev[des["x_logT"].isna().to_numpy()]).all()

    def test_poucos_meses_nao_reconcilia(self):
        s = pd.DataFrame({"uf": "PR", "t": range(10), "T": 5.0, "pop": 1e5, "rt_uf": 1.0})
        s["year"], s["month"] = 2020, s.t + 1
        assert nr.ajustar(nr.desenho(s, 1), np.ones(10, bool)) is None
        assert np.isnan(nr.prever(None, nr.desenho(s, 1))).all()

    def test_reconciliar_fecha_o_total_e_preserva_proporcoes(self):
        c = pd.DataFrame({"code": ["410001", "410002", "420001", "430001"], "year": 2020, "month": 3,
                          "pred": [10.0, 30.0, 5.0, 0.0]})
        tot = pd.DataFrame({"uf": ["PR", "SC", "RS"], "year": 2020, "month": 3, "T_hat": [80.0, np.nan, 7.0]})
        p, f = nr.reconciliar(c, tot)
        assert p[:2].sum() == pytest.approx(80.0) and p[1] / p[0] == pytest.approx(3.0)
        assert p[2] == 5.0 and f[2] == 1.0          # sem T̂: fator 1
        assert p[3] == 0.0 and f[3] == 1.0          # soma 0: fator 1

    def test_novidade_do_sorotipo(self, sorotipo_sint):
        nov = nr.novidade_sorotipo(sorotipo_sint, h=1)
        pr = nov[nov.uf == "PR"].set_index("t")["novidade"]
        t = lambda y, m: y * 12 + m - 1          # noqa: E731
        assert pr[t(2015, 6)] == pytest.approx(1 - (20 * 20 + 2 * 2) / 22 ** 2)   # mesmo sorotipo: baixa
        assert pr[t(2016, 4)] > 0.8                                                # logo após a troca: alta
        assert t(2010, 3) not in pr.index or np.isnan(pr[t(2010, 3)])             # sem 36 meses anteriores


class TestExperimentoV7:
    def test_portao(self, sorotipo_sint):
        from src.ml_pipeline.experimento_v7 import portao_sorotipo
        assert portao_sorotipo(sorotipo_sint)["passa"]
        pouco = sorotipo_sint.assign(n_testados=sorotipo_sint.n_testados.where(sorotipo_sint.MES == 1, 0))
        assert not portao_sorotipo(pouco)["passa"]
        assert not portao_sorotipo(None)["passa"]

    def test_regra_dupla(self):
        from src.ml_pipeline.experimento_v7 import decidir

        def ef(sim, auc=0.0):
            linhas = []
            for passo in ("H_vs_F", "R_vs_F", "R_vs_F_H", "N_vs_F", "N_vs_F_R", "N_vs_F_H", "N_vs_F_HR"):
                for h in (1, 2, 3):
                    linhas.append({"passo": passo, "horizonte": h, "reduz_erro": passo in sim and h <= 2,
                                   "delta_auc": auc if passo in sim else 0.0})
            return pd.DataFrame(linhas)
        base = {"dengue": {"offset": "persistencia"}}
        d = decidir({"dengue": ef({"H_vs_F", "R_vs_F_H", "N_vs_F_HR"})}, base, {})["dengue"]
        assert d["modelo"] == "F_HR_N" and d["ano_min"] == 2010
        assert decidir({"dengue": ef({"R_vs_F", "N_vs_F_R"})}, base, {})["dengue"]["modelo"] == "F_R_N"
        # reduz o erro mas derruba a AUC em mais de 0,01: não entra
        assert decidir({"dengue": ef({"H_vs_F"}, auc=-0.02)}, base, {})["dengue"]["modelo"] == "F"

    def test_ponta_a_ponta(self, painel_v7, sorotipo_sint, tmp_path):
        from src.ml_pipeline import experimento_v7 as v7
        paineis = {"2015": painel_v7[painel_v7.year >= 2015].reset_index(drop=True), "2010": painel_v7}
        base = {"dengue": {"clima": "parcimonioso", "suscetibilidade": True, "offset": "persistencia"},
                "chikungunya": {"clima": "nenhum", "suscetibilidade": True, "offset": "pop"}}
        res, ef, dec = v7.run(paineis_=paineis, out_dir=tmp_path, doencas=("dengue", "chikungunya"), horizontes=(1, 2),
                              base=base, sorotipo=sorotipo_sint, exigir_registro=False, docs_dir=None)
        assert json.loads((tmp_path / "portao_sorotipo.json").read_text(encoding="utf-8"))["passa"]
        assert {"F", "F_R", "F_H", "F_HR", "F_N", "F_HR_NS", "F_teto", "persistencia"} <= set(res[res.doenca == "dengue"].modelo)
        assert not {"F_H", "F_NS"} & set(res[res.doenca == "chikungunya"].modelo)
        assert {"H_vs_F", "S_vs_F_N", "N_vs_F_HR"} <= set(ef[ef.doenca == "dengue"].passo)
        oof = pd.read_csv(tmp_path / "oof_dengue_h1.csv.gz", dtype={"code": str})
        assert oof["year"].min() >= v7.ANO_MIN_TESTE
        # o teto fecha o total real de cada UF × mês; a variante N muda o nível, não a ordem dentro da UF
        uf = oof.code.str[:2]
        g = oof.groupby([uf, oof.year, oof.month])
        assert np.allclose(g["pred_F_teto"].sum(), g["y_true"].sum())
        x = oof[(uf == "41") & (oof.year == 2019) & (oof.month == 3)]
        assert (x["pred_F_N"].rank().values == x["pred_F"].rank().values).all()
        assert set(dec) == {"dengue", "chikungunya"} and not dec["chikungunya"]["historico_2010"]

    def test_producao_com_nivel_regional_e_preditor(self, painel_v7, tmp_path):
        from src.ml_pipeline import experimento_v7 as v7
        from src.ml_pipeline import nivel_regional as nr2
        from src.prediction_service.data_fetcher import FonteDados
        from src.prediction_service.predictor import Preditor
        paineis = {"2015": painel_v7[painel_v7.year >= 2015].reset_index(drop=True), "2010": painel_v7}
        base = {"dengue": {"clima": "parcimonioso", "suscetibilidade": True, "offset": "persistencia"}}
        exp = tmp_path / "exp"
        v7.run(paineis_=paineis, out_dir=exp, doencas=("dengue",), horizontes=(1, 2), base=base,
               exigir_registro=False, docs_dir=None)
        dec = {"dengue": {"historico_2010": True, "rt": True, "nivel_regional": True, "sorotipo": False,
                          "offset": "persistencia", "ano_min": 2010, "cidade": "F_HR", "modelo": "F_HR_N"}}
        (exp / "decisao.json").write_text(json.dumps(dec), encoding="utf-8")
        meta = v7.treinar_producao(paineis_=paineis, exp_dir=exp, out_dir=tmp_path / "mod", horizontes=(1, 2), base=base)
        hm = meta["dengue"]["horizontes"]["h2"]
        assert meta["dengue"]["versao"] == "v7" and hm["nivel_regional"]["nomes"][-1] == "x_acum24"
        assert any("rt_" in f for f in hm["features"])
        p = Preditor(model_dir=tmp_path / "mod", fonte=FonteDados(paineis["2015"]))
        lote = p.prever_lote("dengue", 2)
        tot = nr2.total_previsto(hm["nivel_regional"], nr2.serie_uf(paineis["2015"], "dengue"), 2)
        assert lote["mes_alvo"].iloc[0] == "2021-02"
        soma = lote.groupby("uf")["casos_previstos"].sum()
        for uf, t in tot.set_index("uf")["T_hat"].items():
            assert abs(soma[uf] - t) <= 3                                   # arredondamento por cidade
        um = p.prever("410000", "dengue", 2)
        assert um.casos_previstos == int(lote.set_index("codigo_ibge").loc["410000", "casos_previstos"])
