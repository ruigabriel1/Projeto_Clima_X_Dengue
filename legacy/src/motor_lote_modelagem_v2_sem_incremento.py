#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor complementar: projecoes SEM incremento SSP (delta zero)

Gera saidas separadas para comparacao textual com o motor principal:
- previsao de 2025 sem incremento (ML)
- projecao 2025-2040 sem incremento
- resumo comparativo em txt
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_pdf import PdfPages

import src.processamento.motor_lote_modelagem_v2_por_latitude as base

logger = logging.getLogger(__name__)


def save_sem_increment_outputs(root_dir: Path, projections: pd.DataFrame) -> Path:
    out_dir = root_dir / "output" / "projecoes_sem_incremento"
    out_dir.mkdir(parents=True, exist_ok=True)

    annual = projections.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
    annual["regiao"] = "SUL"
    annual.to_csv(out_dir / "projecao_regiao_sul_sem_incremento_2025_2040.csv", index=False, encoding="utf-8")

    lat_bins = np.linspace(projections["latitude"].min(), projections["latitude"].max(), 9)
    projections = projections.copy()
    projections["lat_faixa"] = pd.cut(projections["latitude"], bins=lat_bins, include_lowest=True)

    for lat_faixa, g_lat in projections.groupby("lat_faixa", observed=False):
        if g_lat.empty:
            continue
        lat_min = float(lat_faixa.left)
        lat_max = float(lat_faixa.right)
        lat_label = f"{lat_min:.1f}a{lat_max:.1f}"
        annual_lat = g_lat.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
        annual_lat["latitude_min"] = lat_min
        annual_lat["latitude_max"] = lat_max
        annual_lat.to_csv(out_dir / f"projecao_latitude_sem_incremento_{lat_label}.csv", index=False, encoding="utf-8")

    return out_dir


def save_ml_2025_sem_increment(root_dir: Path, panel: pd.DataFrame, local_intercepts: Dict[str, float]) -> None:
    out_dir = root_dir / "output" / "projecoes_sem_incremento"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for code, g in panel.groupby("code"):
        g = g.sort_values(["year", "month"]).reset_index(drop=True)
        lat = float(g["latitude"].dropna().iloc[0]) if g["latitude"].notna().any() else base.ARAPONGAS_LAT
        city_name = str(g["city_name"].iloc[0])
        intercept = float(local_intercepts.get(code, 0.0))

        clim = base.build_monthly_climatology(g)
        if clim.empty:
            continue

        hist_cases = g[(g["year"] >= base.TRAIN_START) & (g["year"] <= base.TRAIN_END)]["dengue_cases"].dropna()
        hist_q95 = float(np.nanquantile(hist_cases, 0.95)) if not hist_cases.empty else 50.0
        hist_q95 = max(hist_q95, 10.0)

        pred_2025 = base.predict_annual_cases_2025_no_increment(clim, intercept, lat, hist_q95)
        rows.append(
            {
                "code": code,
                "city_name": city_name,
                "latitude": lat,
                "year": base.CALIBRATION_YEAR,
                "scenario": "sem_incremento",
                "pred_cases": pred_2025,
            }
        )

    if not rows:
        return

    df_2025 = pd.DataFrame(rows).sort_values(["scenario", "code"]).reset_index(drop=True)
    df_2025.to_csv(out_dir / "previsao_ml_2025_sem_incremento_municipios.csv", index=False, encoding="utf-8")

    reg_2025 = df_2025.groupby(["year", "scenario"], as_index=False)["pred_cases"].sum()
    reg_2025["regiao"] = "SUL"
    reg_2025.to_csv(out_dir / "previsao_ml_2025_sem_incremento_regional.csv", index=False, encoding="utf-8")


