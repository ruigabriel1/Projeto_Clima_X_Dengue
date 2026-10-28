"""
Exportação dos resultados do pipeline v4 para o dashboard (multi-doença).

Fontes (todas geradas por `python main.py train`):
  - data/processed/dengue_analytics.db           → histórico real e clima
  - output/ml_run_log_<doenca>_v4.json           → métricas A/B, baselines, SHAP
  - output/backtest/oof_modeloA_<doenca>.csv     → previsões fora-da-amostra (real × previsto)
  - output/projecoes_v4/projecoes_<doenca>_ssp_mensal.csv → cenários SSP por cidade

Saída: output/dashboard/resultados_<doenca>.json (um por doença) + índice.
Não depende mais do motor legado por latitude.
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT_DIR / "data" / "processed" / "dengue_analytics.db"
OUT_DIR = ROOT_DIR / "output"
DASH_DIR = OUT_DIR / "dashboard"

DOENCA_COL_DB = {"dengue": "CASOS_DENGUE", "chikungunya": "CASOS_CHIKUNGUNYA", "zika": "CASOS_ZIKA"}
MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


# ---------------------------------------------------------------- status / cidades
def get_db_status() -> dict:
    """Estatísticas do banco para o painel de status."""
    conn = sqlite3.connect(DB_PATH)
    try:
        s = pd.read_sql_query(
            "SELECT COUNT(*) n, COUNT(DISTINCT CODIGO_MUNICIPIO) cidades, MIN(ANO) ano_min, MAX(ANO) ano_max "
            "FROM ingestao_saude", conn).iloc[0]
        c = pd.read_sql_query(
            "SELECT COUNT(*) n, COUNT(DISTINCT CODIGO_MUNICIPIO) cidades FROM ingestao_clima", conn).iloc[0]
    finally:
        conn.close()
    return {
        "saude_registros": int(s["n"]), "saude_cidades": int(s["cidades"]),
        "clima_registros": int(c["n"]), "clima_cidades": int(c["cidades"]),
        "periodo": f"{int(s['ano_min'])}–{int(s['ano_max'])}",
        "db_size_mb": round(DB_PATH.stat().st_size / 2**20, 1),
        "doencas_disponiveis": doencas_exportadas(),
    }


def get_cidades() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT DISTINCT CODIGO_MUNICIPIO code, NOME_MUNICIPIO nome FROM ingestao_saude ORDER BY nome", conn)
    finally:
        conn.close()
    return df.to_dict(orient="records")


def doencas_exportadas() -> list[str]:
    return sorted(p.stem.replace("resultados_", "") for p in DASH_DIR.glob("resultados_*.json"))


# ---------------------------------------------------------------- helpers
def _code6(s: pd.Series) -> pd.Series:
    return s.astype(str).str.extract(r"(\d{6})", expand=False)


def _mean(values) -> Optional[float]:
    v = [x for x in values if x is not None and not (isinstance(x, float) and np.isnan(x))]
    return round(float(np.mean(v)), 4) if v else None


def _clean(o):
    """Converte numpy/NaN para tipos JSON."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else round(float(o), 4)
    return o


