import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
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

# SPATIAL SPLIT (Split by cities, not by time)
cidades = df_ml['code'].unique()
cidades_treino, cidades_teste = train_test_split(cidades, test_size=0.2, random_state=42)

treino = df_ml[df_ml['code'].isin(cidades_treino)].copy()
teste = df_ml[df_ml['code'].isin(cidades_teste)].copy()

X_treino = treino[FEATURES]
y_treino = treino[TARGET]
X_teste = teste[FEATURES]
y_teste = teste[TARGET]

model = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=8,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model.fit(X_treino, y_treino)
pred = model.predict(X_teste)
r2_espacial = r2_score(y_teste, pred)

# RANDOM SPLIT (Mistura tudo)
X = df_ml[FEATURES]
y = df_ml[TARGET]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

model_rand = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=8,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model_rand.fit(X_tr, y_tr)
pred_rand = model_rand.predict(X_te)
r2_random = r2_score(y_te, pred_rand)

print(f"R2 Spatial Split: {r2_espacial}")
print(f"R2 Random Split: {r2_random}")
