"""
Orquestrador MLOps principal v3.
Acopla ingestão, validação, engenharia de features, treino e avaliação.

Modos de execução:
  - "regional"  → todas as cidades do painel (≈1.190 municípios)
  - "rapido"    → filtra uma cidade para debug rápido

Mudanças v3:
  - Usa validate_panel() após ingestão.
  - Usa get_feature_columns() para selecionar features de forma segura.
  - Expanding Window CV (via model_training v3).
  - Salva modelo .joblib e relatório .json.
"""
from pathlib import Path
import logging
import json
import sys

from src.ml_pipeline.data_ingestion import build_base_panel, validate_panel
from src.ml_pipeline.feature_engineering import build_ml_features, get_feature_columns
from src.ml_pipeline.model_training import train_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_pipeline(
    root_dir: Path,
    modo: str = "regional",
    tune_hyperparams: bool = False,
):
    """
    Executa o pipeline completo de ML.

    Args:
        root_dir: raiz do projeto.
        modo: "regional" (completo) ou "rapido" (1 cidade para debug).
        tune_hyperparams: se True, faz RandomizedSearchCV.

    Returns:
        model, run_log  (ou None, None em caso de erro).
    """
    logger.info("=" * 60)
    logger.info("=== Pipeline ML v3 (XGBoost Poisson + Expanding Window) ===")
    logger.info("=" * 60)

    # ==============================
    # 1. Ingestão
    # ==============================
    logger.info("[FASE 1] Ingestão do painel base...")
    panel = build_base_panel(root_dir, modo=modo)

    if modo == "rapido":
        # Debug: filtra a cidade com mais dados (Joinville = 420910)
        panel = panel[panel["code"] == "420910"].copy()
        if panel.empty:
            # Fallback: primeira cidade disponível
            first_code = panel["code"].iloc[0] if not panel.empty else None
            if first_code:
                panel = panel[panel["code"] == first_code].copy()

    if panel.empty:
        logger.error("Painel vazio após ingestão! Abortando.")
        return None, None

    logger.info(f"Painel: {len(panel)} linhas × {len(panel.columns)} colunas, {panel['code'].nunique()} cidades")

    # ==============================
    # 2. Validação
    # ==============================
    logger.info("[FASE 2] Validação do painel...")
    try:
        validation_report = validate_panel(panel)
    except ValueError as e:
        logger.error(f"Validação falhou: {e}")
        return None, None

    # ==============================
    # 3. Feature Engineering
    # ==============================
    logger.info("[FASE 3] Engenharia de Features...")
    df_features = build_ml_features(panel)

    feature_cols = get_feature_columns(df_features)
    target_col = "dengue_cases"

    # Garantir que não há NaN nas features
    df_train = df_features.dropna(subset=feature_cols + [target_col]).copy()
    logger.info(f"Matriz de treino: {len(df_train)} linhas × {len(feature_cols)} features")
    logger.info(f"Features: {feature_cols}")

    if len(df_train) < 100:
        logger.error(f"Dados insuficientes ({len(df_train)} linhas). Abortando.")
        return None, None

    # ==============================
    # 4. Treinamento + Validação
    # ==============================
    logger.info("[FASE 4] Treinamento e Validação (Expanding Window)...")

    model_path = root_dir / "output" / "models" / "xgboost_poisson_v3.joblib"

    model, metrics, feature_importance = train_model(
        df=df_train,
        feature_cols=feature_cols,
        target_col=target_col,
        tune_hyperparams=tune_hyperparams,
        save_path=model_path,
    )

    # ==============================
    # 5. Salvar relatório de execução
    # ==============================
    logger.info("[FASE 5] Salvando relatório de execução...")

    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    run_log = {
        "pipeline_version": "v3",
        "modo": modo,
        "n_cidades": int(df_train["code"].nunique()),
        "n_samples": len(df_train),
        "n_features": len(feature_cols),
        "features": feature_cols,
        "validation": validation_report,
        "metrics_por_ano": metrics,
        "feature_importance": feature_importance[:20],  # top 20
    }

    log_file = output_dir / "ml_run_log_v3.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"=== Pipeline v3 Finalizado! ===")
    logger.info(f"  Modelo: {model_path}")
    logger.info(f"  Log: {log_file}")

    return model, run_log


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline ML v3 - Dengue × Clima")
    parser.add_argument("--modo", default="regional", choices=["regional", "rapido"])
    parser.add_argument("--tune", action="store_true", help="Tunar hiperparâmetros")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent.parent
    run_pipeline(root, modo=args.modo, tune_hyperparams=args.tune)
