"""
Testes do serviço de previsão v5 (alerta de risco): schemas, níveis, intervalo, preditor, API,
e o teste prospectivo (travas). Modelos treinados em dados sintéticos num diretório temporário.
"""
import json

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from src.ml_pipeline.alerta_risco import nivel_por_probabilidade
from src.prediction_service.predictor import (
    CidadeNaoEncontrada, ModeloIndisponivel, Preditor, aplicar_intervalo,
)
from src.prediction_service.schemas import PredictRequest


class TestSchemas:
    def test_codigo_7_digitos_vira_6(self):
        assert PredictRequest(codigo_ibge="4106902", doenca="dengue", meses_a_frente=2).codigo_ibge == "410690"

    @pytest.mark.parametrize("payload", [
        {"codigo_ibge": "41069", "doenca": "dengue", "meses_a_frente": 1},
        {"codigo_ibge": "410690", "doenca": "dengue", "meses_a_frente": 4},
        {"codigo_ibge": "410690", "doenca": "malaria", "meses_a_frente": 1},
        {"codigo_ibge": "41069x", "doenca": "dengue", "meses_a_frente": 1},
    ])
    def test_entradas_invalidas(self, payload):
        with pytest.raises(ValidationError):
            PredictRequest(**payload)


class TestNiveis:
    @pytest.mark.parametrize("p,nivel", [(0.0, "baixo"), (0.24, "baixo"), (0.3, "medio"), (0.6, "alto"), (0.9, "critico"), (1.0, "critico")])
    def test_faixas(self, p, nivel):
        assert nivel_por_probabilidade(p) == nivel


class TestIntervalo:
    def test_contem_previsao_e_nao_negativo(self):
        calib = {"bordas_pred": [1.0, 10.0], "q_lo": [-1.0, -0.5, -0.4], "q_hi": [1.0, 0.6, 0.5]}
        for pred in (0.0, 3.0, 50.0):
            lo, hi = aplicar_intervalo(pred, calib)
            assert 0 <= lo <= round(pred) <= hi


@pytest.fixture
def artefatos(mini_panel, tmp_path):
    """Experimento v5 + modelos de risco no painel sintético (com clima e suscetibilidade forçados)."""
    from src.ml_pipeline import experimento_v5 as v5
    from src.ml_pipeline.alerta_risco import treinar_modelos_risco

    panel = mini_panel.copy()
    panel["city_name"] = panel["code"].map({"100001": "Cidade A", "200002": "Cidade B"})
    panel["NIVEL_DENGUE"] = 2.0
    exp = tmp_path / "exp"
    v5.run(panel=panel, out_dir=exp, doencas=("dengue",), horizontes=(1, 2))
    (exp / "decisao.json").write_text(json.dumps(
        {"dengue": {"clima": True, "suscetibilidade": True, "modelo": "clima_susc"}}), encoding="utf-8")
    modelos = tmp_path / "modelos"
    treinar_modelos_risco(panel, exp_dir=exp, out_dir=modelos, ano_max=2023, horizontes=(1, 2))
    return modelos, panel, exp


class TestPreditor:
    def test_previsao_de_risco(self, artefatos):
        from src.prediction_service.data_fetcher import FonteDados

        modelos, panel, _ = artefatos
        r = Preditor(model_dir=modelos, fonte=FonteDados(panel)).prever("100001", "dengue", 2)
        assert r.disponivel and r.cidade == "Cidade A"
        assert r.mes_alvo == "2024-02" and r.ultimo_mes_observado == "2023-12"
        assert 0.0 <= r.probabilidade_risco_alto <= 1.0
        assert r.nivel_risco == nivel_por_probabilidade(r.probabilidade_risco_alto)
        assert r.alerta_infodengue_ultimo == 2
        lo, hi = r.intervalo_confianca
        assert 0 <= lo <= r.casos_previstos <= hi
        assert r.modelo_usado == "clima_susc"
        assert "2026 ainda não executado" in r.nota

    def test_sem_clima_vira_aviso(self, artefatos):
        from src.prediction_service.data_fetcher import FonteDados

        modelos, panel, _ = artefatos
        p = panel.copy()
        p.loc[(p.year == 2023) & (p.month >= 9), ["temp_media", "precipitacao"]] = np.nan
        r = Preditor(model_dir=modelos, fonte=FonteDados(p)).prever("100001", "dengue", 1)
        assert r.confiabilidade == "baixa" and any("climáticos" in a for a in r.avisos)

    def test_zika_sem_previsao(self, artefatos):
        modelos, _, _ = artefatos
        r = Preditor(model_dir=modelos).prever("100001", "zika", 1)
        assert r.disponivel is False and r.probabilidade_risco_alto is None and "zika" in r.nota

    def test_cidade_fora_da_cobertura(self, artefatos):
        from src.prediction_service.data_fetcher import FonteDados

        modelos, panel, _ = artefatos
        with pytest.raises(CidadeNaoEncontrada):
            Preditor(model_dir=modelos, fonte=FonteDados(panel)).prever("355030", "dengue", 1)

    def test_modelo_ausente(self, tmp_path):
        with pytest.raises(ModeloIndisponivel):
            Preditor(model_dir=tmp_path).prever("100001", "chikungunya", 1)


