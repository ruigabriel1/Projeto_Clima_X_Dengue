#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de processamento em lote - VERSÃO 2: Organização por Latitude
Gera projeções regionais consolidadas e agrupadas por faixas de latitude

Outputs:
  - CSVs por faixa de latitude
  - CSV consolidado para Região Sul
  - Gráficos por latitude + regional consolidado  
  - Relatório executivo completo com metodologia e resultados
"""

from __future__ import annotations

import os
import re
import json
import textwrap
import unicodedata
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import numpy as np
import logging

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ========================= LOGGING =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ========================= CONFIGURACOES GERAIS =========================
# Importa caminho raiz do config centralizado (portabilidade entre máquinas)
from src.config import BASE_DIR as ROOT_DATA_DIR

TRAIN_START = 2015
TRAIN_END = 2024
CALIBRATION_YEAR = 2025
PROJECTION_START = 2025
PROJECTION_END = 2040

ARAPONGAS_LAT = -23.42
ARAPONGAS_REAL_2025 = 1455.0

# Coeficientes base (log-linear)
BETA_TMED = 0.661
BETA_PREC = 0.093
BETA_ENSO = 0.043
BETA_LAT = 0.142

EPS = 1e-9

# Controle de continuidade entre observado (2024) e primeira projeção (2025)
CONTINUITY_FLOOR_2025 = 0.75
CONTINUITY_DECAY = 0.55

SCENARIOS = {
    "ssp126": {"temp_delta_per_year": 0.02, "precip_delta_pct_per_year": 0.003, "enso_delta_per_year": 0.00},
    "ssp245": {"temp_delta_per_year": 0.04, "precip_delta_pct_per_year": 0.006, "enso_delta_per_year": 0.00},
    "ssp370": {"temp_delta_per_year": 0.06, "precip_delta_pct_per_year": 0.010, "enso_delta_per_year": 0.01},
    "ssp585": {"temp_delta_per_year": 0.08, "precip_delta_pct_per_year": 0.015, "enso_delta_per_year": 0.02},
}

TOTAL_MUNICIPIOS_SUL_OFICIAL = 1191  # PR(399) + SC(295) + RS(497)

@dataclass
class CalibrationBundle:
    intercept_shift: float
    immunity_gamma: float
    threshold_peak_2024: float
    arapongas_code: Optional[str]
    arapongas_pred_2025_raw: float


@dataclass
class CoverageInfo:
    municipios_sul_total: int
    municipios_com_dados: int


# ========================= FUNÇÕES AUXILIARES =========================

def to_float(v) -> float:
    if pd.isna(v):
        return np.nan
    s = str(v).strip().replace(".", "").replace(",", ".") if re.match(r"^\d{1,3}(\.\d{3})+,\d+$", str(v).strip()) else str(v).strip().replace(",", ".")
    try:
        return float(s)
    except Exception:
        return np.nan

def to_int(v) -> Optional[int]:
    try:
        return int(float(str(v).strip().replace(",", ".")))
    except Exception:
        return None

def normalize_code(col_name: str) -> Optional[str]:
    m = re.search(r"(\d{6,7})", str(col_name))
    if not m:
        return None
    return m.group(1)[:6]

def discover_files(root_dir: Path) -> List[Path]:
    csvs: List[Path] = []
    for base, _, files in os.walk(root_dir):
        for fn in files:
            if fn.lower().endswith(".csv"):
                csvs.append(Path(base) / fn)
    return csvs

def read_enso_series(path_enso: Path) -> pd.DataFrame:
    df = pd.read_csv(path_enso, sep=";", dtype=str, encoding="utf-8", engine="python")
    df = df.dropna(axis=1, how="all")
    if df.empty:
        raise ValueError(f"Arquivo ENSO vazio: {path_enso}")

    ano_col = df.columns[0]
    meses = [
        "janeiro", "fevereiro", "marco", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]

    records = []
    for _, row in df.iterrows():
        ano = to_int(row[ano_col])
        if ano is None:
            continue

        mes_idx = 1
        for col in df.columns[1:13]:
            val = to_float(row[col])
            if pd.isna(val):
                mes_idx += 1
                continue
            records.append({"year": ano, "month": mes_idx, "enso": val})
            mes_idx += 1

    out = pd.DataFrame(records)
    out = out.dropna().sort_values(["year", "month"]).reset_index(drop=True)
    return out

def read_wide_monthly(path_csv: Path, value_name: str) -> pd.DataFrame:
    try:
        raw = pd.read_csv(path_csv, sep=";", header=None, dtype=str, encoding="utf-8", engine="python")
    except UnicodeDecodeError:
        raw = pd.read_csv(path_csv, sep=";", header=None, dtype=str, encoding="latin-1", engine="python")

    if raw.shape[1] < 3:
        raise ValueError(f"Arquivo invalido: {path_csv}")

    header_row = None
    for i in range(min(len(raw), 10)):
        vals = raw.iloc[i].fillna("").astype(str).tolist()
        count_codes = sum(1 for v in vals if normalize_code(v) is not None)
        if count_codes >= 20:
            header_row = i
            break

    if header_row is None:
        raise ValueError(f"Nao foi possivel detectar cabecalho em: {path_csv}")

    header = raw.iloc[header_row].fillna("").astype(str).tolist()
    df = raw.iloc[header_row + 1 :].copy()
    df.columns = header

    cols = list(df.columns)
    cols[0] = "year"
    cols[1] = "month"
    df.columns = cols

    valid_cols = ["year", "month"]
    code_map: Dict[str, str] = {}
    for c in df.columns[2:]:
        code = normalize_code(c)
        if code:
            valid_cols.append(c)
            code_map[c] = code

    if len(valid_cols) <= 2:
        raise ValueError(f"Nenhuma coluna municipal em: {path_csv}")

    df = df[valid_cols].copy()
    df["year"] = df["year"].map(to_int)
    df["month"] = df["month"].map(to_int)
    df = df.dropna(subset=["year", "month"])

    long_records = []
    for c in valid_cols[2:]:
        code = code_map[c]
        vals = df[c].map(to_float)
        tmp = pd.DataFrame({
            "code": code,
            "year": df["year"].astype(int),
            "month": df["month"].astype(int),
            value_name: vals,
        })
        long_records.append(tmp)

    out = pd.concat(long_records, ignore_index=True)
    out = out.dropna(subset=[value_name])
    return out

def build_code_lookup_from_latitude_files(csv_paths: List[Path]) -> pd.DataFrame:
    frames = []
    for p in csv_paths:
        name = p.name.lower()
        if "dengue_faixa_latitude" not in name:
            continue
        try:
            d = pd.read_csv(p)
        except Exception:
            continue

        expected = {"CODIGO_MUNICIPIO", "NOME_MUNICIPIO", "LATITUDE"}
        if not expected.issubset(set(d.columns)):
            continue

        part = d[["CODIGO_MUNICIPIO", "NOME_MUNICIPIO", "LATITUDE"]].drop_duplicates()
        part = part.rename(columns={
            "CODIGO_MUNICIPIO": "code",
            "NOME_MUNICIPIO": "city_name",
            "LATITUDE": "latitude",
        })
        part["code"] = part["code"].astype(str).str.extract(r"(\d{6})", expand=False)
        part["latitude"] = part["latitude"].map(to_float)
        frames.append(part)

    if not frames:
        return pd.DataFrame(columns=["code", "city_name", "latitude"])

    lookup = pd.concat(frames, ignore_index=True).dropna(subset=["code", "latitude"])
    lookup = lookup.sort_values(["code"]).drop_duplicates(subset=["code"], keep="first").reset_index(drop=True)
    return lookup

def validate_data_sources(root_dir: Path) -> None:
    """Verifica integridade das fontes de dados antes do processamento.

    Checa existência dos arquivos raw e disponibilidade dos csvs_latitude,
    emitindo avisos quando o pré-processamento de latitude não foi executado.
    """
    raw_required = {
        "dengue": root_dir / "data" / "raw" / "dengue_MENSAL.csv",
        "temp_media": root_dir / "data" / "raw" / "Temp_media_MENSAL.csv",
        "precipitacao": root_dir / "data" / "raw" / "precipitacao_mensal_rev.csv",
        "enso": root_dir / "data" / "raw" / "elnino_lanina_2015-2024.csv",
    }
    missing_raw = [str(p) for p in raw_required.values() if not p.exists()]
    if missing_raw:
        raise FileNotFoundError(
            "Arquivos raw ausentes (execute pré-processamento primeiro):\n  "
            + "\n  ".join(missing_raw)
        )

    csv_dir = root_dir / "output" / "csvs_latitude"
    n_dengue = len(list(csv_dir.glob("dengue_faixa_latitude_*.csv"))) if csv_dir.exists() else 0
    n_temp = len(list(csv_dir.glob("temp_media_faixa_latitude_*.csv"))) if csv_dir.exists() else 0
    n_prec = len(list(csv_dir.glob("precipitacao_faixa_latitude_*.csv"))) if csv_dir.exists() else 0

    logger.info("Validação de fontes: raw OK | csvs_latitude — dengue=%d, temp=%d, prec=%d", n_dengue, n_temp, n_prec)

    if n_dengue < 8 or n_temp < 8 or n_prec < 8:
        logger.warning(
            "output/csvs_latitude/ incompleto (esperado 8 faixas por variável). "
            "Execute processar_dengue_latitude_mapas.py e processar_clima_por_latitude.py "
            "antes do motor para garantir consistência total."
        )
    else:
        logger.info("Validação concluída: fontes primárias e csvs_latitude completos.")


def build_base_panel(root_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Constrói painel base preferindo output/csvs_latitude/ como fonte canônica.

    Quando os arquivos CSV por latitude estão disponíveis (gerados por
    processar_dengue_latitude_mapas.py + processar_clima_por_latitude.py),
    eles são usados como única fonte, garantindo consistência com o modelo ML
    (ambos os modelos — regressão log-linear e HistGradientBoosting — operam
    sobre o mesmo conjunto de 1190 municípios e mesmos valores observados).

    Fallback automático para data/raw/ no formato wide quando csvs_latitude
    não estiver disponível ou incompleto.
    """
    csv_dir = root_dir / "output" / "csvs_latitude"
    dengue_lat = sorted(csv_dir.glob("dengue_faixa_latitude_*.csv")) if csv_dir.exists() else []
    temp_lat = sorted(csv_dir.glob("temp_media_faixa_latitude_*.csv")) if csv_dir.exists() else []
    prec_lat = sorted(csv_dir.glob("precipitacao_faixa_latitude_*.csv")) if csv_dir.exists() else []

    if len(dengue_lat) >= 8 and len(temp_lat) >= 8 and len(prec_lat) >= 8:
        logger.info("build_base_panel → fonte canônica: output/csvs_latitude/ (%d municípios esperados)", TOTAL_MUNICIPIOS_SUL_OFICIAL)
        panel = load_ml_panel_from_csvs_latitude(root_dir)
        lookup = (
            panel[["code", "city_name", "latitude"]]
            .drop_duplicates(subset=["code"])
            .reset_index(drop=True)
        )
        return panel, lookup

    # ---- Fallback: raw wide-format ----
    logger.warning("build_base_panel → fallback para data/raw/ (csvs_latitude ausente ou incompleto)")
    raw_dir = root_dir / "data" / "raw"
    dengue_path = raw_dir / "dengue_MENSAL.csv"
    temp_path   = raw_dir / "Temp_media_MENSAL.csv"
    prec_path   = raw_dir / "precipitacao_mensal_rev.csv"
    enso_path   = raw_dir / "elnino_lanina_2015-2024.csv"

    for p in [dengue_path, temp_path, prec_path, enso_path]:
        if not p.exists():
            raise FileNotFoundError(f"Arquivo essencial não encontrado: {p}")

    dengue = read_wide_monthly(dengue_path, "dengue_cases")
    temp   = read_wide_monthly(temp_path,   "temp_media")
    prec   = read_wide_monthly(prec_path,   "precipitacao")
    enso   = read_enso_series(enso_path)

    panel = dengue.merge(temp,  on=["code", "year", "month"], how="inner")
    panel = panel.merge(prec,   on=["code", "year", "month"], how="inner")
    panel = panel.merge(enso,   on=["year", "month"],         how="left")

    csv_paths = list(csv_dir.glob("*.csv")) if csv_dir.exists() else []
    lookup = build_code_lookup_from_latitude_files(csv_paths)
    panel = panel.merge(lookup, on="code", how="left")
    panel["city_name"] = panel["city_name"].fillna(
        panel["code"].apply(lambda c: f"municipio_{c}")
    )
    panel = panel[panel["code"].str[:2].isin(["41", "42", "43"])].copy()
    panel = panel.sort_values(["code", "year", "month"]).reset_index(drop=True)
    return panel, lookup

