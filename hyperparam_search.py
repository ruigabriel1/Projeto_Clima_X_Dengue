import sys
sys.path.insert(0, ".")
from src.processamento.motor_lote_modelagem_v2_por_latitude import build_base_panel
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import r2_score
from pathlib import Path
import pandas as pd

def run_search():
    from src.processamento.motor_lote_modelagem_v2_por_latitude import _build_ml_features
    
    print("Construindo painel (São Carlos)...")
    panel, _ = build_base_panel(Path("."), modo="rapido")
    
    feat = _build_ml_features(panel)
    
    # Treino só até 2025
    train_data = feat[feat["year"] <= 2025]
    
    # Definir colunas base
    X_cols = [
        "temp_media", "precipitacao", "enso", "latitude", "month_sin", "month_cos",
        "dengue_lag1", "dengue_lag2", "dengue_lag3", "temp_lag1", "prec_lag1", "enso_lag1",
        "dengue_rolling_12",
    ]
    
    X = train_data[X_cols]
    y = train_data["dengue_cases"]
    groups = train_data["year"].values
    
    print(f"Dados para Grid Search: {len(X)} amostras")
    
    best_r2 = -999
    best_params = {}
    logo = LeaveOneGroupOut()
    
    for n_est in [50, 100, 200]:
        for max_d in [3, 5, 8]:
            for min_sl in [2, 3]:
                for max_f in ["sqrt", 1.0]:
                    model = RandomForestRegressor(
                        n_estimators=n_est, max_depth=max_d, 
                        min_samples_leaf=min_sl, max_features=max_f, 
                        random_state=42, n_jobs=-1
                    )
                    
                    y_true_all, y_pred_all = [], []
                    
                    for train_idx, test_idx in logo.split(X, y, groups):
                        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
                        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]
                        
                        model.fit(X_train, y_train)
                        preds = model.predict(X_test)
                        
                        y_true_all.extend(y_test)
                        y_pred_all.extend(preds)
                    
                    r2 = r2_score(y_true_all, y_pred_all)
                    if r2 > best_r2:
                        best_r2 = r2
                        best_params = {'n_estimators': n_est, 'max_depth': max_d, 'min_samples_leaf': min_sl, 'max_features': max_f}
                        print(f"NOVO MELHOR R2: {best_r2:.4f} com {best_params}", flush=True)

    print("Busca finalizada.", flush=True)

if __name__ == "__main__":
    run_search()