def save_comparison_text(root_dir: Path) -> None:
    out_dir = root_dir / "output" / "projecoes_sem_incremento"
    sem_path = out_dir / "projecao_regiao_sul_sem_incremento_2025_2040.csv"
    base_path = root_dir / "output" / "projecoes_regionais" / "projecao_regiao_sul_consolidado.csv"

    if not sem_path.exists():
        return

    sem_df = pd.read_csv(sem_path)
    sem_df = sem_df.groupby("year", as_index=False)["pred_cases"].sum().rename(columns={"pred_cases": "sem_incremento"})

    lines = []
    lines.append("COMPARACAO DE CENARIOS - SEM INCREMENTO VS COM INCREMENTO SSP")
    lines.append("Periodo avaliado: 2025-2040")
    lines.append("")

    if base_path.exists():
        base_df = pd.read_csv(base_path)
        inc_year = base_df.groupby("year", as_index=False).agg(
            inc_min=("pred_cases", "min"),
            inc_max=("pred_cases", "max"),
            inc_mean=("pred_cases", "mean"),
        )
        cmp_df = sem_df.merge(inc_year, on="year", how="left")

        for yr in [2025, 2030, 2035, 2040]:
            row = cmp_df[cmp_df["year"] == yr]
            if row.empty:
                continue
            r = row.iloc[0]
            sem_val = float(r["sem_incremento"])
            mean_val = float(r["inc_mean"]) if not pd.isna(r["inc_mean"]) else np.nan
            var_pct = ((sem_val - mean_val) / max(mean_val, 1e-9) * 100.0) if not np.isnan(mean_val) else np.nan
            lines.append(
                f"Ano {yr}: sem_incremento={sem_val:,.0f} | com_incremento_media={mean_val:,.0f} | diferenca={var_pct:+.2f}%".replace(",", ".")
            )

        lines.append("")
        lines.append("Leitura rapida:")
        lines.append("- sem_incremento representa manutencao da climatologia sem deltas SSP.")
        lines.append("- com_incremento considera aquecimento/precipitacao adicionais por cenario SSP.")
    else:
        for yr in [2025, 2030, 2035, 2040]:
            row = sem_df[sem_df["year"] == yr]
            if row.empty:
                continue
            sem_val = float(row.iloc[0]["sem_incremento"])
            lines.append(f"Ano {yr}: sem_incremento={sem_val:,.0f}".replace(",", "."))

    (out_dir / "comparacao_sem_incremento_vs_ssp.txt").write_text("\n".join(lines), encoding="utf-8")


