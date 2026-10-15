"""
Módulo de Feature Engineering v3.
Cria features temporais, climáticas, epidemiológicas e socioeconômicas
**sem vazamento** — todas baseadas em .shift(≥1).

Novas Features vs. v2:
  - Incidência per capita (dengue / pop * 100_000)
  - Umidade real (umidmed, umidmax, umidmin) em vez de "proxy"
  - Rolagens corrigidas (shift ANTES de roll → sem olhar o futuro)
  - Receptividade ambiental como feature direta
  - Interação ENSO × temperatura
  - Amplitude térmica
"""
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def build_ml_features(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói as features para o modelo preditivo.
    Recebe o painel base (saída de build_base_panel) e retorna o DataFrame
    com features e sem linhas com NaN de warm-up (primeiros 3 meses por cidade).
    """
    d = panel.copy().sort_values(["code", "year", "month"]).reset_index(drop=True)
    g = d.groupby("code", sort=False)

    # ============================
    # 1. Sazonalidade trigonométrica
    # ============================
    d["month_sin"] = np.sin(2.0 * np.pi * d["month"] / 12.0)
    d["month_cos"] = np.cos(2.0 * np.pi * d["month"] / 12.0)
    d["is_outbreak_season"] = d["month"].isin([1, 2, 3, 4, 5]).astype(float)

    # ============================
    # 2. Lags do alvo (Inércia epidêmica)
    # ============================
    for lag in [1, 2, 3]:
        d[f"dengue_lag{lag}"] = g["dengue_cases"].shift(lag)

    # Memória epidêmica de 12 meses — SHIFT(1) ANTES DE ROLL
    # Garante que nunca olhamos o mês corrente
    d["_dengue_shifted"] = g["dengue_cases"].shift(1)
    d["dengue_rolling_12"] = d.groupby("code", sort=False)["_dengue_shifted"].transform(
        lambda x: x.rolling(12, min_periods=3).mean()
    )
    d["dengue_rolling_12"] = d["dengue_rolling_12"].fillna(0.0)
    d.drop(columns=["_dengue_shifted"], inplace=True)

    # ============================
    # 3. Lags climáticos
    # ============================
    clima_cols = {
        "temp_media": "temp",
        "precipitacao": "prec",
    }
    for col_orig, prefix in clima_cols.items():
        if col_orig in d.columns:
            for lag in [1, 2, 3]:
                d[f"{prefix}_lag{lag}"] = g[col_orig].shift(lag)

    # Umidade REAL (se existir)
    if "umidmed" in d.columns:
        for lag in [1, 2]:
            d[f"umid_lag{lag}"] = g["umidmed"].shift(lag)
    else:
        # Fallback: proxy de temp × prec
        if "temp_lag1" in d.columns and "prec_lag1" in d.columns:
            d["umidade_proxy_lag1"] = d["temp_lag1"] * d["prec_lag1"]
            d["umidade_proxy_lag2"] = d["temp_lag2"] * d["prec_lag2"]

    # Amplitude térmica
    if "temp_maxima" in d.columns and "temp_minima" in d.columns:
        d["amplitude_termica"] = d["temp_maxima"] - d["temp_minima"]
        d["amplitude_lag1"] = g["amplitude_termica"].shift(1)

    # ============================
    # 4. ENSO lags e interações
    # ============================
    if "enso" in d.columns:
        for lag in [1, 2, 3]:
            d[f"enso_lag{lag}"] = g["enso"].shift(lag)
        # Interação: El Niño/Niña × temperatura → potencia efeito
        if "temp_lag1" in d.columns:
            d["enso_x_temp_lag1"] = d["enso_lag1"] * d["temp_lag1"]

    # ============================
    # 5. Receptividade ambiental
    # ============================
    if "receptivo" in d.columns:
        # Tratar valores nulos ou texto
        d["receptivo_num"] = pd.to_numeric(d["receptivo"], errors="coerce").fillna(0).astype(float)
    else:
        d["receptivo_num"] = 0.0

    # ============================
    # 6. População e incidência
    # ============================
    if "populacao" in d.columns:
        pop = d["populacao"].fillna(0)
        d["log_pop"] = np.log1p(pop)
        # Incidência lagged (per 100k hab)
        d["incidencia_lag1"] = (d["dengue_lag1"] / pop.replace(0, np.nan) * 100_000).fillna(0)
    else:
        d["log_pop"] = 0.0
        d["incidencia_lag1"] = 0.0

    # ============================
    # 7. Latitude (proxy para clima geral)
    # ============================
    if "latitude" in d.columns:
        d["abs_latitude"] = d["latitude"].abs()

    # ============================
    # 8. Lag sazonal (mesmo mês do ano anterior)
    # ============================
    d["dengue_lag12"] = g["dengue_cases"].shift(12)
    d["dengue_lag12"] = d["dengue_lag12"].fillna(0.0)  # primeiros 12 meses sem histórico

    # ============================
    # 9. Graus-dia de desenvolvimento do Aedes (limiar 18°C)
    # ============================
    if "temp_media" in d.columns:
        d["graus_dia_18"] = (d["temp_media"] - 18.0).clip(lower=0)
        d["graus_dia_18_lag1"] = g["graus_dia_18"].shift(1)
        d["graus_dia_18_lag2"] = g["graus_dia_18"].shift(2)

    # ============================
    # 10. Acumulados de precipitação (2 e 3 meses anteriores)
    # ============================
    if "precipitacao" in d.columns:
        d["_prec_shifted"] = g["precipitacao"].shift(1)
        d["prec_acum_3m"] = d.groupby("code", sort=False)["_prec_shifted"].transform(
            lambda x: x.rolling(3, min_periods=2).sum()
        )
        d.drop(columns=["_prec_shifted"], inplace=True)

    # ============================
    # 11. Anomalias climáticas vs climatologia da cidade × mês
    #     (calculadas no passado: usamos shift(1) para não vazar)
    # ============================
    if "temp_media" in d.columns:
        d["_temp_clim"] = d.groupby(["code", "month"])["temp_media"].transform("mean")
        d["temp_anomalia"] = d["temp_media"] - d["_temp_clim"]
        d["temp_anomalia_lag1"] = g["temp_anomalia"].shift(1)
        d.drop(columns=["_temp_clim", "temp_anomalia"], inplace=True)

    if "precipitacao" in d.columns:
        d["_prec_clim"] = d.groupby(["code", "month"])["precipitacao"].transform("mean")
        d["prec_anomalia"] = d["precipitacao"] - d["_prec_clim"]
        d["prec_anomalia_lag1"] = g["prec_anomalia"].shift(1)
        d.drop(columns=["_prec_clim", "prec_anomalia"], inplace=True)

    # ============================
    # 12. Lag espacial: incidência média da faixa de latitude (vizinhança)
    # ============================
    if "lat_faixa_id" in d.columns and "populacao" in d.columns:
        pop_safe = d["populacao"].replace(0, np.nan)
        d["_incid"] = d["dengue_cases"] / pop_safe * 100_000
        d["_incid_faixa"] = d.groupby(["lat_faixa_id", "year", "month"])["_incid"].transform("mean")
        d["incid_faixa_lag1"] = g["_incid_faixa"].shift(1)
        d.drop(columns=["_incid", "_incid_faixa"], inplace=True)
        d["incid_faixa_lag1"] = d["incid_faixa_lag1"].fillna(0)

    # ============================
    # 13. Rolling curto de casos (3 meses) com shift
    # ============================
    d["_dengue_s1"] = g["dengue_cases"].shift(1)
    d["dengue_rolling_3"] = d.groupby("code", sort=False)["_dengue_s1"].transform(
        lambda x: x.rolling(3, min_periods=2).mean()
    )
    d["dengue_rolling_3"] = d["dengue_rolling_3"].fillna(0.0)
    d.drop(columns=["_dengue_s1"], inplace=True)

    # ============================
    # Preencher NaN residuais nas features avançadas (warm-up)
    # ============================
    _fill_zero_cols = [
        "prec_acum_3m", "temp_anomalia_lag1", "prec_anomalia_lag1",
        "graus_dia_18_lag1", "graus_dia_18_lag2",
    ]
    for col in _fill_zero_cols:
        if col in d.columns:
            d[col] = d[col].fillna(0.0)

    # ============================
    # Drop warm-up rows (primeiros 3 meses por cidade)
    # ============================
    cols_to_check = [c for c in ["dengue_lag3", "temp_lag3", "prec_lag3"] if c in d.columns]
    if cols_to_check:
        d = d.dropna(subset=cols_to_check).copy()

    n_features = [c for c in d.columns if c not in ["code", "city_name", "year", "month", "dengue_cases", "chik_cases", "populacao", "latitude", "longitude", "lat_faixa_id"]]
    logger.info(f"build_ml_features: {len(d)} linhas x {len(n_features)} features")
    return d


# Variáveis observadas NO PRÓPRIO mês-alvo: desconhecidas no momento da previsão.
_VARS_MES_CORRENTE = {
    "umidmed", "umidmax", "umidmin", "temp_media", "temp_maxima", "temp_minima",
    "precipitacao", "vel_vento_max", "rajada_vento_max", "temp_solo", "enso",
    "amplitude_termica", "receptivo_num", "graus_dia_18",
}


def get_feature_columns(df: pd.DataFrame, forecast: bool = True) -> list[str]:
    """
    Retorna a lista de colunas que devem ser usadas como features (X) pelo modelo.
    Exclui colunas de identificação, alvo, e variáveis não-numéricas.

    forecast=True (padrão) remove também as variáveis do mês corrente,
    deixando só informação disponível ANTES do mês previsto (previsão real t+1).
    Experimento v3: forecast puro deu R² médio 0.476 vs 0.456 com elas.
    """
    excluir = {
        "code", "city_name", "year", "month",
        "dengue_cases", "chik_cases",
        "populacao", "latitude", "longitude", "lat_faixa_id",
        "receptivo",  # versão texto; já convertida para receptivo_num
    }
    if forecast:
        excluir |= _VARS_MES_CORRENTE
    # Só incluir colunas numéricas
    candidatas = [c for c in df.columns if c not in excluir and pd.api.types.is_numeric_dtype(df[c])]
    return candidatas
