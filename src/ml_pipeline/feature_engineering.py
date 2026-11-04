"""
Módulo de Feature Engineering v4 (multi-doença, multi-horizonte).

Princípios:
  - Toda feature usada na previsão é calculada com informação de até t-h,
    onde h é o horizonte de previsão (h=1 → prever o mês seguinte).
  - Features epidemiológicas são geradas para TODAS as doenças do painel
    (dengue, chikungunya, zika). A seleção de quais entram no modelo é feita
    em get_feature_columns(), conforme a doença-alvo.
  - Valores ausentes por falta de histórico (ex.: lag12 no primeiro ano) ficam
    como NaN. O XGBoost trata NaN nativamente; preencher com 0 seria afirmar
    "zero casos", o que é falso.
  - Climatologia para anomalias é EXPANDING (só anos anteriores), sem olhar o futuro.

Duas tarefas:
  - Modelo A (previsão): get_feature_columns(df, doenca, horizonte)
  - Modelo B (clima → risco, cenários SSP): get_climate_feature_columns(df)
"""
import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Coluna de casos -> prefixo das features
PREFIXOS = {
    "dengue_cases": "dengue",
    "chik_cases": "chik",
    "zika_cases": "zika",
}
DOENCA_PARA_COL = {"dengue": "dengue_cases", "chikungunya": "chik_cases", "zika": "zika_cases"}

# Variáveis observadas NO PRÓPRIO mês-alvo: desconhecidas no momento da previsão.
_VARS_MES_CORRENTE = {
    "umidmed", "umidmax", "umidmin", "temp_media", "temp_maxima", "temp_minima",
    "precipitacao", "vel_vento_max", "rajada_vento_max", "temp_solo", "enso",
    "amplitude_termica", "receptivo_num", "graus_dia_18",
}

_META = {
    "code", "city_name", "year", "month", "populacao", "latitude", "lat_faixa_id",
    "receptivo",  # versão bruta; usamos receptivo_num
}


def _roll_shifted(d: pd.DataFrame, col: str, shift: int, window: int, min_periods: int, how: str = "mean"):
    """Rolling por cidade aplicado sobre a série já deslocada (nunca inclui t..t-shift+1)."""
    s = d.groupby("code", sort=False)[col].shift(shift)
    r = s.groupby(d["code"], sort=False).rolling(window, min_periods=min_periods)
    r = r.mean() if how == "mean" else r.sum()
    return r.reset_index(level=0, drop=True).sort_index()


def _anomalia_expanding(d: pd.DataFrame, col: str) -> pd.Series:
    """
    Anomalia = valor - média do MESMO mês nos anos ANTERIORES da mesma cidade.
    Primeiro ano de cada cidade fica NaN (sem climatologia prévia).
    """
    clim = d.groupby(["code", "month"], sort=False)[col].transform(
        lambda x: x.shift(1).expanding().mean()
    )
    return d[col] - clim


