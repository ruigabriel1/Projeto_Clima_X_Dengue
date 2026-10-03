"""
server.py — FastAPI backend para a interface Prodígia.
Rotas: status do banco, lista de cidades, treinamento com SSE, resultados.
"""
import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Prodígia", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

# Mount output directory for downloading exports
output_dir = APP_DIR.parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=output_dir), name="output")

templates = Jinja2Templates(directory=APP_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})


@app.get("/api/status")
async def api_status():
    from app.ml_runner import get_db_status
    return get_db_status()


@app.get("/api/cidades")
async def api_cidades():
    from app.ml_runner import get_cidades
    return get_cidades()



@app.get("/api/resultados")
async def api_resultados():
    # Carrega do disco (resultados gerados pelo MLOps export_dashboard.py)
    json_path = APP_DIR.parent / "output" / "prodigia_resultados_v2.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Erro ao ler resultados: {e}"}
            
    return {"error": "Nenhum resultado disponível. Execute 'python main.py export-dashboard' primeiro."}
