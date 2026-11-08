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

from typing import Literal, Optional

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.prediction_service.schemas import (
    CenarioResponse, PredictRequest, PredictResponse, PrevisaoMesResponse, RankingItem, RankingResponse,
)

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
# output/ NÃO é servido: tem logs (com caminhos locais) e os modelos; a aplicação lê só pelas rotas /api.

templates = Jinja2Templates(directory=APP_DIR / "templates")

DASHBOARD_DIR = ROOT_DIR / "output" / "dashboard"


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
async def api_resultados(doenca: Literal["dengue", "chikungunya", "zika"] = "dengue"):
    """Retorna resultados v4 de uma doença específica."""
    # Lista fechada: um texto livre aqui montaria o caminho do arquivo e, no Windows, "/../.." sairia da pasta.
    json_path = DASHBOARD_DIR / f"resultados_{doenca}.json"
    if json_path.exists():
        try:
            return json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.exception("Erro ao ler %s", json_path.name)
            return {"error": "Erro ao ler os resultados."}

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
            "periodo_treino": m.get("periodo_treino"),
            "calibracao": m.get("calibracao"),
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


# ---------------------------------------------------------------- aplicação (produção v5.1)
def _erro_http(e: Exception):
    from src.prediction_service.predictor import CidadeNaoEncontrada, ModeloIndisponivel
    if isinstance(e, (CidadeNaoEncontrada, LookupError)):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, ModeloIndisponivel):
        raise HTTPException(status_code=503, detail=str(e))
    raise e


@app.get("/api/previsao", response_model=PrevisaoMesResponse)
def api_previsao(codigo: str = Query(..., min_length=6, max_length=7, pattern=r"^\d+$"),
                 doenca: Literal["dengue", "chikungunya"] = "dengue",
                 ano: int = Query(..., ge=2015, le=2035), mes: int = Query(..., ge=1, le=12)):
    """
    Casos de um município em um mês. Até 3 meses após o último mês consolidado: previsão do modelo com
    intervalo de 90% e o desempenho real daquele horizonte. Mais longe: faixa histórica (não é previsão).
    """
    from src.prediction_service.predictor import get_preditor
    try:
        return get_preditor().prever_mes(codigo, doenca, ano, mes)
    except Exception as e:
        _erro_http(e)


@app.get("/api/ranking", response_model=RankingResponse)
def api_ranking(doenca: Literal["dengue", "chikungunya"] = "dengue", h: int = Query(1, ge=1, le=3),
                uf: Optional[Literal["PR", "SC", "RS"]] = None, pop_min: int = Query(0, ge=0),
                limite: int = Query(20, ge=1, le=1190)):
    """Cidades ordenadas pela probabilidade de risco alto (relativo ao histórico de cada cidade)."""
    from src.prediction_service.predictor import get_preditor
    try:
        lote = get_preditor().prever_lote(doenca, h)
    except Exception as e:
        _erro_http(e)
    total, lo, hi = int(lote["casos_previstos"].sum()), int(lote["ic_lo"].sum()), int(lote["ic_hi"].sum())
    f = lote[lote["populacao"] >= pop_min]
    if uf:
        f = f[f["uf"] == uf]
    itens = [RankingItem(**{k: r[k] for k in ("codigo_ibge", "cidade", "uf", "populacao", "probabilidade_risco_alto",
                                              "nivel_risco", "casos_previstos", "incidencia_prevista_100k")},
                         intervalo_confianca=[int(r["ic_lo"]), int(r["ic_hi"])],
                         casos_persistencia=None if pd.isna(r["casos_persistencia"]) else int(r["casos_persistencia"]))
             for _, r in f.head(limite).iterrows()]
    return RankingResponse(doenca=doenca, horizonte_meses=h, mes_alvo=str(lote["mes_alvo"].iloc[0]),
                           total_previsto=total, total_intervalo=[lo, hi], itens=itens)


