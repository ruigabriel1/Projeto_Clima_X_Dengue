"""
Testes do serviço de previsão (Fase 4): schemas, risco, intervalo, preditor e rota /api/predict.
Modelos treinados em dados sintéticos num diretório temporário.
"""
import pytest
from pydantic import ValidationError

from src.prediction_service.predictor import (
    CidadeNaoEncontrada, ModeloIndisponivel, Preditor, aplicar_intervalo,
)
from src.prediction_service.risk_classifier import classificar_risco
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


class TestRisco:
    @pytest.mark.parametrize("casos,nivel", [(0.4, "baixo"), (5, "baixo"), (8, "medio"), (15, "alto"), (40, "critico")])
    def test_niveis(self, casos, nivel):
        assert classificar_risco(casos, p50=5, p75=10, p90=20) == nivel


class TestIntervalo:
    def test_contem_previsao_e_nao_negativo(self):
        calib = {"bordas_pred": [1.0, 10.0], "q_lo": [-1.0, -0.5, -0.4], "q_hi": [1.0, 0.6, 0.5]}
        for pred in (0.0, 3.0, 50.0):
            lo, hi = aplicar_intervalo(pred, calib)
            assert 0 <= lo <= round(pred) <= hi


@pytest.fixture
def artefatos(mini_panel, tmp_path):
    """Roda Fase 1 + 2 + 4.1 no painel sintético e devolve (dir_modelos, painel)."""
    from src.ml_pipeline.analise_experimento import run_analise
    from src.ml_pipeline.experimento_horizontes import run_experimento
    from src.ml_pipeline.modelo_final import treinar_modelos_finais

    panel = mini_panel.copy()
    panel["city_name"] = panel["code"].map({"100001": "Cidade A", "200002": "Cidade B"})
    exp = tmp_path / "exp"
    run_experimento(doencas=("dengue",), horizontes=(1, 2), out_dir=exp, panel=panel)
    run_analise(out_dir=exp, com_shap=False)
    import json
    cfg = json.loads((exp / "config_escolhida.json").read_text(encoding="utf-8"))
    # Força clima=True para exercitar o fallback sem clima
    cfg["doencas"]["dengue"].update(usar_clima=True, corte_p99=False)
    modelos = tmp_path / "modelos"
    treinar_modelos_finais(panel, cfg, out_dir=modelos, exp_dir=exp, horizontes=(1, 2))
    return modelos, panel


class TestPreditor:
    def test_previsao_completa(self, artefatos):
        from src.prediction_service.data_fetcher import FonteDados

        modelos, panel = artefatos
        p = Preditor(model_dir=modelos, fonte=FonteDados(panel))
        r = p.prever("100001", "dengue", 2)
        assert r.disponivel and r.cidade == "Cidade A"
        assert r.mes_alvo == "2024-02" and r.ultimo_mes_observado == "2023-12"
        lo, hi = r.intervalo_confianca
        assert 0 <= lo <= r.casos_previstos <= hi
        assert r.nivel_risco in {"baixo", "medio", "alto", "critico"}
        assert r.modelo_usado == "xgb_clima_semcorte"
        assert "2025 ainda não executado" in r.nota

    def test_fallback_sem_clima(self, artefatos):
        from src.prediction_service.data_fetcher import FonteDados

        modelos, panel = artefatos
        sem_clima = panel.copy()
        ultimo = (sem_clima["year"] == 2023) & (sem_clima["month"] >= 9)
        for c in ("temp_media", "temp_maxima", "temp_minima", "precipitacao", "umidmed"):
            sem_clima.loc[ultimo, c] = float("nan")
        r = Preditor(model_dir=modelos, fonte=FonteDados(sem_clima)).prever("100001", "dengue", 1)
        assert r.modelo_usado == "xgb_semclima_semcorte"
        assert any("sem clima" in a for a in r.avisos)

    def test_zika_sem_previsao(self, artefatos):
        modelos, panel = artefatos
        r = Preditor(model_dir=modelos).prever("100001", "zika", 1)
        assert r.disponivel is False and r.casos_previstos is None and "zika" in r.nota

    def test_cidade_fora_da_cobertura(self, artefatos):
        from src.prediction_service.data_fetcher import FonteDados

        modelos, panel = artefatos
        with pytest.raises(CidadeNaoEncontrada):
            Preditor(model_dir=modelos, fonte=FonteDados(panel)).prever("355030", "dengue", 1)

    def test_modelo_ausente(self, tmp_path):
        with pytest.raises(ModeloIndisponivel):
            Preditor(model_dir=tmp_path).prever("100001", "chikungunya", 1)


class TestAPI:
    def test_rota_predict(self, artefatos, monkeypatch):
        pytest.importorskip("httpx")
        from fastapi.testclient import TestClient

        import src.prediction_service.predictor as pred_mod
        from app.server import app
        from src.prediction_service.data_fetcher import FonteDados

        modelos, panel = artefatos
        monkeypatch.setattr(pred_mod, "_PREDITOR", Preditor(model_dir=modelos, fonte=FonteDados(panel)))
        client = TestClient(app)

        r = client.post("/api/predict", json={"codigo_ibge": "100001", "doenca": "dengue", "meses_a_frente": 1})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["casos_previstos"] is not None and len(body["intervalo_confianca"]) == 2

        assert client.post("/api/predict", json={"codigo_ibge": "355030", "doenca": "dengue",
                                                 "meses_a_frente": 1}).status_code == 404
        assert client.post("/api/predict", json={"codigo_ibge": "1", "doenca": "dengue",
                                                 "meses_a_frente": 1}).status_code == 422
        assert "dengue" in client.get("/api/modelo/info").json()
