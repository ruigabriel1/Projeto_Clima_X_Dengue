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
ANO_TESTE_2026 = 2026


def previsoes_teste_2026(panel: pd.DataFrame, exp_dir: Path, doenca: str, h: int) -> pd.DataFrame | None:
    """
    Previsões do teste prospectivo de 2026 (fora da amostra) com o escore do modelo, para entrar na calibração
    de produção (v5.1). O escore usa o P75 de cada cidade com os anos < 2026, como no teste.
    """
    path = exp_dir / f"teste_2026_{doenca}_h{h}.csv.gz"
    if not path.exists():
        return None
    t = pd.read_csv(path, dtype={"code": str})
    alvo = DOENCA_PARA_COL[doenca]
    ant = panel[(panel["year"] < ANO_TESTE_2026) & (panel["populacao"] > 0)].dropna(subset=[alvo])
    p75 = (ant[alvo] / ant["populacao"] * 1e5).groupby(ant["code"]).quantile(Q_RISCO_V5)
    pop = panel[panel["year"] == ANO_TESTE_2026].groupby("code")["populacao"].last()
    t["pop"] = t["code"].map(pop)
    t["escore"] = (t["pred"] / t["pop"] * 1e5) / (t["code"].map(p75).fillna(p75.median()) + EPS_INCID)
    return t.dropna(subset=["pop"])


def desempenho(res: pd.DataFrame, bench: pd.DataFrame | None, teste: dict | None, doenca: str, h: int, mod: str,
               t26: pd.DataFrame | None, intervalo_dev: dict) -> dict:
    """Resumo honesto por horizonte para a aplicação ("quão confiável é"): dev, 2025 e teste de 2026."""
    cols = ["mae", "skill", "auc", "brier_skill", "mae_incid_mediana_cidades"]
    out = {}
    for per, rotulo in (("dev_2018_2024", "validacao_2018_2024"), ("validacao_2025_ja_vista", "validacao_2025")):
        r = res[(res.doenca == doenca) & (res.horizonte == h) & (res.periodo == per)].set_index("modelo")
        if mod in r.index:
            out[rotulo] = {"modelo": r.loc[mod, cols].astype(float).round(4).to_dict(),
                           "persistencia": (r.loc["persistencia", cols].astype(float).round(4).to_dict()
                                            if "persistencia" in r.index else None)}
        if bench is not None:
            b = bench[(bench.doenca == doenca) & (bench.horizonte == h) & (bench.periodo == per)]
            if len(b) and rotulo in out:
                out[rotulo]["auc_infodengue"] = round(float(b["auc_infodengue"].iloc[0]), 4)
    tt = (teste or {}).get(doenca, {}).get(f"h{h}")
    if tt:
        sub = ("mae", "skill", "auc", "brier_skill", "mae_incid_mediana_cidades")
        out["teste_2026"] = {
            "meses": tt.get("meses"),
            "modelo": {k: round(float(tt[k]), 4) for k in sub if tt.get(k) is not None},
            "persistencia": {k: round(float(tt["persistencia"][k]), 4) for k in sub if tt["persistencia"].get(k) is not None},
            "auc_infodengue": round(float(tt["infodengue"]["auc"]), 4) if tt.get("infodengue") else None,
        }
        if t26 is not None and len(t26):
            from src.prediction_service.predictor import aplicar_intervalo
            iv = np.array([aplicar_intervalo(float(p), intervalo_dev) for p in t26["pred"]])
            out["teste_2026"].update({
                "casos_reais": int(t26["y_true"].sum()), "casos_previstos": int(round(t26["pred"].sum())),
                "razao_previsto_real": round(float(t26["pred"].sum() / max(t26["y_true"].sum(), 1)), 3),
                "cobertura_intervalo_90": round(float(np.mean((t26["y_true"] >= iv[:, 0]) & (t26["y_true"] <= iv[:, 1]))), 4),
            })
    return out


