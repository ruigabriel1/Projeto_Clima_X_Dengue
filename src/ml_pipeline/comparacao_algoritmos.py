"""
Comparação exploratória de algoritmos para o relatório técnico da UC de IA (UNISUL).

Registrada em docs/PROTOCOLO_V5.md (Desvios, 2026-11-22) ANTES de rodar. Só descritiva: não muda o modelo
de produção, nem XGB_PARAMS, nem nenhuma decisão de protocolo.

- Previsores: XGBoost Poisson (referência), Regressão Linear (MQO), Árvore CART e MLP, contra a persistência.
  Mesmos dados (2015–2024), mesmos folds expanding window 2018–2024 e mesmas métricas da v5.
- K-Means: agrupa municípios pelo perfil sazonal da dengue (descritivo).
- Picos em % da população: incidência notificada observada, 2015–2025 (descritivo).

Uso: python -m src.ml_pipeline.comparacao_algoritmos   (saídas em output/comparacao_algoritmos/)
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

from src.config import BASE_DIR, OUTPUT_DIR
from src.ml_pipeline.experimento_horizontes import configurar_log, git_commit
from src.ml_pipeline.experimento_v5 import EPS_INCID, Q_RISCO_V5, calibrar_temporal, metricas
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, PREFIXOS, build_ml_features, get_feature_columns
from src.ml_pipeline.model_training import XGB_PARAMS, _expanding_window_splits, fit_predict_fold, limiares_por_cidade

logger = logging.getLogger(__name__)

OUT = OUTPUT_DIR / "comparacao_algoritmos"
ANO_FIM_DEV = 2024           # 2025 e 2026 não entram na comparação
ANO_FIM_PICOS = 2025         # picos observados (descritivo)
CONFIG_PRODUCAO = {"dengue": ("parcimonioso", True), "chikungunya": ("nenhum", True)}

CART_PARAMS = dict(criterion="poisson", max_depth=5, min_samples_leaf=50, random_state=42)
MLP_PARAMS = dict(hidden_layer_sizes=(32, 16), activation="relu", solver="adam", learning_rate_init=0.001,
                  max_iter=200, early_stopping=True, validation_fraction=0.1, random_state=42)
ALGORITMOS = ["xgboost", "regressao_linear", "arvore_cart", "mlp"]


def _pre():
    return [SimpleImputer(strategy="median"), StandardScaler()]


def prever_sklearn(nome: str, d_tr: pd.DataFrame, d_te: pd.DataFrame, feats: list[str], alvo: str) -> np.ndarray:
    """Treina um algoritmo do sklearn sobre a incidência e devolve casos previstos (≥ 0)."""
    inc_tr = d_tr[alvo].to_numpy(float) / d_tr["populacao"].to_numpy(float) * 1e5
    if nome == "regressao_linear":
        modelo, y, log = make_pipeline(*_pre(), LinearRegression()), np.log1p(inc_tr), True
    elif nome == "arvore_cart":
        modelo, y, log = make_pipeline(SimpleImputer(strategy="median"), DecisionTreeRegressor(**CART_PARAMS)), inc_tr, False
    elif nome == "mlp":
        modelo, y, log = make_pipeline(*_pre(), MLPRegressor(**MLP_PARAMS)), np.log1p(inc_tr), True
    else:
        raise ValueError(nome)
    modelo.fit(d_tr[feats], y)
    p = modelo.predict(d_te[feats])
    inc = np.expm1(np.clip(p, None, 12)) if log else p      # clip evita overflow do MQO em extrapolação
    return np.maximum(inc, 0) * d_te["populacao"].to_numpy(float) / 1e5


def rodar(panel: pd.DataFrame, doenca: str, h: int) -> tuple[pd.DataFrame, list[str]]:
    alvo = DOENCA_PARA_COL[doenca]
    p = PREFIXOS[alvo]
    df = build_ml_features(panel, doenca=doenca, horizonte=h).dropna(subset=[alvo])
    df = df[df["populacao"].notna() & (df["populacao"] > 0)].reset_index(drop=True)
    clima, susc = CONFIG_PRODUCAO[doenca]
    feats = get_feature_columns(df, doenca=doenca, clima=clima, suscetibilidade=susc)
    df = df.assign(_incid=df[alvo] / df["populacao"] * 1e5)
    partes = []
    for tr, te, ano in _expanding_window_splits(df["year"], 3, ANO_FIM_DEV):
        d_tr, d_te = df[tr], df[te]
        parte = pd.DataFrame({
            "code": d_te["code"].values, "year": d_te["year"].values, "month": d_te["month"].values,
            "pop": d_te["populacao"].to_numpy(float), "y_true": d_te[alvo].to_numpy(float),
            "y_persistencia": d_te[f"{p}_lag{h}"].to_numpy(float),
            "p75_incid": limiares_por_cidade(d_tr, d_te["code"], "_incid", Q_RISCO_V5),
        })
        for nome in ALGORITMOS:
            t0 = time.time()
            if nome == "xgboost":
                _, pred = fit_predict_fold(d_tr, d_te, feats, alvo, use_pop_offset=True)
            else:
                pred = prever_sklearn(nome, d_tr, d_te, feats, alvo)
            parte[f"pred_{nome}"] = pred
            logger.info(f"  {doenca} h={h} {ano} {nome}: {time.time() - t0:.1f}s")
        partes.append(parte)
    oof = pd.concat(partes, ignore_index=True)
    oof["incid"] = oof["y_true"] / oof["pop"] * 1e5
    oof["risco_alto"] = (oof["incid"] > oof["p75_incid"]).astype(int)
    for nome in ALGORITMOS + ["persistencia"]:
        col = "y_persistencia" if nome == "persistencia" else f"pred_{nome}"
        oof[f"escore_{nome}"] = (oof[col].fillna(0) / oof["pop"] * 1e5) / (oof["p75_incid"] + EPS_INCID)
        oof[f"prob_{nome}"] = calibrar_temporal(oof, f"escore_{nome}")
    return oof, feats


def tabela(oof: pd.DataFrame, doenca: str, h: int, n_feats: int) -> list[dict]:
    linhas = []
    for nome in ALGORITMOS + ["persistencia"]:
        col = "y_persistencia" if nome == "persistencia" else f"pred_{nome}"
        m = metricas(oof, col, f"escore_{nome}", f"prob_{nome}")
        m["previsto_sobre_real"] = float(np.nansum(oof[col]) / oof["y_true"].sum())
        linhas.append({"doenca": doenca, "horizonte": h, "algoritmo": nome, "n_features": n_feats, **m})
    return linhas


def kmeans_sazonal(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Perfil sazonal: fração média dos casos anuais de cada mês, por município (2015–2024)."""
    d = panel[(panel["year"] <= ANO_FIM_DEV)][["code", "year", "month", "dengue_cases"]].dropna()
    tot_cidade = d.groupby("code")["dengue_cases"].sum()
    d = d[d["code"].isin(tot_cidade[tot_cidade >= 50].index)]
    ano = d.groupby(["code", "year"])["dengue_cases"].transform("sum")
    d = d[ano > 0].assign(frac=lambda x: x["dengue_cases"] / ano[ano > 0])
    perfil = d.pivot_table(index="code", columns="month", values="frac", aggfunc="mean").fillna(0)
    perfil = perfil.div(perfil.sum(axis=1), axis=0)
    inercias = {}
    for k in range(2, 9):
        inercias[k] = float(KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42).fit(perfil).inertia_)
    k_escolhido = 2
    for k in range(3, 9):
        if (inercias[k - 1] - inercias[k]) / inercias[k - 1] >= 0.10:
            k_escolhido = k
        else:
            break
    km = KMeans(n_clusters=k_escolhido, init="k-means++", n_init=10, random_state=42).fit(perfil)
    rot = pd.DataFrame({"code": perfil.index, "grupo": km.labels_})
    rot["uf"] = rot["code"].astype(str).str[:2].map({"41": "PR", "42": "SC", "43": "RS"})
    cent = pd.DataFrame(km.cluster_centers_, columns=[f"m{int(m):02d}" for m in perfil.columns])
    cent["n_municipios"] = rot["grupo"].value_counts().sort_index().values
    cent["mes_pico"] = [int(perfil.columns[i]) for i in km.cluster_centers_.argmax(axis=1)]
    cent["frac_jan_mai"] = cent[[f"m{m:02d}" for m in range(1, 6)]].sum(axis=1)
    por_uf = rot.groupby(["grupo", "uf"]).size().unstack(fill_value=0)
    for uf in por_uf.columns:
        cent[f"n_{uf}"] = por_uf[uf].values
    return rot, cent, {"inercias": inercias, "k": k_escolhido, "n_municipios": len(perfil)}


