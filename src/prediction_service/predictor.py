"""
Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md).

Produto principal: P(risco alto) = P(incidência do mês-alvo > P75 da própria cidade), calibrada
por isotônica no OOF. A contagem de casos é secundária e sempre vem com intervalo de 90%.

Regras de qualidade:
  - Sempre há incerteza explícita (probabilidade; intervalo para a contagem).
  - Cidade com poucos meses com caso → confiabilidade "baixa" + aviso.
  - Zika: sem previsão (dados insuficientes) — resposta explicativa.
  - Sem dados climáticos para o mês necessário (se o modelo usa clima) → resposta com aviso e
    confiabilidade baixa (o XGBoost trata a ausência, mas o desempenho validado não se aplica).
  - Modelo com prazo de retreino vencido → aviso.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.ml_pipeline.alerta_risco import OUT_MODELOS_V5, nivel_por_probabilidade
from src.ml_pipeline.feature_engineering import is_climate_feature
from src.prediction_service.data_fetcher import FonteDados
from src.prediction_service.schemas import PredictResponse

logger = logging.getLogger(__name__)

MIN_MESES_COM_CASO = 6
MESES_RETREINO = 12
MSG_ZIKA = (
    "Não há previsão para zika: a série do InfoDengue termina em 2024 e tem poucos casos "
    "na Região Sul, o que torna qualquer modelo pouco confiável."
)


class ModeloIndisponivel(RuntimeError):
    pass


class CidadeNaoEncontrada(LookupError):
    pass


def _fmt_mes(ano: int, mes: int) -> str:
    return f"{ano}-{mes:02d}"


def aplicar_intervalo(pred: float, calib: dict | None) -> tuple[int, int]:
    """Intervalo de 90% a partir dos quantis de resíduo log1p calibrados no OOF."""
    if not calib:
        return int(np.floor(pred * 0.5)), int(np.ceil(pred * 1.5 + 1))
    b = int(np.searchsorted(np.asarray(calib["bordas_pred"]), pred, side="right"))
    lo = np.expm1(np.log1p(pred) + calib["q_lo"][b])
    hi = np.expm1(np.log1p(pred) + calib["q_hi"][b])
    return int(max(0, np.floor(lo))), int(max(np.ceil(hi), round(pred)))


class Preditor:
    def __init__(self, model_dir: Path = OUT_MODELOS_V5, fonte: FonteDados | None = None):
        self.model_dir = Path(model_dir)
        self.fonte = fonte or FonteDados()
        self._meta: dict[str, dict] = {}
        self._objs: dict[tuple, object] = {}
        self._lock = threading.Lock()

    def metadata(self, doenca: str) -> dict:
        if doenca not in self._meta:
            path = self.model_dir / doenca / "metadata.json"
            if not path.exists():
                raise ModeloIndisponivel(
                    f"Modelo de risco de {doenca} não encontrado em {path.parent}. Rode: python main.py modelo-risco"
                )
            self._meta[doenca] = json.loads(path.read_text(encoding="utf-8"))
        return self._meta[doenca]

    def _carregar(self, doenca: str, arquivo: str):
        chave = (doenca, arquivo)
        if chave not in self._objs:
            with self._lock:
                if chave not in self._objs:
                    self._objs[chave] = joblib.load(self.model_dir / doenca / arquivo)
        return self._objs[chave]

    def doencas_disponiveis(self) -> list[str]:
        return sorted(p.parent.name for p in self.model_dir.glob("*/metadata.json"))

    def aquecer(self):
        for d in self.doencas_disponiveis():
            for h in self.metadata(d)["horizontes"]:
                self.fonte.features_previsao(d, int(h[1:]))
        logger.info("Cache de previsão aquecido.")

    # ------------------------------------------------------------------ previsão
    def prever(self, codigo_ibge: str, doenca: str, meses_a_frente: int) -> PredictResponse:
        code, h = codigo_ibge[:6], int(meses_a_frente)
        base = dict(codigo_ibge=code, doenca=doenca, horizonte_meses=h)
        if doenca == "zika":
            return PredictResponse(**base, disponivel=False, nota=MSG_ZIKA)

        meta = self.metadata(doenca)
        cid = meta["cidades"].get(code)
        if cid is None or not self.fonte.tem_cidade(code):
            raise CidadeNaoEncontrada(
                f"Município {code} fora da área de cobertura (1.190 municípios da Região Sul: PR, SC, RS)."
            )
        hm = meta["horizontes"].get(f"h{h}")
        if hm is None:
            raise ModeloIndisponivel(f"Sem modelo para horizonte {h}.")
        feats_df = self.fonte.features_previsao(doenca, h)
        if code not in feats_df.index:
            raise CidadeNaoEncontrada(f"Sem histórico suficiente para prever {code}.")
        linha = feats_df.loc[[code]]
        avisos: list[str] = []
        baixa = False

        clima_cols = [c for c in hm["features"] if is_climate_feature(c)]
        if clima_cols and linha[clima_cols].isna().all(axis=None):
            baixa = True
            avisos.append("Dados climáticos indisponíveis para os meses necessários; previsão fora das condições validadas.")

        pop = float(linha["populacao"].iloc[0])
        modelo = self._carregar(doenca, hm["arquivo"])
        margem = np.log(np.array([max(pop, 1.0)]) / 100_000.0)
        pred = float(max(0.0, modelo.predict(linha[hm["features"]], base_margin=margem)[0]))
        incid = pred / pop * 100_000
        escore = incid / (cid["p75_incid"] + meta["eps_incid"])
        prob = float(self._carregar(doenca, hm["calibrador"]).predict([escore])[0])
        lo, hi = aplicar_intervalo(pred, hm.get("intervalo_contagem"))

        if cid["meses_com_caso"] < MIN_MESES_COM_CASO:
            baixa = True
            avisos.append(f"Município com apenas {cid['meses_com_caso']} meses com casos no histórico: previsão pouco confiável.")
        teste = hm.get("teste_prospectivo_2026")
        if teste and teste.get("brier_skill") is not None and teste["brier_skill"] < 0:
            baixa = True
            avisos.append("No teste prospectivo de 2026 a probabilidade foi pior que a climatologia; use com cautela.")
        avisos.append("Os meses mais recentes do InfoDengue/SINAN podem estar incompletos (atraso de notificação).")
        retreino = (pd.Timestamp(meta["treinado_em"]) + pd.DateOffset(months=MESES_RETREINO)).strftime("%Y-%m")
        if retreino < date.today().strftime("%Y-%m"):
            avisos.append(f"Modelo com retreino vencido (previsto até {retreino}).")

        ult = self.fonte.ultimo_mes_observado(code, doenca)
        alerta = self.fonte.alerta_infodengue(code, doenca, ult)

        dev = (hm.get("metricas") or {}).get("dev_2018_2024", {})
        if teste:
            nota = (f"Validado prospectivamente em jan–ago/2026: AUC {teste['auc']:.2f}, Brier skill {teste['brier_skill']:.2f}. "
                    "Risco é relativo ao histórico da própria cidade.")
        elif dev:
            nota = (f"Validação 2018–2024: AUC {dev.get('auc', float('nan')):.2f}, Brier skill "
                    f"{dev.get('brier_skill', float('nan')):.2f}. Teste prospectivo 2026 ainda não executado.")
        else:
            nota = "Métricas de validação indisponíveis."

        return PredictResponse(
            **base,
            cidade=cid.get("nome"),
            mes_alvo=_fmt_mes(int(linha["year"].iloc[0]), int(linha["month"].iloc[0])),
            ultimo_mes_observado=_fmt_mes(*ult) if ult else None,
            probabilidade_risco_alto=round(prob, 3),
            nivel_risco=nivel_por_probabilidade(prob),
            limiar_risco_incidencia_100k=round(cid["p75_incid"], 1),
            alerta_infodengue_ultimo=alerta,
            casos_previstos=int(round(pred)),
            intervalo_confianca=[lo, hi],
            incidencia_prevista_100k=round(incid, 2),
            modelo_usado=meta["modelo"],
            confiabilidade="baixa" if baixa else "normal",
            avisos=avisos,
            nota=nota,
        )


_PREDITOR: Preditor | None = None
_PREDITOR_LOCK = threading.Lock()


def get_preditor() -> Preditor:
    global _PREDITOR
    if _PREDITOR is None:
        with _PREDITOR_LOCK:
            if _PREDITOR is None:
                _PREDITOR = Preditor()
    return _PREDITOR