def save_integrity_report(root_dir: Path, projections: pd.DataFrame) -> Path:
    out_dir = root_dir / "output" / "projecoes_sem_incremento"
    out_dir.mkdir(parents=True, exist_ok=True)

    regional = projections.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
    years_expected = set(range(base.PROJECTION_START, base.PROJECTION_END + 1))
    years_found = set(regional["year"].astype(int).unique().tolist())
    missing_years = sorted(years_expected - years_found)

    issues = []
    if projections.empty:
        issues.append("Projecoes vazias.")
    if (projections["pred_cases"] < 0).any():
        issues.append("Foram encontrados valores negativos em pred_cases.")
    if projections["pred_cases"].isna().any():
        issues.append("Foram encontrados NaN em pred_cases.")
    if missing_years:
        issues.append(f"Anos ausentes no horizonte projetado: {missing_years}")
    if set(projections["scenario"].astype(str).unique().tolist()) != {"sem_incremento"}:
        issues.append("Existe cenario diferente de sem_incremento nas projecoes geradas.")

    lines = []
    lines.append("RELATORIO DE INTEGRIDADE - PROJECOES SEM INCREMENTO")
    lines.append(f"Registros de projecao: {len(projections):,}".replace(",", "."))
    lines.append(f"Municipios projetados: {projections['code'].nunique():,}".replace(",", "."))
    lines.append(f"Anos esperados: {base.PROJECTION_START}-{base.PROJECTION_END}")
    lines.append(f"Anos encontrados: {min(years_found) if years_found else 'N/A'}-{max(years_found) if years_found else 'N/A'}")
    lines.append("")
    if issues:
        lines.append("STATUS: ATENCAO")
        lines.extend([f"- {msg}" for msg in issues])
    else:
        lines.append("STATUS: OK")
        lines.append("- Integridade basica aprovada (anos, cenario, nao negatividade e ausencia de NaN).")

    path = out_dir / "integridade_projecoes_sem_incremento.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def save_sem_increment_pdf_reports(root_dir: Path, panel: pd.DataFrame, projections: pd.DataFrame) -> Path:
    out_dir = root_dir / "output" / "projecoes_sem_incremento"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "relatorio_graficos_sem_incremento.pdf"

    hist = panel[(panel["year"] >= 2015) & (panel["year"] <= 2024)].copy()
    lat_bins = np.linspace(projections["latitude"].min(), projections["latitude"].max(), 9)
    projections = projections.copy()
    projections["lat_faixa"] = pd.cut(projections["latitude"], bins=lat_bins, include_lowest=True)
    hist["lat_faixa"] = pd.cut(hist["latitude"], bins=lat_bins, include_lowest=True)

    model_codes = set(panel["code"].astype(str).unique().tolist())
    hist_lat_csv, hist_regional_csv = base.load_historical_incidents_from_csvs_latitude(root_dir, lat_bins, model_codes=model_codes)

    color_sem = "#cc7f2a"

    with PdfPages(pdf_path) as pdf:
        # Consolidado historico
        fig, ax1 = plt.subplots(figsize=(12, 6.5))
        if not hist_regional_csv.empty:
            hist_regional = hist_regional_csv.copy()
        else:
            hist_regional = hist.groupby("year", as_index=False)["dengue_cases"].sum().rename(columns={"dengue_cases": "incidentes"})
        hist_regional = pd.DataFrame({"year": np.arange(2015, 2025, 1)}).merge(hist_regional, on="year", how="left")
        hist_regional["incidentes"] = hist_regional["incidentes"].fillna(0.0)

        ax1.fill_between(hist_regional["year"], 0.0, hist_regional["incidentes"], color="#2d9590", alpha=0.25)
        ax1.plot(hist_regional["year"], hist_regional["incidentes"], color="#1f706c", linewidth=2.4, marker="o", markersize=4)
        ax1.set_title("CONSOLIDADO HISTORICO - REGIAO SUL (2015-2024)", fontsize=12, fontweight="bold")
        ax1.set_xlabel("ANO")
        ax1.set_ylabel("INCIDENTES")
        ax1.set_xticks(np.arange(2015, 2025, 1))
        ax1.yaxis.set_major_formatter(FuncFormatter(base.incidentes_formatter))
        ax1.grid(True, linestyle="-", alpha=0.20)
        plt.tight_layout()
        pdf.savefig(fig, dpi=300)
        plt.close(fig)

        # Consolidado projetado
        fig, ax2 = plt.subplots(figsize=(12, 6.5))
        proj_regional = projections.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
        hist_2024_reg = float(hist_regional.loc[hist_regional["year"] == 2024, "incidentes"].sum())
        ax2.plot(hist_regional["year"], hist_regional["incidentes"], color="black", linewidth=2.2, marker="o", markersize=3, label="Dados observados (2015-2024)")

        ds = proj_regional.sort_values("year")
        if not ds.empty:
            hist_cv = float(np.std(hist_regional["incidentes"].to_numpy()) / max(np.mean(hist_regional["incidentes"].to_numpy()), base.EPS)) if len(hist_regional) > 1 else 0.20
            lo, hi = base.uncertainty_bounds(ds["year"].to_numpy(dtype=float), ds["pred_cases"].to_numpy(dtype=float), hist_cv, "ssp245")
            ax2.fill_between(ds["year"], lo, hi, color=color_sem, alpha=0.14, linewidth=0)
            ax2.plot(ds["year"], ds["pred_cases"], color=color_sem, linewidth=2.3, marker="o", markersize=4, label="Previsao sem incremento (2025-2040)")
            y2025 = float(ds.loc[ds["year"] == base.PROJECTION_START, "pred_cases"].iloc[0]) if (ds["year"] == base.PROJECTION_START).any() else float(ds["pred_cases"].iloc[0])
            ax2.plot([2024, base.PROJECTION_START], [hist_2024_reg, y2025], color="black", linewidth=1.6, linestyle="-", alpha=0.85)

        ax2.set_title(f"CONSOLIDADO PROJETADO - SEM INCREMENTO ({base.PROJECTION_START}-{base.PROJECTION_END})", fontsize=12, fontweight="bold")
        ax2.set_xlabel("ANO")
        ax2.set_ylabel("")
        ax2.set_xticks(np.arange(2015, base.PROJECTION_END + 1, 5))
        ax2.yaxis.set_major_formatter(FuncFormatter(base.incidentes_formatter))
        ax2.grid(True, linestyle="-", alpha=0.20)
        ax2.legend(loc="upper left", fontsize=8.5, frameon=True, title="Series")
        plt.tight_layout()
        pdf.savefig(fig, dpi=300)
        plt.close(fig)

        # Faixas de latitude (historico + projetado em paginas separadas)
        for lat_faixa in sorted(projections["lat_faixa"].dropna().unique())[:8]:
            lat_min = float(lat_faixa.left)
            lat_max = float(lat_faixa.right)
            lat_label = f"{abs(lat_min):.1f}S a {abs(lat_max):.1f}S"

            if not hist_lat_csv.empty:
                hist_lat = hist_lat_csv[hist_lat_csv["lat_faixa"] == lat_faixa].copy()
            else:
                hist_lat = hist[hist["lat_faixa"] == lat_faixa].groupby("year", as_index=False)["dengue_cases"].sum().rename(columns={"dengue_cases": "incidentes"})

            full_years = pd.DataFrame({"year": np.arange(2015, 2025, 1)})
            hist_lat = full_years.merge(hist_lat[["year", "incidentes"]], on="year", how="left")
            hist_lat["incidentes"] = hist_lat["incidentes"].fillna(0.0)

            fig, ax1 = plt.subplots(figsize=(12, 6.5))
            ax1.fill_between(hist_lat["year"], 0.0, hist_lat["incidentes"], color="#2c908b", alpha=0.22)
            ax1.plot(hist_lat["year"], hist_lat["incidentes"], color="#1d6e6a", linewidth=2.2, marker="o", markersize=4)
            ax1.set_title(f"HISTORICO - FAIXA {lat_label} (2015-2024)", fontsize=12, fontweight="bold")
            ax1.set_xlabel("ANO")
            ax1.set_ylabel("INCIDENTES")
            ax1.set_xticks(np.arange(2015, 2025, 1))
            ax1.yaxis.set_major_formatter(FuncFormatter(base.incidentes_formatter))
            ax1.grid(True, linestyle="-", alpha=0.20)
            plt.tight_layout()
            pdf.savefig(fig, dpi=300)
            plt.close(fig)

            fig, ax2 = plt.subplots(figsize=(12, 6.5))
            proj_lat = projections[projections["lat_faixa"] == lat_faixa].groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()
            hist_2024_lat = float(hist_lat.loc[hist_lat["year"] == 2024, "incidentes"].sum())

            ax2.plot(hist_lat["year"], hist_lat["incidentes"], color="black", linewidth=2.0, marker="o", markersize=3, label="Dados observados (2015-2024)")
            ds = proj_lat.sort_values("year")
            if not ds.empty:
                hist_cv = float(np.std(hist_lat["incidentes"].to_numpy()) / max(np.mean(hist_lat["incidentes"].to_numpy()), base.EPS)) if len(hist_lat) > 1 else 0.20
                lo, hi = base.uncertainty_bounds(ds["year"].to_numpy(dtype=float), ds["pred_cases"].to_numpy(dtype=float), hist_cv, "ssp245")
                ax2.fill_between(ds["year"], lo, hi, color=color_sem, alpha=0.14, linewidth=0)
                ax2.plot(ds["year"], ds["pred_cases"], color=color_sem, linewidth=2.3, marker="o", markersize=4, label="Previsao sem incremento (2025-2040)")
                y2025 = float(ds.loc[ds["year"] == base.PROJECTION_START, "pred_cases"].iloc[0]) if (ds["year"] == base.PROJECTION_START).any() else float(ds["pred_cases"].iloc[0])
                ax2.plot([2024, base.PROJECTION_START], [hist_2024_lat, y2025], color="black", linewidth=1.6, linestyle="-", alpha=0.85)

            ax2.set_title("")
            ax2.set_xlabel("ANO")
            ax2.set_ylabel("")
            ax2.set_xticks([2015, 2020, 2024, 2030, 2035, 2040])
            ax2.yaxis.set_major_formatter(FuncFormatter(base.incidentes_formatter))
            ax2.grid(True, linestyle="-", alpha=0.20)
            ax2.legend(loc="upper left", fontsize=8.5, frameon=True, title="Series")
            plt.tight_layout()
            pdf.savefig(fig, dpi=300)
            plt.close(fig)

    return pdf_path


