"""
Orquestrador MLOps principal v4 (multi-doença).
Acopla ingestão, validação, engenharia de features, treino e avaliação.

Modos de execução:
  - "regional"  → todas as cidades do painel (≈1.190 municípios)
  - "rapido"    → filtra uma cidade para debug rápido

Doenças suportadas:
  - dengue | chikungunya | zika | todas (loop)

Mudanças v4:
  - Aceita --doenca para rodar o pipeline por doença.
  - "todas" itera sobre dengue + chikungunya + zika.
  - Nomes de arquivos (modelo, log) incluem a doença.
  - Passa target_col correto ao feature_engineering, training e baselines.
"""
from pathlib import Path
import logging
import json
import sys

import pandas as pd

from src.config import ANO_HOLDOUT
from src.ml_pipeline.data_ingestion import build_base_panel, validate_panel, DOENCAS
from src.ml_pipeline.feature_engineering import (
    build_ml_features, get_feature_columns, DOENCA_PARA_COL,
)
from src.ml_pipeline.model_training import train_model
from src.ml_pipeline.baselines import evaluate_baselines

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _run_single_disease(
    panel: pd.DataFrame,
    doenca: str,
    root_dir: Path,
    modo: str,
    validation_report: dict,
):
    """Executa o pipeline para uma doença específica."""

    target_col = DOENCA_PARA_COL[doenca]
    logger.info("=" * 50)
    logger.info(f"=== Doença: {doenca.upper()} (alvo: {target_col}) ===")
    logger.info("=" * 50)

    # Verificar se a coluna existe no painel
    if target_col not in panel.columns:
        logger.warning(f"Coluna {target_col} ausente do painel. Pulando {doenca}.")
        return None, None

    # Verificar se há dados suficientes (não todos nulos)
    n_validos = panel[target_col].notna().sum()
    n_positivos = (panel[target_col] > 0).sum()
    logger.info(f"  {doenca}: {n_validos} registros válidos, {n_positivos} com casos > 0")
    if n_positivos < 50:
        logger.warning(f"Dados insuficientes para {doenca} ({n_positivos} positivos). Pulando.")
        return None, None

    # ==============================
    # 3. Feature Engineering
    # ==============================
    logger.info(f"[FASE 3] Engenharia de Features ({doenca})...")
    df_features = build_ml_features(panel, doenca=doenca)

    feature_cols = get_feature_columns(df_features, doenca=doenca)

    # Remove apenas linhas sem alvo. NaN nas features é informação ("sem histórico")
    # e o XGBoost trata nativamente; o GLM imputa internamente com medianas do treino.
    df_train = df_features.dropna(subset=[target_col]).copy()
    logger.info(f"Matriz de treino ({doenca}): {len(df_train)} linhas × {len(feature_cols)} features")
    logger.info(f"Features ({doenca}): {feature_cols}")

    if len(df_train) < 100:
        logger.error(f"Dados insuficientes para {doenca} ({len(df_train)} linhas). Pulando.")
        return None, None

    # ==============================
    # 4. Treinamento + Validação
    # ==============================
    logger.info(f"[FASE 4] Treinamento e Validação ({doenca})...")

    model_path = root_dir / "output" / "models" / f"xgboost_poisson_{doenca}_v4.joblib"

    model, metrics, feature_importance, oof_a = train_model(
        df=df_train,
        feature_cols=feature_cols,
        target_col=target_col,
        save_path=model_path,
        return_oof=True,
        max_test_year=ANO_HOLDOUT - 1,   # 2025 é holdout do experimento final: não validar nele
    )
    backtest_dir = root_dir / "output" / "backtest"
    backtest_dir.mkdir(parents=True, exist_ok=True)
    oof_a.to_csv(backtest_dir / f"oof_modeloA_{doenca}.csv", index=False)

    # ==============================
    # 5. Baselines
    # ==============================
    logger.info(f"[FASE 5] Avaliando baselines ({doenca})...")
    try:
        baseline_results = evaluate_baselines(df_train, target_col)
    except Exception as e:
        logger.warning(f"Baselines falharam para {doenca}: {e}")
        baseline_results = []

    # ==============================
    # 6. Interpretabilidade (SHAP + PDPs)
    # ==============================
    interp_report = {}
    logger.info(f"[FASE 6] Interpretabilidade ({doenca})...")
    try:
        from src.ml_pipeline.interpretability import run_interpretability
        interp_dir = root_dir / "output" / "interpretability"
        interp_report = run_interpretability(
            model=model,
            df=df_train,
            feature_cols=feature_cols,
            output_dir=interp_dir,
            doenca=doenca,
        )
    except Exception as e:
        logger.warning(f"Interpretabilidade falhou para {doenca}: {e}")

    # ==============================
    # 7. Salvar relatório
    # (O Modelo B "só clima" e as projeções SSP foram removidos na v5: ver
    #  docs/PLANO_V5_LIMPEZA_PUBLICAVEL.md, Step 1.)
    # ==============================
    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    run_log = {
        "pipeline_version": "v4.1",
        "doenca": doenca,
        "target_col": target_col,
        "modo": modo,
        "n_cidades": int(df_train["code"].nunique()),
        "n_samples": len(df_train),
        "n_features": len(feature_cols),
        "features": feature_cols,
        "validation": validation_report,
        "metrics_por_ano": metrics,
        "baselines_por_ano": baseline_results,
        "feature_importance": feature_importance[:20],
        "interpretability": interp_report,
    }

    log_file = output_dir / f"ml_run_log_{doenca}_v4.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"  Modelo salvo: {model_path}")
    logger.info(f"  Log salvo: {log_file}")

    return model, run_log