def north_weight(latitude: float) -> float:
    lat_abs = abs(float(latitude))
    n = (32.0 - lat_abs) / 10.0
    n = float(np.clip(n, 0.0, 1.0))
    return 0.7 + 0.8 * n

def train_local_intercept(city_df: pd.DataFrame) -> float:
    d = city_df.copy().sort_values(["year", "month"]).reset_index(drop=True)

    d["temp_lag3"] = d["temp_media"].shift(3)
    d["prec_lag3"] = d["precipitacao"].shift(3)
    d["enso_lag3"] = d["enso"].shift(3)

    d = d[(d["year"] >= TRAIN_START) & (d["year"] <= TRAIN_END)].copy()
    d = d.dropna(subset=["temp_lag3", "prec_lag3", "enso_lag3", "dengue_cases"])

    if d.empty:
        return 0.0

    lat = d["latitude"].dropna().iloc[0] if d["latitude"].notna().any() else ARAPONGAS_LAT
    linear_part = (
        BETA_TMED * d["temp_lag3"]
        + BETA_PREC * d["prec_lag3"]
        + BETA_ENSO * d["enso_lag3"]
        + BETA_LAT * lat
    )

    y_log = np.log1p(d["dengue_cases"].clip(lower=0.0))
    residual = y_log - linear_part

    return float(np.nanmedian(residual))

def build_monthly_climatology(city_df: pd.DataFrame) -> pd.DataFrame:
    d = city_df[(city_df["year"] >= TRAIN_START) & (city_df["year"] <= TRAIN_END)].copy()
    g = d.groupby("month", as_index=False).agg(
        base_temp=("temp_media", "mean"),
        base_prec=("precipitacao", "mean"),
        base_enso=("enso", "mean"),
    )
    return g


def build_yearly_templates(city_df: pd.DataFrame) -> pd.DataFrame:
    """Cria templates mensais por ano historico para manter variacao interanual (formato serrilhado)."""
    d = city_df[(city_df["year"] >= TRAIN_START) & (city_df["year"] <= TRAIN_END)].copy()
    d = d.dropna(subset=["temp_media", "precipitacao", "enso"])
    d = d[["year", "month", "temp_media", "precipitacao", "enso"]]

    # Mantem apenas anos com 12 meses completos
    valid_years = d.groupby("year")["month"].nunique()
    valid_years = valid_years[valid_years == 12].index.tolist()
    d = d[d["year"].isin(valid_years)].copy()
    return d.sort_values(["year", "month"]).reset_index(drop=True)

def predict_annual_cases_2025_no_increment(
    climatology: pd.DataFrame,
    intercept: float,
    latitude: float,
    hist_q95: float,
) -> float:
    d = climatology.copy().sort_values("month").reset_index(drop=True)
    d["year"] = CALIBRATION_YEAR
    d["temp"] = d["base_temp"]
    d["prec"] = d["base_prec"]
    d["enso"] = d["base_enso"]

    hist_tail = d[d["month"].isin([10, 11, 12])].copy()
    hist_tail = hist_tail.assign(year=CALIBRATION_YEAR - 1)
    seq = pd.concat([hist_tail, d], ignore_index=True).sort_values(["year", "month"]).reset_index(drop=True)

    seq["temp_lag3"] = seq["temp"].shift(3)
    seq["prec_lag3"] = seq["prec"].shift(3)
    seq["enso_lag3"] = seq["enso"].shift(3)

    pred = seq[seq["year"] == CALIBRATION_YEAR].copy()
    lp = (
        intercept
        + BETA_TMED * pred["temp_lag3"]
        + BETA_PREC * pred["prec_lag3"]
        + BETA_ENSO * pred["enso_lag3"]
        + BETA_LAT * latitude
    )
    monthly_cases = np.expm1(lp).clip(lower=0.0)
    monthly_cap = float(hist_q95) * (1.0 + 0.04 * 1.0 * 1.0)
    monthly_cases = np.minimum(monthly_cases, monthly_cap)
    return float(np.nansum(monthly_cases))


def predict_annual_cases_2025_with_increment(
    climatology: pd.DataFrame,
    intercept: float,
    latitude: float,
    cfg: Dict[str, float],
    hist_q95: float,
) -> float:
    """Previsao anual de 2025 com 1 passo de incremento SSP (base 2024)."""
    d = climatology.copy().sort_values("month").reset_index(drop=True)
    d["year"] = CALIBRATION_YEAR

    # Aplicar um incremento em 2025 sobre base 2024.
    d["temp"] = d["base_temp"] + float(cfg["temp_delta_per_year"])
    d["prec"] = d["base_prec"] * (1.0 + float(cfg["precip_delta_pct_per_year"]))
    d["enso"] = d["base_enso"] + float(cfg["enso_delta_per_year"])

    hist_tail = d[["month"]].copy()
    hist_tail = hist_tail[hist_tail["month"].isin([10, 11, 12])]
    hist_tail["year"] = CALIBRATION_YEAR - 1
    hist_tail = hist_tail.merge(
        climatology[["month", "base_temp", "base_prec", "base_enso"]],
        on="month",
        how="left",
    )
    hist_tail = hist_tail.rename(columns={"base_temp": "temp", "base_prec": "prec", "base_enso": "enso"})

    seq = pd.concat([hist_tail[["year", "month", "temp", "prec", "enso"]], d[["year", "month", "temp", "prec", "enso"]]], ignore_index=True)
    seq = seq.sort_values(["year", "month"]).reset_index(drop=True)

    seq["temp_lag3"] = seq["temp"].shift(3)
    seq["prec_lag3"] = seq["prec"].shift(3)
    seq["enso_lag3"] = seq["enso"].shift(3)

    pred = seq[seq["year"] == CALIBRATION_YEAR].copy()
    lp = (
        intercept
        + BETA_TMED * pred["temp_lag3"]
        + BETA_PREC * pred["prec_lag3"]
        + BETA_ENSO * pred["enso_lag3"]
        + BETA_LAT * latitude
    )
    monthly_cases = np.expm1(lp).clip(lower=0.0)
    scenario_mult = max(float(cfg["temp_delta_per_year"]) / 0.02, 1.0)
    monthly_cap = float(hist_q95) * (1.0 + 0.04 * scenario_mult * 1.0)
    monthly_cases = np.minimum(monthly_cases, monthly_cap)
    return float(np.nansum(monthly_cases))

def calibrate_region(panel: pd.DataFrame, local_intercepts: Dict[str, float]) -> CalibrationBundle:
    # Versao focada apenas nos dados fornecidos: sem calibracao externa e sem imunidade.
    return CalibrationBundle(0.0, 0.0, 0.0, None, np.nan)