@app.get("/api/cenario", response_model=CenarioResponse)
def api_cenario(codigo: str = Query("sul", description="Código IBGE ou 'sul' (soma da região)"),
                doenca: Literal["dengue", "chikungunya"] = "dengue",
                delta_temp: float = Query(0.0, ge=0.0, le=3.0), anos: int = Query(5, ge=1, le=5)):
    """Próximos anos: faixa histórica por mês (P10–P90) e cenário de aquecimento pelo DLNM. NÃO é previsão."""
    from src.prediction_service.predictor import get_preditor
    code = codigo if codigo == "sul" else codigo[:6]
    try:
        r = get_preditor().cenarios.projecao(code, doenca, delta_temp, meses=12 * anos)
    except Exception as e:
        _erro_http(e)
    return CenarioResponse(
        codigo_ibge=code, doenca=doenca, delta_temp=delta_temp, **r,
        nota=("Cenário, não previsão: o que costuma acontecer em cada mês (P10–P90 dos anos observados), "
              "ajustado pelo efeito da temperatura estimado no DLNM quando delta_temp > 0."))


@app.get("/api/confiabilidade")
def api_confiabilidade(doenca: Literal["dengue", "chikungunya"] = "dengue"):
    """Quão confiável é: desempenho por horizonte (validação, teste de 2026) e monitoramento ao vivo."""
    from src.prediction_service.monitoramento import avaliar
    from src.prediction_service.predictor import get_preditor
    p = get_preditor()
    try:
        m = p.metadata(doenca)
    except Exception as e:
        _erro_http(e)
    # só o modelo em produção; o modo sombra (v6) é avaliado à parte, no fim do teste
    ao_vivo = [x for x in avaliar(p.fonte.panel) if x["doenca"] == doenca and x["modelo"] == m["versao"]]
    return {"doenca": doenca, "versao": m["versao"], "periodo_treino": m.get("periodo_treino"),
            "calibracao": m.get("calibracao"), "treinado_em": m["treinado_em"],
            "ultimo_mes_consolidado": "{}-{:02d}".format(*p.ultimo_mes_consolidado(doenca)),
            "horizontes": {h: x.get("desempenho") for h, x in m["horizontes"].items()},
            "ao_vivo": ao_vivo}


@app.get("/api/municipios")
def api_municipios(doenca: Literal["dengue", "chikungunya"] = "dengue"):
    """Municípios cobertos pelo modelo (código de 6 dígitos, nome, UF, população), ordenados por nome."""
    from src.prediction_service.predictor import UF_POR_PREFIXO, get_preditor
    try:
        cid = get_preditor().metadata(doenca)["cidades"]
    except Exception as e:
        _erro_http(e)
    out = [{"codigo": c, "nome": v.get("nome"), "uf": UF_POR_PREFIXO.get(c[:2], "?"), "populacao": v.get("populacao")}
           for c, v in cid.items()]
    return sorted(out, key=lambda x: (x["nome"] or ""))


@app.get("/api/historico")
def api_historico(codigo: str = Query("sul"), doenca: Literal["dengue", "chikungunya"] = "dengue",
                  meses: int = Query(36, ge=1, le=240)):
    """Casos observados (consolidados) dos últimos `meses` de um município ou da região ('sul')."""
    from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL
    from src.prediction_service.predictor import get_preditor
    p = get_preditor().fonte.panel
    alvo = DOENCA_PARA_COL[doenca]
    o = p.dropna(subset=[alvo])
    if codigo != "sul":
        o = o[o["code"] == codigo[:6]]
        if o.empty:
            raise HTTPException(status_code=404, detail=f"Sem histórico para {codigo}.")
    s = o.groupby(["year", "month"])[alvo].sum().reset_index().tail(meses)
    return [{"mes": f"{int(r.year)}-{int(r.month):02d}", "casos": int(r[alvo])} for _, r in s.iterrows()]


@app.post("/api/recarregar")
def api_recarregar(x_token: Optional[str] = Header(None)):
    """Relê o banco depois de uma ingestão (protegido pela variável de ambiente PRODIGIA_TOKEN)."""
    import hmac
    import os
    token = os.environ.get("PRODIGIA_TOKEN")
    if not token or not x_token or not hmac.compare_digest(x_token.encode(), token.encode()):
        raise HTTPException(status_code=403, detail="Recarga desabilitada ou token inválido.")
    from src.prediction_service.predictor import get_preditor
    get_preditor().fonte.recarregar()
    return {"ok": True}
