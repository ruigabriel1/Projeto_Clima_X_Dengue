"""
Preditor de produção: carrega os modelos finais (Fase 4.1), monta as features do mês-alvo
e devolve casos previstos + intervalo de 90% + nível de risco + avisos de confiabilidade.

Regras de qualidade (plano §4.4):
  - Sempre devolve intervalo de confiança, nunca só um número.
  - Cidade com poucos meses com caso ou R² fora-da-amostra < 0,2 → confiabilidade "baixa" + aviso.
  - Zika: sem previsão (dados insuficientes) — resposta explicativa.
  - Sem dados climáticos para o mês necessário → usa o modelo sem clima (fallback).
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

from src.config import OUTPUT_MODELOS_FINAIS
from src.ml_pipeline.feature_engineering import is_climate_feature
from src.ml_pipeline.modelo_final import MIN_MESES_COM_CASO
from src.prediction_service.data_fetcher import FonteDados
from src.prediction_service.risk_classifier import classificar_risco
from src.prediction_service.schemas import PredictResponse

logger = logging.getLogger(__name__)

R2_MINIMO_CONFIAVEL = 0.2
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
    def __init__(self, model_dir: Path = OUTPUT_MODELOS_FINAIS, fonte: FonteDados | None = None):
        self.model_dir = Path(model_dir)
        self.fonte = fonte or FonteDados()
        self._meta: dict[str, dict] = {}
        self._modelos: dict[tuple, object] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ artefatos
    def metadata(self, doenca: str) -> dict:
        if doenca not in self._meta:
            path = self.model_dir / doenca / "metadata.json"
            if not path.exists():
                raise ModeloIndisponivel(
                    f"Modelo final de {doenca} não encontrado em {path.parent}. Rode: python main.py modelo-final"
                )
            self._meta[doenca] = json.loads(path.read_text(encoding="utf-8"))
        return self._meta[doenca]

    def _modelo(self, doenca: str, arquivo: str):
        chave = (doenca, arquivo)
        if chave not in self._modelos:
            with self._lock:
                if chave not in self._modelos:
                    self._modelos[chave] = joblib.load(self.model_dir / doenca / arquivo)
        return self._modelos[chave]

    def doencas_disponiveis(self) -> list[str]:
        return sorted(p.parent.name for p in self.model_dir.glob("*/metadata.json"))

    def aquecer(self):
        """Pré-calcula as features de previsão (≈10 s por doença × horizonte) para respostas rápidas."""
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
        hmeta = meta["horizontes"].get(f"h{h}")
        if hmeta is None:
            raise ModeloIndisponivel(f"Sem modelo para horizonte {h}.")

        feats_df = self.fonte.features_previsao(doenca, h)
        if code not in feats_df.index:
            raise CidadeNaoEncontrada(f"Sem histórico suficiente para prever {code}.")
        linha = feats_df.loc[[code]]
        avisos: list[str] = []

        # ---------- escolha da variante (fallback sem clima) ----------
        var = hmeta["variantes"]["principal"]
        if var["usar_clima"]:
            clima_cols = [c for c in var["features"] if is_climate_feature(c) and not c.startswith(("enso_", "receptivo_"))]
            faltando = linha[clima_cols].isna().all(axis=None) if clima_cols else False
            if faltando and "sem_clima" in hmeta["variantes"]:
                var = hmeta["variantes"]["sem_clima"]
                avisos.append("Dados climáticos indisponíveis para os meses necessários: usado o modelo sem clima.")

        modelo = self._modelo(doenca, var["arquivo"])
        pred = float(max(0.0, modelo.predict(linha[var["features"]])[0]))
        lo, hi = aplicar_intervalo(pred, var.get("intervalo"))

        # ---------- confiabilidade ----------
        r2_cidade = (cid.get("r2_oof") or {}).get(f"h{h}")
        baixa = False
        if cid["meses_com_caso"] < MIN_MESES_COM_CASO:
            baixa = True
            avisos.append(
                f"Município com apenas {cid['meses_com_caso']} meses com casos no histórico: previsão pouco confiável."
            )
        if r2_cidade is None or r2_cidade < R2_MINIMO_CONFIAVEL:
            baixa = True
            r2_txt = "indisponível" if r2_cidade is None else f"{r2_cidade:.3f}"
            avisos.append(
                f"R² fora-da-amostra deste município = {r2_txt} (< {R2_MINIMO_CONFIAVEL}): previsão pouco confiável."
            )

        ult = self.fonte.ultimo_mes_observado(code, doenca)
        alvo_ano, alvo_mes = int(linha["year"].iloc[0]), int(linha["month"].iloc[0])
        avisos.append(
            "Os meses mais recentes do InfoDengue/SINAN podem estar incompletos (atraso de notificação); "
            "a previsão herda essa subnotificação."
        )
        if meta.get("retreinar_ate") and meta["retreinar_ate"] < date.today().strftime("%Y-%m"):
            avisos.append(f"Modelo com retreino vencido (previsto até {meta['retreinar_ate']}).")

        pop = cid.get("populacao")
        incid = round(pred / pop * 100_000, 2) if pop else None

        teste = hmeta.get("metricas_teste_2025")
        val = var.get("metricas_validacao") or {}
        if teste:
            nota = (f"Modelo validado no ano de 2025 (teste único): MAE {teste['mae']:.1f} casos/mês, "
                    f"R² {teste['r2']:.2f}, Skill vs. persistência {teste['skill_score']:.2f}.")
        elif val:
            nota = (f"Métricas de validação 2018–2024: MAE {val['mae']:.1f}, R² {val['r2']:.2f}. "
                    "Teste final em 2025 ainda não executado.")
        else:
            nota = "Métricas de validação indisponíveis."

        return PredictResponse(
            **base,
            cidade=cid.get("nome"),
            mes_alvo=_fmt_mes(alvo_ano, alvo_mes),
            ultimo_mes_observado=_fmt_mes(*ult) if ult else None,
            casos_previstos=int(round(pred)),
            intervalo_confianca=[lo, hi],
            nivel_risco=classificar_risco(pred, cid["p50"], cid["p75"], cid["p90"]),
            incidencia_prevista_100k=incid,
            modelo_usado=var["modelo"],
            confiabilidade="baixa" if baixa else "normal",
            avisos=avisos,
            nota=nota,
        )


_PREDITOR: Preditor | None = None
_PREDITOR_LOCK = threading.Lock()


def get_preditor() -> Preditor:
    """Singleton usado pela API (carrega painel e modelos sob demanda)."""
    global _PREDITOR
    if _PREDITOR is None:
        with _PREDITOR_LOCK:
            if _PREDITOR is None:
                _PREDITOR = Preditor()
    return _PREDITOR
