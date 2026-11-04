"""
Produto v5: alerta de risco (docs/PROTOCOLO_V5.md).

1. benchmark_infodengue(): compara o modelo com o alerta oficial do InfoDengue no mesmo OOF.
   O benchmark é o `nivel` (1 verde … 4 vermelho) do mês t−h — o último alerta oficial conhecido
   no momento da previsão. AUC usa o nível como escore; Brier usa a isotônica temporal do nível.
2. treinar_modelos_risco(): modelo de produção por doença × horizonte com a configuração decidida
   em output/experimento_v5/decisao.json, treinado até `ano_max`, com:
     - calibrador isotônico escore → P(risco alto), ajustado no OOF (2019–2025);
     - calibração do intervalo de 90% da contagem (secundária);
     - limiares por cidade (P75 da incidência mensal = definição de risco alto).

Artefatos: output/models/final_v5/<doenca>/{h<h>.joblib, h<h>_calibrador.joblib, metadata.json}
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

from src.config import DB_PATH, HORIZONTES, OUTPUT_DIR
from src.ml_pipeline.experimento_horizontes import git_commit
from src.ml_pipeline.experimento_v5 import ANO_FIM_DEV, EPS_INCID, OUT_V5, Q_RISCO_V5, calibrar_temporal, nome
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, build_ml_features, get_feature_columns
from src.ml_pipeline.model_training import XGB_PARAMS, fit_predict_fold
from src.ml_pipeline.modelo_final import calibrar_intervalo

logger = logging.getLogger(__name__)

OUT_MODELOS_V5 = OUTPUT_DIR / "models" / "final_v5"
COL_NIVEL = {"dengue": "NIVEL_DENGUE", "chikungunya": "NIVEL_CHIKUNGUNYA"}
# Faixas de probabilidade → nível de risco (fixadas aqui, antes do teste prospectivo)
FAIXAS_PROB = ((0.25, "baixo"), (0.50, "medio"), (0.75, "alto"), (1.01, "critico"))


def nivel_por_probabilidade(p: float) -> str:
    for lim, nivel in FAIXAS_PROB:
        if p < lim:
            return nivel
    return "critico"


# ------------------------------------------------------------------ benchmark InfoDengue
def niveis_infodengue(db_path: Path = DB_PATH) -> pd.DataFrame:
    with sqlite3.connect(db_path) as c:
        cols = {r[1] for r in c.execute("PRAGMA table_info(ingestao_saude)")}
        if not set(COL_NIVEL.values()) <= cols:
            raise RuntimeError("Colunas NIVEL_* ausentes: rode `python main.py atualizar-dados --alvo infodengue`.")
        n = pd.read_sql_query(
            "SELECT CODIGO_MUNICIPIO code, ANO year, MES month, NIVEL_DENGUE, NIVEL_CHIKUNGUNYA FROM ingestao_saude", c)
    n["code"] = n["code"].astype(str).str[:6]
    return n


def benchmark_infodengue(exp_dir: Path = OUT_V5, doencas=("dengue", "chikungunya"), horizontes=HORIZONTES,
                         niveis: pd.DataFrame | None = None) -> pd.DataFrame:
    niveis = niveis if niveis is not None else niveis_infodengue()
    dec = json.loads((exp_dir / "decisao.json").read_text(encoding="utf-8"))
    linhas = []
    for d in doencas:
        mod = dec[d]["modelo"]
        nv = niveis[["code", "year", "month", COL_NIVEL[d]]].rename(columns={COL_NIVEL[d]: "nivel"})
        for h in horizontes:
            oof = pd.read_csv(exp_dir / f"oof_{d}_h{h}.csv.gz", dtype={"code": str})
            # nível conhecido em t−h: desloca o mês do alerta h meses para frente
            idx = nv["year"] * 12 + nv["month"] - 1 + h
            alvo = nv.assign(year=idx // 12, month=idx % 12 + 1)
            oof = oof.merge(alvo, on=["code", "year", "month"], how="left")
            oof["prob_nivel"] = calibrar_temporal(oof.assign(escore_nivel=oof["nivel"].fillna(1)), "escore_nivel")
            for periodo, g in (("dev_2018_2024", oof[oof.year <= ANO_FIM_DEV]), ("validacao_2025_ja_vista", oof[oof.year == 2025])):
                g = g[g["nivel"].notna()]
                if g.empty or g["risco_alto"].nunique() < 2:
                    continue
                c = g[g["prob_nivel"].notna() & g[f"prob_{mod}"].notna()]
                linhas.append({
                    "doenca": d, "horizonte": h, "periodo": periodo, "n": len(g),
                    "cobertura_nivel": float(len(g) / max(1, len(oof[oof.year.isin(g.year.unique())]))),
                    "auc_modelo": roc_auc_score(g["risco_alto"], g[f"escore_{mod}"]),
                    "auc_infodengue": roc_auc_score(g["risco_alto"], g["nivel"]),
                    "auc_persistencia": roc_auc_score(g["risco_alto"], g["escore_persistencia"].fillna(0)),
                    "brier_modelo": brier_score_loss(c["risco_alto"], c[f"prob_{mod}"]) if len(c) else np.nan,
                    "brier_infodengue": brier_score_loss(c["risco_alto"], c["prob_nivel"]) if len(c) else np.nan,
                    "brier_persistencia": (brier_score_loss(c["risco_alto"], c["prob_persistencia"].fillna(c["risco_alto"].mean()))
                                           if len(c) else np.nan),
                })
    out = pd.DataFrame(linhas)
    out.to_csv(exp_dir / "benchmark_infodengue.csv", index=False)
    salvar_calibracao(exp_dir, dec, horizontes)
    return out


def salvar_calibracao(exp_dir: Path, dec: dict, horizontes):
    """Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF 2019–2025."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(dec), figsize=(5.5 * len(dec), 4.5), squeeze=False)
    for ax, (d, info) in zip(axes[0], dec.items()):
        for h in horizontes:
            oof = pd.read_csv(exp_dir / f"oof_{d}_h{h}.csv.gz").dropna(subset=[f"prob_{info['modelo']}"])
            b = pd.cut(oof[f"prob_{info['modelo']}"], np.linspace(0, 1, 11), include_lowest=True)
            g = oof.groupby(b, observed=True).agg(p=(f"prob_{info['modelo']}", "mean"), o=("risco_alto", "mean"))
            ax.plot(g["p"], g["o"], "o-", label=f"h={h}")
        ax.plot([0, 1], [0, 1], "k--", lw=0.8)
        ax.set_title(f"{d.capitalize()} — {info['modelo']}")
        ax.set_xlabel("Probabilidade prevista de risco alto"); ax.set_ylabel("Frequência observada")
        ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(exp_dir / "calibracao_risco.png", dpi=120)
    plt.close(fig)