def project_city(
    city_df: pd.DataFrame,
    intercept_local: float,
    calib: CalibrationBundle,
) -> pd.DataFrame:
    city_df = city_df.sort_values(["year", "month"]).reset_index(drop=True)

    code = city_df["code"].iloc[0]
    city_name = city_df["city_name"].iloc[0]
    lat = float(city_df["latitude"].dropna().iloc[0]) if city_df["latitude"].notna().any() else ARAPONGAS_LAT

    templates = build_yearly_templates(city_df)
    clim = build_monthly_climatology(city_df)
    if templates.empty and clim.empty:
        return pd.DataFrame()

    template_years = sorted(templates["year"].unique().tolist()) if not templates.empty else []
    hist_cases = city_df[(city_df["year"] >= TRAIN_START) & (city_df["year"] <= TRAIN_END)]["dengue_cases"].dropna()
    hist_q95 = float(np.nanquantile(hist_cases, 0.95)) if not hist_cases.empty else 50.0
    hist_q95 = max(hist_q95, 10.0)
    annual_2024_city = float(city_df[city_df["year"] == 2024]["dengue_cases"].sum())
    cap_base = max(hist_q95, annual_2024_city / 12.0)

    records = []
    for scenario_name, cfg in SCENARIOS.items():
        seq = []
        for year in range(CALIBRATION_YEAR, PROJECTION_END + 1):
            # Em 2025 aplica-se 1 passo de delta SSP (base 2024).
            years_from_2024 = year - (CALIBRATION_YEAR - 1)
            t_delta = cfg["temp_delta_per_year"] * years_from_2024
            p_delta = cfg["precip_delta_pct_per_year"] * years_from_2024
            e_delta = cfg["enso_delta_per_year"] * years_from_2024

            if template_years:
                template_year = template_years[(year - CALIBRATION_YEAR) % len(template_years)]
                base_rows = templates[templates["year"] == template_year]
            else:
                base_rows = clim.rename(columns={"base_temp": "temp_media", "base_prec": "precipitacao", "base_enso": "enso"})

            for _, row in base_rows.iterrows():
                m = int(row["month"])
                base_temp = float(row["temp_media"])
                base_prec = float(row["precipitacao"])
                base_enso = float(row["enso"])

                seq.append({
                    "code": code,
                    "city_name": city_name,
                    "latitude": lat,
                    "scenario": scenario_name,
                    "year": year,
                    "month": m,
                    "temp": base_temp + t_delta,
                    "prec": base_prec * (1.0 + p_delta),
                    "enso": base_enso + e_delta,
                })

        dfp = pd.DataFrame(seq).sort_values(["year", "month"]).reset_index(drop=True)

        # Garante lag-3 completo no inicio de 2025 usando meses 10-12 de 2024.
        if template_years:
            template_year = template_years[0]
            tail_rows = templates[(templates["year"] == template_year) & (templates["month"].isin([10, 11, 12]))].copy()
            if tail_rows.empty:
                tail_rows = clim[clim["month"].isin([10, 11, 12])].rename(
                    columns={"base_temp": "temp_media", "base_prec": "precipitacao", "base_enso": "enso"}
                )
        else:
            tail_rows = clim[clim["month"].isin([10, 11, 12])].rename(
                columns={"base_temp": "temp_media", "base_prec": "precipitacao", "base_enso": "enso"}
            )

        pre_tail = pd.DataFrame(
            {
                "code": code,
                "city_name": city_name,
                "latitude": lat,
                "scenario": scenario_name,
                "year": CALIBRATION_YEAR - 1,
                "month": tail_rows["month"].astype(int).values,
                "temp": tail_rows["temp_media"].astype(float).values,
                "prec": tail_rows["precipitacao"].astype(float).values,
                "enso": tail_rows["enso"].astype(float).values,
            }
        )

        full = pd.concat([pre_tail, dfp], ignore_index=True).sort_values(["year", "month"]).reset_index(drop=True)
        full["temp_lag3"] = full["temp"].shift(3)
        full["prec_lag3"] = full["prec"].shift(3)
        full["enso_lag3"] = full["enso"].shift(3)

        fut = full[(full["year"] >= PROJECTION_START) & (full["year"] <= PROJECTION_END)].copy()

        lp = (
            intercept_local
            + BETA_TMED * fut["temp_lag3"]
            + BETA_PREC * fut["prec_lag3"]
            + BETA_ENSO * fut["enso_lag3"]
            + BETA_LAT * lat
        )

        pred_cases = np.expm1(lp).clip(lower=0.0)

        # Limite plausivel em escala de casos absolutos, baseado no historico observado.
        years_from = (fut["year"] - CALIBRATION_YEAR).astype(float)
        scenario_mult = max(cfg["temp_delta_per_year"] / 0.02, 1.0)
        cap_factor = 1.0 + (0.04 * scenario_mult * years_from)
        monthly_cap = cap_base * cap_factor
        pred_cases = np.minimum(pred_cases, monthly_cap)

        # Correção de continuidade: evita queda abrupta irrealista de 2024 para 2025.
        if annual_2024_city > 0:
            mask_2025 = fut["year"] == CALIBRATION_YEAR
            pred_2025 = float(np.nansum(pred_cases.loc[mask_2025])) if mask_2025.any() else 0.0
            target_2025 = annual_2024_city * CONTINUITY_FLOOR_2025
            if pred_2025 > 0 and pred_2025 < target_2025:
                boost = min(target_2025 / max(pred_2025, EPS), 3.0)
                years_arr = fut["year"].to_numpy(dtype=float)
                decay = np.exp(-CONTINUITY_DECAY * (years_arr - CALIBRATION_YEAR))
                pred_cases = pred_cases * (1.0 + (boost - 1.0) * decay)

        fut["pred_cases"] = pred_cases
        fut["pred_log_y1"] = np.log1p(fut["pred_cases"])
        fut["high_peak_2024"] = 0
        fut["peak_2024"] = np.nan
        fut["peak_threshold_2024"] = np.nan

        records.append(
            fut[
                [
                    "code", "city_name", "latitude", "scenario", "year", "month",
                    "temp", "prec", "enso", "temp_lag3", "prec_lag3", "enso_lag3",
                    "pred_log_y1", "pred_cases", "high_peak_2024", "peak_2024", "peak_threshold_2024",
                ]
            ]
        )

    return pd.concat(records, ignore_index=True) if records else pd.DataFrame()


# ========================= FUNÇÕES DE SAÍDA =========================

def save_outputs_by_latitude(root_dir: Path, projections: pd.DataFrame, calibration: CalibrationBundle) -> None:
    """Salva saídas organizadas por faixa de latitude + consolidado regional."""
    out_dir = root_dir / "output" / "projecoes_regionais"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Limpa CSVs legados por cidade (projecao_nome_123456.csv).
    removed_city_csv = 0
    for p in out_dir.glob("projecao_*.csv"):
        if re.search(r"_\d{6}\.csv$", p.name):
            p.unlink(missing_ok=True)
            removed_city_csv += 1

    # Binning em 8 faixas de latitude
    lat_bins = np.linspace(projections["latitude"].min(), projections["latitude"].max(), 9)
    projections["lat_faixa"] = pd.cut(projections["latitude"], bins=lat_bins, include_lowest=True)

    # CSVs por faixa de latitude
    for lat_faixa, g_lat in projections.groupby("lat_faixa", observed=False):
        if g_lat.empty:
            continue

        lat_min = float(lat_faixa.left)
        lat_max = float(lat_faixa.right)
        lat_label = f"{lat_min:.1f}a{lat_max:.1f}"

        # Agrupa por scenario e year
        annual = g_lat.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
        annual["latitude_min"] = lat_min
        annual["latitude_max"] = lat_max
        annual["n_municipios"] = g_lat["code"].nunique()

        path = out_dir / f"projecao_latitude_{lat_label}.csv"
        annual.sort_values(["scenario", "year"]).to_csv(path, index=False, encoding="utf-8")

    # CSV consolidado - Região Sul
    regional = projections.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
    regional["latitude_min"] = projections["latitude"].min()
    regional["latitude_max"] = projections["latitude"].max()
    regional["n_municipios"] = projections["code"].nunique()
    regional["regiao"] = "SUL"

    regional_path = out_dir / "projecao_regiao_sul_consolidado.csv"
    regional.sort_values(["scenario", "year"]).to_csv(regional_path, index=False, encoding="utf-8")

    # Calibração JSON
    calib_json = {
        "intercept_shift": float(calibration.intercept_shift),
        "immunity_gamma": float(calibration.immunity_gamma),
        "threshold_peak_2024": float(calibration.threshold_peak_2024),
        "arapongas_code": calibration.arapongas_code,
        "arapongas_pred_2025_raw": float(calibration.arapongas_pred_2025_raw) if not np.isnan(calibration.arapongas_pred_2025_raw) else None,
        "arapongas_real_2025": ARAPONGAS_REAL_2025,
    }
    with open(out_dir / "calibracao_regional.json", "w", encoding="utf-8") as f:
        json.dump(calib_json, f, ensure_ascii=False, indent=2)

    print(f"[OK] {(out_dir / 'projecao_latitude_*.csv').name}: Arquivos salvos por latitude")
    print(f"[OK] {regional_path.name}: Consolidado regional")
    print(f"[OK] calibracao_regional.json: Parâmetros de calibração")
    if removed_city_csv > 0:
        print(f"[OK] CSVs legados por cidade removidos: {removed_city_csv}")


def save_ml_2025_forecasts(root_dir: Path, panel: pd.DataFrame, local_intercepts: Dict[str, float]) -> None:
    """Salva previsão anual de 2025 com e sem incremento SSP."""
    out_dir = root_dir / "output" / "projecoes_regionais"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for code, g in panel.groupby("code"):
        g = g.sort_values(["year", "month"]).reset_index(drop=True)
        lat = float(g["latitude"].dropna().iloc[0]) if g["latitude"].notna().any() else ARAPONGAS_LAT
        city_name = str(g["city_name"].iloc[0])
        intercept = float(local_intercepts.get(code, 0.0))
        clim = build_monthly_climatology(g)
        if clim.empty:
            continue

        hist_cases = g[(g["year"] >= TRAIN_START) & (g["year"] <= TRAIN_END)]["dengue_cases"].dropna()
        hist_q95 = float(np.nanquantile(hist_cases, 0.95)) if not hist_cases.empty else 50.0
        hist_q95 = max(hist_q95, 10.0)

        pred_sem = predict_annual_cases_2025_no_increment(clim, intercept, lat, hist_q95)
        rows.append(
            {
                "code": code,
                "city_name": city_name,
                "latitude": lat,
                "year": CALIBRATION_YEAR,
                "scenario": "sem_incremento",
                "tipo_incremento": "sem_incremento",
                "pred_cases": pred_sem,
            }
        )

        for sc, cfg in SCENARIOS.items():
            pred_com = predict_annual_cases_2025_with_increment(clim, intercept, lat, cfg, hist_q95)
            rows.append(
                {
                    "code": code,
                    "city_name": city_name,
                    "latitude": lat,
                    "year": CALIBRATION_YEAR,
                    "scenario": sc,
                    "tipo_incremento": "com_incremento_ssp",
                    "pred_cases": pred_com,
                }
            )

    if not rows:
        return

    df_2025 = pd.DataFrame(rows)
    df_2025 = df_2025.sort_values(["scenario", "code"]).reset_index(drop=True)
    df_2025.to_csv(out_dir / "previsao_ml_2025_municipios.csv", index=False, encoding="utf-8")

    reg = df_2025.groupby(["year", "scenario", "tipo_incremento"], as_index=False)["pred_cases"].sum()
    reg["regiao"] = "SUL"
    reg.to_csv(out_dir / "previsao_ml_2025_regional.csv", index=False, encoding="utf-8")

    print("[OK] previsao_ml_2025_municipios.csv: Previsão anual 2025 por município (com e sem incremento SSP)")
    print("[OK] previsao_ml_2025_regional.csv: Previsão anual 2025 consolidada regional")