def _historico(doenca: str, codes: Optional[list[str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    col = DOENCA_COL_DB[doenca]
    conn = sqlite3.connect(DB_PATH)
    try:
        saude = pd.read_sql_query(f"SELECT CODIGO_MUNICIPIO code, ANO year, MES month, {col} casos FROM ingestao_saude", conn)
        clima = pd.read_sql_query("SELECT CODIGO_MUNICIPIO code, ANO year, MES month, temp_media, precipitacao FROM ingestao_clima", conn)
        try:
            pop = pd.read_sql_query("SELECT CODIGO_MUNICIPIO code, ANO year, POPULACAO pop FROM ingestao_populacao", conn)
        except Exception:
            pop = pd.DataFrame(columns=["code", "year", "pop"])
    finally:
        conn.close()
    for d in (saude, clima, pop):
        d["code"] = _code6(d["code"])
    if codes:
        saude, clima, pop = (d[d["code"].isin(codes)] for d in (saude, clima, pop))
    mensal = saude.groupby(["year", "month"])["casos"].sum(min_count=1).reset_index()
    cl = clima.groupby(["year", "month"]).agg(temp_media=("temp_media", "mean"), precipitacao=("precipitacao", "mean")).reset_index()
    mensal = mensal.merge(cl, on=["year", "month"], how="left").sort_values(["year", "month"])
    pop_ano = pop.groupby("year")["pop"].sum().reset_index()
    return mensal, pop_ano


# ---------------------------------------------------------------- export
def exportar_doenca(doenca: str, codigo_ibge: Optional[str] = None) -> dict:
    log_path = OUT_DIR / f"ml_run_log_{doenca}_v4.json"
    if not log_path.exists():
        raise FileNotFoundError(f"{log_path.name} não existe. Rode: python main.py train --doenca {doenca}")
    log = json.loads(log_path.read_text(encoding="utf-8"))
    codes = [str(codigo_ibge)[:6]] if codigo_ibge else None
    avisos = []

    # --- Métricas A (média dos folds) e baselines
    mA = log.get("metrics_por_ano", [])
    bl = log.get("baselines_por_ano", [])
    mB = log.get("modelo_b", {}).get("metrics_por_ano", [])
    metricas = {
        "r2": _mean(m["r2"] for m in mA), "mae": _mean(m["mae"] for m in mA), "rmse": _mean(m["rmse"] for m in mA),
        "anos_teste": [m["year"] for m in mA],
    }
    baselines = {k: _mean(b.get(k) for b in bl) for k in ("persist_mae", "sazonal_mae", "glm_nb_mae", "persist_r2", "sazonal_r2", "glm_nb_r2")}
    metricas_b = {"r2": _mean(m["r2"] for m in mB), "mae": _mean(m["mae"] for m in mB)}
    melhor_baseline = min((v for k, v in baselines.items() if k.endswith("_mae") and v is not None), default=None)
    if melhor_baseline is not None and metricas["mae"] is not None and metricas["mae"] >= melhor_baseline:
        avisos.append(f"O Modelo A NÃO supera o melhor baseline (MAE {metricas['mae']:.1f} vs {melhor_baseline:.1f}).")

    # --- Importância: SHAP se houver, senão ganho
    shap = log.get("interpretability", {}).get("top_shap_features", [])
    fi = ([{"feature": s["feature"], "importance": s["mean_abs_shap"]} for s in shap] if shap
          else [{"feature": f, "importance": float(v)} for f, v in log.get("feature_importance", [])])

    # --- Histórico real
    hist, pop_ano = _historico(doenca, codes)
    hist = hist[hist["casos"].notna()]
    n_cidades = len(codes) if codes else log.get("n_cidades")

    # --- Backtest (fora-da-amostra)
    serie = {"labels": [], "real": [], "previsto": []}
    oof_path = OUT_DIR / "backtest" / f"oof_modeloA_{doenca}.csv"
    if oof_path.exists():
        oof = pd.read_csv(oof_path, dtype={"code": str})
        if codes:
            oof = oof[oof["code"].isin(codes)]
        bt = oof.groupby(["year", "month"])[["y_true", "y_pred"]].sum().reset_index()
        serie = {
            "labels": [f"{y}-{m:02d}" for y, m in zip(bt["year"], bt["month"])],
            "real": bt["y_true"].round(1).tolist(),
            "previsto": bt["y_pred"].round(1).tolist(),
        }

    # --- Tabela epidemiológica histórica
    tabela = []
    for ano, g in hist.groupby("year"):
        total = float(g["casos"].sum())
        pico = g.loc[g["casos"].idxmax()]
        pop = pop_ano.loc[pop_ano["year"] == ano, "pop"]
        inc = round(total / float(pop.iloc[0]) * 1e5, 1) if len(pop) and pop.iloc[0] > 0 else None
        prev = tabela[-1]["casos"] if tabela else None
        tabela.append({
            "ano": int(ano), "casos": int(total), "incidencia": inc,
            "pico": int(pico["casos"]), "mes_pico": MESES_PT[int(pico["month"]) - 1],
            "variacao": round((total - prev) / prev * 100, 1) if prev else None,
        })

    # --- Correlação de Spearman com lags (série agregada do escopo)
    correl = []
    try:
        from scipy.stats import spearmanr
        testes = []
        for var, nome in (("temp_media", "Temperatura média (°C)"), ("precipitacao", "Precipitação (mm)")):
            for lag in range(0, 4):
                v = hist[["casos"]].assign(x=hist[var].shift(lag)).dropna()
                if len(v) > 10:
                    r, p = spearmanr(v["x"], v["casos"])
                    testes.append((nome, lag, r, p))
        for nome, lag, r, p in testes:
            p_adj = min(p * len(testes), 1.0)  # Bonferroni
            correl.append({"preditor": nome, "lag": lag, "rho": round(float(r), 3), "p_ajustado": float(p_adj)})
    except Exception as e:
        logger.warning(f"Correlação falhou: {e}")

    # --- Sazonalidade histórica
    saz = hist.groupby("month").agg(casos=("casos", "mean"), temp=("temp_media", "mean")).reindex(range(1, 13))
    dist_sazonal = {
        "meses": list(range(1, 13)),
        "casos_mean": saz["casos"].round(1).tolist(),
        "temp_mean": saz["temp"].round(1).tolist(),
        "heatmap": [],
    }

    # --- Projeções SSP
    projecao = {}
    proj_path = OUT_DIR / "projecoes_v4" / f"projecoes_{doenca}_ssp_mensal.csv"
    intervalo = log.get("modelo_b", {}).get("intervalo_empirico", {})
    if proj_path.exists():
        pj = pd.read_csv(proj_path, dtype={"code": str})
        if codes:
            pj = pj[pj["code"].isin(codes)]
        anual = pj.groupby(["scenario", "period"], sort=False)["predicted_cases"].sum()
        base = float(anual.get(("baseline", "historico"), np.nan))
        for sc in ("ssp126", "ssp245", "ssp585"):
            if sc not in anual.index.get_level_values(0):
                continue
            s = anual.loc[sc]
            projecao[sc] = {
                "anos": ["Baseline"] + list(s.index),
                "casos": [round(base)] + [round(float(x)) for x in s.values],
                "delta_pct": [0.0] + [round((float(x) / base - 1) * 100, 2) if base else None for x in s.values],
            }
            if intervalo.get("ratio_min") is not None:
                projecao[sc]["low"] = [round(c * intervalo["ratio_min"]) for c in projecao[sc]["casos"]]
                projecao[sc]["high"] = [round(c * intervalo["ratio_max"]) for c in projecao[sc]["casos"]]
        hm = pj[pj["scenario"].isin(["baseline", "ssp245"])].groupby(["period", "month"], sort=False)["predicted_cases"].sum().reset_index()
        dist_sazonal["heatmap"] = [
            {"ano": "Baseline" if r.period == "historico" else r.period, "mes": int(r.month), "casos": round(float(r.predicted_cases), 1)}
            for r in hm.itertuples()
        ]
    else:
        avisos.append("Projeções SSP ausentes (Modelo B não rodou).")

    if metricas_b["r2"] is not None and metricas_b["r2"] < 0.3:
        avisos.append(f"Modelo B (só clima) tem R² baixo ({metricas_b['r2']:.2f}): leia as projeções como sensibilidade relativa ao clima, não como previsão de casos.")

    anos_hist = sorted(hist["year"].unique())
    return _clean({
        "doenca": doenca,
        "escopo": codigo_ibge or "regional",
        "n_cidades": n_cidades,
        "periodo": f"{anos_hist[0]}–{anos_hist[-1]}" if anos_hist else "-",
        "projecao_ate": 2040,
        "metricas": metricas,
        "metricas_modelo_b": metricas_b,
        "baselines": baselines,
        "feature_importance": fi,
        "serie_temporal_mensal": serie,
        "tabela_epidemiologica": tabela,
        "tabela_correlacao": correl,
        "dist_sazonal": dist_sazonal,
        "projecao_cenarios": projecao,
        "intervalo_empirico": intervalo,
        "avisos": avisos,
    })


def exportar_dados_dashboard(doenca: str = "todas", codigo_ibge: Optional[str] = None) -> dict:
    DASH_DIR.mkdir(parents=True, exist_ok=True)
    alvo = list(DOENCA_COL_DB) if doenca == "todas" else [doenca]
    out = {}
    for d in alvo:
        try:
            res = exportar_doenca(d, codigo_ibge)
        except FileNotFoundError as e:
            logger.warning(str(e))
            continue
        (DASH_DIR / f"resultados_{d}.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        out[d] = res
        print(f"  ✅ {d}: output/dashboard/resultados_{d}.json  avisos={len(res['avisos'])}")
    return out


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Exporta resultados v4 para o dashboard")
    p.add_argument("--doenca", default="todas", choices=["dengue", "chikungunya", "zika", "todas"])
    p.add_argument("--codigo_ibge", default=None)
    a = p.parse_args()
    exportar_dados_dashboard(a.doenca, a.codigo_ibge)
