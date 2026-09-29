"""
Orquestrador MLOps principal.
Acopla a ingestão, engenharia de features, treino e avaliação.
"""
from pathlib import Path
import logging
import json

from src.ml_pipeline.data_ingestion import build_base_panel
from src.ml_pipeline.feature_engineering import build_ml_features
from src.ml_pipeline.model_training import train_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_pipeline(root_dir: Path, modo="rapido", tune_hyperparams=True):
    logger.info("=== Iniciando Pipeline MLOps (XGBoost Poisson) ===")
    
    # 1. Ingestão
    panel = build_base_panel(root_dir, modo=modo)
    if modo == "rapido":
        panel = panel[panel["code"] == "421600"].copy()
        
    if panel.empty:
        logger.error("Painel vazio! Abortando.")
        return

    # 2. Engenharia de Features
    logger.info("Executando Feature Engineering (Lags profundos + Umidade)...")
    df_features = build_ml_features(panel)
    
    # Prepara matrizes
    target_col = "dengue_cases"
    feature_cols = [c for c in df_features.columns if c not in ["code", "city_name", "lat_faixa_id", "date", target_col]]
    
    df_train = df_features.dropna(subset=feature_cols + [target_col])
    X = df_train[feature_cols]
    y = df_train[target_col]
    groups = df_train["year"]
    
    logger.info(f"Matriz X: {X.shape}, Alvo y: {y.shape}")

    # 3. Treinamento com LOYO, Clipping 2024 e Tuning
    logger.info("Iniciando Fase de Treinamento e Avaliação (LOYO)...")
    model, metrics, feature_importance = train_model(X, y, groups, tune_hyperparams=tune_hyperparams)
    
    # 4. Salvar logs de execução (Rastreabilidade MLOps)
    log_file = root_dir / "output" / "ml_run_log.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Salvar o modelo matemático compilado
    model_file = root_dir / "output" / "xgboost_poisson_model.json"
    model.save_model(model_file)
    logger.info(f"Modelo salvo com sucesso em {model_file}")
    
    run_log = {
        "modo": modo,
        "n_samples": len(X),
        "features": feature_cols,
        "metrics": metrics,
        "feature_importance": feature_importance
    }
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=4, ensure_ascii=False)
        
    logger.info(f"=== Pipeline Finalizado! Log salvo em {log_file} ===")
    return model, run_log

if __name__ == "__main__":
    # Teste isolado do novo pipeline (Modo Rápido - São Carlos)
    root = Path(__file__).resolve().parent.parent.parent
    run_pipeline(root, modo="rapido", tune_hyperparams=True)