def main() -> None:
    root_dir = base.ROOT_DATA_DIR
    if not root_dir.exists():
        raise FileNotFoundError(f"Diretorio raiz nao encontrado: {root_dir}")

    print("=" * 90)
    print("MOTOR COMPLEMENTAR - PROJECOES SEM INCREMENTO SSP")
    print("=" * 90)

    panel, _lookup = base.build_base_panel(root_dir)
    if panel.empty:
        raise RuntimeError("Painel base vazio apos leitura.")

    local_intercepts: Dict[str, float] = {}
    for code, g in panel.groupby("code"):
        local_intercepts[code] = base.train_local_intercept(g)

    calib = base.calibrate_region(panel, local_intercepts)

    # Cenario unico sem incremento para todo horizonte.
    scenario_backup = dict(base.SCENARIOS)
    base.SCENARIOS = {
        "sem_incremento": {
            "temp_delta_per_year": 0.0,
            "precip_delta_pct_per_year": 0.0,
            "enso_delta_per_year": 0.0,
        }
    }

    try:
        all_proj = []
        for code, g in panel.groupby("code"):
            p = base.project_city(g, local_intercepts.get(code, 0.0), calib)
            if not p.empty:
                all_proj.append(p)

        if not all_proj:
            raise RuntimeError("Nenhuma projecao sem incremento foi gerada.")

        projections = pd.concat(all_proj, ignore_index=True)
        out_dir = save_sem_increment_outputs(root_dir, projections)
        save_ml_2025_sem_increment(root_dir, panel, local_intercepts)
        save_comparison_text(root_dir)
        integrity_path = save_integrity_report(root_dir, projections)
        pdf_path = save_sem_increment_pdf_reports(root_dir, panel, projections)

        print(f"[OK] Saidas geradas em: {out_dir}")
        print("[OK] Arquivos principais:")
        print("  - projecao_regiao_sul_sem_incremento_2025_2040.csv")
        print("  - previsao_ml_2025_sem_incremento_municipios.csv")
        print("  - previsao_ml_2025_sem_incremento_regional.csv")
        print("  - comparacao_sem_incremento_vs_ssp.txt")
        print(f"  - {integrity_path.name}")
        print(f"  - {pdf_path.name}")
    finally:
        base.SCENARIOS = scenario_backup


if __name__ == "__main__":
    main()
