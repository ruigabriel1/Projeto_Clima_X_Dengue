"""
server.py — FastAPI backend para a interface Prodígia.
Rotas: status do banco, lista de cidades, resultados (v4 multi-doença) e
API de previsão (POST /api/predict, documentação em /docs).
"""
import json
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.prediction_service.schemas import PredictRequest, PredictResponse

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Aquece o preditor (painel + features de previsão) em segundo plano, sem bloquear o servidor."""
    from src.prediction_service.predictor import get_preditor

    def _run():
        try:
            get_preditor().aquecer()
        except Exception as e:  # modelos ainda não treinados: a rota responde 503
            logger.warning(f"Aquecimento do preditor ignorado: {e}")

    threading.Thread(target=_run, daemon=True).start()
    yield


app = FastAPI(
    title="Prodígia — Previsão de Arboviroses (Região Sul)",
    description="Previsão de casos de dengue e chikungunya por município, 1 a 3 meses à frente.",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

# Mount output directory for downloading exports
output_dir = ROOT_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=output_dir), name="output")

templates = Jinja2Templates(directory=APP_DIR / "templates")

DASHBOARD_DIR = output_dir / "dashboard"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})


@app.get("/api/status")
async def api_status():
    from src.ml_pipeline.export_dashboard import get_db_status
    return get_db_status()


@app.get("/api/cidades")
async def api_cidades():
    from src.ml_pipeline.export_dashboard import get_cidades
    return get_cidades()


@app.get("/api/doencas")
async def api_doencas():
    """Lista doenças com resultados exportados."""
    from src.ml_pipeline.export_dashboard import doencas_exportadas
    return doencas_exportadas()


@app.get("/api/resultados")
async def api_resultados(doenca: str = Query("dengue")):
    """Retorna resultados v4 de uma doença específica."""
    json_path = DASHBOARD_DIR / f"resultados_{doenca}.json"
    if json_path.exists():
        try:
            return json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            return {"error": f"Erro ao ler resultados: {e}"}

    # Fallback: JSON legado
    legacy = ROOT_DIR / "output" / "prodigia_resultados_v2.json"
    if legacy.exists():
        try:
            return json.loads(legacy.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "error": f"Nenhum resultado para '{doenca}'. Execute:\n"
                 f"  python main.py train --doenca {doenca}\n"
                 f"  python main.py export-dashboard --doenca {doenca}"
    }


# ---------------------------------------------------------------- previsão (Fase 4)
@app.post("/api/predict", response_model=PredictResponse)
def api_predict(req: PredictRequest):
    """
    Previsão de casos para um município, doença e horizonte (1–3 meses).
    Rota síncrona: o FastAPI a executa em threadpool (o cálculo de features é CPU-bound).
    """
    from src.prediction_service.predictor import CidadeNaoEncontrada, ModeloIndisponivel, get_preditor

    try:
        return get_preditor().prever(req.codigo_ibge, req.doenca, req.meses_a_frente)
    except CidadeNaoEncontrada as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ModeloIndisponivel as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/modelo/info")
def api_modelo_info():
    """Resumo dos modelos de produção carregados (config, métricas, data de retreino)."""
    from src.prediction_service.predictor import get_preditor

    p = get_preditor()
    info = {}
    for d in p.doencas_disponiveis():
        m = p.metadata(d)
        info[d] = {
            "versao": m["versao"],
            "modelo": m["modelo"],
            "clima": m["clima"],
            "suscetibilidade": m["suscetibilidade"],
            "treinado_em": m["treinado_em"],
            "anos_treino": m["anos_treino"],
            "horizontes": {
                h: {
                    "metricas": x["metricas"],
                    "benchmark_infodengue": x["benchmark_infodengue"],
                    "teste_prospectivo_2026": x["teste_prospectivo_2026"],
                }
                for h, x in m["horizontes"].items()
            },
        }
    return info
