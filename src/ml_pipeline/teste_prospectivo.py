"""
Step 8 — Teste prospectivo único em jan–ago/2026 (docs/PROTOCOLO_V5.md).

  - Configuração: output/experimento_v5/decisao.json (fixada no desenvolvimento).
  - Treino: 2015–2025 completo. Teste: meses de 2026 com ≥ 8 semanas entre o fim do mês e a
    data de ingestão (coluna INGERIDO_EM), limitados a jan–ago.
  - Probabilidade: isotônica ajustada no OOF 2019–2025 (nunca em 2026).
  - Reporta modelo, persistência e o alerta do InfoDengue (nível em t−h), com as mesmas métricas.
  - Uso único: exige --confirmar e grava trava. Nada é ajustado depois.
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, mean_absolute_error, roc_auc_score

from src.config import BASE_DIR, DB_PATH, HORIZONTES
from src.ml_pipeline.alerta_risco import COL_NIVEL
from src.ml_pipeline.experimento_horizontes import configurar_log, git_commit
from src.ml_pipeline.experimento_v5 import EPS_INCID, OUT_V5, Q_RISCO_V5, nome
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, PREFIXOS, build_ml_features, get_feature_columns
from src.ml_pipeline.model_training import fit_predict_fold, limiares_por_cidade

logger = logging.getLogger(__name__)

ANO_TESTE, MESES_TESTE = 2026, tuple(range(1, 9))
SEMANAS_CONSOLIDACAO = 8
LOCK = "teste_prospectivo_2026.lock"


class HoldoutJaUsado(RuntimeError):
    pass


def meses_consolidados(db_path: Path = DB_PATH) -> list[int]:
    """Meses de jan–ago/2026 com ≥ 8 semanas entre o fim do mês e a ingestão mais antiga do mês."""
    with sqlite3.connect(db_path) as c:
        g = pd.read_sql_query(
            f"SELECT MES, MIN(INGERIDO_EM) ing FROM ingestao_saude WHERE ANO = {ANO_TESTE} GROUP BY MES", c)
    ok = []
    for r in g.itertuples():
        fim = pd.Timestamp(ANO_TESTE, int(r.MES), 1) + pd.offsets.MonthEnd(0)
        if r.MES in MESES_TESTE and r.ing and (pd.Timestamp(r.ing) - fim).days >= 7 * SEMANAS_CONSOLIDACAO:
            ok.append(int(r.MES))
    return sorted(ok)


def _metricas(y, pred, persist, risco, escore, prob, pop, code) -> dict:
    mae, mae_p = mean_absolute_error(y, pred), mean_absolute_error(y, np.nan_to_num(persist))
    err_inc = pd.Series(np.abs(y - pred) / pop * 1e5).groupby(np.asarray(code)).mean()
    out = {"n": int(len(y)), "mae": mae, "mae_persistencia": mae_p,
           "skill": (mae_p - mae) / mae_p if mae_p > 0 else np.nan,
           "mae_incid_mediana_cidades": float(err_inc.median()), "prevalencia_risco": float(np.mean(risco))}
    if len(set(risco)) == 2:
        out["auc"] = roc_auc_score(risco, escore)
        out["brier"] = brier_score_loss(risco, prob)
        out["brier_climatologia"] = brier_score_loss(risco, np.full(len(risco), np.mean(risco)))
        out["brier_skill"] = 1 - out["brier"] / out["brier_climatologia"]
    return out


def avaliar(panel: pd.DataFrame, doenca: str, h: int, info: dict, meses: list[int], exp_dir: Path) -> tuple[dict, pd.DataFrame]:
    alvo, p = DOENCA_PARA_COL[doenca], PREFIXOS[DOENCA_PARA_COL[doenca]]
    clima = "parcimonioso" if info["clima"] else "nenhum"
    mod = nome(clima, info["suscetibilidade"])
    base = panel[(panel.year < ANO_TESTE) | ((panel.year == ANO_TESTE) & panel.month.isin(meses))]
    df = build_ml_features(base, doenca=doenca, horizonte=h).dropna(subset=[alvo])
    df = df[df["populacao"] > 0].assign(_incid=lambda x: x[alvo] / x["populacao"] * 1e5)
    tr, te = df[df.year < ANO_TESTE], df[df.year == ANO_TESTE]
    feats = get_feature_columns(df, doenca=doenca, clima=clima, suscetibilidade=info["suscetibilidade"])
    _, pred = fit_predict_fold(tr, te, feats, alvo, use_pop_offset=True)

    oof_dev = pd.read_csv(exp_dir / f"oof_{doenca}_h{h}.csv.gz", dtype={"code": str})
    iso_m = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof_dev[f"escore_{mod}"].fillna(0), oof_dev["risco_alto"])
    iso_p = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof_dev["escore_persistencia"].fillna(0), oof_dev["risco_alto"])

    pop = te["populacao"].to_numpy(float)
    p75 = limiares_por_cidade(tr, te["code"], "_incid", Q_RISCO_V5)
    y = te[alvo].to_numpy(float)
    risco = (y / pop * 1e5 > p75).astype(int)
    persist = te[f"{p}_lag{h}"].to_numpy(float)
    esc_m = (pred / pop * 1e5) / (p75 + EPS_INCID)
    esc_p = (np.nan_to_num(persist) / pop * 1e5) / (p75 + EPS_INCID)

    res = {"modelo": mod, "meses": meses,
           **_metricas(y, pred, persist, risco, esc_m, iso_m.predict(esc_m), pop, te["code"]),
           "persistencia": _metricas(y, np.nan_to_num(persist), persist, risco, esc_p, iso_p.predict(esc_p), pop, te["code"])}

    # Combinação modelo + persistência (desvio pré-registrado): peso final escolhido com 2018–2025
    comb_path = exp_dir / "combinacao.json"
    if comb_path.exists() and "escore_comb" in oof_dev.columns:
        from src.ml_pipeline.combinacao import combinar
        w = json.loads(comb_path.read_text(encoding="utf-8"))[doenca]["horizontes"][f"h{h}"]["peso_final"]
        pred_c = combinar(pred, persist, w)
        esc_c = (pred_c / pop * 1e5) / (p75 + EPS_INCID)
        iso_c = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(
            oof_dev["escore_comb"].fillna(0), oof_dev["risco_alto"])
        res["combinacao"] = {"peso_modelo": w,
                             **_metricas(y, pred_c, persist, risco, esc_c, iso_c.predict(esc_c), pop, te["code"])}

    if COL_NIVEL[doenca] in panel.columns:
        nv = panel[["code", "year", "month", COL_NIVEL[doenca]]].rename(columns={COL_NIVEL[doenca]: "nivel"})
        idx = nv.year * 12 + nv.month - 1 + h
        nv = nv.assign(year=idx // 12, month=idx % 12 + 1)
        t = te[["code", "year", "month"]].reset_index(drop=True).merge(nv, on=["code", "year", "month"], how="left")
        m = t["nivel"].notna().to_numpy()
        if m.sum() and len(set(risco[m])) == 2:
            iso_n = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
            nv_dev = oof_dev.merge(nv, on=["code", "year", "month"], how="inner").dropna(subset=["nivel"])
            if len(nv_dev):
                iso_n.fit(nv_dev["nivel"].fillna(1), nv_dev["risco_alto"])
                prob_n = iso_n.predict(t.loc[m, "nivel"])
            else:
                prob_n = np.full(m.sum(), risco[m].mean())
            res["infodengue"] = {"n": int(m.sum()), "auc": roc_auc_score(risco[m], t.loc[m, "nivel"]),
                                 "brier": brier_score_loss(risco[m], prob_n)}
    det = te[["code", "year", "month"]].assign(y_true=y, pred=pred, risco_alto=risco, prob=iso_m.predict(esc_m))
    return res, det


def run(confirmar: bool = False, forcar: bool = False, panel: pd.DataFrame | None = None, exp_dir: Path = OUT_V5,
        meses: list[int] | None = None):
    lock = exp_dir / LOCK
    if lock.exists() and not forcar:
        raise HoldoutJaUsado(f"Teste prospectivo já executado em {lock.read_text(encoding='utf-8')}. Reusar invalida o teste.")
    if not confirmar:
        raise PermissionError("O teste prospectivo 2026 é de uso único. Revise output/experimento_v5/ e rode com --confirmar.")
    dec = json.loads((exp_dir / "decisao.json").read_text(encoding="utf-8"))
    meses = meses if meses is not None else meses_consolidados()
    if not meses:
        raise RuntimeError("Nenhum mês de 2026 consolidado (≥ 8 semanas). Rode a ingestão antes.")
    if panel is None:
        from src.ml_pipeline.data_ingestion import build_base_panel
        panel = build_base_panel(BASE_DIR)
    rel = {"executado_em": time.strftime("%Y-%m-%d %H:%M:%S"), "git_commit": git_commit(),
           "reexecucao_forcada": lock.exists(), "meses_2026": meses}
    for doenca, info in dec.items():
        rel[doenca] = {}
        for h in HORIZONTES:
            r, det = avaliar(panel, doenca, h, info, meses, exp_dir)
            det.to_csv(exp_dir / f"teste_2026_{doenca}_h{h}.csv.gz", index=False)
            rel[doenca][f"h{h}"] = r
            logger.info(f"Teste 2026 {doenca} h={h}: AUC={r.get('auc'):.3f} Brier skill={r.get('brier_skill'):.3f}")
    (exp_dir / "teste_prospectivo_2026.json").write_text(json.dumps(rel, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    (exp_dir / "teste_prospectivo_2026.md").write_text(markdown(rel), encoding="utf-8")
    lock.write_text(rel["executado_em"], encoding="utf-8")
    return rel


def markdown(rel: dict) -> str:
    def f(v, n=3):
        return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{n}f}"
    md = [f"# Teste prospectivo único — 2026 (meses {rel['meses_2026']}), executado {rel['executado_em']}\n",
          "Treino 2015–2025; nada ajustado depois. Risco alto = incidência > P75 da cidade.\n"]
    if rel["reexecucao_forcada"]:
        md.append("> ⚠️ Reexecução forçada: o holdout já tinha sido usado.\n")
    for d in [k for k in rel if isinstance(rel[k], dict) and k not in ("meses_2026",)]:
        md += [f"\n## {d.capitalize()}\n",
               "| h | previsor | MAE | Skill | MAE incid. (mediana cidades) | AUC | Brier skill |",
               "|---|---|---|---|---|---|---|"]
        for h, r in rel[d].items():
            linhas = [(f"modelo ({r['modelo']})", r), ("persistência", r["persistencia"])]
            if "combinacao" in r:
                linhas.append((f"combinação (peso modelo {r['combinacao']['peso_modelo']:.1f})", r["combinacao"]))
            for nome_, x in linhas:
                md.append(f"| {h[1:]} | {nome_} | {f(x['mae'], 2)} | {f(x['skill'])} | "
                          f"{f(x['mae_incid_mediana_cidades'], 1)} | {f(x.get('auc'))} | {f(x.get('brier_skill'))} |")
            nv = r.get("infodengue", {})
            md.append(f"| {h[1:]} | alerta InfoDengue | — | — | — | {f(nv.get('auc'))} | — |")
    return "\n".join(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Teste prospectivo único em 2026")
    ap.add_argument("--confirmar", action="store_true")
    ap.add_argument("--forcar", action="store_true")
    a = ap.parse_args(argv)
    configurar_log()
    run(confirmar=a.confirmar, forcar=a.forcar)


if __name__ == "__main__":
    main()
