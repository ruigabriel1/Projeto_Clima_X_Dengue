"""
Módulo de Feature Engineering.
Responsável por criar as features (lags, médias móveis, sazonalidade, umidade) 
garantindo que não haja vazamento de dados futuros.
"""
import numpy as np
import pandas as pd

def build_ml_features(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói as features para o modelo preditivo.
    Adiciona lags de 1 a 3 meses, features sazonais e de memória epidêmica.
    """
    d = panel.copy().sort_values(["code", "year", "month"]).reset_index(drop=True)
    
    # Sazonalidade trigonométrica
    d["month_sin"] = np.sin(2.0 * np.pi * d["month"] / 12.0)
    d["month_cos"] = np.cos(2.0 * np.pi * d["month"] / 12.0)
    
    # Lags do alvo (Inércia da doença)
    d["dengue_lag1"] = d.groupby("code")["dengue_cases"].shift(1)
    d["dengue_lag2"] = d.groupby("code")["dengue_cases"].shift(2)
    d["dengue_lag3"] = d.groupby("code")["dengue_cases"].shift(3)
    
    # Lags climáticos
    d["temp_lag1"] = d.groupby("code")["temp_media"].shift(1)
    d["temp_lag2"] = d.groupby("code")["temp_media"].shift(2)
    d["temp_lag3"] = d.groupby("code")["temp_media"].shift(3)
    
    d["prec_lag1"] = d.groupby("code")["precipitacao"].shift(1)
    d["prec_lag2"] = d.groupby("code")["precipitacao"].shift(2)
    d["prec_lag3"] = d.groupby("code")["precipitacao"].shift(3)
    
    # ENSO Lags
    d["enso_lag1"] = d.groupby("code")["enso"].shift(1)
    d["enso_lag2"] = d.groupby("code")["enso"].shift(2)
    d["enso_lag3"] = d.groupby("code")["enso"].shift(3)
    
    # Proxy de Umidade (Temperatura x Precipitação) nos meses anteriores
    d["umidade_proxy_lag1"] = d["temp_lag1"] * d["prec_lag1"]
    d["umidade_proxy_lag2"] = d["temp_lag2"] * d["prec_lag2"]
    d["umidade_proxy_lag3"] = d["temp_lag3"] * d["prec_lag3"]
    
    # Memória epidêmica (Média móvel)
    d["dengue_rolling_12"] = d.groupby("code")["dengue_cases"].transform(
        lambda x: x.rolling(12, min_periods=3).mean()
    )
    d["dengue_rolling_12"] = d["dengue_rolling_12"].fillna(0.0)
    
    # Flag Sazonal (Verão/Outono tem maior peso epidêmico)
    d["is_outbreak_season"] = d["month"].isin([1, 2, 3, 4, 5]).astype(float)
    
    # Drop rows without enough lag history (first 3 months will be dropped)
    cols_to_drop_na = [
        "dengue_lag3", "temp_lag3", "prec_lag3", "enso_lag3"
    ]
    d = d.dropna(subset=cols_to_drop_na).copy()
    
    return d
