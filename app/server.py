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
from sse_starlette.sse import EventSourceResponse

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Prodígia", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

# Mount output directory for downloading exports
output_dir = APP_DIR.parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=output_dir), name="output")

templates = Jinja2Templates(directory=APP_DIR / "templates")

# Estado global do treinamento (simplificado para single-user local)
_train_state = {"running": False, "result": None, "progress": None}


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


@app.post("/api/treinar")
async def api_treinar(request: Request):
    if _train_state["running"]:
        return {"error": "Treinamento já em andamento."}

    body = await request.json()
    modo = body.get("modo", "rapido")
    codigo_ibge = body.get("codigo_ibge")

    _train_state["running"] = True
    _train_state["result"] = None
    _train_state["progress"] = asyncio.Queue()

    async def run_training():
        from app.ml_runner import treinar

        def on_progress(msg: str, pct: int):
            try:
                _train_state["progress"].put_nowait({"msg": msg, "pct": pct})
            except Exception:
                pass

        try:
            result = await asyncio.to_thread(
                treinar, modo=modo, codigo_ibge=codigo_ibge, on_progress=on_progress,
            )
            _train_state["result"] = result
            on_progress("Treinamento concluído com sucesso!", 100)
        except Exception as e:
            on_progress(f"Erro: {e}", -1)
        finally:
            _train_state["running"] = False

    asyncio.create_task(run_training())
    return {"status": "started"}


@app.get("/api/treinar/progresso")
async def api_progresso(request: Request):
    async def event_generator():
        q = _train_state.get("progress")
        if not q:
            yield {"data": json.dumps({"msg": "Sem treinamento ativo.", "pct": -1})}
            return
        while True:
            if await request.is_disconnected():
                break
            try:
                item = await asyncio.wait_for(q.get(), timeout=1.0)
                yield {"data": json.dumps(item, ensure_ascii=False)}
                if item.get("pct", 0) >= 100 or item.get("pct", 0) == -1:
                    break
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": ""}

    return EventSourceResponse(event_generator())


@app.get("/api/resultados")
async def api_resultados():
    if _train_state["result"]:
        return _train_state["result"]
    return {"error": "Nenhum resultado disponível. Execute o treinamento primeiro."}