# ------------------------------------------------------------------ modelos de produção
def treinar_modelos_risco(panel: pd.DataFrame, exp_dir: Path = OUT_V5, out_dir: Path = OUT_MODELOS_V5,
                          ano_max: int = 2025, horizontes=HORIZONTES) -> dict:
    dec = json.loads((exp_dir / "decisao.json").read_text(encoding="utf-8"))
    res = pd.read_csv(exp_dir / "resultados.csv")
    bench = exp_dir / "benchmark_infodengue.csv"
    bench = pd.read_csv(bench) if bench.exists() else None
    teste = exp_dir / "teste_prospectivo_2026.json"
    teste = json.loads(teste.read_text(encoding="utf-8")) if teste.exists() else None
    p = panel[panel["year"] <= ano_max]
    todas = {}
    for doenca, info in dec.items():
        alvo = DOENCA_PARA_COL[doenca]
        clima = "parcimonioso" if info["clima"] else "nenhum"
        mod = nome(clima, info["suscetibilidade"])
        dest = out_dir / doenca
        dest.mkdir(parents=True, exist_ok=True)
        meta = {"versao": "v5", "doenca": doenca, "modelo": mod, "clima": clima,
                "suscetibilidade": info["suscetibilidade"], "treinado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                "git_commit": git_commit(), "anos_treino": [int(p.year.min()), ano_max],
                "xgb_params": XGB_PARAMS, "q_risco": Q_RISCO_V5, "eps_incid": EPS_INCID,
                "faixas_probabilidade": FAIXAS_PROB, "horizontes": {}}
        for h in horizontes:
            df = build_ml_features(p, doenca=doenca, horizonte=h).dropna(subset=[alvo])
            df = df[df["populacao"] > 0]
            feats = get_feature_columns(df, doenca=doenca, clima=clima, suscetibilidade=info["suscetibilidade"])
            model, _ = fit_predict_fold(df, df.iloc[:1], feats, alvo, use_pop_offset=True)
            joblib.dump(model, dest / f"h{h}.joblib")
            oof = pd.read_csv(exp_dir / f"oof_{doenca}_h{h}.csv.gz")
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof[f"escore_{mod}"].fillna(0), oof["risco_alto"])
            joblib.dump(iso, dest / f"h{h}_calibrador.joblib")
            r = res[(res.doenca == doenca) & (res.horizonte == h) & (res.modelo == mod)].set_index("periodo")
            cols = ["mae", "skill", "auc", "brier_skill", "mae_incid_mediana_cidades"]
            meta["horizontes"][f"h{h}"] = {
                "arquivo": f"h{h}.joblib", "calibrador": f"h{h}_calibrador.joblib", "features": feats,
                "intervalo_contagem": calibrar_intervalo(oof["y_true"], oof[f"pred_{mod}"]),
                "metricas": {per: r.loc[per, cols].astype(float).round(4).to_dict() for per in r.index},
                "benchmark_infodengue": (bench[(bench.doenca == doenca) & (bench.horizonte == h)].round(4).to_dict("records")
                                         if bench is not None else None),
                "teste_prospectivo_2026": (teste or {}).get(doenca, {}).get(f"h{h}"),
            }
            logger.info(f"Risco {doenca} h={h}: {mod}, {len(feats)} features")
        hist = p.dropna(subset=[alvo]).assign(_inc=lambda x: x[alvo] / x["populacao"] * 1e5)
        q = hist.groupby("code").agg(p75_incid=("_inc", lambda s: s.quantile(Q_RISCO_V5)),
                                     meses_com_caso=(alvo, lambda s: int((s > 0).sum())),
                                     nome=("city_name", "last"), populacao=("populacao", "last"))
        meta["cidades"] = {str(c): {"nome": r.nome, "populacao": int(r.populacao), "p75_incid": float(r.p75_incid),
                                    "meses_com_caso": int(r.meses_com_caso)} for c, r in q.iterrows()}
        (dest / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        todas[doenca] = meta
    return todas
