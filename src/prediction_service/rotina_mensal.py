"""
Rotina mensal da produção v5.1 (python main.py atualizar-mensal).

1. Atualiza o banco (InfoDengue, Open-Meteo, NOAA), de forma incremental e idempotente.
2. Recarrega o servidor, se PRODIGIA_URL e PRODIGIA_TOKEN estiverem definidos.
3. Avalia as previsões registradas cujo mês-alvo já consolidou (monitoramento ao vivo).
4. Emite e registra as previsões de todas as cidades para os próximos 1–3 meses e grava o ranking em CSV.

O retreino NÃO é mensal: é anual (python main.py modelo-risco --producao), com o mesmo procedimento.
"""
from __future__ import annotations

import json
import logging
import os

from src.config import OUTPUT_DIR
from src.prediction_service.monitoramento import ARQ_PREVISOES, avaliar, registrar

logger = logging.getLogger(__name__)

DIR_RANKING = OUTPUT_DIR / "monitoramento" / "ranking"


def recarregar_servidor() -> bool:
    url, token = os.environ.get("PRODIGIA_URL"), os.environ.get("PRODIGIA_TOKEN")
    if not (url and token):
        return False
    import requests
    r = requests.post(url.rstrip("/") + "/api/recarregar", headers={"x-token": token}, timeout=60)
    r.raise_for_status()
    return True


def executar(atualizar_dados: bool = True, doencas=("dengue", "chikungunya"), horizontes=(1, 2, 3)) -> dict:
    if atualizar_dados:
        from src.processamento.atualizacao_incremental import main as atualizar
        atualizar(["--alvo", "todos"])
    try:
        if recarregar_servidor():
            logger.info("Servidor recarregado.")
    except Exception as e:  # o servidor pode estar fora do ar; a rotina segue
        logger.warning(f"Não foi possível recarregar o servidor: {e}")

    from src.prediction_service.predictor import Preditor
    p = Preditor()
    resumo = {"ao_vivo": avaliar(p.fonte.panel), "emitidas": {}}
    DIR_RANKING.mkdir(parents=True, exist_ok=True)
    for d in doencas:
        for h in horizontes:
            lote = p.prever_lote(d, h)
            n = registrar(lote, d, h)
            mes = lote["mes_alvo"].iloc[0]
            lote.to_csv(DIR_RANKING / f"ranking_{d}_{mes}_h{h}.csv", index=False)
            resumo["emitidas"][f"{d}_h{h}"] = {"mes_alvo": mes, "novas": n, "total_previsto": int(lote["casos_previstos"].sum())}
    logger.info(json.dumps(resumo, ensure_ascii=False, indent=1))
    logger.info(f"Previsões registradas em {ARQ_PREVISOES}")
    return resumo
