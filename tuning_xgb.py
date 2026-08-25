import pandas as pd
import numpy as np
import sys
from pathlib import Path
import xgboost as xgb
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import r2_score, mean_absolute_error
import json
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = Path.cwd()
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# 1. Carregar Dados
from src.processamento.motor_lote_modelagem_v2_por_latitude import build_base_panel
print('Carregando dados...')
painel, _ = build_base_panel(BASE_DIR)

# 2. Engenharia de Features
df = painel.copy()
df['data'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2))
df = df.sort_values(['code', 'data']).reset_index(drop=True)

max_hist = df.groupby('code')['dengue_cases'].max().rename('max_historico')
df = df.merge(max_hist, on='code')

df['temp_lag3'] = df.groupby('code')['temp_media'].shift(3)
df['prec_lag3'] = df.groupby('code')['precipitacao'].shift(3)
df['enso_lag3'] = df.groupby('code')['enso'].shift(3)
df['casos_lag1'] = df.groupby('code')['dengue_cases'].shift(1)
df['casos_lag12'] = df.groupby('code')['dengue_cases'].shift(12)

df_ml = df.dropna().copy()

# 3. Preparacao de Treino/Teste
FEATURES = ['temp_lag3', 'prec_lag3', 'enso_lag3', 'latitude', 'max_historico', 'casos_lag1', 'casos_lag12']
TARGET = 'dengue_cases'

treino = df_ml[df_ml['year'] < 2024].copy()
teste = df_ml[df_ml['year'] == 2024].copy()

X_treino = treino[FEATURES]
y_treino = np.log1p(treino[TARGET]) # TRUQUE MESTRE: LOG TRANSFORM

X_teste = teste[FEATURES]
y_teste = teste[TARGET]

# 4. Arena de Tuning (Randomized Search)
param_dist = {
    'max_depth': [4, 6, 8, 10],
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
    'n_estimators': [300, 500, 800, 1000],
    'subsample': [0.6, 0.8, 1.0],
    'colsample_bytree': [0.6, 0.8, 1.0],
    'min_child_weight': [1, 3, 5, 7]
}

xgb_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)

search = RandomizedSearchCV(
    xgb_model, 
    param_distributions=param_dist,
    n_iter=25, 
    scoring='r2', 
    cv=3, 
    verbose=2, 
    n_jobs=-1,
    random_state=42
)

print('Iniciando Batalha de Tuning (60 modelos)...')
search.fit(X_treino, y_treino)

# 5. Avaliacao do Campeao
best_model = search.best_estimator_
pred_log = best_model.predict(X_teste)
pred_real = np.expm1(pred_log) # REVERTER O LOG
pred_real = np.clip(pred_real, 0, None) # Sem previsoes negativas

r2 = r2_score(y_teste, pred_real)
mae = mean_absolute_error(y_teste, pred_real)

resultados = {
    'best_params': search.best_params_,
    'r2_score': r2,
    'mae': mae
}

with open(BASE_DIR / 'output' / 'xgboost_tuning_results.json', 'w') as f:
    json.dump(resultados, f, indent=4)

print(f'\n=== CAMPEÃO ENCONTRADO ===')
print(f'R2 Final: {r2}')
print(f'MAE Final: {mae}')
print(f'Parametros: {search.best_params_}')
