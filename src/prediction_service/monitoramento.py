"""
Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1").

1. registrar(): grava as previsões emitidas (ranking mensal de todas as cidades) em
   output/monitoramento/previsoes.csv. Só a PRIMEIRA emissão de cada (cidade, doença, mês-alvo, h) conta:
   reemitir depois que o mês aconteceu não pode "melhorar" o histórico.
2. avaliar(): quando o mês-alvo chega (e consolida), compara previsto × real e a persistência × real.
   É o desempenho que a aplicação mostra como "ao vivo", ao lado do teste de 2026.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import OUTPUT_DIR
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL

logger = logging.getLogger(__name__)

ARQ_PREVISOES = OUTPUT_DIR / "monitoramento" / "previsoes.csv"
CHAVE = ["codigo_ibge", "doenca", "mes_alvo", "horizonte"]


def registrar(lote: pd.DataFrame, doenca: str, h: int, path: Path = ARQ_PREVISOES) -> int:
    """Acrescenta as previsões do lote; ignora as que já tinham sido emitidas. Retorna quantas entraram."""
    novo = lote[["codigo_ibge", "mes_alvo", "casos_previstos", "ic_lo", "ic_hi", "probabilidade_risco_alto",
                 "casos_persistencia"]].assign(doenca=doenca, horizonte=int(h),
                                               emitido_em=datetime.now().isoformat(timespec="seconds"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        antigo = pd.read_csv(path, dtype={"codigo_ibge": str})
        ja = antigo.set_index(CHAVE).index
        novo = novo[~novo.set_index(CHAVE).index.isin(ja)]
        if novo.empty:
            return 0
        pd.concat([antigo, novo], ignore_index=True).to_csv(path, index=False)
    else:
        novo.to_csv(path, index=False)
    logger.info(f"Monitoramento: {len(novo)} previsões novas de {doenca} h={h}")
    return len(novo)


def avaliar(panel: pd.DataFrame, path: Path = ARQ_PREVISOES) -> list[dict]:
    """Desempenho por doença × horizonte das previsões cujo mês-alvo já foi observado (painel consolidado)."""
    if not path.exists():
        return []
    prev = pd.read_csv(path, dtype={"codigo_ibge": str})
    saida = []
    for (doenca, h), g in prev.groupby(["doenca", "horizonte"]):
        alvo = DOENCA_PARA_COL[doenca]
        real = panel.dropna(subset=[alvo]).assign(mes_alvo=lambda x: x["year"].astype(str) + "-" + x["month"].map("{:02d}".format))
        real = real[["code", "mes_alvo", alvo]].rename(columns={"code": "codigo_ibge", alvo: "real"})
        m = g.merge(real, on=["codigo_ibge", "mes_alvo"], how="inner")
        if m.empty:
            continue
        mae = float(np.mean(np.abs(m["real"] - m["casos_previstos"])))
        mae_p = float(np.mean(np.abs(m["real"] - m["casos_persistencia"].fillna(0))))
        saida.append({
            "doenca": doenca, "horizonte": int(h), "meses": sorted(m["mes_alvo"].unique().tolist()), "n": int(len(m)),
            "casos_reais": int(m["real"].sum()), "casos_previstos": int(m["casos_previstos"].sum()),
            "razao_previsto_real": round(float(m["casos_previstos"].sum() / max(m["real"].sum(), 1)), 3),
            "mae": round(mae, 3), "mae_persistencia": round(mae_p, 3),
            "skill": round(1 - mae / mae_p, 4) if mae_p > 0 else None,
            "cobertura_intervalo_90": round(float(np.mean((m["real"] >= m["ic_lo"]) & (m["real"] <= m["ic_hi"]))), 4),
        })
    return saida