def build_ml_features(panel: pd.DataFrame, doenca: str = "dengue", horizonte: int = 1) -> pd.DataFrame:
    """
    Constrói as features a partir do painel base.

    Args:
        panel: saída de build_base_panel (ou painel sintético nos testes).
        doenca: "dengue" | "chikungunya" | "zika" — define quais linhas de warm-up remover.
        horizonte: h ≥ 1. Lags começam em h (prever t usando até t-h).
    """
    if horizonte < 1:
        raise ValueError("horizonte deve ser >= 1")
    h = horizonte
    alvo = DOENCA_PARA_COL[doenca]
    if alvo not in panel.columns:
        raise ValueError(f"Coluna-alvo '{alvo}' ausente do painel.")

    d = panel.copy().sort_values(["code", "year", "month"]).reset_index(drop=True)
    g = d.groupby("code", sort=False)
    has_pop = "populacao" in d.columns
    pop = d["populacao"].replace(0, np.nan) if has_pop else None

    # ---------- 1. Sazonalidade ----------
    d["month_sin"] = np.sin(2.0 * np.pi * d["month"] / 12.0)
    d["month_cos"] = np.cos(2.0 * np.pi * d["month"] / 12.0)
    d["is_outbreak_season"] = d["month"].isin([1, 2, 3, 4, 5]).astype(float)

    # ---------- 2. Memória epidêmica (todas as doenças) ----------
    for col, p in PREFIXOS.items():
        if col not in d.columns:
            continue
        for k in (h, h + 1, h + 2):
            d[f"{p}_lag{k}"] = g[col].shift(k)
        if h <= 12:
            d[f"{p}_lag12"] = g[col].shift(12)
        d[f"{p}_rolling_3"] = _roll_shifted(d, col, h, 3, 2)
        d[f"{p}_rolling_12"] = _roll_shifted(d, col, h, 12, 3)
        if has_pop:
            d[f"{p}_incid_lag{h}"] = d[f"{p}_lag{h}"] / pop * 100_000

    # ---------- 3. Lag espacial: incidência média da faixa de latitude ----------
    if "lat_faixa_id" in d.columns and has_pop:
        p_alvo = PREFIXOS[alvo]
        incid = d[alvo] / pop * 100_000
        faixa = incid.groupby([d["lat_faixa_id"], d["year"], d["month"]]).transform("mean")
        d[f"{p_alvo}_incid_faixa_lag{h}"] = faixa.groupby(d["code"], sort=False).shift(h)

    # ---------- 4. Clima: lags ----------
    clima_lags = {
        "temp_media": ("temp", 3),
        "precipitacao": ("prec", 3),
        "umidmed": ("umid", 2),
        "temp_maxima": ("tmax", 1),
        "temp_minima": ("tmin", 1),
        "temp_solo": ("tsolo", 1),
        "vel_vento_max": ("vento", 1),
    }
    for col, (p, n) in clima_lags.items():
        if col in d.columns:
            for k in range(h, h + n):
                d[f"{p}_lag{k}"] = g[col].shift(k)

    if "temp_maxima" in d.columns and "temp_minima" in d.columns:
        d["amplitude_termica"] = d["temp_maxima"] - d["temp_minima"]
        d[f"amplitude_lag{h}"] = g["amplitude_termica"].shift(h)

    if "temp_media" in d.columns:
        # Graus-dia acima de 18 °C (limiar de desenvolvimento do Aedes aegypti)
        d["graus_dia_18"] = (d["temp_media"] - 18.0).clip(lower=0)
        for k in (h, h + 1):
            d[f"graus_dia_18_lag{k}"] = g["graus_dia_18"].shift(k)
        d["_temp_anom"] = _anomalia_expanding(d, "temp_media")
        d[f"temp_anomalia_lag{h}"] = g["_temp_anom"].shift(h)

    if "precipitacao" in d.columns:
        d[f"prec_acum_3m_lag{h}"] = _roll_shifted(d, "precipitacao", h, 3, 2, how="sum")
        d["_prec_anom"] = _anomalia_expanding(d, "precipitacao")
        d[f"prec_anomalia_lag{h}"] = g["_prec_anom"].shift(h)

    d = d.drop(columns=[c for c in ("_temp_anom", "_prec_anom") if c in d.columns])

    # ---------- 5. ENSO (efeito defasado de vários meses) ----------
    if "enso" in d.columns:
        for k in range(h, h + 6):
            d[f"enso_lag{k}"] = g["enso"].shift(k)
        if f"temp_lag{h}" in d.columns:
            d[f"enso_x_temp_lag{h}"] = d[f"enso_lag{h}"] * d[f"temp_lag{h}"]

    # ---------- 6. Receptividade (InfoDengue) ----------
    if "receptivo" in d.columns:
        d["receptivo_num"] = pd.to_numeric(d["receptivo"], errors="coerce").astype(float)
        d[f"receptivo_lag{h}"] = d.groupby("code", sort=False)["receptivo_num"].shift(h)

    # ---------- 7. Estáticas da cidade ----------
    if has_pop:
        d["log_pop"] = np.log1p(d["populacao"].fillna(0))
    if "latitude" in d.columns:
        d["abs_latitude"] = d["latitude"].abs()

    # ---------- Warm-up: remove linhas sem o histórico mínimo da doença-alvo ----------
    p_alvo = PREFIXOS[alvo]
    d = d[d[f"{p_alvo}_lag{h + 2}"].notna()].copy()

    logger.info(f"build_ml_features[{doenca}, h={h}]: {len(d)} linhas x {d.shape[1]} colunas")
    return d


