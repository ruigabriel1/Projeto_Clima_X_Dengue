"""
Módulo de treinamento do motor de ML.
Isola o algoritmo e a tunagem de hiperparâmetros (XGBoost Regressor Poisson).
Lida com a anomalia de 2024 usando Clipping de threshold seguro.
"""
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import LeaveOneGroupOut, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def clip_outliers(y: np.ndarray, percentile: float = 99.0) -> np.ndarray:
    """Aplica clipping para domar os picos anômalos extremos (ex: 2024)."""
    if len(y) == 0:
        return y
    p99 = np.percentile(y, percentile)
    return np.clip(y, 0, p99)

def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 1.0
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)

def train_model(X, y, groups, tune_hyperparams=False):
    """
    Treina o modelo XGBoost com Poisson Objective, validação LOYO (Leave One Year Out)
    e suporta tunagem automática.
    """
    # 1. Tratamento da anomalia de 2024 via Clipping
    # Evitamos que picos absurdos destruam o gradiente, limitando ao p99 (q99)
    y_clipped = clip_outliers(y.values)
    
    logo = LeaveOneGroupOut()
    metrics = []
    
    # Modelo Base - O Poisson é vital para não gerar previsões negativas
    # e domar a inflação de zeros na base
    base_model = xgb.XGBRegressor(
        objective="count:poisson",
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="poisson-nloglik"
    )

    if tune_hyperparams:
        print("[INFO] Tuning hyperparams for XGBoost Poisson...")
        param_grid = {
            'max_depth': [3, 4, 5, 6],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'n_estimators': [50, 100, 150, 200],
            'subsample': [0.7, 0.8, 0.9],
            'colsample_bytree': [0.7, 0.8, 0.9]
        }
        # Random search to save time while still exploring broadly
        search = RandomizedSearchCV(
            base_model, param_distributions=param_grid, 
            n_iter=10, cv=logo, scoring='neg_mean_absolute_error',
            random_state=42, n_jobs=-1
        )
        search.fit(X, y_clipped, groups=groups)
        best_model = search.best_estimator_
        print(f"[INFO] Best Params: {search.best_params_}")
    else:
        best_model = base_model
        
    print("[Iniciando Validação Cruzada Anual (LOYO)]")
    
    # 2. LOYO Cross-Validation para métricas rigorosas
    # Precisamos validar o modelo "O-of-Bag" (OOB) ano a ano
    for train_idx, test_idx in logo.split(X, y_clipped, groups):
        X_train, y_train = X.iloc[train_idx], y_clipped[train_idx]
        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx].values # Valida no valor real (sem clipping)
        year_test = int(groups.iloc[test_idx].unique()[0])

        model_loyo = xgb.XGBRegressor(**best_model.get_params())
        model_loyo.fit(X_train, y_train)
        
        preds = model_loyo.predict(X_test)
        
        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        metrics.append({
            "year": year_test,
            "r2": r2,
            "mae": mae,
            "mape": _safe_mape(y_test, preds),
            "rmse": np.sqrt(mean_squared_error(y_test, preds))
        })
        print(f"[INFO]   LOYO {year_test}: R²={r2:.3f} MAE={mae:.1f} (n={len(y_test)})")
        
    avg_r2 = np.mean([m["r2"] for m in metrics])
    avg_mae = np.mean([m["mae"] for m in metrics])
    print(f"[INFO] LOYO Final - R² Médio: {avg_r2:.3f} | MAE Médio: {avg_mae:.1f}")

    # 3. Treino Final Retraining no dataset completo (com clipping)
    print("[INFO] Treinando Modelo Unificado no Dataset Completo...")
    best_model.fit(X, y_clipped)
    
    # 4. Feature Importance
    importance_dict = dict(zip(X.columns, best_model.feature_importances_))
    sorted_fi = sorted(importance_dict.items(), key=lambda item: item[1], reverse=True)
    
    return best_model, metrics, sorted_fi
