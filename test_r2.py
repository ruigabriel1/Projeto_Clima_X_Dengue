import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import r2_score
from pathlib import Path

BASE_DIR = Path.cwd()
from src.processamento.motor_lote_modelagem_v2_por_latitude import build_base_panel
painel, _ = build_base_panel(BASE_DIR)

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

FEATURES = ['temp_lag3', 'prec_lag3', 'enso_lag3', 'latitude', 'max_historico', 'casos_lag1', 'casos_lag12']
TARGET = 'dengue_cases'

treino = df_ml[df_ml['year'] < 2024].copy()
teste = df_ml[df_ml['year'] == 2024].copy()

X_treino = treino[FEATURES]
y_treino = treino[TARGET]
X_teste = teste[FEATURES]
y_teste = teste[TARGET]

# Testar Tweedie Regression e parametros otimizados para R2
model = xgb.XGBRegressor(
    objective='reg:tweedie',
    tweedie_variance_power=1.5,
    n_estimators=500,
    learning_rate=0.05,
    max_depth=8,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model.fit(X_treino, y_treino)
pred = model.predict(X_teste)
r2_tweedie = r2_score(y_teste, pred)

# Testar Squarederror normal com hiperparametros mais agressivos
model2 = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=800,
    learning_rate=0.05,
    max_depth=8,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42
)
model2.fit(X_treino, y_treino)
pred2 = model2.predict(X_teste)
r2_normal = r2_score(y_teste, pred2)

print(f"R2 Tweedie: {r2_tweedie}")
print(f"R2 Normal (Agressivo): {r2_normal}")
