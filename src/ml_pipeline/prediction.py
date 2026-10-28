"""
Módulo de projeção de cenários SSP (v4 multi-doença).

Usa o **Modelo B** (clima → risco, sem lags de casos) para estimar a resposta
das arboviroses a deltas climáticos (SSP1-2.6, SSP2-4.5, SSP5-8.5).

Procedimento:
  1. Climatologia histórica: média de cada variável climática por cidade × mês.
  2. Cenário "baseline" = climatologia sem deltas (referência).
  3. Cenários SSP = climatologia + deltas medianos de temperatura/precipitação.
  4. As features do Modelo B são reconstruídas EXATAMENTE como no treino
     (lags circulares dez→jan, acumulado de 3 meses defasado, offset de população).
  5. Incerteza empírica: razão real/previsto dos totais anuais nos folds
     fora-da-amostra (OOF) do Modelo B, aplicada às projeções.

Limitações (devem constar no artigo):
  - Os deltas são valores medianos regionais (IPCC AR6, Sul da América do Sul),
    não saída de downscaling por município.
  - ENSO é mantido na climatologia (≈ neutro); população congelada no último ano.
  - O resultado é uma ANÁLISE DE SENSIBILIDADE ao clima, não previsão de casos:
    imunidade de rebanho, sorotipos, vigilância e controle vetorial não estão no modelo.
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# --- Deltas medianos CMIP6 para o Sul do Brasil (relativos a 1995–2014) ---
# Fonte: IPCC AR6 WGI, Atlas interativo (região SES). Temperatura em °C, precipitação em %.
SSP_DELTAS = {
    "ssp126": {
        "2025-2030": {"temp_delta": 0.5, "prec_pct": 2.0},
        "2030-2035": {"temp_delta": 0.7, "prec_pct": 3.0},
        "2035-2040": {"temp_delta": 0.8, "prec_pct": 3.5},
    },
    "ssp245": {
        "2025-2030": {"temp_delta": 0.6, "prec_pct": 2.5},
        "2030-2035": {"temp_delta": 1.0, "prec_pct": 4.0},
        "2035-2040": {"temp_delta": 1.3, "prec_pct": 5.0},
    },
    "ssp585": {
        "2025-2030": {"temp_delta": 0.8, "prec_pct": 3.0},
        "2030-2035": {"temp_delta": 1.4, "prec_pct": 6.0},
        "2035-2040": {"temp_delta": 2.0, "prec_pct": 8.0},
    },
}

_CLIMA_COLS = ["temp_media", "temp_maxima", "temp_minima", "precipitacao", "umidmed", "enso"]
_STATIC_COLS = ["populacao", "latitude", "longitude", "log_pop"]


def compute_city_climatology(panel: pd.DataFrame) -> pd.DataFrame:
    """Média mensal de cada variável climática por cidade + estáticas (último ano)."""
    available = [c for c in _CLIMA_COLS if c in panel.columns]
    clim = panel.groupby(["code", "month"])[available].mean().reset_index()

    static_cols = [c for c in _STATIC_COLS if c in panel.columns]
    if static_cols:
        last = panel.sort_values(["code", "year", "month"]).groupby("code")[static_cols].last().reset_index()
        clim = clim.merge(last, on="code", how="left")

    # Só cidades com os 12 meses (lags circulares exigem o ciclo completo)
    full = clim.groupby("code")["month"].transform("nunique") == 12
    dropped = clim.loc[~full, "code"].nunique()
    if dropped:
        logger.warning(f"Climatologia: {dropped} cidades sem 12 meses foram descartadas.")
    clim = clim[full].sort_values(["code", "month"]).reset_index(drop=True)
    logger.info(f"Climatologia: {clim['code'].nunique()} cidades × 12 meses")
    return clim


def _circular_lag(df: pd.DataFrame, col: str, k: int) -> pd.Series:
    """Valor do mês m-k no ciclo climatológico (jan ← dez). df ordenado por code, month."""
    return df.groupby("code", sort=False)[col].transform(lambda s: np.roll(s.values, k))


def build_climate_features(clim: pd.DataFrame) -> pd.DataFrame:
    """Reconstrói as features do Modelo B a partir de uma climatologia (12 meses/cidade)."""
    df = clim.sort_values(["code", "month"]).reset_index(drop=True).copy()

    if {"temp_maxima", "temp_minima"} <= set(df.columns):
        df["amplitude_termica"] = df["temp_maxima"] - df["temp_minima"]
    if "temp_media" in df.columns:
        df["graus_dia_18"] = (df["temp_media"] - 18.0).clip(lower=0)

    df["month_sin"] = np.sin(2.0 * np.pi * df["month"] / 12.0)
    df["month_cos"] = np.cos(2.0 * np.pi * df["month"] / 12.0)
    if "latitude" in df.columns:
        df["abs_latitude"] = df["latitude"].abs()
    if "log_pop" not in df.columns and "populacao" in df.columns:
        df["log_pop"] = np.log1p(df["populacao"].fillna(0))

    lags = [
        ("temp_media", "temp_lag", (1, 2)),
        ("precipitacao", "prec_lag", (1, 2)),
        ("graus_dia_18", "graus_dia_18_lag", (1,)),
        ("enso", "enso_lag", (1, 2, 3)),
    ]
    for src, prefix, ks in lags:
        if src in df.columns:
            for k in ks:
                df[f"{prefix}{k}"] = _circular_lag(df, src, k)

    # Igual a _roll_shifted(shift=1, window=3, how="sum"): meses t-1, t-2, t-3
    if "precipitacao" in df.columns:
        df["prec_acum_3m_lag1"] = sum(_circular_lag(df, "precipitacao", k) for k in (1, 2, 3))

    return df


def apply_ssp_deltas(clim: pd.DataFrame, scenario: str, period: str) -> pd.DataFrame:
    """Soma o delta de temperatura e escala a precipitação na climatologia."""
    d = SSP_DELTAS[scenario][period]
    df = clim.copy()
    for col in ("temp_media", "temp_maxima", "temp_minima"):
        if col in df.columns:
            df[col] = df[col] + d["temp_delta"]
    if "precipitacao" in df.columns:
        df["precipitacao"] = df["precipitacao"] * (1 + d["prec_pct"] / 100.0)
    return df


def _predict(model, df: pd.DataFrame, feature_cols: list[str], use_pop_offset: bool) -> np.ndarray:
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Features ausentes na projeção: {missing}")
    kw = {}
    if use_pop_offset and "populacao" in df.columns:
        kw["base_margin"] = np.log(df["populacao"].fillna(1).clip(lower=1).values / 100_000.0)
    return np.maximum(model.predict(df[feature_cols], **kw), 0)


def empirical_interval(oof: pd.DataFrame) -> dict:
    """
    Erro multiplicativo anual do Modelo B fora-da-amostra:
    razão (casos reais do ano) / (casos previstos do ano), somando todas as cidades.
    Poucos anos de teste → usamos mínimo e máximo, não percentis.
    """
    if oof is None or oof.empty:
        return {"ratio_min": None, "ratio_max": None, "ratios": {}}
    ann = oof.groupby("year")[["y_true", "y_pred"]].sum()
    ann = ann[ann["y_pred"] > 0]
    ratios = (ann["y_true"] / ann["y_pred"]).round(3)
    return {
        "ratio_min": float(ratios.min()) if len(ratios) else None,
        "ratio_max": float(ratios.max()) if len(ratios) else None,
        "ratios": {int(k): float(v) for k, v in ratios.items()},
    }


def predict_scenarios(
    model,
    panel: pd.DataFrame,
    feature_cols: list[str],
    doenca: str = "dengue",
    use_pop_offset: bool = True,
    oof: Optional[pd.DataFrame] = None,
    output_dir: Optional[Path] = None,
) -> dict:
    """
    Projeta casos anuais sob o baseline e cada cenário SSP × período.

    Returns dict com:
      mensal  — DataFrame code, month, scenario, period, predicted_cases
      anual   — DataFrame scenario, period, total_cases, low, high, delta_pct_vs_baseline
      intervalo — razões empíricas usadas para low/high
    """
    clim = compute_city_climatology(panel)

    blocks = []
    base_feats = build_climate_features(clim)
    base_feats["predicted_cases"] = _predict(model, base_feats, feature_cols, use_pop_offset)
    base_feats["scenario"], base_feats["period"] = "baseline", "historico"
    blocks.append(base_feats)

    for sc, periods in SSP_DELTAS.items():
        for period in periods:
            f = build_climate_features(apply_ssp_deltas(clim, sc, period))
            f["predicted_cases"] = _predict(model, f, feature_cols, use_pop_offset)
            f["scenario"], f["period"] = sc, period
            blocks.append(f)

    keep = ["code", "month", "scenario", "period", "predicted_cases", "temp_media", "precipitacao", "populacao"]
    mensal = pd.concat(blocks, ignore_index=True)
    mensal = mensal[[c for c in keep if c in mensal.columns]]

    interval = empirical_interval(oof)
    anual = mensal.groupby(["scenario", "period"], sort=False)["predicted_cases"].sum().reset_index()
    anual = anual.rename(columns={"predicted_cases": "total_cases"})
    base_total = float(anual.loc[anual["scenario"] == "baseline", "total_cases"].iloc[0])
    anual["delta_pct_vs_baseline"] = ((anual["total_cases"] / base_total - 1) * 100).round(2) if base_total else np.nan
    if interval["ratio_min"] is not None:
        anual["low"] = anual["total_cases"] * interval["ratio_min"]
        anual["high"] = anual["total_cases"] * interval["ratio_max"]

    logger.info(f"=== Projeções {doenca} (casos/ano, todas as cidades) ===")
    for _, r in anual.iterrows():
        logger.info(f"  {r['scenario']:>8} {r['period']:>10}: {r['total_cases']:>10.0f}  ({r['delta_pct_vs_baseline']:+.1f}% vs baseline)")

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        mensal.to_csv(output_dir / f"projecoes_{doenca}_ssp_mensal.csv", index=False)
        anual.to_csv(output_dir / f"projecoes_{doenca}_ssp_anual.csv", index=False)
        logger.info(f"Projeções salvas em {output_dir}")

    return {"mensal": mensal, "anual": anual, "intervalo": interval}
