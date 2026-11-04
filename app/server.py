"""
server.py — FastAPI backend para a interface Prodígia.
Rotas: status do banco, lista de cidades, resultados (v4 multi-doença).
"""
import json
from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent

app = FastAPI(title="Prodígia", docs_url=None, redoc_url=None)
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