def picos_populacao(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Incidência notificada observada por município-ano: acumulada no ano e no mês de pico (% da pop.)."""
    d = panel[["code", "year", "month", "dengue_cases", "populacao"]].dropna()
    d = d[d["populacao"] > 0]
    g = d.groupby(["code", "year"]).agg(casos_ano=("dengue_cases", "sum"), pico_mes=("dengue_cases", "max"),
                                        pop=("populacao", "mean")).reset_index()
    g["pct_ano"] = g["casos_ano"] / g["pop"] * 100
    g["pct_mes_pico"] = g["pico_mes"] / g["pop"] * 100
    g["incid_100mil_ano"] = g["casos_ano"] / g["pop"] * 1e5
    resumo = g.groupby("year").agg(
        casos=("casos_ano", "sum"), populacao=("pop", "sum"),
        municipios_epidemicos=("incid_100mil_ano", lambda s: int((s >= 300).sum())),
        municipios_acima_1pct=("pct_ano", lambda s: int((s >= 1).sum())),
        municipios_acima_5pct=("pct_ano", lambda s: int((s >= 5).sum())),
        pct_max=("pct_ano", "max"),
    ).reset_index()
    resumo["pct_regiao"] = resumo["casos"] / resumo["populacao"] * 100
    return g, resumo


def run(out_dir: Path = OUT, doencas=("dengue", "chikungunya"), horizontes=(1, 2, 3)):
    from src.ml_pipeline.data_ingestion import build_base_panel
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    panel_full = build_base_panel(BASE_DIR)
    panel = panel_full[panel_full["year"] <= ANO_FIM_DEV].copy()      # 2025/2026 fora da comparação
    res, n_feats = [], {}
    for doenca in doencas:
        for h in horizontes:
            logger.info(f"=== comparação {doenca} h={h} ===")
            oof, feats = rodar(panel, doenca, h)
            n_feats[f"{doenca}_h{h}"] = feats
            res += tabela(oof, doenca, h, len(feats))
            pd.DataFrame(res).to_csv(out_dir / "resultados.csv", index=False)
    rot, cent, km_meta = kmeans_sazonal(panel)
    rot.to_csv(out_dir / "kmeans_municipios.csv", index=False)
    cent.to_csv(out_dir / "kmeans_centroides.csv", index=False)
    g, resumo = picos_populacao(panel_full[panel_full["year"] <= ANO_FIM_PICOS])
    g.to_csv(out_dir / "picos_municipio_ano.csv", index=False)
    resumo.to_csv(out_dir / "picos_resumo_ano.csv", index=False)
    (out_dir / "meta.json").write_text(json.dumps({
        "executado_em": time.strftime("%Y-%m-%d %H:%M:%S"), "git_commit": git_commit(),
        "duracao_min": round((time.time() - t0) / 60, 1), "anos_comparacao": [2015, ANO_FIM_DEV],
        "xgb_params": XGB_PARAMS, "cart_params": CART_PARAMS, "mlp_params": MLP_PARAMS,
        "config_producao": CONFIG_PRODUCAO, "kmeans": km_meta, "features": n_feats,
    }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    logger.info(f"Comparação concluída em {(time.time() - t0) / 60:.1f} min → {out_dir}")
    return pd.DataFrame(res)


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    configurar_log()
    run()


if __name__ == "__main__":
    main()
