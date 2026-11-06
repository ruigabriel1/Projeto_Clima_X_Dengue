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

Seleção de features para previsão: get_feature_columns(df, doenca, usar_clima).
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

# Limiar fixo de "mês epidêmico" para as features de suscetibilidade (casos por 100 mil hab./mês)
LIMIAR_SURTO_100K = 100.0

# Variáveis observadas NO PRÓPRIO mês-alvo: desconhecidas no momento da previsão.
_VARS_MES_CORRENTE = {
    "umidmed", "umidmax", "umidmin", "temp_media", "temp_maxima", "temp_minima",
    "precipitacao", "vel_vento_max", "rajada_vento_max", "temp_solo", "enso",
    "amplitude_termica", "receptivo_num", "graus_dia_18",
}

_META = {
    "code", "city_name", "year", "month", "populacao", "latitude", "lat_faixa_id",
    "receptivo",  # versão bruta; usamos receptivo_num
    # Alerta oficial do InfoDengue do PRÓPRIO mês: benchmark, nunca feature (seria vazamento).
    "NIVEL_DENGUE", "NIVEL_CHIKUNGUNYA", "NIVEL_ZIKA",
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


N_VIZINHOS = 8   # protocolo v6


def _incidencia_vizinhos(d: pd.DataFrame, alvo: str, k: int = N_VIZINHOS) -> pd.Series | None:
    """
    Incidência agregada (casos / pop × 100 mil) das k cidades mais próximas (haversine), no MESMO mês.
    O deslocamento para t−h é feito por quem chama. Cidades sem coordenada ficam NaN.
    """
    coords = d.groupby("code", sort=False)[["latitude", "longitude"]].first().dropna()
    if len(coords) <= k:
        return None
    lat, lon = np.radians(coords["latitude"].to_numpy()), np.radians(coords["longitude"].to_numpy())
    dlat, dlon = lat[:, None] - lat[None, :], lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2) ** 2
    dist = 2 * np.arcsin(np.sqrt(a))
    np.fill_diagonal(dist, np.inf)
    viz = np.argsort(dist, axis=1)[:, :k]                          # (n_cidades, k)
    t = (d["year"] * 12 + d["month"]).to_numpy()
    casos = d.pivot_table(index=t, columns="code", values=alvo, aggfunc="sum").reindex(columns=coords.index)
    pops = d.assign(_p=d["populacao"].where(d[alvo].notna())).pivot_table(
        index=t, columns="code", values="_p", aggfunc="sum").reindex(columns=coords.index)
    c, p = casos.to_numpy(float), pops.to_numpy(float)              # (meses, cidades)
    soma_c = np.nansum(c[:, viz], axis=2)                          # (meses, cidades)
    soma_p = np.nansum(p[:, viz], axis=2)
    with np.errstate(invalid="ignore", divide="ignore"):
        inc = np.where(soma_p > 0, soma_c / soma_p * 100_000, np.nan)
    tab = pd.DataFrame(inc, index=casos.index, columns=coords.index).stack(future_stack=True)
    chave = pd.MultiIndex.from_arrays([t, d["code"]])
    return pd.Series(tab.reindex(chave).to_numpy(), index=d.index)


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

    # ---------- 6b. Suscetibilidade (proxy de imunidade de rebanho), protocolo v5 ----------
    # Incidência acumulada em 12/24/36 meses terminando em t−h e meses desde o último mês
    # com incidência ≥ LIMIAR_SURTO_100K (limiar fixo: não usa quantis, logo não vaza).
    if has_pop:
        p_alvo = PREFIXOS[alvo]
        d["_incid"] = d[alvo] / pop * 100_000
        for janela in (12, 24, 36):
            d[f"{p_alvo}_susc_acum{janela}_lag{h}"] = _roll_shifted(
                d, "_incid", h, janela, max(3, janela // 2), how="sum"
            )
        surto = (d["_incid"] >= LIMIAR_SURTO_100K).astype(float).where(d["_incid"].notna())
        # índice do mês (contínuo) e índice do último surto até o mês corrente
        idx = (d["year"] * 12 + d["month"]).astype(float)
        ultimo = idx.where(surto == 1.0).groupby(d["code"], sort=False).ffill()
        meses_desde = (idx - ultimo)          # 0 no próprio mês do surto, NaN se nunca houve
        d[f"{p_alvo}_susc_meses_desde_surto_lag{h}"] = (
            meses_desde.groupby(d["code"], sort=False).shift(h) + h
        ).clip(upper=60)
        d = d.drop(columns=["_incid"])

    # ---------- 6c. Protocolo v6: vizinhos (V) e imunidade longa (L) ----------
    # Desligadas por padrão em get_feature_columns (vizinhos=False, imunidade_longa=False).
    if has_pop:
        p_alvo = PREFIXOS[alvo]
        d["_incid"] = d[alvo] / pop * 100_000
        for janela in (48, 60):
            d[f"{p_alvo}_imun_acum{janela}_lag{h}"] = _roll_shifted(d, "_incid", h, janela, janela // 2, how="sum")
        # imunidade do estado: incidência da UF (casos/pop da UF) acumulada em 24 meses até t−h
        uf = d["code"].astype(str).str[:2]
        chave = [uf, d["year"], d["month"]]
        casos_uf = d[alvo].groupby(chave).transform("sum")
        pop_uf = pop.where(d[alvo].notna()).groupby(chave).transform("sum")
        d["_inc_uf"] = casos_uf / pop_uf * 100_000
        d[f"{p_alvo}_imun_uf_acum24_lag{h}"] = _roll_shifted(d, "_inc_uf", h, 24, 12, how="sum")
        if {"latitude", "longitude"} <= set(d.columns):
            viz = _incidencia_vizinhos(d, alvo)
            if viz is not None:
                d["_inc_viz"] = viz
                d[f"{p_alvo}_viz_incid_lag{h}"] = d.groupby("code", sort=False)["_inc_viz"].shift(h)
                d[f"{p_alvo}_viz_incid_media3_lag{h}"] = _roll_shifted(d, "_inc_viz", h, 3, 2)
        d = d.drop(columns=[c for c in ("_incid", "_inc_uf", "_inc_viz") if c in d.columns])

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


def is_clima_parcimonioso(col: str) -> bool:
    """Conjunto climático a priori do protocolo v5: só temp média e precipitação defasadas."""
    return re.fullmatch(r"(temp|prec)_lag\d+", col) is not None


def is_suscetibilidade(col: str) -> bool:
    return "_susc_" in col


def is_vizinhos(col: str) -> bool:
    """Protocolo v6, grupo V."""
    return "_viz_" in col


def is_imunidade_longa(col: str) -> bool:
    """Protocolo v6, grupo L."""
    return "_imun_" in col


def get_feature_columns(
    df: pd.DataFrame,
    forecast: bool = True,
    doenca: str = "dengue",
    usar_clima: bool = True,
    clima: str | None = None,
    suscetibilidade: bool = False,
    vizinhos: bool = False,
    imunidade_longa: bool = False,
) -> list[str]:
    """
    Features do Modelo A (previsão).

    - Inclui toda a memória epidêmica da doença-alvo.
    - Das outras doenças (mesmo vetor, co-circulação, confusão diagnóstica), inclui
      apenas o lag mais recente e a média de 3 meses. Zika só entra como feature
      no modelo da própria zika (a série termina em 2024).
    - forecast=True remove variáveis do mês corrente (desconhecidas na previsão).
    - clima: "completo" (todas as climáticas, experimento v4), "parcimonioso" (protocolo v5:
      temp_lag*, prec_lag*) ou "nenhum". Se None, deriva de usar_clima (compatível com a v4).
    - suscetibilidade=True inclui as features *_susc_* (protocolo v5). Padrão False preserva
      exatamente os conjuntos do experimento v4.
    """
    if clima is None:
        clima = "completo" if usar_clima else "nenhum"
    if clima not in ("completo", "parcimonioso", "nenhum"):
        raise ValueError(f"clima inválido: {clima}")

    def _clima_ok(c: str) -> bool:
        if not is_climate_feature(c):
            return True
        return clima == "completo" or (clima == "parcimonioso" and is_clima_parcimonioso(c))

    p_alvo = PREFIXOS[DOENCA_PARA_COL[doenca]]
    excluir = set(_META) | set(PREFIXOS.keys())
    if forecast:
        excluir |= _VARS_MES_CORRENTE

    candidatas = [
        c for c in df.columns
        if c not in excluir and not c.startswith("_")   # "_" = coluna auxiliar (ex.: _incid do alvo), nunca feature
        and pd.api.types.is_numeric_dtype(df[c])
        and _clima_ok(c) and (suscetibilidade or not is_suscetibilidade(c))
        and (vizinhos or not is_vizinhos(c)) and (imunidade_longa or not is_imunidade_longa(c))
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


def grupos_de_features(df: pd.DataFrame, doenca: str) -> dict[str, list[str]]:
    """Grupos do protocolo v5: casos (sempre), clima_parcimonioso e suscetibilidade."""
    base = get_feature_columns(df, doenca=doenca, clima="nenhum")
    com_clima = get_feature_columns(df, doenca=doenca, clima="parcimonioso")
    com_susc = get_feature_columns(df, doenca=doenca, clima="nenhum", suscetibilidade=True)
    return {
        "casos": base,
        "clima_parcimonioso": [c for c in com_clima if c not in base],
        "suscetibilidade": [c for c in com_susc if c not in base],
    }