def uncertainty_bounds(years: np.ndarray, values: np.ndarray, hist_cv: float, scenario_code: str) -> Tuple[np.ndarray, np.ndarray]:
    """Faixa simétrica (+/- erro%) por SSP, com erro crescente no horizonte."""
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)
    horizon = years - np.nanmin(years)

    # Percentual base por cenário (menor no SSP1-2.6, maior no SSP5-8.5).
    base_pct_map = {
        "ssp126": 0.06,
        "ssp245": 0.07,
        "ssp370": 0.08,
        "ssp585": 0.09,
    }
    growth_pct_map = {
        "ssp126": 0.0025,
        "ssp245": 0.0030,
        "ssp370": 0.0035,
        "ssp585": 0.0040,
    }

    base_pct = float(base_pct_map.get(scenario_code, 0.12))
    growth_pct = float(growth_pct_map.get(scenario_code, 0.005))

    # Pequeno ajuste por variabilidade historica, sem inverter ordem entre SSPs.
    hist_adj = float(np.clip(hist_cv, 0.05, 0.60)) * 0.02
    margin_pct = np.clip(base_pct + hist_adj + growth_pct * horizon, 0.05, 0.16)

    low = np.maximum(values * (1.0 - margin_pct), 0.0)
    high = values * (1.0 + margin_pct)
    return low, high


def should_shade_scenario(scenario_code: str) -> bool:
    """Sombras em cenários de referência, no estilo do exemplo IPCC."""
    return scenario_code in {"ssp126", "ssp370"}


def incidentes_formatter(x, _pos):
    return f"{int(x):,}".replace(",", ".")


