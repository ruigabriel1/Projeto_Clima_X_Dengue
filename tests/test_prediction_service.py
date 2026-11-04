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
