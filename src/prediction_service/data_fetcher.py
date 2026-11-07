"""
Fonte de dados do serviço de previsão.

A fonte de verdade é o SQLite (data/processed/dengue_analytics.db), alimentado pelos robôs
de ingestão das APIs públicas (InfoDengue, Open-Meteo, NOAA, IBGE):

    python -m src.processamento.ingestor_api_sul --alvo infodengue
    python -m src.processamento.ingestor_api_sul --alvo openmeteo
    python -m src.processamento.ingestor_api_sul --alvo noaa

Depois de atualizar o banco, chame FonteDados.recarregar() (ou reinicie o servidor).

Para prever o mês T = último observado + h, acrescentamos h linhas "futuras" (casos e clima
desconhecidos) a cada cidade e reconstruímos as features EXATAMENTE como no treino
(build_ml_features). Como toda feature usa lags ≥ h, a linha T só depende de dados observados.
"""
from __future__ import annotations

import logging
import threading

import numpy as np
import pandas as pd

from src.config import BASE_DIR
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, build_ml_features

logger = logging.getLogger(__name__)

_COLS_ESTATICAS = ["city_name", "latitude", "longitude", "lat_faixa_id", "populacao", "log_pop"]


DIAS_MIN_CONSOLIDACAO = 28


def remover_meses_nao_consolidados(panel: pd.DataFrame, dias: int = DIAS_MIN_CONSOLIDACAO) -> pd.DataFrame:
    """
    Remove meses ingeridos menos de `dias` após o fim do mês: o InfoDengue ainda acrescenta notificações
    a eles, e usá-los como "último mês observado" subestimaria a previsão.
    """
    if "INGERIDO_EM" not in panel.columns:
        return panel
    ing = pd.to_datetime(panel["INGERIDO_EM"], errors="coerce")
    fim_mes = pd.to_datetime(dict(year=panel["year"], month=panel["month"], day=1)) + pd.offsets.MonthEnd(0)
    recente = ing.notna() & ((ing - fim_mes).dt.days < dias)
    if recente.any():
        logger.info(f"Removidos {int(recente.sum())} registros de meses não consolidados (< {dias} dias).")
    return panel[~recente].copy()


class FonteDados:
    def __init__(self, panel: pd.DataFrame | None = None, incluir_rt: bool = False):
        self._panel = panel
        self.incluir_rt = incluir_rt   # v7: o painel traz o Rt do InfoDengue (features só defasadas)
        self._cache: dict[tuple[str, int], pd.DataFrame] = {}
        self._lock = threading.Lock()
        # Uma trava por (doença, h): o aquecimento e as requisições não recalculam a mesma coisa em paralelo
        self._locks_feat: dict[tuple[str, int], threading.Lock] = {}

    # ------------------------------------------------------------------ painel
    @property
    def panel(self) -> pd.DataFrame:
        if self._panel is None:
            with self._lock:
                if self._panel is None:
                    from src.ml_pipeline.data_ingestion import build_base_panel
                    self._panel = remover_meses_nao_consolidados(build_base_panel(BASE_DIR, incluir_rt=self.incluir_rt))
                    logger.info(f"Painel carregado: {len(self._panel)} linhas")
        return self._panel

    def recarregar(self):
        with self._lock:
            self._panel = None
            self._cache.clear()

    def tem_cidade(self, code: str) -> bool:
        return code in set(self.panel["code"].unique())

    def ultimo_mes_observado(self, code: str, doenca: str) -> tuple[int, int] | None:
        alvo = DOENCA_PARA_COL[doenca]
        p = self.panel
        s = p[(p["code"] == code) & p[alvo].notna()]
        if s.empty:
            return None
        ult = s.sort_values(["year", "month"]).iloc[-1]
        return int(ult["year"]), int(ult["month"])

    def alerta_infodengue(self, code: str, doenca: str, ano_mes: tuple[int, int] | None) -> int | None:
        """Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível."""
        col = {"dengue": "NIVEL_DENGUE", "chikungunya": "NIVEL_CHIKUNGUNYA"}.get(doenca)
        p = self.panel
        if not ano_mes or col not in p.columns:
            return None
        v = p.loc[(p["code"] == code) & (p["year"] == ano_mes[0]) & (p["month"] == ano_mes[1]), col]
        return int(v.iloc[0]) if len(v) and pd.notna(v.iloc[0]) else None

    # ------------------------------------------------------------------ features
    def _com_linhas_futuras(self, doenca: str, h: int) -> pd.DataFrame:
        """Painel + h meses futuros por cidade (após o último mês com alvo observado)."""
        alvo = DOENCA_PARA_COL[doenca]
        p = self.panel
        obs = p[p[alvo].notna()]
        ultimos = obs.sort_values(["year", "month"]).groupby("code").tail(1)
        estaticas = [c for c in _COLS_ESTATICAS if c in p.columns]
        futuras = []
        for k in range(1, h + 1):
            idx = ultimos["year"] * 12 + (ultimos["month"] - 1) + k
            f = ultimos[["code"] + estaticas].copy()
            f["year"] = (idx // 12).astype(int).values
            f["month"] = (idx % 12 + 1).astype(int).values
            futuras.append(f)
        fut = pd.concat(futuras, ignore_index=True)
        # Remove do painel linhas sem alvo após o último observado (evita duplicar chaves)
        chave = p["year"] * 12 + p["month"]
        lim = p["code"].map(ultimos.set_index("code").eval("year * 12 + month"))
        base = p[chave <= lim.fillna(np.inf)]
        return pd.concat([base, fut], ignore_index=True, sort=False)

    def features_previsao(self, doenca: str, h: int) -> pd.DataFrame:
        """Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com cache."""
        chave = (doenca, h)
        if chave in self._cache:
            return self._cache[chave]
        with self._lock:
            trava = self._locks_feat.setdefault(chave, threading.Lock())
        with trava:
            if chave not in self._cache:
                alvo = DOENCA_PARA_COL[doenca]
                ext = self._com_linhas_futuras(doenca, h)
                feats = build_ml_features(ext, doenca=doenca, horizonte=h)
                alvo_rows = feats[feats[alvo].isna()]
                # Mantém só o mês T (o h-ésimo futuro) de cada cidade
                alvo_rows = alvo_rows.sort_values(["code", "year", "month"]).groupby("code").tail(1)
                self._cache[chave] = alvo_rows.set_index("code")
                logger.info(f"Features de previsão {chave}: {len(alvo_rows)} cidades")
        return self._cache[chave]
