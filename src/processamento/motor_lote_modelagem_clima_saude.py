#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de processamento em lote para modelagem clima-saude (dengue) na Regiao Sul.

ONDE CONFIGURAR O DIRETORIO PRINCIPAL DE DADOS:
- Ajuste a variavel ROOT_DATA_DIR abaixo para apontar para a raiz do seu projeto.

Fluxo principal:
1) Descobre arquivos com os.walk.
2) Monta painel mensal por municipio (dengue + clima + ENSO + latitude).
3) Treina modelo local robusto (intercepto local com coeficientes base fixos).
4) Calibra ajuste regional via Arapongas (bias 2025 e termo de imunidade pos-surto).
5) Projeta 2026-2040 por cenario SSP (metodo delta).
6) Salva CSV por localidade e um resumo geral.
"""

from __future__ import annotations

import os
import re
import json
import unicodedata
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


# ========================= CONFIGURACOES GERAIS =========================
# Importa caminho raiz do config centralizado (portabilidade entre máquinas)
from src.config import BASE_DIR as ROOT_DATA_DIR

TRAIN_START = 2014
TRAIN_END = 2024
CALIBRATION_YEAR = 2025
PROJECTION_START = 2026
PROJECTION_END = 2040

ARAPONGAS_LAT = -23.42
ARAPONGAS_REAL_2025 = 1455.0

# Coeficientes base informados (modelo log-linear)
BETA_TMED = 0.661
BETA_PREC = 0.093
BETA_ENSO = 0.043
BETA_LAT = 0.142

# Parametros de robustez / seguranca numerica
EPS = 1e-9

# Deltas climaticos anuais (defaults praticos para AR6 SSP)
SCENARIOS = {
    "ssp126": {"temp_delta_per_year": 0.02, "precip_delta_pct_per_year": 0.003, "enso_delta_per_year": 0.00},
    "ssp245": {"temp_delta_per_year": 0.04, "precip_delta_pct_per_year": 0.006, "enso_delta_per_year": 0.00},
    "ssp370": {"temp_delta_per_year": 0.06, "precip_delta_pct_per_year": 0.010, "enso_delta_per_year": 0.01},
    "ssp585": {"temp_delta_per_year": 0.08, "precip_delta_pct_per_year": 0.015, "enso_delta_per_year": 0.02},
}


@dataclass
class CalibrationBundle:
    intercept_shift: float
    immunity_gamma: float
    threshold_peak_2024: float
    arapongas_code: Optional[str]
    arapongas_pred_2025_raw: float


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_") or "localidade"


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
    # Leitura robusta para arquivos wide com variacao de cabecalho
    try:
        raw = pd.read_csv(path_csv, sep=";", header=None, dtype=str, encoding="utf-8", engine="python")
    except UnicodeDecodeError:
        raw = pd.read_csv(path_csv, sep=";", header=None, dtype=str, encoding="latin-1", engine="python")

    if raw.shape[1] < 3:
        raise ValueError(f"Arquivo invalido para formato wide: {path_csv}")

    # Detecta linha de cabecalho com varios codigos municipais
    header_row = None
    for i in range(min(len(raw), 10)):
        vals = raw.iloc[i].fillna("").astype(str).tolist()
        count_codes = sum(1 for v in vals if normalize_code(v) is not None)
        if count_codes >= 20:
            header_row = i
            break

    if header_row is None:
        raise ValueError(f"Nao foi possivel detectar cabecalho municipal em: {path_csv}")

    header = raw.iloc[header_row].fillna("").astype(str).tolist()
    df = raw.iloc[header_row + 1 :].copy()
    df.columns = header

    # Renomeia as 2 primeiras colunas para year/month
    cols = list(df.columns)
    cols[0] = "year"
    cols[1] = "month"
    df.columns = cols

    # Mantem apenas colunas com codigo municipal (6 digitos)
    valid_cols = ["year", "month"]
    code_map: Dict[str, str] = {}
    for c in df.columns[2:]:
        code = normalize_code(c)
        if code:
            valid_cols.append(c)
            code_map[c] = code

    if len(valid_cols) <= 2:
        raise ValueError(f"Nenhuma coluna municipal encontrada em: {path_csv}")

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


def build_base_panel(root_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    raw_dir = root_dir / "data" / "raw"
    output_lat_dir = root_dir / "output" / "csvs_latitude"

    dengue_path = raw_dir / "dengue_MENSAL.csv"
    temp_path = raw_dir / "Temp_media_MENSAL.csv"
    prec_path = raw_dir / "precipitacao_mensal_rev.csv"
    enso_path = raw_dir / "elnino_lanina_2015-2024.csv"

    for p in [dengue_path, temp_path, prec_path, enso_path]:
        if not p.exists():
            raise FileNotFoundError(f"Arquivo essencial nao encontrado: {p}")

    dengue = read_wide_monthly(dengue_path, "dengue_cases")
    temp = read_wide_monthly(temp_path, "temp_media")
    prec = read_wide_monthly(prec_path, "precipitacao")
    enso = read_enso_series(enso_path)

    panel = dengue.merge(temp, on=["code", "year", "month"], how="inner")
    panel = panel.merge(prec, on=["code", "year", "month"], how="inner")
    panel = panel.merge(enso, on=["year", "month"], how="left")

    # Lookup de latitude e nome municipal
    csv_paths = [p for p in discover_files(output_lat_dir) if p.suffix.lower() == ".csv"] if output_lat_dir.exists() else []
    lookup = build_code_lookup_from_latitude_files(csv_paths)

    panel = panel.merge(lookup, on="code", how="left")
    panel["city_name"] = panel["city_name"].fillna(panel["code"].apply(lambda c: f"municipio_{c}"))

    # Filtro regiao sul por prefixo de UF no codigo (41, 42, 43)
    panel = panel[panel["code"].str[:2].isin(["41", "42", "43"])].copy()

    panel = panel.sort_values(["code", "year", "month"]).reset_index(drop=True)
    return panel, lookup


def north_weight(latitude: float) -> float:
    # Norte (aprox -23) recebe peso maior; Sul (aprox -32) peso menor
    lat_abs = abs(float(latitude))
    n = (32.0 - lat_abs) / 10.0
    n = float(np.clip(n, 0.0, 1.0))
    return 0.7 + 0.8 * n


def train_local_intercept(city_df: pd.DataFrame) -> float:
    d = city_df.copy().sort_values(["year", "month"]).reset_index(drop=True)

    # Lags de 3 meses para variaveis climaticas e ENSO
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

    # Estimativa robusta do intercepto via mediana
    return float(np.nanmedian(residual))


def build_monthly_climatology(city_df: pd.DataFrame) -> pd.DataFrame:
    d = city_df[(city_df["year"] >= TRAIN_START) & (city_df["year"] <= TRAIN_END)].copy()
    g = d.groupby("month", as_index=False).agg(
        base_temp=("temp_media", "mean"),
        base_prec=("precipitacao", "mean"),
        base_enso=("enso", "mean"),
    )
    return g


def predict_annual_cases_2025_no_increment(climatology: pd.DataFrame, intercept: float, latitude: float) -> float:
    # Construcao de serie mensal 2025 com baseline climatologico sem incremento
    d = climatology.copy().sort_values("month").reset_index(drop=True)
    d["year"] = CALIBRATION_YEAR
    d["temp"] = d["base_temp"]
    d["prec"] = d["base_prec"]
    d["enso"] = d["base_enso"]

    # Para manter lag3, concatena 3 meses finais de 2024 aproximados por climatologia mensal 10-12
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
    return float(np.nansum(monthly_cases))


def calibrate_region(panel: pd.DataFrame, local_intercepts: Dict[str, float]) -> CalibrationBundle:
    city_meta = panel[["code", "city_name", "latitude"]].drop_duplicates("code").copy()

    # Localiza Arapongas por nome; se nao achar, usa latitude mais proxima de -23.42
    city_meta["city_name_norm"] = city_meta["city_name"].astype(str).str.lower()
    arap = city_meta[city_meta["city_name_norm"].str.contains("arapongas", na=False)]

    if not arap.empty:
        arap_code = arap.iloc[0]["code"]
    else:
        city_meta["lat_dist"] = (city_meta["latitude"].astype(float) - ARAPONGAS_LAT).abs()
        arap_code = city_meta.sort_values("lat_dist").iloc[0]["code"] if not city_meta.empty else None

    # Threshold para "pico alto em 2024"
    annual_2024 = panel[panel["year"] == 2024].groupby("code", as_index=False)["dengue_cases"].sum()
    if annual_2024.empty:
        threshold = 500.0
    else:
        threshold = float(max(500.0, np.nanquantile(annual_2024["dengue_cases"], 0.75)))

    if arap_code is None:
        return CalibrationBundle(0.0, 0.0, threshold, None, np.nan)

    arap_df = panel[panel["code"] == arap_code].copy()
    if arap_df.empty:
        return CalibrationBundle(0.0, 0.0, threshold, arap_code, np.nan)

    lat = float(arap_df["latitude"].dropna().iloc[0]) if arap_df["latitude"].notna().any() else ARAPONGAS_LAT
    intercept = local_intercepts.get(arap_code, 0.0)
    clim = build_monthly_climatology(arap_df)
    pred_2025_raw = predict_annual_cases_2025_no_increment(clim, intercept, lat)

    # Ajuste de intercepto regional via bias (escala log)
    intercept_shift = float(np.log1p(ARAPONGAS_REAL_2025) - np.log1p(max(pred_2025_raw, EPS)))

    # Calibra termo de imunidade para igualar 2025 em Arapongas
    annual_2024_arap = float(arap_df[arap_df["year"] == 2024]["dengue_cases"].sum())
    peak_idx = max(0.0, (annual_2024_arap - threshold) / max(threshold, EPS))
    lat_w = north_weight(lat)

    if pred_2025_raw > ARAPONGAS_REAL_2025 and peak_idx > 0:
        immunity_gamma = float(np.log((pred_2025_raw + EPS) / (ARAPONGAS_REAL_2025 + EPS)) / max(peak_idx * lat_w, EPS))
    else:
        immunity_gamma = 0.0

    return CalibrationBundle(intercept_shift, immunity_gamma, threshold, arap_code, pred_2025_raw)


def project_city(
    city_df: pd.DataFrame,
    intercept_local: float,
    calib: CalibrationBundle,
) -> pd.DataFrame:
    city_df = city_df.sort_values(["year", "month"]).reset_index(drop=True)

    code = city_df["code"].iloc[0]
    city_name = city_df["city_name"].iloc[0]
    lat = float(city_df["latitude"].dropna().iloc[0]) if city_df["latitude"].notna().any() else ARAPONGAS_LAT

    clim = build_monthly_climatology(city_df)
    if clim.empty:
        return pd.DataFrame()

    # Base para regra de pico alto em 2024
    annual_2024 = float(city_df[city_df["year"] == 2024]["dengue_cases"].sum())
    high_peak_2024 = annual_2024 >= calib.threshold_peak_2024
    peak_idx = max(0.0, (annual_2024 - calib.threshold_peak_2024) / max(calib.threshold_peak_2024, EPS))
    lat_w = north_weight(lat)

    records = []
    for scenario_name, cfg in SCENARIOS.items():
        # Serie mensal 2025-2040 com metodo delta sobre climatologia mensal
        seq = []
        for year in range(CALIBRATION_YEAR, PROJECTION_END + 1):
            years_from_2025 = year - CALIBRATION_YEAR
            t_delta = cfg["temp_delta_per_year"] * years_from_2025
            p_delta = cfg["precip_delta_pct_per_year"] * years_from_2025
            e_delta = cfg["enso_delta_per_year"] * years_from_2025

            for _, row in clim.iterrows():
                m = int(row["month"])
                base_temp = float(row["base_temp"])
                base_prec = float(row["base_prec"])
                base_enso = float(row["base_enso"])

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

        # Necessario para lag3 em 2025: injeta meses 10-12 de 2024 com climatologia sem delta
        pre_tail = clim[clim["month"].isin([10, 11, 12])].copy()
        pre_tail = pre_tail.rename(columns={"base_temp": "temp", "base_prec": "prec", "base_enso": "enso"})
        pre_tail["year"] = 2024
        pre_tail["code"] = code
        pre_tail["city_name"] = city_name
        pre_tail["latitude"] = lat
        pre_tail["scenario"] = scenario_name
        pre_tail = pre_tail[["code", "city_name", "latitude", "scenario", "year", "month", "temp", "prec", "enso"]]

        full = pd.concat([pre_tail, dfp], ignore_index=True).sort_values(["year", "month"]).reset_index(drop=True)
        full["temp_lag3"] = full["temp"].shift(3)
        full["prec_lag3"] = full["prec"].shift(3)
        full["enso_lag3"] = full["enso"].shift(3)

        fut = full[(full["year"] >= PROJECTION_START) & (full["year"] <= PROJECTION_END)].copy()

        lp = (
            intercept_local
            + calib.intercept_shift
            + BETA_TMED * fut["temp_lag3"]
            + BETA_PREC * fut["prec_lag3"]
            + BETA_ENSO * fut["enso_lag3"]
            + BETA_LAT * lat
        )

        pred_cases = np.expm1(lp).clip(lower=0.0)

        # Ajuste de imunidade pos-surto apenas em 2026 para cidades de pico alto em 2024
        if high_peak_2024 and calib.immunity_gamma > 0:
            mask_2026 = fut["year"] == 2026
            if mask_2026.any():
                damp = np.exp(-calib.immunity_gamma * peak_idx * lat_w)
                pred_cases.loc[mask_2026] = pred_cases.loc[mask_2026] * damp

        fut["pred_cases"] = pred_cases
        fut["pred_log_y1"] = np.log1p(fut["pred_cases"])
        fut["high_peak_2024"] = int(high_peak_2024)
        fut["peak_2024"] = annual_2024
        fut["peak_threshold_2024"] = calib.threshold_peak_2024

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


def save_outputs(root_dir: Path, projections: pd.DataFrame, calibration: CalibrationBundle) -> None:
    out_dir = root_dir / "output" / "projecoes_regionais"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Remove CSVs legados por cidade para manter apenas o solicitado.
    removed_city_csv = 0
    for p in out_dir.glob("projecao_*.csv"):
        if re.search(r"_\d{6}\.csv$", p.name):
            p.unlink(missing_ok=True)
            removed_city_csv += 1

    # CSV POR FAIXA DE LATITUDE (binning automático em 8 faixas)
    lat_bins = np.linspace(projections["latitude"].min(), projections["latitude"].max(), 9)  # 8 faixas
    projections["lat_faixa"] = pd.cut(projections["latitude"], bins=lat_bins, include_lowest=True)
    
    lat_group_summary = []
    for lat_faixa, g_lat in projections.groupby("lat_faixa", observed=False):
        if g_lat.empty:
            continue
        
        lat_min = float(lat_faixa.left)
        lat_max = float(lat_faixa.right)
        lat_label = f"latitude_{lat_min:.1f}_a_{lat_max:.1f}"
        
        annual = g_lat.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
        annual["lat_min"] = lat_min
        annual["lat_max"] = lat_max
        annual["n_municipios"] = g_lat["code"].nunique()
        
        path = out_dir / f"projecao_faixa_latitude_{lat_label}.csv"
        annual.sort_values(["scenario", "year"]).to_csv(path, index=False, encoding="utf-8")
        
        lat_group_summary.append(annual)

    # CSV CONSOLIDADO REGIÃO SUL
    regional = projections.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
    regional["regiao"] = "SUL"
    regional["n_municipios"] = projections["code"].nunique()
    regional["n_faixas_latitude"] = projections["lat_faixa"].nunique()
    regional_path = out_dir / "projecao_regiao_sul_consolidado.csv"
    regional.sort_values(["scenario", "year"]).to_csv(regional_path, index=False, encoding="utf-8")

    # Calibração JSON
    calib_json = {
        "intercept_shift": calibration.intercept_shift,
        "immunity_gamma": calibration.immunity_gamma,
        "threshold_peak_2024": calibration.threshold_peak_2024,
        "arapongas_code": calibration.arapongas_code,
        "arapongas_pred_2025_raw": calibration.arapongas_pred_2025_raw,
        "arapongas_real_2025": ARAPONGAS_REAL_2025,
    }
    with open(out_dir / "calibracao_regional.json", "w", encoding="utf-8") as f:
        json.dump(calib_json, f, ensure_ascii=False, indent=2)

    if removed_city_csv > 0:
        print(f"CSVs legados por cidade removidos: {removed_city_csv}")


def pick_report_cities(panel: pd.DataFrame) -> List[str]:
    city_meta = panel[["code", "city_name"]].drop_duplicates("code").copy()
    city_meta["norm"] = city_meta["city_name"].astype(str).str.lower()

    wanted = ["joinville", "porto alegre", "arapongas"]
    selected: List[str] = []

    for w in wanted:
        hit = city_meta[city_meta["norm"].str.contains(w, na=False)]
        if not hit.empty:
            selected.append(str(hit.iloc[0]["code"]))

    if len(selected) >= 3:
        return selected[:3]

    annual_2024 = panel[panel["year"] == 2024].groupby("code", as_index=False)["dengue_cases"].sum()
    top_codes = annual_2024.sort_values("dengue_cases", ascending=False)["code"].astype(str).tolist()

    for c in top_codes:
        if c not in selected:
            selected.append(c)
        if len(selected) >= 3:
            break

    return selected


def save_pdf_report(root_dir: Path, panel: pd.DataFrame, projections: pd.DataFrame) -> Path:
    out_dir = root_dir / "output" / "projecoes_regionais"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "relatorio_graficos_projecao.pdf"

    city_codes = pick_report_cities(panel)

    hist = panel[(panel["year"] >= 2015) & (panel["year"] <= 2024)].copy()
    hist_annual = hist.groupby(["code", "city_name", "year"], as_index=False)["dengue_cases"].sum()
    hist_annual = hist_annual[hist_annual["code"].isin(city_codes)].copy()

    proj_annual = projections.groupby(["code", "city_name", "scenario", "year"], as_index=False)["pred_cases"].sum()
    proj_annual = proj_annual[proj_annual["code"].isin(city_codes)].copy()

    city_name_map = (
        panel[["code", "city_name"]]
        .drop_duplicates("code")
        .set_index("code")["city_name"]
        .to_dict()
    )

    with PdfPages(pdf_path) as pdf:
        # Pagina 1: historico anual em barras
        fig, ax = plt.subplots(figsize=(14, 8))
        years = list(range(2015, 2025))
        x = np.arange(len(years))
        bar_w = 0.24
        colors = ["#1b9e9a", "#e78f2f", "#8e56a9"]

        for idx, code in enumerate(city_codes):
            city_name = city_name_map.get(code, f"municipio_{code}")
            s = hist_annual[hist_annual["code"] == code].set_index("year")["dengue_cases"]
            y = [float(s.get(y0, 0.0)) for y0 in years]
            ax.bar(x + (idx - 1) * bar_w, y, width=bar_w, label=city_name.upper(), color=colors[idx % len(colors)], alpha=0.9)

        ax.set_title("CASOS HISTÓRICOS DE DENGUE (2015-2024): VARIAÇÃO REGIONAL", fontsize=18, fontweight="bold")
        ax.set_xlabel("ANO", fontsize=14)
        ax.set_ylabel("CASOS DE DENGUE", fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.legend(loc="upper left", frameon=True)
        plt.tight_layout()
        pdf.savefig(fig, dpi=300)
        plt.close(fig)

        # Pagina 2: projecoes anuais por cenario (escala log)
        focus_code = city_codes[0] if city_codes else None
        fig, ax = plt.subplots(figsize=(14, 8))

        if focus_code is not None and not proj_annual.empty:
            focus_name = city_name_map.get(focus_code, f"municipio_{focus_code}")
            d = proj_annual[proj_annual["code"] == focus_code].copy()

            scen_order = ["ssp126", "ssp245", "ssp370", "ssp585"]
            scen_labels = {
                "ssp126": "CENÁRIO SSP1-2.6",
                "ssp245": "CENÁRIO SSP2-4.5",
                "ssp370": "CENÁRIO SSP3-7.0",
                "ssp585": "CENÁRIO SSP5-8.5",
            }
            scen_colors = {
                "ssp126": "#3f8f8f",
                "ssp245": "#3b5f8a",
                "ssp370": "#cc7f2a",
                "ssp585": "#b24a3a",
            }

            pivot = d.pivot_table(index="year", columns="scenario", values="pred_cases", aggfunc="sum")
            y_min = pivot.min(axis=1)
            y_max = pivot.max(axis=1)
            ax.fill_between(y_min.index, y_min.values, y_max.values, color="#8bbdc0", alpha=0.25, label="FAIXA ENTRE CENÁRIOS")

            for sc in scen_order:
                ds = d[d["scenario"] == sc].sort_values("year")
                if ds.empty:
                    continue
                ax.plot(ds["year"], ds["pred_cases"], linewidth=2.2, color=scen_colors.get(sc, None), label=scen_labels.get(sc, sc.upper()))

            if "arapongas" in str(focus_name).lower():
                ax.scatter([2025], [ARAPONGAS_REAL_2025], color="#7a3e9d", marker="D", s=70, zorder=5, label="VALIDAÇÃO ARAPONGAS 2025: 1455 CASOS")

            ax.set_title(
                f"PROJEÇÃO DE DENGUE (2026-2040): CENÁRIOS CLIMÁTICOS | {str(focus_name).upper()}",
                fontsize=16,
                fontweight="bold",
            )
            ax.set_xlabel("ANO", fontsize=14)
            ax.set_ylabel("CASOS PROJETADOS (ESCALA LOG)", fontsize=14)
            ax.set_yscale("log")
            ax.grid(True, linestyle="--", alpha=0.35)
            ax.legend(loc="upper left", frameon=True)
        else:
            ax.text(0.5, 0.5, "Sem dados suficientes para montar gráfico de projeção.", ha="center", va="center", fontsize=14)
            ax.axis("off")

        plt.tight_layout()
        pdf.savefig(fig, dpi=300)
        plt.close(fig)

    return pdf_path



def main() -> None:
    # Redireciona para o motor V2 para manter um unico padrao de saida solicitado.
    from motor_lote_modelagem_v2_por_latitude import main as main_v2

    print("Script legado detectado. Redirecionando para o motor V2 por latitude...")
    main_v2()
    return

    root_dir = ROOT_DATA_DIR
    if not root_dir.exists():
        raise FileNotFoundError(f"Diretorio raiz nao encontrado: {root_dir}")

    print("=" * 90)
    print("MOTOR LOTE - MODELAGEM CLIMA SAUDE (DENGUE) | REGIAO SUL")
    print("=" * 90)
    print(f"Raiz: {root_dir}")

    # 1) Descoberta de arquivos
    all_csv = discover_files(root_dir)
    print(f"CSVs encontrados via os.walk: {len(all_csv)}")

    # 2) Painel base
    panel, _ = build_base_panel(root_dir)
    if panel.empty:
        raise RuntimeError("Painel base vazio apos leitura e merges.")

    print(f"Registros no painel base: {len(panel):,}")
    print(f"Municipios unicos no painel: {panel['code'].nunique():,}")

    # 3) Treinamento local (intercepto robusto)
    local_intercepts: Dict[str, float] = {}
    for code, g in panel.groupby("code"):
        local_intercepts[code] = train_local_intercept(g)

    print(f"Modelos locais treinados: {len(local_intercepts):,}")

    # 4) Calibracao regional por Arapongas
    calib = calibrate_region(panel, local_intercepts)
    print("Calibracao regional:")
    print(f"  - arapongas_code: {calib.arapongas_code}")
    print(f"  - pred_2025_raw: {calib.arapongas_pred_2025_raw:.2f}")
    print(f"  - intercept_shift: {calib.intercept_shift:.5f}")
    print(f"  - immunity_gamma: {calib.immunity_gamma:.5f}")
    print(f"  - threshold_peak_2024: {calib.threshold_peak_2024:.2f}")

    # 5) Projecao por cidade
    all_proj = []
    for code, g in panel.groupby("code"):
        proj = project_city(g, local_intercepts.get(code, 0.0), calib)
        if not proj.empty:
            all_proj.append(proj)

    if not all_proj:
        raise RuntimeError("Nenhuma projecao foi gerada.")

    projections = pd.concat(all_proj, ignore_index=True)

    # 6) Persistencia
    save_outputs(root_dir, projections, calib)
    pdf_report = save_pdf_report(root_dir, panel, projections)

    print("=" * 90)
    print("Concluido com sucesso.")
    print(f"Saida: {root_dir / 'output' / 'projecoes_regionais'}")
    print(f"PDF de graficos: {pdf_report}")
    print("=" * 90)


if __name__ == "__main__":
    main()