def test_remove_meses_nao_consolidados():
    from src.prediction_service.data_fetcher import remover_meses_nao_consolidados
    p = pd.DataFrame({"year": [2026, 2026, 2025], "month": [9, 10, 12],
                      "INGERIDO_EM": ["2026-11-04T10:00:00", "2026-11-04T10:00:00", None]})
    out = remover_meses_nao_consolidados(p)
    assert list(zip(out.year, out.month)) == [(2026, 9), (2025, 12)]   # out/2026: só 4 dias após o fim


class TestAPI:
    def test_rota_predict(self, artefatos, monkeypatch):
        pytest.importorskip("httpx")
        from fastapi.testclient import TestClient

        import src.prediction_service.predictor as pred_mod
        from app.server import app
        from src.prediction_service.data_fetcher import FonteDados

        modelos, panel, _ = artefatos
        monkeypatch.setattr(pred_mod, "_PREDITOR", Preditor(model_dir=modelos, fonte=FonteDados(panel)))
        client = TestClient(app)
        r = client.post("/api/predict", json={"codigo_ibge": "100001", "doenca": "dengue", "meses_a_frente": 1})
        assert r.status_code == 200, r.text
        assert r.json()["probabilidade_risco_alto"] is not None
        assert client.post("/api/predict", json={"codigo_ibge": "355030", "doenca": "dengue",
                                                 "meses_a_frente": 1}).status_code == 404
        assert client.post("/api/predict", json={"codigo_ibge": "1", "doenca": "dengue",
                                                 "meses_a_frente": 1}).status_code == 422
        assert client.get("/api/modelo/info").json()["dengue"]["versao"] == "v5"