def load_historical_incidents_from_csvs_latitude(
    root_dir: Path,
    lat_bins: np.ndarray,
    model_codes: Optional[set] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega histórico diretamente de output/csvs_latitude para preservar integridade dos incidentes observados."""
    csv_dir = root_dir / "output" / "csvs_latitude"
    files = sorted(csv_dir.glob("dengue_faixa_latitude_*.csv"))
    if not files:
        return pd.DataFrame(columns=["lat_faixa", "year", "incidentes"]), pd.DataFrame(columns=["year", "incidentes"])

    frames = []
    for fp in files:
        try:
            d = pd.read_csv(fp)
        except Exception:
            continue
        required = {"CODIGO_MUNICIPIO", "ANO", "CASOS_DENGUE", "LATITUDE"}
        if not required.issubset(set(d.columns)):
            continue
        part = d[["CODIGO_MUNICIPIO", "ANO", "CASOS_DENGUE", "LATITUDE"]].copy()
        part["CODIGO_MUNICIPIO"] = part["CODIGO_MUNICIPIO"].astype(str).str.extract(r"(\d{6})", expand=False)
        if model_codes:
            part = part[part["CODIGO_MUNICIPIO"].isin(model_codes)].copy()
        part["ANO"] = part["ANO"].map(to_int)
        part["CASOS_DENGUE"] = part["CASOS_DENGUE"].map(to_float).fillna(0.0)
        part["LATITUDE"] = part["LATITUDE"].map(to_float)
        part = part.dropna(subset=["ANO", "LATITUDE"])
        frames.append(part)

    if not frames:
        return pd.DataFrame(columns=["lat_faixa", "year", "incidentes"]), pd.DataFrame(columns=["year", "incidentes"])

    all_hist = pd.concat(frames, ignore_index=True)
    all_hist = all_hist[(all_hist["ANO"] >= 2015) & (all_hist["ANO"] <= 2024)].copy()
    all_hist["lat_faixa"] = pd.cut(all_hist["LATITUDE"], bins=lat_bins, include_lowest=True)

    hist_lat = all_hist.groupby(["lat_faixa", "ANO"], as_index=False, observed=False)["CASOS_DENGUE"].sum()
    hist_lat = hist_lat.rename(columns={"ANO": "year", "CASOS_DENGUE": "incidentes"})

    hist_regional = all_hist.groupby("ANO", as_index=False)["CASOS_DENGUE"].sum()
    hist_regional = hist_regional.rename(columns={"ANO": "year", "CASOS_DENGUE": "incidentes"})
    return hist_lat, hist_regional


def load_ml_panel_from_csvs_latitude(root_dir: Path) -> pd.DataFrame:
    """Monta painel mensal para ML a partir dos CSVs por latitude."""
    csv_dir = root_dir / "output" / "csvs_latitude"
    if not csv_dir.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {csv_dir}")

    dengue_files = sorted(csv_dir.glob("dengue_faixa_latitude_*.csv"))
    temp_files = sorted(csv_dir.glob("temp_media_faixa_latitude_*.csv"))
    prec_files = sorted(csv_dir.glob("precipitacao_faixa_latitude_*.csv"))

    if not dengue_files or not temp_files or not prec_files:
        raise RuntimeError("Faltam arquivos de dengue/temperatura/precipitação em output/csvs_latitude")

    dengue_parts: List[pd.DataFrame] = []
    temp_parts: List[pd.DataFrame] = []
    prec_parts: List[pd.DataFrame] = []

    for fp in dengue_files:
        d = pd.read_csv(fp)
        req = {"CODIGO_MUNICIPIO", "ANO", "MES", "CASOS_DENGUE", "LATITUDE", "NOME_MUNICIPIO", "FAIXA_LATITUDE"}
        if not req.issubset(set(d.columns)):
            continue
        d = d[["CODIGO_MUNICIPIO", "ANO", "MES", "CASOS_DENGUE", "LATITUDE", "NOME_MUNICIPIO", "FAIXA_LATITUDE"]].copy()
        d = d.rename(columns={
            "CODIGO_MUNICIPIO": "code",
            "ANO": "year",
            "MES": "month",
            "CASOS_DENGUE": "dengue_cases",
            "LATITUDE": "latitude",
            "NOME_MUNICIPIO": "city_name",
            "FAIXA_LATITUDE": "lat_faixa_id",
        })
        dengue_parts.append(d)

    for fp in temp_files:
        d = pd.read_csv(fp)
        req = {"CODIGO_MUNICIPIO", "ANO", "MES", "TEMP_MEDIA"}
        if not req.issubset(set(d.columns)):
            continue
        d = d[["CODIGO_MUNICIPIO", "ANO", "MES", "TEMP_MEDIA"]].copy()
        d = d.rename(columns={"CODIGO_MUNICIPIO": "code", "ANO": "year", "MES": "month", "TEMP_MEDIA": "temp_media"})
        temp_parts.append(d)

    for fp in prec_files:
        d = pd.read_csv(fp)
        req = {"CODIGO_MUNICIPIO", "ANO", "MES", "PRECIPITACAO_MENSAL"}
        if not req.issubset(set(d.columns)):
            continue
        d = d[["CODIGO_MUNICIPIO", "ANO", "MES", "PRECIPITACAO_MENSAL"]].copy()
        d = d.rename(columns={"CODIGO_MUNICIPIO": "code", "ANO": "year", "MES": "month", "PRECIPITACAO_MENSAL": "precipitacao"})
        prec_parts.append(d)

    if not dengue_parts:
        raise RuntimeError("Não foi possível montar painel de dengue a partir dos CSVs por latitude")

    dengue = pd.concat(dengue_parts, ignore_index=True)
    temp = pd.concat(temp_parts, ignore_index=True) if temp_parts else pd.DataFrame(columns=["code", "year", "month", "temp_media"])
    prec = pd.concat(prec_parts, ignore_index=True) if prec_parts else pd.DataFrame(columns=["code", "year", "month", "precipitacao"])

    for df in [dengue, temp, prec]:
        df["code"] = df["code"].astype(str).str.extract(r"(\d{6})", expand=False)
        df["year"] = df["year"].map(to_int)
        df["month"] = df["month"].map(to_int)

    dengue["dengue_cases"] = dengue["dengue_cases"].map(to_float).fillna(0.0)
    dengue["latitude"] = dengue["latitude"].map(to_float)
    temp["temp_media"] = temp["temp_media"].map(to_float)
    prec["precipitacao"] = prec["precipitacao"].map(to_float)

    panel = dengue.merge(temp, on=["code", "year", "month"], how="left")
    panel = panel.merge(prec, on=["code", "year", "month"], how="left")

    enso_path = root_dir / "data" / "raw" / "elnino_lanina_2015-2024.csv"
    enso = read_enso_series(enso_path)
    panel = panel.merge(enso, on=["year", "month"], how="left")

    panel = panel.dropna(subset=["code", "year", "month", "latitude"]).copy()
    panel = panel[(panel["year"] >= TRAIN_START) & (panel["year"] <= TRAIN_END)].copy()
    panel = panel.sort_values(["code", "year", "month"]).reset_index(drop=True)

    # Imputação simples por mediana mensal para variáveis climáticas.
    for col in ["temp_media", "precipitacao", "enso"]:
        panel[col] = panel[col].astype(float)
        month_med = panel.groupby("month")[col].transform("median")
        panel[col] = panel[col].fillna(month_med)
        panel[col] = panel[col].fillna(panel[col].median())

    return panel


def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 1.0
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def _build_ml_features(panel: pd.DataFrame) -> pd.DataFrame:
    d = panel.copy().sort_values(["code", "year", "month"]).reset_index(drop=True)
    d["month_sin"] = np.sin(2.0 * np.pi * d["month"] / 12.0)
    d["month_cos"] = np.cos(2.0 * np.pi * d["month"] / 12.0)

    d["dengue_lag1"] = d.groupby("code")["dengue_cases"].shift(1)
    d["dengue_lag2"] = d.groupby("code")["dengue_cases"].shift(2)
    d["dengue_lag3"] = d.groupby("code")["dengue_cases"].shift(3)

    d["temp_lag1"] = d.groupby("code")["temp_media"].shift(1)
    d["prec_lag1"] = d.groupby("code")["precipitacao"].shift(1)
    d["enso_lag1"] = d.groupby("code")["enso"].shift(1)

    d = d.dropna(subset=["dengue_lag1", "dengue_lag2", "dengue_lag3", "temp_lag1", "prec_lag1", "enso_lag1"]).copy()
    return d


def _evaluate_split(y_true: np.ndarray, y_pred: np.ndarray, split_name: str) -> Dict[str, float]:
    return {
        "split": split_name,
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mape_pct": _safe_mape(y_true, y_pred),
        "r2": float(r2_score(y_true, y_pred)),
    }


def run_full_ml_from_csvs_latitude(root_dir: Path, panel: Optional[pd.DataFrame] = None) -> None:
    """Treina ML completo com split temporal e projeta 2025-2040 usando csvs_latitude.

    Parameters
    ----------
    root_dir : Path
        Diretório raiz do projeto.
    panel : pd.DataFrame, optional
        Painel já carregado por build_base_panel() para evitar dupla leitura.
        Se None, carrega internamente via load_ml_panel_from_csvs_latitude().
    """
    out_dir = root_dir / "output" / "projecoes_regionais" / "ml_completo"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Reutiliza painel já carregado para evitar dupla leitura de disco.
    if panel is None:
        logger.info("run_full_ml: carregando painel de csvs_latitude (não fornecido externamente)")
        panel_ml = load_ml_panel_from_csvs_latitude(root_dir)
    else:
        logger.info("run_full_ml: reutilizando painel fornecido (%d registros)", len(panel))
        panel_ml = panel.copy()

    feat = _build_ml_features(panel_ml)

    feature_cols = [
        "temp_media", "precipitacao", "enso", "latitude", "month_sin", "month_cos",
        "dengue_lag1", "dengue_lag2", "dengue_lag3", "temp_lag1", "prec_lag1", "enso_lag1",
    ]

    train_df = feat[feat["year"] <= 2021].copy()
    val_df = feat[feat["year"] == 2022].copy()
    test_df = feat[(feat["year"] >= 2023) & (feat["year"] <= 2024)].copy()

    if train_df.empty or val_df.empty or test_df.empty:
        raise RuntimeError("Split temporal insuficiente para treino/validação/teste do ML completo")

    model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_depth=6,
        max_iter=500,
        min_samples_leaf=40,
        l2_regularization=0.1,
        random_state=42,
    )

    y_train_log = np.log1p(train_df["dengue_cases"].to_numpy(dtype=float))
    model.fit(train_df[feature_cols].to_numpy(dtype=float), y_train_log)

    val_pred = np.expm1(model.predict(val_df[feature_cols].to_numpy(dtype=float))).clip(min=0.0)
    test_pred = np.expm1(model.predict(test_df[feature_cols].to_numpy(dtype=float))).clip(min=0.0)

    metrics_rows = [
        _evaluate_split(val_df["dengue_cases"].to_numpy(dtype=float), val_pred, "valid_2022"),
        _evaluate_split(test_df["dengue_cases"].to_numpy(dtype=float), test_pred, "test_2023_2024"),
    ]
    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(out_dir / "metricas_ml_completo.csv", index=False, encoding="utf-8")
    with open(out_dir / "metricas_ml_completo.json", "w", encoding="utf-8") as f:
        json.dump(metrics_rows, f, ensure_ascii=False, indent=2)

    # Re-treino com todo histórico 2015-2024.
    full_model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_depth=6,
        max_iter=600,
        min_samples_leaf=40,
        l2_regularization=0.1,
        random_state=42,
    )
    full_model.fit(feat[feature_cols].to_numpy(dtype=float), np.log1p(feat["dengue_cases"].to_numpy(dtype=float)))

    # Projeção recursiva mensal 2025-2040 por município e cenário.
    clim = panel_ml.groupby(["code", "month"], as_index=False).agg(
        base_temp=("temp_media", "mean"),
        base_prec=("precipitacao", "mean"),
        base_enso=("enso", "mean"),
        latitude=("latitude", "median"),
        city_name=("city_name", "last"),
        lat_faixa_id=("lat_faixa_id", "last"),
    )

    hist_tail = panel_ml.sort_values(["code", "year", "month"]).groupby("code").tail(3)
    tail_map: Dict[str, List[float]] = {}
    for code, g in hist_tail.groupby("code"):
        vals = g.sort_values(["year", "month"])["dengue_cases"].astype(float).tolist()
        if len(vals) < 3:
            vals = ([0.0] * (3 - len(vals))) + vals
        tail_map[code] = vals[-3:]

    climate_tail = panel_ml.sort_values(["code", "year", "month"]).groupby("code").tail(1)
    ctail_map = {
        str(r["code"]): (float(r["temp_media"]), float(r["precipitacao"]), float(r["enso"]))
        for _, r in climate_tail.iterrows()
    }

    future_rows = []
    for code, g_code in clim.groupby("code"):
        code = str(code)
        lat = float(g_code["latitude"].iloc[0])
        city_name = str(g_code["city_name"].iloc[0])
        faixa = g_code["lat_faixa_id"].iloc[0]

        if code not in tail_map:
            continue
        dengue_lags = tail_map[code].copy()
        temp_last, prec_last, enso_last = ctail_map.get(code, (float(g_code["base_temp"].mean()), float(g_code["base_prec"].mean()), float(g_code["base_enso"].mean())))

        month_base = {int(r["month"]): (float(r["base_temp"]), float(r["base_prec"]), float(r["base_enso"])) for _, r in g_code.iterrows()}

        for sc, cfg in SCENARIOS.items():
            # Reinicia lags por cenário para manter independência das trajetórias.
            d_lags = dengue_lags.copy()
            t_lag1, p_lag1, e_lag1 = temp_last, prec_last, enso_last

            for year in range(PROJECTION_START, PROJECTION_END + 1):
                years_from_2024 = year - (CALIBRATION_YEAR - 1)
                for month in range(1, 13):
                    bt, bp, be = month_base.get(month, (np.nan, np.nan, np.nan))
                    if pd.isna(bt):
                        bt = float(g_code["base_temp"].mean())
                    if pd.isna(bp):
                        bp = float(g_code["base_prec"].mean())
                    if pd.isna(be):
                        be = float(g_code["base_enso"].mean())

                    temp = bt + float(cfg["temp_delta_per_year"]) * years_from_2024
                    prec = bp * (1.0 + float(cfg["precip_delta_pct_per_year"]) * years_from_2024)
                    enso = be + float(cfg["enso_delta_per_year"]) * years_from_2024

                    month_sin = float(np.sin(2.0 * np.pi * month / 12.0))
                    month_cos = float(np.cos(2.0 * np.pi * month / 12.0))

                    x = np.array([
                        temp, prec, enso, lat, month_sin, month_cos,
                        d_lags[-1], d_lags[-2], d_lags[-3], t_lag1, p_lag1, e_lag1,
                    ], dtype=float).reshape(1, -1)

                    pred_cases = float(np.expm1(full_model.predict(x)[0]))
                    pred_cases = max(pred_cases, 0.0)

                    future_rows.append(
                        {
                            "code": code,
                            "city_name": city_name,
                            "latitude": lat,
                            "lat_faixa_id": faixa,
                            "scenario": sc,
                            "year": year,
                            "month": month,
                            "pred_cases_ml": pred_cases,
                        }
                    )

                    d_lags.append(pred_cases)
                    d_lags = d_lags[-3:]
                    t_lag1, p_lag1, e_lag1 = temp, prec, enso

    fut = pd.DataFrame(future_rows)
    if fut.empty:
        raise RuntimeError("ML completo não gerou projeções futuras")

    fut.to_csv(out_dir / "projecao_ml_completa_municipios_mensal.csv", index=False, encoding="utf-8")

    fut_anual = fut.groupby(["code", "city_name", "latitude", "lat_faixa_id", "scenario", "year"], as_index=False)["pred_cases_ml"].sum()
    fut_anual.to_csv(out_dir / "projecao_ml_completa_municipios_anual.csv", index=False, encoding="utf-8")

    fut_reg = fut_anual.groupby(["scenario", "year"], as_index=False)["pred_cases_ml"].sum()
    fut_reg["regiao"] = "SUL"
    fut_reg.to_csv(out_dir / "projecao_ml_completa_regional_anual.csv", index=False, encoding="utf-8")

    # Exporta previsões e observados para inspeção rápida.
    val_out = val_df[["code", "year", "month", "dengue_cases"]].copy()
    val_out["pred_cases_ml"] = val_pred
    val_out["split"] = "valid_2022"

    test_out = test_df[["code", "year", "month", "dengue_cases"]].copy()
    test_out["pred_cases_ml"] = test_pred
    test_out["split"] = "test_2023_2024"

    pd.concat([val_out, test_out], ignore_index=True).to_csv(out_dir / "backtest_ml_completo.csv", index=False, encoding="utf-8")

    logger.info("ML completo treinado com csvs_latitude (train/val/test temporal)")
    logger.info("Saídas ML: output/projecoes_regionais/ml_completo/")


def save_pdf_reports(
    root_dir: Path,
    panel: pd.DataFrame,
    projections: pd.DataFrame,
    calibration: CalibrationBundle,
    coverage: CoverageInfo,
) -> Tuple[Path, Path]:
    """Gera dois PDFs: gráficos por latitude + relatório executivo."""
    out_dir = root_dir / "output" / "projecoes_regionais"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ======== PDF 1: Gráficos por Latitude ========
    pdf_lat_path = out_dir / "relatorio_graficos_por_latitude.pdf"
    plt.style.use("seaborn-v0_8-whitegrid")
    hist = panel[(panel["year"] >= 2015) & (panel["year"] <= 2024)].copy()

    lat_bins = np.linspace(projections["latitude"].min(), projections["latitude"].max(), 9)
    projections["lat_faixa"] = pd.cut(projections["latitude"], bins=lat_bins, include_lowest=True)
    hist["lat_faixa"] = pd.cut(hist["latitude"], bins=lat_bins, include_lowest=True)
    model_codes = set(panel["code"].astype(str).unique().tolist())
    hist_lat_csv, hist_regional_csv = load_historical_incidents_from_csvs_latitude(root_dir, lat_bins, model_codes=model_codes)

    scen_order = ["ssp126", "ssp245", "ssp370", "ssp585"]
    scen_fill_order = ["ssp585", "ssp370", "ssp245", "ssp126"]
    scen_labels = {
        "ssp126": "SSP1-2.6 (Otimista)",
        "ssp245": "SSP2-4.5 (Intermediário Baixo)",
        "ssp370": "SSP3-7.0 (Intermediário Alto)",
        "ssp585": "SSP5-8.5 (Severo)",
    }
    scen_colors = {
        "ssp126": "#3f8f8f",
        "ssp245": "#3b5f8a",
        "ssp370": "#cc7f2a",
        "ssp585": "#b24a3a",
    }
    scen_alpha = {
        "ssp126": 0.12,
        "ssp245": 0.13,
        "ssp370": 0.14,
        "ssp585": 0.15,
    }

    with PdfPages(pdf_lat_path) as pdf:
        # Página 1: Visão consolidada (histórico + projeção)
        fig, ax1 = plt.subplots(figsize=(12, 6.5))
        if not hist_regional_csv.empty:
            hist_regional = hist_regional_csv.copy()
        else:
            hist_regional = hist.groupby("year", as_index=False)["dengue_cases"].sum().rename(columns={"dengue_cases": "incidentes"})

        hist_regional = pd.DataFrame({"year": np.arange(2015, 2025, 1)}).merge(hist_regional, on="year", how="left")
        hist_regional["incidentes"] = hist_regional["incidentes"].fillna(0.0)

        ax1.fill_between(hist_regional["year"], 0.0, hist_regional["incidentes"], color="#3a9f9a", alpha=0.25)
        ax1.plot(hist_regional["year"], hist_regional["incidentes"], color="#1f7f7a", linewidth=2.8, marker="o", markersize=5)
        ax1.set_title("INCIDENTES HISTÓRICOS - REGIÃO SUL CONSOLIDADA (2015-2024)", fontsize=12, fontweight="bold")
        ax1.set_xlabel("ANO", fontsize=10)
        ax1.set_ylabel("TOTAL DE INCIDENTES", fontsize=10)
        ax1.set_xticks(np.arange(2015, 2025, 1))
        ax1.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
        ax1.grid(False)
        ax1.grid(axis="y", linestyle="-", alpha=0.22)
        ax1.grid(axis="x", linestyle="-", alpha=0.08)

        max_year = hist_regional.loc[hist_regional["incidentes"].idxmax(), "year"]
        max_cases = hist_regional["incidentes"].max()
        prev_cases = float(hist_regional.loc[hist_regional["year"] == (max_year - 1), "incidentes"].sum())
        var_pct = ((max_cases - prev_cases) / max(prev_cases, EPS)) * 100.0
        peak_label = f"Pico: {int(max_cases):,}".replace(",", ".") + f"\n({var_pct:+.1f}% vs {int(max_year - 1)})"
        ax1.annotate(
            peak_label,
            xy=(max_year, max_cases),
            xytext=(max_year - 2.2, max_cases * 0.78),
            arrowprops=dict(arrowstyle="->", color="red", lw=1.6),
            fontsize=9,
            color="red",
            fontweight="bold",
        )

        plt.tight_layout()
        pdf.savefig(fig, dpi=300)
        plt.close(fig)

        fig, ax2 = plt.subplots(figsize=(12, 6.5))

        proj_regional = projections.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
        hist_regional_series = hist_regional["incidentes"].to_numpy()
        hist_regional_cv = float(np.std(hist_regional_series) / max(np.mean(hist_regional_series), EPS)) if len(hist_regional_series) > 1 else 0.20

        hist_2024_reg = float(hist_regional.loc[hist_regional["year"] == 2024, "incidentes"].sum())
        ax2.plot(
            hist_regional["year"],
            hist_regional["incidentes"],
            color="black",
            linewidth=2.2,
            marker="o",
            markersize=3,
            label="Dados observados (2015-2024)",
            zorder=4,
        )

        for sc in scen_fill_order:
            ds = proj_regional[proj_regional["scenario"] == sc].sort_values("year")
            if ds.empty:
                continue
            years_np = ds["year"].to_numpy(dtype=float)
            vals_np = ds["pred_cases"].to_numpy(dtype=float)
            lo, hi = uncertainty_bounds(years_np, vals_np, hist_regional_cv, sc)
            ax2.fill_between(ds["year"], lo, hi, color=scen_colors[sc], alpha=scen_alpha[sc], linewidth=0, zorder=1)

        for sc in scen_order:
            ds = proj_regional[proj_regional["scenario"] == sc].sort_values("year")
            if ds.empty:
                continue
            ax2.plot(
                ds["year"],
                ds["pred_cases"],
                linewidth=2.3,
                color=scen_colors[sc],
                label=f"Previsão {scen_labels[sc]}",
                marker="o",
                markersize=4,
                zorder=3,
            )
            y2025 = float(ds.loc[ds["year"] == PROJECTION_START, "pred_cases"].iloc[0]) if (ds["year"] == PROJECTION_START).any() else float(ds["pred_cases"].iloc[0])
            ax2.plot([2024, PROJECTION_START], [hist_2024_reg, y2025], color="black", linewidth=1.6, linestyle="-", alpha=0.85, zorder=3)

        ax2.set_title(f"PROJEÇÃO - REGIÃO SUL ({PROJECTION_START}-{PROJECTION_END})", fontsize=12, fontweight="bold")
        ax2.set_xlabel("ANO", fontsize=10)
        ax2.set_ylabel("")
        ax2.set_xticks(np.arange(2015, PROJECTION_END + 1, 5))
        ax2.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
        ax2.grid(True, linestyle="-", alpha=0.20)
        ax2.legend(loc="upper left", fontsize=8.5, frameon=True, title="Cenários (linha + faixa de incerteza %)")

        plt.tight_layout()
        pdf.savefig(fig, dpi=300)
        plt.close(fig)

        # Páginas 2-9: Histórico + Projeção por latitude
        for lat_faixa in sorted(projections["lat_faixa"].dropna().unique())[:8]:
            fig, ax1 = plt.subplots(figsize=(12, 6.5))

            lat_min = float(lat_faixa.left)
            lat_max = float(lat_faixa.right)
            lat_label = f"{abs(lat_min):.1f}°S a {abs(lat_max):.1f}°S"

            # Histórico
            if not hist_lat_csv.empty:
                hist_lat = hist_lat_csv[hist_lat_csv["lat_faixa"] == lat_faixa].copy()
            else:
                hist_lat = hist[hist["lat_faixa"] == lat_faixa].groupby("year", as_index=False)["dengue_cases"].sum().rename(columns={"dengue_cases": "incidentes"})

            full_years = pd.DataFrame({"year": np.arange(2015, 2025, 1)})
            hist_lat = full_years.merge(hist_lat[["year", "incidentes"]], on="year", how="left")
            hist_lat["incidentes"] = hist_lat["incidentes"].fillna(0.0)

            ax1.fill_between(hist_lat["year"], 0.0, hist_lat["incidentes"], color="#2c908b", alpha=0.22)
            ax1.plot(hist_lat["year"], hist_lat["incidentes"], color="#1d6e6a", linewidth=2.4, marker="o", markersize=4)
            ax1.set_title(f"HISTÓRICO - FAIXA {lat_label}\n(2015-2024)", fontsize=12, fontweight="bold")
            ax1.set_xlabel("ANO", fontsize=10)
            ax1.set_ylabel("INCIDENTES", fontsize=10)
            ax1.set_xticks(np.arange(2015, 2025, 1))
            ax1.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
            ax1.grid(False)
            ax1.grid(axis="y", linestyle="-", alpha=0.20)
            ax1.grid(axis="x", linestyle="-", alpha=0.08)

            plt.tight_layout()
            pdf.savefig(fig, dpi=300)
            plt.close(fig)

            fig, ax2 = plt.subplots(figsize=(12, 6.5))

            # Projeção
            proj_lat = projections[projections["lat_faixa"] == lat_faixa].groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()

            # Mantém trecho histórico no painel de projeção (2015-2024), como solicitado.
            ax2.plot(
                hist_lat["year"],
                hist_lat["incidentes"],
                color="black",
                linewidth=2.0,
                marker="o",
                markersize=3,
                label="Dados observados (2015-2024)",
                zorder=4,
            )
            hist_2024_lat = float(hist_lat.loc[hist_lat["year"] == 2024, "incidentes"].sum())

            for sc in scen_fill_order:
                ds = proj_lat[proj_lat["scenario"] == sc].sort_values("year")
                if not ds.empty:
                    hist_series = hist_lat["incidentes"].to_numpy()
                    hist_cv = float(np.std(hist_series) / max(np.mean(hist_series), EPS)) if len(hist_series) > 1 else 0.20
                    years_np = ds["year"].to_numpy(dtype=float)
                    vals_np = ds["pred_cases"].to_numpy(dtype=float)
                    lo, hi = uncertainty_bounds(years_np, vals_np, hist_cv, sc)
                    ax2.fill_between(ds["year"], lo, hi, color=scen_colors[sc], alpha=scen_alpha[sc], linewidth=0, zorder=1)

            for sc in scen_order:
                ds = proj_lat[proj_lat["scenario"] == sc].sort_values("year")
                if not ds.empty:
                    ax2.plot(
                        ds["year"],
                        ds["pred_cases"],
                        linewidth=2.3,
                        color=scen_colors[sc],
                        label=f"Previsão {scen_labels[sc]}",
                        marker="o",
                        markersize=4,
                        zorder=3,
                    )
                    y2025 = float(ds.loc[ds["year"] == PROJECTION_START, "pred_cases"].iloc[0]) if (ds["year"] == PROJECTION_START).any() else float(ds["pred_cases"].iloc[0])
                    ax2.plot([2024, PROJECTION_START], [hist_2024_lat, y2025], color="black", linewidth=1.6, linestyle="-", alpha=0.85, zorder=3)

            ax2.set_title("")
            ax2.set_xlabel("ANO", fontsize=10)
            ax2.set_ylabel("")
            ax2.set_xticks([2015, 2020, 2024, 2030, 2035, 2040])
            ax2.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
            ax2.grid(True, linestyle="-", alpha=0.20)
            ax2.legend(loc="upper left", fontsize=8.5, frameon=True, title="Séries")
            ax2.text(
                0.52,
                0.03,
                "2024: fim dos dados observados | 2025: início da previsão",
                transform=ax2.transAxes,
                fontsize=8.6,
                color="#333333",
                ha="center",
            )

            plt.tight_layout()
            pdf.savefig(fig, dpi=300)
            plt.close(fig)

        # Última página: Consolidado regional
        fig, ax1 = plt.subplots(figsize=(12, 6.5))

        if not hist_regional_csv.empty:
            hist_regional = hist_regional_csv.copy()
        else:
            hist_regional = hist.groupby("year", as_index=False)["dengue_cases"].sum().rename(columns={"dengue_cases": "incidentes"})

        hist_regional = pd.DataFrame({"year": np.arange(2015, 2025, 1)}).merge(hist_regional, on="year", how="left")
        hist_regional["incidentes"] = hist_regional["incidentes"].fillna(0.0)

        ax1.fill_between(hist_regional["year"], 0.0, hist_regional["incidentes"], color="#2d9590", alpha=0.25)
        ax1.plot(hist_regional["year"], hist_regional["incidentes"], color="#1f706c", linewidth=2.7, marker="o", markersize=4)
        ax1.set_title("CONSOLIDADO HISTÓRICO - REGIÃO SUL (2015-2024)", fontsize=12, fontweight="bold")
        ax1.set_xlabel("ANO", fontsize=10)
        ax1.set_ylabel("INCIDENTES", fontsize=10)
        ax1.set_xticks(np.arange(2015, 2025, 1))
        ax1.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
        ax1.grid(False)
        ax1.grid(axis="y", linestyle="-", alpha=0.22)
        ax1.grid(axis="x", linestyle="-", alpha=0.08)

        max_year = hist_regional.loc[hist_regional["incidentes"].idxmax(), "year"]
        max_cases = hist_regional["incidentes"].max()
        prev_cases = float(hist_regional.loc[hist_regional["year"] == (max_year - 1), "incidentes"].sum())
        var_pct = ((max_cases - prev_cases) / max(prev_cases, EPS)) * 100.0
        peak_label = f"Pico: {int(max_cases):,}".replace(",", ".") + f"\n({var_pct:+.1f}% vs {int(max_year - 1)})"
        ax1.annotate(
            peak_label,
            xy=(max_year, max_cases),
            xytext=(max_year - 2.2, max_cases * 0.78),
            arrowprops=dict(arrowstyle="->", color="#b24a3a", lw=1.5),
            fontsize=8.5,
            color="#b24a3a",
            fontweight="bold",
        )

        plt.tight_layout()
        pdf.savefig(fig, dpi=300)
        plt.close(fig)

        fig, ax2 = plt.subplots(figsize=(12, 6.5))

        proj_regional = projections.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
        hist_regional_series = hist_regional["incidentes"].to_numpy()
        hist_regional_cv = float(np.std(hist_regional_series) / max(np.mean(hist_regional_series), EPS)) if len(hist_regional_series) > 1 else 0.20

        hist_2024_reg = float(hist_regional.loc[hist_regional["year"] == 2024, "incidentes"].sum())
        ax2.plot(
            hist_regional["year"],
            hist_regional["incidentes"],
            color="black",
            linewidth=2.2,
            marker="o",
            markersize=3,
            label="Dados observados (2015-2024)",
            zorder=4,
        )

        for sc in scen_fill_order:
            ds = proj_regional[proj_regional["scenario"] == sc].sort_values("year")
            if not ds.empty:
                years_np = ds["year"].to_numpy(dtype=float)
                vals_np = ds["pred_cases"].to_numpy(dtype=float)
                lo, hi = uncertainty_bounds(years_np, vals_np, hist_regional_cv, sc)
                ax2.fill_between(ds["year"], lo, hi, color=scen_colors[sc], alpha=scen_alpha[sc], linewidth=0, zorder=1)

        for sc in scen_order:
            ds = proj_regional[proj_regional["scenario"] == sc].sort_values("year")
            if not ds.empty:
                ax2.plot(
                    ds["year"],
                    ds["pred_cases"],
                    linewidth=2.2,
                    color=scen_colors[sc],
                    label=f"Previsão {scen_labels[sc]}",
                    marker="s",
                    markersize=5,
                    zorder=3,
                )
                y2025 = float(ds.loc[ds["year"] == PROJECTION_START, "pred_cases"].iloc[0]) if (ds["year"] == PROJECTION_START).any() else float(ds["pred_cases"].iloc[0])
                ax2.plot([2024, PROJECTION_START], [hist_2024_reg, y2025], color="black", linewidth=1.6, linestyle="-", alpha=0.85, zorder=3)

        ax2.set_title(f"CONSOLIDADO PROJETADO - REGIÃO SUL ({PROJECTION_START}-{PROJECTION_END})", fontsize=12, fontweight="bold")
        ax2.set_xlabel("ANO", fontsize=10)
        ax2.set_ylabel("")
        ax2.set_xticks(np.arange(2015, PROJECTION_END + 1, 5))
        ax2.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
        ax2.grid(True, linestyle="-", alpha=0.20)
        ax2.legend(loc="upper left", fontsize=8.5, frameon=True, title="Cenários (linha + faixa de incerteza %)")

        plt.tight_layout()
        pdf.savefig(fig, dpi=300)
        plt.close(fig)

    # ======== PDF 2: Relatório Executivo ========
    pdf_exec_path = out_dir / "relatorio_executivo_completo.pdf"

    with PdfPages(pdf_exec_path) as pdf:
        def write_paragraph(ax_obj, text: str, y0: float, *, x0: float = 0.07, width: int = 105, fontsize: int = 10, line_h: float = 0.029, color: str = "#222222", weight: str = "normal") -> float:
            lines = textwrap.wrap(text, width=width)
            y = y0
            for ln in lines:
                ax_obj.text(x0, y, ln, fontsize=fontsize, transform=ax_obj.transAxes, color=color, fontweight=weight, va="top")
                y -= line_h
            return y

        hist_reg = panel[(panel["year"] >= 2015) & (panel["year"] <= 2024)].groupby("year", as_index=False)["dengue_cases"].sum()
        hist_reg = hist_reg.rename(columns={"dengue_cases": "incidentes"})
        hist_reg = pd.DataFrame({"year": np.arange(2015, 2025, 1)}).merge(hist_reg, on="year", how="left")
        hist_reg["incidentes"] = hist_reg["incidentes"].fillna(0.0)

        proj_reg = projections.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
        hist_2024 = float(hist_reg.loc[hist_reg["year"] == 2024, "incidentes"].sum())
        avg_hist = float(hist_reg["incidentes"].mean())
        ssp126_2040 = float(proj_reg[(proj_reg["scenario"] == "ssp126") & (proj_reg["year"] == 2040)]["pred_cases"].sum())
        ssp585_2040 = float(proj_reg[(proj_reg["scenario"] == "ssp585") & (proj_reg["year"] == 2040)]["pred_cases"].sum())
        gap_2040 = ((ssp585_2040 - ssp126_2040) / max(ssp126_2040, EPS)) * 100.0
        proj_2040 = projections[projections["year"] == 2040].copy()
        proj_2040["lat_faixa"] = pd.cut(proj_2040["latitude"], bins=lat_bins, include_lowest=True)
        lat_2040_ssp585 = (
            proj_2040[proj_2040["scenario"] == "ssp585"]
            .groupby("lat_faixa", as_index=False, observed=False)["pred_cases"]
            .sum()
            .sort_values("lat_faixa")
        )
        lat_2040_ssp126 = (
            proj_2040[proj_2040["scenario"] == "ssp126"]
            .groupby("lat_faixa", as_index=False, observed=False)["pred_cases"]
            .sum()
            .sort_values("lat_faixa")
        )

        # Pagina 1 - Capa (ABNT simplificado)
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis("off")
        ax.text(0.5, 0.88, "PROJETO CLIMA X DENGUE", ha="center", fontsize=24, fontweight="bold", transform=ax.transAxes, color="#1f706c")
        ax.text(0.5, 0.81, "RELATORIO EXECUTIVO TECNICO", ha="center", fontsize=14, fontweight="bold", transform=ax.transAxes)
        ax.text(0.5, 0.76, f"Regiao Sul do Brasil | Horizonte {PROJECTION_START}-{PROJECTION_END}", ha="center", fontsize=11, transform=ax.transAxes)
        ax.text(0.5, 0.13, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ha="center", fontsize=10, transform=ax.transAxes, color="#555555")
        plt.tight_layout()
        pdf.savefig(fig, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Pagina 2 - Sumario (inicio do documento)
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis("off")
        ax.text(0.5, 0.95, "SUMARIO", ha="center", fontsize=16, fontweight="bold", transform=ax.transAxes)
        sum_items = [
            "1 INTRODUCAO ............................................................ 3",
            "2 OBJETIVOS ............................................................ 3",
            "3 CONFIGURACAO DO MODELO ............................................... 4",
            "4 METODOLOGIA .......................................................... 4",
            "5 RESULTADOS E ANALISE ................................................. 5",
            "6 DISCUSSAO ............................................................ 6",
            "7 CONCLUSAO E RECOMENDACOES ............................................ 6",
            "APENDICE A - DEFINICOES OPERACIONAIS ................................... 7",
        ]
        y = 0.86
        for item in sum_items:
            ax.text(0.12, y, item, fontsize=11, transform=ax.transAxes, family="serif")
            y -= 0.08
        plt.tight_layout()
        pdf.savefig(fig, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Pagina 3 - Introducao e objetivos
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis("off")
        ax.text(0.07, 0.95, "1 INTRODUCAO", fontsize=14, fontweight="bold", transform=ax.transAxes)
        y = 0.90
        y = write_paragraph(
            ax,
            "A dengue representa um desafio recorrente para a saude publica brasileira. No Sul, a variabilidade climatica interanual e a heterogeneidade territorial exigem planejamento antecipado e criterio tecnico para alocacao de recursos.",
            y,
            width=106,
            fontsize=11,
            line_h=0.032,
        )
        y -= 0.01
        y = write_paragraph(
            ax,
            "Este relatorio foi estruturado em formato academico para documentar premissas, metodo, resultados e limites da modelagem. A narrativa foi organizada para permitir leitura por equipes tecnicas e por gestores, mantendo rastreabilidade entre graficos e decisoes.",
            y,
            width=106,
            fontsize=11,
            line_h=0.032,
        )
        y -= 0.02
        ax.text(0.07, y, "2 OBJETIVOS", fontsize=14, fontweight="bold", transform=ax.transAxes)
        y -= 0.05
        goals = [
            "2.1 Estimar o comportamento historico regional de incidentes entre 2015 e 2024.",
            f"2.2 Projetar incidentes para {PROJECTION_START}-{PROJECTION_END} em quatro cenarios SSP.",
            "2.3 Comparar diferencas territoriais por oito faixas de latitude.",
            "2.4 Produzir material interpretativo para apoio a vigilancia epidemiologica.",
        ]
        for g in goals:
            y = write_paragraph(ax, g, y, width=104, fontsize=11, line_h=0.034)
        plt.tight_layout()
        pdf.savefig(fig, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Pagina 4 - Configuracao do modelo + Metodologia
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis("off")
        ax.text(0.07, 0.95, "3 CONFIGURACAO DO MODELO", fontsize=14, fontweight="bold", transform=ax.transAxes)
        y = 0.90
        model_cfg = [
            f"Janela de treino local (config): {TRAIN_START}-{TRAIN_END}.",
            f"Ano de calibracao/projecao inicial: {CALIBRATION_YEAR}.",
            f"Horizonte final de projecao: {PROJECTION_END}.",
            "Cenarios ativos: SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5.",
            "Variaveis do modelo: temperatura, precipitacao, ENSO (lag 3) e latitude.",
            "Sem imunidade dinamica e sem calibracao exogena nesta versao.",
        ]
        for s in model_cfg:
            y = write_paragraph(ax, s, y, width=104, fontsize=11, line_h=0.034)
        y -= 0.01
        y = write_paragraph(
            ax,
            "Formula estrutural: log(Y+1) = alpha_local + beta_temp*T_lag3 + beta_prec*P_lag3 + beta_enso*ENSO_lag3 + beta_lat*Latitude.",
            y,
            width=104,
            fontsize=11,
            line_h=0.034,
        )
        y = write_paragraph(
            ax,
            f"Coeficientes utilizados nesta versao: beta_temp={BETA_TMED:.3f}, beta_prec={BETA_PREC:.3f}, beta_enso={BETA_ENSO:.3f}, beta_lat={BETA_LAT:.3f}.",
            y,
            width=104,
            fontsize=11,
            line_h=0.034,
        )
        y -= 0.02
        ax.text(0.07, y, "4 METODOLOGIA", fontsize=14, fontweight="bold", transform=ax.transAxes)
        y -= 0.05
        methodology = [
            "4.1 Integracao e limpeza de dados em painel mensal por municipio.",
            "4.2 Estimacao de intercepto local robusto por serie municipal.",
            "4.3 Aplicacao de deltas SSP sobre climatologia base 2024.",
            "4.4 Agregacao anual por faixa de latitude e consolidado regional.",
            "4.5 Bandas de incerteza percentuais para leitura de risco.",
        ]
        for m in methodology:
            y = write_paragraph(ax, m, y, width=104, fontsize=11, line_h=0.034)
        plt.tight_layout()
        pdf.savefig(fig, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Pagina 5 - Resultados regionais com figuras
        fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(11, 8.5))
        fig.suptitle("5 RESULTADOS E ANALISE", fontsize=14, fontweight="bold", y=0.98)

        ax_l.fill_between(hist_reg["year"], 0.0, hist_reg["incidentes"], color="#3a9f9a", alpha=0.24)
        ax_l.plot(hist_reg["year"], hist_reg["incidentes"], color="#1f7f7a", linewidth=2.0, marker="o", markersize=3)
        ax_l.set_title("Figura 1 - Serie historica regional", fontsize=10)
        ax_l.set_xlabel("Ano")
        ax_l.set_ylabel("Incidentes")
        ax_l.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
        ax_l.grid(axis="y", linestyle="-", alpha=0.20)

        for sc in ["ssp126", "ssp245", "ssp370", "ssp585"]:
            ds = proj_reg[proj_reg["scenario"] == sc].sort_values("year")
            if ds.empty:
                continue
            ax_r.plot(ds["year"], ds["pred_cases"], linewidth=2.0, marker="o", markersize=2.5, label=sc.upper())
        ax_r.set_title("Figura 2 - Projecoes regionais SSP", fontsize=10)
        ax_r.set_xlabel("Ano")
        ax_r.set_ylabel("Incidentes projetados")
        ax_r.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
        ax_r.grid(axis="y", linestyle="-", alpha=0.20)
        ax_r.legend(loc="upper left", fontsize=8)

        fig.text(0.08, 0.08, f"Interpretacao: em 2040, o diferencial entre SSP5-8.5 e SSP1-2.6 e de {gap_2040:.1f}%, indicando sensibilidade substancial ao cenario climaticamente mais severo.", fontsize=9.5)
        plt.tight_layout(rect=[0, 0.11, 1, 0.95])
        pdf.savefig(fig, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Pagina 6 - Resultados por latitude + discussao/conclusao
        fig, ax = plt.subplots(figsize=(11, 8.5))
        faixa_labels = [f"F{i+1}" for i in range(len(lat_2040_ssp585))]
        x = np.arange(len(faixa_labels))
        w = 0.36
        ax.bar(x - w / 2, lat_2040_ssp126["pred_cases"].to_numpy(), w, label="SSP1-2.6", color="#3f8f8f", alpha=0.85)
        ax.bar(x + w / 2, lat_2040_ssp585["pred_cases"].to_numpy(), w, label="SSP5-8.5", color="#b24a3a", alpha=0.85)
        ax.set_title("5 RESULTADOS POR FAIXA DE LATITUDE (2040)", fontsize=14, fontweight="bold")
        ax.set_xlabel("Faixas de latitude")
        ax.set_ylabel("Incidentes projetados")
        ax.set_xticks(x)
        ax.set_xticklabels(faixa_labels)
        ax.yaxis.set_major_formatter(FuncFormatter(incidentes_formatter))
        ax.grid(axis="y", linestyle="-", alpha=0.20)
        ax.legend(loc="upper left")
        fig.text(0.08, 0.08, "6 DISCUSSAO: o contraste entre faixas reforca a necessidade de priorizacao territorial na vigilancia.", fontsize=9.5)
        fig.text(0.08, 0.05, "7 CONCLUSAO: a configuracao atual do modelo permite leitura consistente de cenarios e apoio ao planejamento operacional.", fontsize=9.5)
        plt.tight_layout(rect=[0, 0.08, 1, 0.96])
        pdf.savefig(fig, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Pagina 7 - Apendice
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis("off")
        ax.text(0.5, 0.95, "APENDICE A - DEFINICOES OPERACIONAIS", ha="center", fontsize=14, fontweight="bold", transform=ax.transAxes)
        y = 0.88
        glossary = [
            "Incidentes: total anual agregado de casos observados/projetados de dengue.",
            "Cenarios SSP: trajetorias climatico-socioeconomicas usadas para projecao prospectiva.",
            "Faixa de incerteza: intervalo percentual simetrico em torno da curva projetada.",
            "Faixas de latitude: agrupamentos espaciais para leitura territorial da serie.",
            "Lag 3 meses: defasagem aplicada para capturar resposta epidemiologica ao clima.",
        ]
        for g in glossary:
            y = write_paragraph(ax, f"- {g}", y, width=104, fontsize=11, line_h=0.034)
        ax.text(0.5, 0.08, "Documento estruturado para uso tecnico-institucional e apoio a planejamento.", ha="center", fontsize=9.5, transform=ax.transAxes)
        plt.tight_layout()
        pdf.savefig(fig, dpi=300, bbox_inches="tight")
        plt.close(fig)

    return pdf_lat_path, pdf_exec_path


# ========================= MAIN =========================

def main() -> None:
    root_dir = ROOT_DATA_DIR
    if not root_dir.exists():
        raise FileNotFoundError(f"Diretório raiz não encontrado: {root_dir}")

    logger.info("=" * 70)
    logger.info("MOTOR V2 — MODELAGEM CLIMA-SAÚDE (DENGUE) | REGIÃO SUL POR LATITUDE")
    logger.info("=" * 70)

    # 0) Validação de fontes antes de qualquer leitura
    validate_data_sources(root_dir)

    # 1) Painel base (fonte canônica: csvs_latitude quando disponível)
    panel, lookup = build_base_panel(root_dir)
    if panel.empty:
        raise RuntimeError("Painel base vazio após leitura.")

    lookup_sul = (
        lookup[lookup["code"].astype(str).str[:2].isin(["41", "42", "43"])].copy()
        if not lookup.empty
        else pd.DataFrame(columns=["code"])
    )
    coverage = CoverageInfo(
        municipios_sul_total=max(
            TOTAL_MUNICIPIOS_SUL_OFICIAL,
            int(lookup_sul["code"].nunique()) if not lookup_sul.empty else int(panel["code"].nunique()),
        ),
        municipios_com_dados=int(panel["code"].nunique()),
    )

    logger.info("Painel base construído:")
    logger.info("  Registros        : %s", f"{len(panel):,}")
    logger.info("  Municípios Sul   : %s", f"{coverage.municipios_sul_total:,}")
    logger.info("  Municípios dados : %s", f"{coverage.municipios_com_dados:,}")
    logger.info("  Período          : %s-%s", panel['year'].min(), panel['year'].max())
    logger.info("  Latitude range   : %.1f°S a %.1f°S", panel['latitude'].min(), panel['latitude'].max())

    # 2) Treinamento local (intercepto por município)
    local_intercepts: Dict[str, float] = {}
    for code, g in panel.groupby("code"):
        local_intercepts[code] = train_local_intercept(g)
    logger.info("Treinamento local concluído: %d modelos", len(local_intercepts))

    # 3) Calibração regional (desativada — sem ajuste externo)
    calib = calibrate_region(panel, local_intercepts)
    logger.info("Calibração externa desativada (sem imunidade, sem âncora Arapongas)")

    # 4) Projeção por município
    all_proj = []
    for code, g in panel.groupby("code"):
        proj = project_city(g, local_intercepts.get(code, 0.0), calib)
        if not proj.empty:
            all_proj.append(proj)

    if not all_proj:
        raise RuntimeError("Nenhuma projeção gerada.")

    projections = pd.concat(all_proj, ignore_index=True)
    logger.info("Projeções log-linear geradas: %s registros", f"{len(projections):,}")

    # 5) Saída por latitude + consolidado regional
    save_outputs_by_latitude(root_dir, projections, calib)

    # 5.1) Previsão pontual 2025 (com e sem incremento SSP)
    save_ml_2025_forecasts(root_dir, panel, local_intercepts)

    # 5.2) ML completo (HistGradientBoosting) — reutiliza painel já carregado
    run_full_ml_from_csvs_latitude(root_dir, panel=panel)

    # 6) PDFs
    pdf_lat, pdf_exec = save_pdf_reports(root_dir, panel, projections, calib, coverage)
    logger.info("Relatórios gerados:")
    logger.info("  PDF gráficos : %s", pdf_lat.name)
    logger.info("  PDF executivo: %s", pdf_exec.name)

    logger.info("=" * 70)
    logger.info("CONCLUÍDO — Saída em output/projecoes_regionais/")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