def _prefixo_doenca(col: str):
    for p in PREFIXOS.values():
        if col.startswith(p + "_"):
            return p
    return None


# Prefixos de features derivadas de clima (inclui ENSO e a receptividade do InfoDengue,
# que é um índice calculado a partir de temperatura/umidade). Usado no experimento
# "com vs. sem clima": sem clima = só histórico de casos + sazonalidade + geografia.
_PREFIXOS_CLIMA = (
    "temp_", "prec_", "umid_", "tmax_", "tmin_", "tsolo_", "vento_",
    "amplitude_", "graus_dia_18", "enso_", "receptivo_",
)


def is_climate_feature(col: str) -> bool:
    """True se a feature é derivada de variáveis climáticas/ENSO."""
    return col.startswith(_PREFIXOS_CLIMA)


def get_feature_columns(
    df: pd.DataFrame,
    forecast: bool = True,
    doenca: str = "dengue",
    usar_clima: bool = True,
) -> list[str]:
    """
    Features do Modelo A (previsão).

    - Inclui toda a memória epidêmica da doença-alvo.
    - Das outras doenças (mesmo vetor, co-circulação, confusão diagnóstica), inclui
      apenas o lag mais recente e a média de 3 meses. Zika só entra como feature
      no modelo da própria zika (a série termina em 2024).
    - forecast=True remove variáveis do mês corrente (desconhecidas na previsão).
    - usar_clima=False remove todas as features climáticas (ver is_climate_feature).
    """
    p_alvo = PREFIXOS[DOENCA_PARA_COL[doenca]]
    excluir = set(_META) | set(PREFIXOS.keys())
    if forecast:
        excluir |= _VARS_MES_CORRENTE

    candidatas = [
        c for c in df.columns
        if c not in excluir and pd.api.types.is_numeric_dtype(df[c])
        and (usar_clima or not is_climate_feature(c))
    ]

    # Menor lag disponível por doença (depende do horizonte)
    menor_lag = {}
    for c in candidatas:
        m = re.fullmatch(r"(dengue|chik|zika)_lag(\d+)", c)
        if m:
            p, k = m.group(1), int(m.group(2))
            menor_lag[p] = min(k, menor_lag.get(p, 999))

    out = []
    for c in candidatas:
        p = _prefixo_doenca(c)
        if p is None or p == p_alvo:
            out.append(c)
        elif p == "zika":
            continue
        elif c in (f"{p}_rolling_3", f"{p}_lag{menor_lag.get(p)}"):
            out.append(c)
    return out


# Features do Modelo B: apenas clima, sazonalidade e contexto da cidade.
# Nenhuma informação de casos (nem lags). É o que permite projetar cenários SSP,
# onde não existe "caso do mês anterior".
_FEATURES_MODELO_B = [
    "temp_media", "temp_maxima", "temp_minima", "precipitacao", "umidmed",
    "graus_dia_18", "amplitude_termica",
    "temp_lag1", "temp_lag2", "prec_lag1", "prec_lag2", "graus_dia_18_lag1",
    "prec_acum_3m_lag1",
    "enso", "enso_lag1", "enso_lag2", "enso_lag3",
    "month_sin", "month_cos",
    "abs_latitude", "longitude", "log_pop",
]


def get_climate_feature_columns(df: pd.DataFrame) -> list[str]:
    """Features do Modelo B (clima → risco). Requer build_ml_features(..., horizonte=1)."""
    return [c for c in _FEATURES_MODELO_B if c in df.columns]