class TestAplicacaoV51:
    """Produção v5.1: previsão por mês, ranking, cenário, monitoramento e endpoints."""

    @pytest.fixture
    def preditor(self, artefatos):
        from src.prediction_service.data_fetcher import FonteDados
        modelos, panel, _ = artefatos
        return Preditor(model_dir=modelos, fonte=FonteDados(panel))

    def test_roteamento_por_mes(self, preditor, mini_panel):
        # último mês observado: 2023-12; modelos do fixture: h1 e h2
        r = preditor.prever_mes("100001", "dengue", 2024, 2)
        assert r.modo == "previsao" and r.horizonte_meses == 2 and r.previsao.mes_alvo == "2024-02"
        real_dez = int(mini_panel.query("code == '100001' and year == 2023 and month == 12")["dengue_cases"].iloc[0])
        assert r.casos_persistencia == real_dez
        r = preditor.prever_mes("100001", "dengue", 2024, 3)       # h=3 > h_max=2 → faixa histórica
        assert r.modo == "cenario" and r.previsao is None
        assert r.disponivel_a_partir_de == "2024-02-28"            # fim de jan/2024 + 28 dias
        assert r.faixa_historica.p10 <= r.faixa_historica.p50 <= r.faixa_historica.p90
        r = preditor.prever_mes("100001", "dengue", 2023, 6)
        real_jun = int(mini_panel.query("code == '100001' and year == 2023 and month == 6")["dengue_cases"].iloc[0])
        assert r.modo == "observado" and r.casos_reais == real_jun

    def test_faixa_historica_e_quantil_do_mes(self, preditor, mini_panel):
        f = preditor.cenarios.faixa_historica("100001", "dengue")
        jan = mini_panel.query("code == '100001' and month == 1")["dengue_cases"]
        assert f.loc[1, "p50"] == pytest.approx(jan.quantile(0.5))
        regiao = preditor.cenarios.faixa_historica("sul", "dengue")
        assert regiao.loc[1, "p50"] > f.loc[1, "p50"]              # soma das cidades

    def test_lote_uma_linha_por_cidade_ordenado(self, preditor):
        lote = preditor.prever_lote("dengue", 1)
        assert sorted(lote["codigo_ibge"]) == ["100001", "200002"]
        assert lote["probabilidade_risco_alto"].is_monotonic_decreasing
        assert (lote["ic_lo"] <= lote["casos_previstos"]).all() and (lote["casos_previstos"] <= lote["ic_hi"]).all()

    def test_curva_clima_monotonica_e_neutra_no_frio(self):
        from src.prediction_service.cenarios import CurvaClima
        x = np.linspace(10, 27, 50)
        rr = 1 + 0.02 * (x - 18) ** 2                                # formato em U, mínimo em 18 °C
        c = CurvaClima(pd.DataFrame({"valor": x, "rr": rr, "ic_lo": rr * 0.8, "ic_hi": rr * 1.2}))
        assert c.fator([22.0], 0.0)[0][0] == pytest.approx(1.0)
        f1, f2 = c.fator([22.0], 1.0)[0][0], c.fator([22.0], 2.0)[0][0]
        assert 1.0 < f1 < f2                                         # aquecer na parte quente aumenta o risco
        assert c.fator([12.0], 2.0)[0][0] == pytest.approx(1.0)     # cauda fria: sem efeito (não diminui)
        _, lo, hi = c.fator([22.0], 1.0)
        assert lo[0] <= hi[0]

    def test_producao_treina_so_meses_consolidados(self, artefatos, tmp_path):
        from src.ml_pipeline.alerta_risco import treinar_modelos_risco
        _, panel, exp = artefatos
        p = panel.assign(INGERIDO_EM=None)
        p.loc[(p.year == 2023) & (p.month == 12), "INGERIDO_EM"] = "2024-01-05T10:00:00"   # dez/2023 não consolidou
        meta = treinar_modelos_risco(p, exp_dir=exp, out_dir=tmp_path / "prod", horizontes=(1,), producao=True)
        assert meta["dengue"]["versao"] == "v5.1"
        assert meta["dengue"]["periodo_treino"].endswith("2023-11")

    def test_monitoramento_primeira_emissao_vale(self, preditor, mini_panel, tmp_path):
        from src.prediction_service.monitoramento import avaliar, registrar
        arq = tmp_path / "prev.csv"
        lote = preditor.prever_lote("dengue", 1)
        assert registrar(lote, "dengue", 1, arq) == 2
        assert registrar(lote.assign(casos_previstos=0), "dengue", 1, arq) == 0      # reemissão ignorada
        assert avaliar(mini_panel, arq) == []                                       # 2024-01 ainda não observado
        jan24 = mini_panel[mini_panel.year == 2023].assign(year=2024)
        res = avaliar(pd.concat([mini_panel, jan24]), arq)
        assert res[0]["meses"] == ["2024-01"] and res[0]["n"] == 2 and 0 <= res[0]["cobertura_intervalo_90"] <= 1

    def test_endpoints(self, preditor, monkeypatch):
        pytest.importorskip("httpx")
        from fastapi.testclient import TestClient

        import src.prediction_service.predictor as pred_mod
        from app.server import app

        monkeypatch.setattr(pred_mod, "_PREDITOR", preditor)
        monkeypatch.delenv("PRODIGIA_TOKEN", raising=False)
        c = TestClient(app)
        r = c.get("/api/previsao", params={"codigo": "100001", "ano": 2024, "mes": 1})
        assert r.status_code == 200 and r.json()["modo"] == "previsao", r.text
        assert c.get("/api/previsao", params={"codigo": "355030", "ano": 2024, "mes": 1}).status_code == 404
        j = c.get("/api/ranking", params={"h": 1}).json()
        assert j["mes_alvo"] == "2024-01" and len(j["itens"]) == 2
        j = c.get("/api/cenario", params={"codigo": "sul", "anos": 2}).json()
        assert len(j["pontos"]) == 24 and all(p["fator_clima"] == 1.0 for p in j["pontos"])
        j = c.get("/api/confiabilidade").json()
        assert j["ultimo_mes_consolidado"] == "2023-12" and set(j["horizontes"]) == {"h1", "h2"}
        assert c.post("/api/recarregar").status_code == 403


class TestTesteProspectivo:
    def test_exige_confirmacao_e_trava(self, tmp_path):
        from src.ml_pipeline.teste_prospectivo import LOCK, HoldoutJaUsado, run

        with pytest.raises(PermissionError):
            run(exp_dir=tmp_path)
        (tmp_path / LOCK).write_text("2026-11-04", encoding="utf-8")
        with pytest.raises(HoldoutJaUsado):
            run(confirmar=True, exp_dir=tmp_path)

    def test_avaliacao_usa_treino_ate_2025(self, artefatos):
        from src.ml_pipeline.teste_prospectivo import avaliar

        _, panel, exp = artefatos
        p = panel.copy()
        p["year"] = p["year"] + 3                                   # 2018–2023 → 2021–2026
        mods = []
        for f in exp.glob("oof_dengue_h*.csv.gz"):                  # OOF desloca junto
            o = pd.read_csv(f); o["year"] += 3; o.to_csv(f, index=False); mods.append(f)
        res, det = avaliar(p, "dengue", 1, {"clima": True, "suscetibilidade": True}, [1, 2, 3], exp)
        assert set(det["year"]) == {2026} and set(det["month"]) == {1, 2, 3}
        assert {"auc", "brier_skill", "persistencia"} <= set(res)
