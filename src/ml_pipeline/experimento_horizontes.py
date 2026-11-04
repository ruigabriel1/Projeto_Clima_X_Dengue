"""
Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md).

Fatores:  doença {dengue, chikungunya} × horizonte {1, 2, 3} × clima {com, sem} × corte P99 {com, sem}
          = 24 modelos XGBoost Poisson (hiperparâmetros fixos) + baselines por doença × horizonte
          (persistência = casos[t−h]; sazonal = casos[t−12]).

Validação: expanding window, folds de teste 2018..2024. O ano de 2025 (holdout) é REMOVIDO
do painel antes de qualquer cálculo. Todas as configurações de uma mesma doença × horizonte
são avaliadas exatamente nas mesmas linhas.

Saídas em output/experimento/:
  resultados.csv          1 linha por (doença, horizonte, modelo) — métricas no OOF agregado 2018–2024
  resultados_por_ano.csv  mesmas métricas por fold
  oof_<doenca>_h<h>.csv.gz  previsões fora-da-amostra (base para análise, intervalos e SHAP)
  experimento_meta.json   parâmetros, features, commit, tempo de execução
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    ANO_HOLDOUT, DOENCAS_EXPERIMENTO, HORIZONTES, OUTPUT_EXPERIMENTO, BASE_DIR,
)
from src.ml_pipeline.data_ingestion import build_base_panel
from src.ml_pipeline.feature_engineering import (
    DOENCA_PARA_COL, PREFIXOS, build_ml_features, get_feature_columns,
)
from src.ml_pipeline.metricas import Q_RISCO, Q_SURTO, avaliar_criterios, calcular_metricas
from src.ml_pipeline.model_training import (
    XGB_PARAMS, _expanding_window_splits, fit_predict_fold, limiares_por_cidade,
)

logger = logging.getLogger(__name__)

CLIP_PERCENTIL = 99.0
# (usar_clima, corte_p99)
CONFIGS = [(True, True), (True, False), (False, True), (False, False)]


def nome_config(usar_clima: bool, corte_p99: bool) -> str:
    return f"xgb_{'clima' if usar_clima else 'semclima'}_{'p99' if corte_p99 else 'semcorte'}"


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=BASE_DIR, text=True
        ).strip()
    except Exception:
        return None


def preparar_dados(panel: pd.DataFrame, doenca: str, horizonte: int, ano_max: int) -> pd.DataFrame:
    """Features para (doença, h) usando só anos ≤ ano_max; remove linhas sem alvo."""
    alvo = DOENCA_PARA_COL[doenca]
    p = panel[panel["year"] <= ano_max]
    df = build_ml_features(p, doenca=doenca, horizonte=horizonte)
    return df.dropna(subset=[alvo]).reset_index(drop=True)


def rodar_doenca_horizonte(
    df: pd.DataFrame,
    doenca: str,
    horizonte: int,
    max_test_year: int,
) -> tuple[pd.DataFrame, dict]:
    """
    Roda os 4 modelos + 2 baselines em todos os folds. Retorna (oof_wide, features_por_config).
    oof_wide: uma linha por cidade × mês de teste, com y_true, limiares, baselines e
    uma coluna de previsão por configuração.
    """
    alvo = DOENCA_PARA_COL[doenca]
    p = PREFIXOS[alvo]
    feats = {
        nome_config(c, k): get_feature_columns(df, doenca=doenca, usar_clima=c)
        for c, k in CONFIGS
    }
    partes = []
    for train_mask, test_mask, ano in _expanding_window_splits(df["year"], 3, max_test_year):
        df_tr, df_te = df[train_mask], df[test_mask]
        t0 = time.time()
        parte = pd.DataFrame({
            "code": df_te["code"].values,
            "year": df_te["year"].values,
            "month": df_te["month"].values,
            "y_true": df_te[alvo].to_numpy(dtype=float),
            "limiar_surto": limiares_por_cidade(df_tr, df_te["code"], alvo, Q_SURTO),
            "limiar_risco": limiares_por_cidade(df_tr, df_te["code"], alvo, Q_RISCO),
            "y_persistencia": df_te[f"{p}_lag{horizonte}"].to_numpy(dtype=float),
            "y_sazonal": df_te[f"{p}_lag12"].to_numpy(dtype=float),
        })
        for usar_clima, corte in CONFIGS:
            nome = nome_config(usar_clima, corte)
            _, preds = fit_predict_fold(
                df_tr, df_te, feats[nome], alvo,
                clip_percentile=CLIP_PERCENTIL if corte else None,
            )
            parte[f"pred_{nome}"] = preds
        partes.append(parte)
        logger.info(f"    {doenca} h={horizonte} fold {ano}: {len(df_te)} linhas, {time.time() - t0:.1f}s")
    return pd.concat(partes, ignore_index=True), feats


def _linha(doenca, h, modelo, usar_clima, corte, n_feat, oof, col_pred) -> dict:
    m = calcular_metricas(
        oof["y_true"], oof[col_pred], oof["y_persistencia"], oof["limiar_surto"], oof["limiar_risco"]
    )
    return {
        "doenca": doenca, "horizonte": h, "modelo": modelo,
        "usar_clima": usar_clima, "corte_p99": corte, "n_features": n_feat,
        **m, **avaliar_criterios(m, doenca),
    }


def metricas_de_oof(oof: pd.DataFrame, doenca: str, h: int, feats: dict) -> list[dict]:
    """Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline."""
    linhas = []
    for usar_clima, corte in CONFIGS:
        nome = nome_config(usar_clima, corte)
        linhas.append(_linha(doenca, h, nome, usar_clima, corte, len(feats[nome]), oof, f"pred_{nome}"))
    linhas.append(_linha(doenca, h, "persistencia", None, None, 0, oof, "y_persistencia"))
    linhas.append(_linha(doenca, h, "sazonal", None, None, 0, oof, "y_sazonal"))
    return linhas


def run_experimento(
    root_dir: Path = BASE_DIR,
    doencas=DOENCAS_EXPERIMENTO,
    horizontes=HORIZONTES,
    n_cidades: int | None = None,
    out_dir: Path = OUTPUT_EXPERIMENTO,
    panel: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Executa o experimento completo e grava os resultados. Retorna o DataFrame de resultados."""
    t_ini = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    ano_max_dev = ANO_HOLDOUT - 1

    if panel is None:
        panel = build_base_panel(root_dir)
    panel = panel[panel["year"] <= ano_max_dev].copy()   # holdout fora, antes de tudo
    if n_cidades:
        codes = sorted(panel["code"].unique())
        rng = np.random.default_rng(42)
        panel = panel[panel["code"].isin(rng.choice(codes, n_cidades, replace=False))]
        logger.info(f"Modo amostra: {n_cidades} cidades")

    logger.info(
        f"Painel dev: {len(panel)} linhas, {panel['code'].nunique()} cidades, "
        f"{panel['year'].min()}–{panel['year'].max()}"
    )

    resultados, por_ano, meta_feats = [], [], {}
    for doenca in doencas:
        for h in horizontes:
            logger.info(f"=== {doenca} | horizonte {h} ===")
            df = preparar_dados(panel, doenca, h, ano_max_dev)
            oof, feats = rodar_doenca_horizonte(df, doenca, h, ano_max_dev)
            oof.to_csv(out_dir / f"oof_{doenca}_h{h}.csv.gz", index=False)
            meta_feats[f"{doenca}_h{h}"] = feats

            resultados += metricas_de_oof(oof, doenca, h, feats)
            for ano, g in oof.groupby("year"):
                for linha in metricas_de_oof(g, doenca, h, feats):
                    por_ano.append({"ano_teste": int(ano), **linha})

    res = pd.DataFrame(resultados)
    res.to_csv(out_dir / "resultados.csv", index=False)
    pd.DataFrame(por_ano).to_csv(out_dir / "resultados_por_ano.csv", index=False)

    meta = {
        "executado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duracao_min": round((time.time() - t_ini) / 60, 1),
        "git_commit": git_commit(),
        "anos_painel": [int(panel["year"].min()), int(panel["year"].max())],
        "ano_holdout_excluido": ANO_HOLDOUT,
        "folds_teste": sorted(int(a) for a in pd.DataFrame(por_ano)["ano_teste"].unique()),
        "n_cidades": int(panel["code"].nunique()),
        "amostra_cidades": n_cidades,
        "xgb_params": XGB_PARAMS,
        "clip_percentil": CLIP_PERCENTIL,
        "q_surto": Q_SURTO, "q_risco": Q_RISCO,
        "features": meta_feats,
    }
    (out_dir / "experimento_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    logger.info(f"Experimento concluído em {meta['duracao_min']} min → {out_dir / 'resultados.csv'}")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fase 1 — experimento horizontes × clima × corte P99")
    ap.add_argument("--doenca", choices=list(DOENCAS_EXPERIMENTO) + ["todas"], default="todas")
    ap.add_argument("--horizonte", type=int, choices=list(HORIZONTES), default=None)
    ap.add_argument("--amostra", type=int, default=None, help="Rodar com N cidades (teste rápido)")
    args = ap.parse_args(argv)

    configurar_log()
    doencas = DOENCAS_EXPERIMENTO if args.doenca == "todas" else (args.doenca,)
    horizontes = HORIZONTES if args.horizonte is None else (args.horizonte,)
    out = OUTPUT_EXPERIMENTO if args.amostra is None else OUTPUT_EXPERIMENTO / f"amostra_{args.amostra}"
    res = run_experimento(doencas=doencas, horizontes=horizontes, n_cidades=args.amostra, out_dir=out)
    cols = ["doenca", "horizonte", "modelo", "mae", "r2", "skill_score", "auc_risco_alto", "passa_todos"]
    print(res[cols].to_string(index=False, float_format=lambda v: f"{v:.3f}"))


def configurar_log():
    """Log INFO em stdout UTF-8 (o console do Windows usa cp1252 por padrão)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout)], force=True)


if __name__ == "__main__":
    main()