def treinar_modelos_risco(panel: pd.DataFrame, exp_dir: Path = OUT_V5, out_dir: Path = OUT_MODELOS_V5,
                          ano_max: int = 2025, horizontes=HORIZONTES, producao: bool = False,
                          dlnm_curvas: Path | None = None) -> dict:
    """
    producao=False: reproduz a v5 (treino até `ano_max`, calibração no OOF 2018–2025).
    producao=True: v5.1 (PROTOCOLO_V5.md, "Produção v5.1") — treino com todos os meses consolidados e
    calibração/intervalo no OOF 2018–2025 + previsões do teste de 2026.
    """
    dec = json.loads((exp_dir / "decisao.json").read_text(encoding="utf-8"))
    res = pd.read_csv(exp_dir / "resultados.csv")
    bench = exp_dir / "benchmark_infodengue.csv"
    bench = pd.read_csv(bench) if bench.exists() else None
    teste = exp_dir / "teste_prospectivo_2026.json"
    teste = json.loads(teste.read_text(encoding="utf-8")) if teste.exists() else None
    if producao:
        from src.prediction_service.data_fetcher import remover_meses_nao_consolidados
        p = remover_meses_nao_consolidados(panel)
    else:
        p = panel[panel["year"] <= ano_max]
    dlnm_curvas = dlnm_curvas or (OUTPUT_DIR / "dlnm" / "curvas_exposicao_resposta.csv")
    todas = {}
    for doenca, info in dec.items():
        alvo = DOENCA_PARA_COL[doenca]
        clima = "parcimonioso" if info["clima"] else "nenhum"
        mod = nome(clima, info["suscetibilidade"])
        dest = out_dir / doenca
        dest.mkdir(parents=True, exist_ok=True)
        obs = p.dropna(subset=[alvo])
        ini, fim = obs.sort_values(["year", "month"]).iloc[[0, -1]][["year", "month"]].astype(int).values
        meta = {"versao": "v5.1" if producao else "v5", "doenca": doenca, "modelo": mod, "clima": clima,
                "suscetibilidade": info["suscetibilidade"], "treinado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                "git_commit": git_commit(), "anos_treino": [int(ini[0]), int(fim[0])],
                "periodo_treino": f"{ini[0]}-{ini[1]:02d} a {fim[0]}-{fim[1]:02d}",
                "calibracao": "OOF 2018–2025 + teste 2026" if producao else "OOF 2018–2025",
                "xgb_params": XGB_PARAMS, "q_risco": Q_RISCO_V5, "eps_incid": EPS_INCID,
                "faixas_probabilidade": FAIXAS_PROB, "horizontes": {}}
        for h in horizontes:
            df = build_ml_features(p, doenca=doenca, horizonte=h).dropna(subset=[alvo])
            df = df[df["populacao"] > 0]
            feats = get_feature_columns(df, doenca=doenca, clima=clima, suscetibilidade=info["suscetibilidade"])
            model, _ = fit_predict_fold(df, df.iloc[:1], feats, alvo, use_pop_offset=True)
            joblib.dump(model, dest / f"h{h}.joblib")
            oof = pd.read_csv(exp_dir / f"oof_{doenca}_h{h}.csv.gz", dtype={"code": str})
            intervalo_dev = calibrar_intervalo(oof["y_true"], oof[f"pred_{mod}"])
            t26 = previsoes_teste_2026(panel, exp_dir, doenca, h)
            esc, risco = oof[f"escore_{mod}"].fillna(0), oof["risco_alto"]
            y_cal, p_cal = oof["y_true"], oof[f"pred_{mod}"]
            if producao and t26 is not None:
                esc, risco = pd.concat([esc, t26["escore"]]), pd.concat([risco, t26["risco_alto"]])
                y_cal, p_cal = pd.concat([y_cal, t26["y_true"]]), pd.concat([p_cal, t26["pred"]])
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(esc, risco)
            joblib.dump(iso, dest / f"h{h}_calibrador.joblib")
            r = res[(res.doenca == doenca) & (res.horizonte == h) & (res.modelo == mod)].set_index("periodo")
            cols = ["mae", "skill", "auc", "brier_skill", "mae_incid_mediana_cidades"]
            meta["horizontes"][f"h{h}"] = {
                "arquivo": f"h{h}.joblib", "calibrador": f"h{h}_calibrador.joblib", "features": feats,
                "intervalo_contagem": calibrar_intervalo(y_cal, p_cal),
                "metricas": {per: r.loc[per, cols].astype(float).round(4).to_dict() for per in r.index},
                "benchmark_infodengue": (bench[(bench.doenca == doenca) & (bench.horizonte == h)].round(4).to_dict("records")
                                         if bench is not None else None),
                "teste_prospectivo_2026": (teste or {}).get(doenca, {}).get(f"h{h}"),
                "desempenho": desempenho(res, bench, teste, doenca, h, mod, t26, intervalo_dev),
            }
            logger.info(f"Risco {doenca} h={h}: {mod}, {len(feats)} features, treino {meta['periodo_treino']}")
        if dlnm_curvas.exists():
            cur = pd.read_csv(dlnm_curvas)
            cur = cur[(cur.doenca == doenca) & (cur.especificacao == "principal") & (cur.variavel == "temp_media")]
            cur[["valor", "rr", "ic_lo", "ic_hi"]].to_csv(dest / "dlnm_curva.csv", index=False)
        hist = p.dropna(subset=[alvo]).assign(_inc=lambda x: x[alvo] / x["populacao"] * 1e5)
        q = hist.groupby("code").agg(p75_incid=("_inc", lambda s: s.quantile(Q_RISCO_V5)),
                                     meses_com_caso=(alvo, lambda s: int((s > 0).sum())),
                                     nome=("city_name", "last"), populacao=("populacao", "last"))
        meta["cidades"] = {str(c): {"nome": r.nome, "populacao": int(r.populacao), "p75_incid": float(r.p75_incid),
                                    "meses_com_caso": int(r.meses_com_caso)} for c, r in q.iterrows()}
        (dest / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        todas[doenca] = meta
    return todas