def run_pipeline(
    root_dir: Path,
    modo: str = "regional",
    doenca: str = "dengue",
):
    """
    Executa o pipeline completo de ML (hiperparâmetros fixos, sem tunagem).

    Args:
        root_dir: raiz do projeto.
        modo: "regional" (completo) ou "rapido" (1 cidade para debug).
        doenca: "dengue" | "chikungunya" | "zika" | "todas".

    Returns:
        results — dict de {doença: (model, run_log)}.
    """
    logger.info("=" * 60)
    logger.info("=== Pipeline ML v4 (XGBoost Poisson + Multi-Doença) ===")
    logger.info("=" * 60)

    # ==============================
    # 1. Ingestão
    # ==============================
    logger.info("[FASE 1] Ingestão do painel base...")
    panel = build_base_panel(root_dir, modo=modo)

    if modo == "rapido":
        # Debug: filtra a cidade com mais dados (Joinville = 420910)
        if "420910" in panel["code"].values:
            panel = panel[panel["code"] == "420910"].copy()
        elif not panel.empty:
            first_code = panel["code"].iloc[0]
            panel = panel[panel["code"] == first_code].copy()

    if panel.empty:
        logger.error("Painel vazio após ingestão! Abortando.")
        return {}

    logger.info(f"Painel: {len(panel)} linhas × {len(panel.columns)} colunas, {panel['code'].nunique()} cidades")

    # ==============================
    # 2. Validação
    # ==============================
    logger.info("[FASE 2] Validação do painel...")
    try:
        validation_report = validate_panel(panel)
    except ValueError as e:
        logger.error(f"Validação falhou: {e}")
        return {}

    # ==============================
    # 3-6. Loop por doença
    # ==============================
    doencas_para_rodar = list(DOENCA_PARA_COL.keys()) if doenca == "todas" else [doenca]
    results = {}

    for d in doencas_para_rodar:
        if d not in DOENCA_PARA_COL:
            logger.error(f"Doença '{d}' não reconhecida. Opções: {list(DOENCA_PARA_COL.keys())} ou 'todas'.")
            continue
        model, run_log = _run_single_disease(
            panel=panel,
            doenca=d,
            root_dir=root_dir,
            modo=modo,
            validation_report=validation_report,
        )
        if model is not None:
            results[d] = (model, run_log)

    logger.info("=" * 60)
    logger.info(f"=== Pipeline v4 Finalizado! Doenças treinadas: {list(results.keys())} ===")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline ML v4 - Arboviroses × Clima")
    parser.add_argument("--modo", default="regional", choices=["regional", "rapido"])
    parser.add_argument(
        "--doenca",
        default="dengue",
        choices=["dengue", "chikungunya", "zika", "todas"],
        help="Doença-alvo (ou 'todas' para loop)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent.parent
    run_pipeline(root, modo=args.modo, doenca=args.doenca)
