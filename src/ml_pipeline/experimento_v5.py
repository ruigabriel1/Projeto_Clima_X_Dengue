"""
Experimento v5 (docs/PROTOCOLO_V5.md) — responde H2 (clima) e H3 (suscetibilidade).

Fatores: doença {dengue, chikungunya} × h {1,2,3} × clima {nenhum, parcimonioso} × suscetibilidade {não, sim}.
Modelo: XGBoost Poisson, XGB_PARAMS fixos, offset log(pop) (aprende incidência), sem corte.
Validação: expanding window; folds 2018–2024 = desenvolvimento; fold 2025 reportado à parte como
"segunda validação já vista" (foi o holdout da v4). Dados de 2026 são removidos ANTES de tudo.

Risco: alto = incidência > P75 da incidência mensal da própria cidade nos anos de treino.
Escore = incidência prevista / P75 (ε evita divisão por zero). Probabilidade = isotônica ajustada
nos folds ANTERIORES (cross-fitting temporal; o 1º fold fica sem probabilidade).

Saídas em output/experimento_v5/: resultados.csv, efeitos.csv, decisao.json, relatorio.md,
oof_<doenca>_h<h>.csv.gz, meta.json
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, mean_absolute_error, roc_auc_score

from src.config import BASE_DIR, DOENCAS_EXPERIMENTO, HORIZONTES, OUTPUT_DIR
from src.ml_pipeline.analise_experimento import bootstrap_delta_mae
from src.ml_pipeline.experimento_horizontes import configurar_log, git_commit
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, PREFIXOS, build_ml_features, get_feature_columns
from src.ml_pipeline.model_training import XGB_PARAMS, _expanding_window_splits, fit_predict_fold, limiares_por_cidade

logger = logging.getLogger(__name__)

OUT_V5 = OUTPUT_DIR / "experimento_v5"
ANO_MAX = 2025               # 2026 é o holdout prospectivo: nunca entra aqui
ANO_FIM_DEV = 2024
Q_RISCO_V5 = 0.75
EPS_INCID = 1.0              # casos/100 mil — evita escore infinito em cidades com P75 = 0
CONFIGS = [("nenhum", False), ("parcimonioso", False), ("nenhum", True), ("parcimonioso", True)]


def nome(clima: str, susc: bool) -> str:
    return f"{'clima' if clima == 'parcimonioso' else 'semclima'}_{'susc' if susc else 'semsusc'}"


def preparar(panel: pd.DataFrame, doenca: str, h: int) -> pd.DataFrame:
    p = panel[panel["year"] <= ANO_MAX]
    df = build_ml_features(p, doenca=doenca, horizonte=h)
    df = df.dropna(subset=[DOENCA_PARA_COL[doenca]])
    return df[df["populacao"].notna() & (df["populacao"] > 0)].reset_index(drop=True)


def rodar(df: pd.DataFrame, doenca: str, h: int) -> tuple[pd.DataFrame, dict]:
    alvo = DOENCA_PARA_COL[doenca]
    p = PREFIXOS[alvo]
    feats = {nome(c, s): get_feature_columns(df, doenca=doenca, clima=c, suscetibilidade=s) for c, s in CONFIGS}
    df = df.assign(_incid=df[alvo] / df["populacao"] * 1e5)
    partes = []
    for tr, te, ano in _expanding_window_splits(df["year"], 3, ANO_MAX):
        d_tr, d_te = df[tr], df[te]
        t0 = time.time()
        parte = pd.DataFrame({
            "code": d_te["code"].values, "year": d_te["year"].values, "month": d_te["month"].values,
            "pop": d_te["populacao"].to_numpy(float),
            "y_true": d_te[alvo].to_numpy(float),
            "y_persistencia": d_te[f"{p}_lag{h}"].to_numpy(float),
            "p75_incid": limiares_por_cidade(d_tr, d_te["code"], "_incid", Q_RISCO_V5),
        })
        for c, s in CONFIGS:
            _, pred = fit_predict_fold(d_tr, d_te, feats[nome(c, s)], alvo, use_pop_offset=True)
            parte[f"pred_{nome(c, s)}"] = pred
        partes.append(parte)
        logger.info(f"  {doenca} h={h} fold {ano}: {len(d_te)} linhas, {time.time() - t0:.1f}s")
    oof = pd.concat(partes, ignore_index=True)
    oof["incid"] = oof["y_true"] / oof["pop"] * 1e5
    oof["risco_alto"] = (oof["incid"] > oof["p75_incid"]).astype(int)
    for c, s in CONFIGS:
        n = nome(c, s)
        oof[f"escore_{n}"] = (oof[f"pred_{n}"] / oof["pop"] * 1e5) / (oof["p75_incid"] + EPS_INCID)
        oof[f"prob_{n}"] = calibrar_temporal(oof, f"escore_{n}")
    pe = (oof["y_persistencia"] / oof["pop"] * 1e5) / (oof["p75_incid"] + EPS_INCID)
    oof["escore_persistencia"] = pe
    oof["prob_persistencia"] = calibrar_temporal(oof, "escore_persistencia")
    return oof, feats


def calibrar_temporal(oof: pd.DataFrame, col: str) -> pd.Series:
    """Isotônica ajustada só nos anos anteriores ao fold avaliado."""
    prob = pd.Series(np.nan, index=oof.index)
    for ano in sorted(oof["year"].unique()):
        ant = oof[oof["year"] < ano]
        if ant.empty:
            continue
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
        iso.fit(ant[col].fillna(0), ant["risco_alto"])
        m = oof["year"] == ano
        prob[m] = iso.predict(oof.loc[m, col].fillna(0))
    return prob


def metricas(oof: pd.DataFrame, col_pred: str, col_escore: str, col_prob: str) -> dict:
    y, pred = oof["y_true"].to_numpy(float), oof[col_pred].to_numpy(float)
    persist = np.nan_to_num(oof["y_persistencia"].to_numpy(float))
    mae, mae_p = mean_absolute_error(y, pred), mean_absolute_error(y, persist)
    err_inc = (np.abs(y - pred) / oof["pop"] * 1e5).groupby(oof["code"]).mean()
    out = {
        "n": len(oof), "mae": mae, "mae_persistencia": mae_p,
        "skill": (mae_p - mae) / mae_p if mae_p > 0 else np.nan,
        "mae_incid_mediana_cidades": float(err_inc.median()),
        "auc": roc_auc_score(oof["risco_alto"], oof[col_escore].fillna(0)) if oof["risco_alto"].nunique() == 2 else np.nan,
        "prevalencia_risco": float(oof["risco_alto"].mean()),
    }
    c = oof[oof[col_prob].notna()]
    if len(c) and c["risco_alto"].nunique() == 2:
        out["brier"] = brier_score_loss(c["risco_alto"], c[col_prob])
        out["brier_climatologia"] = brier_score_loss(c["risco_alto"], np.full(len(c), oof["risco_alto"].mean()))
        out["brier_skill"] = 1 - out["brier"] / out["brier_climatologia"]
    return out


def tabela_resultados(oof: pd.DataFrame, doenca: str, h: int, feats: dict, periodo: str) -> list[dict]:
    linhas = []
    for c, s in CONFIGS:
        n = nome(c, s)
        linhas.append({"doenca": doenca, "horizonte": h, "periodo": periodo, "modelo": n, "clima": c,
                       "suscetibilidade": s, "n_features": len(feats[n]),
                       **metricas(oof, f"pred_{n}", f"escore_{n}", f"prob_{n}")})
    linhas.append({"doenca": doenca, "horizonte": h, "periodo": periodo, "modelo": "persistencia",
                   **metricas(oof, "y_persistencia", "escore_persistencia", "prob_persistencia")})
    return linhas


def efeitos(oof_dev: pd.DataFrame, doenca: str, h: int, res_dev: pd.DataFrame) -> list[dict]:
    """ΔMAE de cada grupo, com o outro grupo fixo no nível de menor MAE (regra do protocolo)."""
    r = res_dev[(res_dev.doenca == doenca) & (res_dev.horizonte == h) & (res_dev.modelo != "persistencia")]
    mae = r.set_index(["clima", "suscetibilidade"])["mae"]
    susc_best = bool(mae.xs("nenhum", level="clima").idxmin())
    clima_best = mae.xs(False, level="suscetibilidade").idxmin()
    out = []
    for grupo, com, sem in (
        ("clima", nome("parcimonioso", susc_best), nome("nenhum", susc_best)),
        ("suscetibilidade", nome(clima_best, True), nome(clima_best, False)),
    ):
        d, lo, hi = bootstrap_delta_mae(oof_dev, f"pred_{com}", f"pred_{sem}")
        out.append({"doenca": doenca, "horizonte": h, "grupo": grupo, "com": com, "sem": sem,
                    "delta_mae": d, "ic95_lo": lo, "ic95_hi": hi,
                    "delta_pct": 100 * d / (oof_dev["y_true"] - oof_dev[f"pred_{sem}"]).abs().mean(),
                    "reduz_erro": bool(hi < 0)})
    return out


def decidir(ef: pd.DataFrame) -> dict:
    """Grupo entra se reduzir o erro (IC 95% < 0) em ≥ 2 dos 3 horizontes."""
    dec = {}
    for d, g in ef.groupby("doenca"):
        dec[d] = {grupo: bool(x["reduz_erro"].sum() >= 2) for grupo, x in g.groupby("grupo")}
        dec[d]["modelo"] = nome("parcimonioso" if dec[d]["clima"] else "nenhum", dec[d]["suscetibilidade"])
    return dec


def run(panel: pd.DataFrame | None = None, out_dir: Path = OUT_V5, doencas=DOENCAS_EXPERIMENTO, horizontes=HORIZONTES):
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    if panel is None:
        from src.ml_pipeline.data_ingestion import build_base_panel
        panel = build_base_panel(BASE_DIR)
    panel = panel[panel["year"] <= ANO_MAX].copy()       # 2026 fora, antes de qualquer cálculo
    res, ef_all, meta_feats = [], [], {}
    for doenca in doencas:
        for h in horizontes:
            logger.info(f"=== v5 {doenca} h={h} ===")
            oof, feats = rodar(preparar(panel, doenca, h), doenca, h)
            oof.to_csv(out_dir / f"oof_{doenca}_h{h}.csv.gz", index=False)
            meta_feats[f"{doenca}_h{h}"] = feats
            dev, v25 = oof[oof["year"] <= ANO_FIM_DEV], oof[oof["year"] == ANO_MAX]
            res += tabela_resultados(dev, doenca, h, feats, "dev_2018_2024")
            if len(v25):
                res += tabela_resultados(v25, doenca, h, feats, "validacao_2025_ja_vista")
            ef_all += efeitos(dev, doenca, h, pd.DataFrame(res).query("periodo == 'dev_2018_2024'"))
    resultados, ef = pd.DataFrame(res), pd.DataFrame(ef_all)
    resultados.to_csv(out_dir / "resultados.csv", index=False)
    ef.to_csv(out_dir / "efeitos.csv", index=False)
    dec = decidir(ef)
    (out_dir / "decisao.json").write_text(json.dumps(dec, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "relatorio.md").write_text(relatorio(resultados, ef, dec), encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({
        "executado_em": time.strftime("%Y-%m-%d %H:%M:%S"), "git_commit": git_commit(),
        "duracao_min": round((time.time() - t0) / 60, 1), "anos": [int(panel.year.min()), int(panel.year.max())],
        "xgb_params": XGB_PARAMS, "q_risco": Q_RISCO_V5, "features": meta_feats,
    }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    logger.info(f"Experimento v5 concluído → {out_dir}")
    return resultados, ef, dec


def relatorio(res: pd.DataFrame, ef: pd.DataFrame, dec: dict) -> str:
    def f(v, n=3):
        return "—" if pd.isna(v) else f"{v:.{n}f}"
    md = ["# Experimento v5 — clima parcimonioso × suscetibilidade (protocolo v5)\n",
          "Dev = OOF 2018–2024. 2025 = segunda validação, já vista na v4 (não é teste limpo). "
          "Risco alto = incidência > P75 da cidade (treino).\n"]
    for d in res["doenca"].unique():
        md += [f"\n## {d.capitalize()}\n",
               "| período | h | modelo | MAE | Skill | MAE incid. (mediana cidades) | AUC | Brier skill |",
               "|---|---|---|---|---|---|---|---|"]
        for x in res[res.doenca == d].sort_values(["periodo", "horizonte", "modelo"]).itertuples():
            md.append(f"| {x.periodo} | {x.horizonte} | {x.modelo} | {f(x.mae, 2)} | {f(x.skill)} | "
                      f"{f(x.mae_incid_mediana_cidades, 1)} | {f(x.auc)} | {f(getattr(x, 'brier_skill', np.nan))} |")
        md += ["\n### Efeitos (ΔMAE com − sem, IC 95% bootstrap por município)\n",
               "| h | grupo | ΔMAE | IC 95% | Δ% | reduz erro? |", "|---|---|---|---|---|---|"]
        for x in ef[ef.doenca == d].itertuples():
            md.append(f"| {x.horizonte} | {x.grupo} | {x.delta_mae:+.3f} | [{x.ic95_lo:+.3f}, {x.ic95_hi:+.3f}] | "
                      f"{x.delta_pct:+.1f}% | {'sim' if x.reduz_erro else 'não'} |")
        md.append(f"\n**Decisão (regra pré-registrada):** clima = {'entra' if dec[d]['clima'] else 'fica de fora'}; "
                  f"suscetibilidade = {'entra' if dec[d]['suscetibilidade'] else 'fica de fora'} → `{dec[d]['modelo']}`")
    return "\n".join(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Experimento v5 (protocolo pré-registrado)")
    ap.add_argument("--doenca", choices=list(DOENCAS_EXPERIMENTO) + ["todas"], default="todas")
    a = ap.parse_args(argv)
    configurar_log()
    run(doencas=DOENCAS_EXPERIMENTO if a.doenca == "todas" else (a.doenca,))


if __name__ == "__main__":
    main()
