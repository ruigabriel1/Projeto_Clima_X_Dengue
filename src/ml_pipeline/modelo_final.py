"""
Fase 4.1 — Modelo final para produção (docs/PLANO_EXPERIMENTO_FINAL.md).

Retreina a configuração escolhida no painel completo (2015–2025) para cada doença e
cada horizonte (1, 2, 3 meses). Se a configuração usa clima, treina também a variante
SEM clima, usada como fallback quando faltam dados climáticos.

Artefatos em output/models/final/<doenca>/:
  h<h>_principal.joblib, h<h>_sem_clima.joblib (se aplicável)
  metadata.json  — config, features, métricas (validação e teste 2025), calibração do
                   intervalo de confiança, estatísticas por cidade (nome, limiares de risco,
                   R² fora-da-amostra), data dos dados e prazo de retreino.

Intervalo de confiança (90%): quantis 5%/95% do resíduo em escala log1p,
log1p(real) − log1p(previsto), no OOF de validação 2018–2024 da mesma configuração,
estratificados por faixa de valor previsto (o erro cresce com a magnitude).
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from src.config import ANO_HOLDOUT, BASE_DIR, HORIZONTES, OUTPUT_EXPERIMENTO, OUTPUT_MODELOS_FINAIS
from src.ml_pipeline.experimento_horizontes import (
    CLIP_PERCENTIL, configurar_log, git_commit, nome_config, preparar_dados,
)
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, get_feature_columns
from src.ml_pipeline.model_training import XGB_PARAMS, fit_predict_fold

logger = logging.getLogger(__name__)

N_BINS_INTERVALO = 5
Q_INTERVALO = (0.05, 0.95)
MESES_RETREINO = 12
MIN_MESES_COM_CASO = 6       # abaixo disso, a previsão da cidade recebe aviso


def calibrar_intervalo(y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = N_BINS_INTERVALO) -> dict:
    """Quantis do resíduo log1p por faixa de valor previsto. Bordas por quantil de y_pred."""
    y_true = np.asarray(y_true, float)
    y_pred = np.asarray(y_pred, float)
    res = np.log1p(y_true) - np.log1p(y_pred)
    bordas = np.unique(np.quantile(y_pred, np.linspace(0, 1, n_bins + 1)[1:-1]))
    idx = np.searchsorted(bordas, y_pred, side="right")
    q_lo, q_hi = [], []
    for b in range(len(bordas) + 1):
        r = res[idx == b]
        if len(r) < 20:          # bin pequeno: usa o resíduo global
            r = res
        q_lo.append(float(np.quantile(r, Q_INTERVALO[0])))
        q_hi.append(float(np.quantile(r, Q_INTERVALO[1])))
    cobertura = None
    if len(res):
        lo = np.asarray(q_lo)[idx]
        hi = np.asarray(q_hi)[idx]
        cobertura = float(np.mean((res >= lo) & (res <= hi)))
    return {"bordas_pred": bordas.tolist(), "q_lo": q_lo, "q_hi": q_hi,
            "nivel": Q_INTERVALO[1] - Q_INTERVALO[0], "cobertura_oof": cobertura}


def estatisticas_cidades(panel: pd.DataFrame, alvo: str, oofs: dict[int, pd.DataFrame]) -> dict:
    """Nome, limiares de risco (histórico completo) e R² OOF por horizonte para cada cidade."""
    hist = panel.dropna(subset=[alvo])
    q = hist.groupby("code")[alvo].quantile([0.5, 0.75, 0.9]).unstack()
    meses_caso = hist.assign(pos=hist[alvo] > 0).groupby("code")["pos"].sum()
    nomes = hist.groupby("code")["city_name"].last() if "city_name" in hist else pd.Series(dtype=str)
    pops = hist.sort_values(["year", "month"]).groupby("code")["populacao"].last() \
        if "populacao" in hist else pd.Series(dtype=float)

    r2_h = {}
    for h, oof in oofs.items():
        r2_h[h] = oof.groupby("code").apply(
            lambda g: r2_score(g["y_true"], g["y_pred"]) if g["y_true"].nunique() > 1 else np.nan,
            include_groups=False,
        )

    out = {}
    for code in q.index:
        out[str(code)] = {
            "nome": None if pd.isna(nomes.get(code)) else str(nomes.get(code)),
            "populacao": None if pd.isna(pops.get(code, np.nan)) else int(pops.get(code)),
            "p50": float(q.loc[code, 0.5]), "p75": float(q.loc[code, 0.75]), "p90": float(q.loc[code, 0.9]),
            "meses_com_caso": int(meses_caso.get(code, 0)),
            "r2_oof": {f"h{h}": (None if pd.isna(s.get(code, np.nan)) else round(float(s.get(code)), 3))
                       for h, s in r2_h.items()},
        }
    return out


def treinar_modelos_finais(
    panel: pd.DataFrame,
    config: dict,
    out_dir: Path = OUTPUT_MODELOS_FINAIS,
    exp_dir: Path = OUTPUT_EXPERIMENTO,
    horizontes=HORIZONTES,
) -> dict:
    """Treina e salva os modelos de produção. Retorna {doenca: metadata}."""
    dev = pd.read_csv(exp_dir / "resultados.csv") if (exp_dir / "resultados.csv").exists() else None
    teste_path = exp_dir / "teste_final_2025.json"
    teste = json.loads(teste_path.read_text(encoding="utf-8")) if teste_path.exists() else None
    if teste is None:
        logger.warning("Teste final 2025 ainda não executado: metadata terá só métricas de validação.")

    ano_max = int(panel["year"].max())
    todas = {}
    for doenca, dec in config["doencas"].items():
        alvo = DOENCA_PARA_COL[doenca]
        dest = out_dir / doenca
        dest.mkdir(parents=True, exist_ok=True)
        variantes = {"principal": dec["usar_clima"]}
        if dec["usar_clima"]:
            variantes["sem_clima"] = False

        meta = {
            "doenca": doenca,
            "treinado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
            "git_commit": git_commit(),
            "config": {"usar_clima": dec["usar_clima"], "corte_p99": dec["corte_p99"]},
            "xgb_params": XGB_PARAMS,
            "anos_treino": [int(panel["year"].min()), ano_max],
            "retreinar_ate": (pd.Timestamp.now() + pd.DateOffset(months=MESES_RETREINO)).strftime("%Y-%m"),
            "horizontes": {},
        }
        oofs = {}
        for h in horizontes:
            df = preparar_dados(panel, doenca, h, ano_max)
            ultimo = df.loc[df[alvo].notna(), ["year", "month"]].max()
            hmeta = {"variantes": {}}
            for var, usar_clima in variantes.items():
                feats = get_feature_columns(df, doenca=doenca, usar_clima=usar_clima)
                model, _ = fit_predict_fold(df, df.iloc[:1], feats, alvo, CLIP_PERCENTIL if dec["corte_p99"] else None)
                arq = dest / f"h{h}_{var}.joblib"
                joblib.dump(model, arq)
                nome = nome_config(usar_clima, dec["corte_p99"])

                intervalo, val = None, None
                oof_path = exp_dir / f"oof_{doenca}_h{h}.csv.gz"
                if oof_path.exists():
                    oof = pd.read_csv(oof_path, dtype={"code": str})
                    intervalo = calibrar_intervalo(oof["y_true"], oof[f"pred_{nome}"])
                    if var == "principal":
                        oofs[h] = oof.rename(columns={f"pred_{nome}": "y_pred"})[["code", "y_true", "y_pred"]]
                if dev is not None:
                    r = dev[(dev["doenca"] == doenca) & (dev["horizonte"] == h) & (dev["modelo"] == nome)]
                    if len(r):
                        val = r.iloc[0][["mae", "r2", "mae_surto", "skill_score", "auc_risco_alto"]].astype(float).round(4).to_dict()
                hmeta["variantes"][var] = {
                    "arquivo": arq.name, "modelo": nome, "usar_clima": usar_clima,
                    "features": feats, "intervalo": intervalo, "metricas_validacao": val,
                }
                logger.info(f"  {doenca} h={h} {var}: {len(feats)} features, {len(df)} linhas → {arq.name}")
            if teste:
                hmeta["metricas_teste_2025"] = (
                    teste["doencas"].get(doenca, {}).get("horizontes", {}).get(f"h{h}", {}).get("teste_2025")
                )
            hmeta["ultimo_mes_treino"] = f"{int(ultimo['year'])}-{int(ultimo['month']):02d}"
            meta["horizontes"][f"h{h}"] = hmeta

        meta["cidades"] = estatisticas_cidades(panel, alvo, oofs)
        (dest / "metadata.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
        todas[doenca] = meta
        logger.info(f"Modelos finais de {doenca} salvos em {dest}")
    return todas


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fase 4.1 — retreino final (2015–2025) para produção")
    ap.add_argument("--sem-teste", action="store_true",
                    help="Permite treinar antes do teste final 2025 (só para desenvolvimento)")
    args = ap.parse_args(argv)
    configurar_log()

    from src.ml_pipeline.data_ingestion import build_base_panel
    from src.ml_pipeline.teste_final import carregar_config

    if not (OUTPUT_EXPERIMENTO / "teste_final_2025.json").exists() and not args.sem_teste:
        raise SystemExit("Rode a Fase 3 (python main.py teste-final --confirmar) antes, ou use --sem-teste.")
    cfg = carregar_config(OUTPUT_EXPERIMENTO)
    panel = build_base_panel(BASE_DIR)
    if int(panel["year"].max()) < ANO_HOLDOUT:
        logger.warning(f"Painel termina antes de {ANO_HOLDOUT}.")
    treinar_modelos_finais(panel, cfg)


if __name__ == "__main__":
    main()
