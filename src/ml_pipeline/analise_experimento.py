"""
Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md).

Lê output/experimento/{resultados.csv, resultados_por_ano.csv, oof_*.csv.gz} e produz:
  analise.md              tabela comparativa, efeito do clima e do corte, SHAP, recomendação
  efeito_clima.csv        ΔMAE (com − sem clima) por doença × horizonte × corte, IC 95% bootstrap por cidade
  shap_<doenca>_h<h>.csv  ranking SHAP (modelo com clima, treino 2015–2024)
  skill_por_horizonte.png gráfico do Skill Score por horizonte
  config_escolhida.json   configuração sugerida por doença (precisa de confirmação humana)

REGRA DE DECISÃO (registrada antes de ver os resultados completos — não alterar depois):
  Para cada doença, olhando a média dos 3 horizontes no OOF 2018–2024:
  1. Clima: usar_clima = True somente se o Skill Score médio COM clima superar o SEM clima
     em mais de 0,01 (1 ponto percentual), comparando com o mesmo tratamento de corte.
     Caso contrário, fica o modelo sem clima (parcimônia: menos dados de entrada, menos falhas).
  2. Corte P99: corte_p99 = True somente se reduzir o MAE médio em mais de 1% SEM reduzir
     o R² médio em mais de 0,01. Caso contrário, sem corte (sem transformação do alvo).
  Hiperparâmetros não são escolhidos (fixos).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import ANO_HOLDOUT, DOENCAS_EXPERIMENTO, HORIZONTES, OUTPUT_EXPERIMENTO, BASE_DIR
from src.ml_pipeline.experimento_horizontes import CLIP_PERCENTIL, configurar_log, nome_config, preparar_dados

logger = logging.getLogger(__name__)

LIMIAR_SKILL_CLIMA = 0.01
LIMIAR_MAE_CORTE = 0.01
LIMIAR_R2_CORTE = 0.01
N_BOOT = 1000


# ------------------------------------------------------------------ efeito do clima
def bootstrap_delta_mae(oof: pd.DataFrame, col_a: str, col_b: str, n_boot: int = N_BOOT, seed: int = 42):
    """
    ΔMAE = MAE(a) − MAE(b) com IC 95% por bootstrap de CIDADES (preserva a dependência
    temporal dentro de cada cidade). Negativo = 'a' erra menos.
    """
    g = oof.assign(
        ea=(oof["y_true"] - oof[col_a]).abs(),
        eb=(oof["y_true"] - oof[col_b]).abs(),
    ).groupby("code")[["ea", "eb"]].agg(["sum", "count"])
    sa, sb, n = g[("ea", "sum")].to_numpy(), g[("eb", "sum")].to_numpy(), g[("ea", "count")].to_numpy()
    delta = (sa.sum() - sb.sum()) / n.sum()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(n), size=(n_boot, len(n)))
    boot = (sa[idx].sum(1) - sb[idx].sum(1)) / n[idx].sum(1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(delta), float(lo), float(hi)


def tabela_efeito_clima(out_dir: Path, doencas, horizontes) -> pd.DataFrame:
    linhas = []
    for d in doencas:
        for h in horizontes:
            f = out_dir / f"oof_{d}_h{h}.csv.gz"
            if not f.exists():
                continue
            oof = pd.read_csv(f, dtype={"code": str})
            for corte in (True, False):
                a = f"pred_{nome_config(True, corte)}"
                b = f"pred_{nome_config(False, corte)}"
                delta, lo, hi = bootstrap_delta_mae(oof, a, b)
                mae_b = (oof["y_true"] - oof[b]).abs().mean()
                linhas.append({
                    "doenca": d, "horizonte": h, "corte_p99": corte,
                    "delta_mae_clima": delta, "ic95_lo": lo, "ic95_hi": hi,
                    "delta_mae_pct": 100 * delta / mae_b,
                    "clima_significativo": bool(hi < 0 or lo > 0),
                    "clima_ajuda": bool(hi < 0),
                })
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ decisão
def decidir_config(res: pd.DataFrame, doenca: str) -> dict:
    """Aplica a regra de decisão registrada no docstring do módulo."""
    r = res[(res["doenca"] == doenca) & res["modelo"].str.startswith("xgb_")]
    medias = r.groupby(["usar_clima", "corte_p99"])[["skill_score", "mae", "r2"]].mean()

    ganhos_clima = {
        corte: medias.loc[(True, corte), "skill_score"] - medias.loc[(False, corte), "skill_score"]
        for corte in (True, False)
    }
    usar_clima = bool(max(ganhos_clima.values()) > LIMIAR_SKILL_CLIMA)

    com, sem = medias.loc[(usar_clima, True)], medias.loc[(usar_clima, False)]
    reducao_mae = (sem["mae"] - com["mae"]) / sem["mae"]
    perda_r2 = sem["r2"] - com["r2"]
    corte_p99 = bool(reducao_mae > LIMIAR_MAE_CORTE and perda_r2 <= LIMIAR_R2_CORTE)

    escolhido = r[(r["usar_clima"] == usar_clima) & (r["corte_p99"] == corte_p99)]
    return {
        "usar_clima": usar_clima,
        "corte_p99": corte_p99,
        "modelo": nome_config(usar_clima, corte_p99),
        "ganho_skill_clima_medio": {("p99" if k else "semcorte"): round(float(v), 4) for k, v in ganhos_clima.items()},
        "corte_reducao_mae_pct": round(float(100 * reducao_mae), 2),
        "corte_perda_r2": round(float(perda_r2), 4),
        "metricas_dev_por_horizonte": escolhido.set_index("horizonte")[
            ["mae", "r2", "mae_surto", "pico_medio_surto", "skill_score", "auc_risco_alto", "passa_todos"]
        ].round(4).to_dict(orient="index"),
    }


# ------------------------------------------------------------------ SHAP
def shap_clima(panel: pd.DataFrame, doenca: str, h: int, corte: bool, n_amostra: int = 20000) -> pd.DataFrame:
    """Treina o modelo COM clima em 2015–2024 e devolve o ranking SHAP (média |SHAP|)."""
    from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, get_feature_columns, is_climate_feature
    from src.ml_pipeline.interpretability import compute_shap_values
    from src.ml_pipeline.model_training import fit_predict_fold

    alvo = DOENCA_PARA_COL[doenca]
    df = preparar_dados(panel, doenca, h, ANO_HOLDOUT - 1)
    feats = get_feature_columns(df, doenca=doenca, usar_clima=True)
    model, _ = fit_predict_fold(df, df.iloc[:1], feats, alvo, CLIP_PERCENTIL if corte else None)
    amostra = df[df["year"] >= ANO_HOLDOUT - 3]
    amostra = amostra.sample(min(n_amostra, len(amostra)), random_state=42)
    sv = compute_shap_values(model, amostra[feats])
    rank = (sv.drop(columns="bias").abs().mean().sort_values(ascending=False)
            .rename("mean_abs_shap").reset_index().rename(columns={"index": "feature"}))
    rank["rank"] = np.arange(1, len(rank) + 1)
    rank["clima"] = rank["feature"].map(is_climate_feature)
    rank["share"] = rank["mean_abs_shap"] / rank["mean_abs_shap"].sum()
    return rank


# ------------------------------------------------------------------ diagnóstico exploratório
def diagnostico_grupos_clima(panel: pd.DataFrame, doencas=DOENCAS_EXPERIMENTO, horizontes=(1, 3)) -> pd.DataFrame:
    """
    EXPLORATÓRIO — não entra na regra de decisão. Mede qual grupo de variáveis climáticas
    move o erro (OOF 2018–2024, sem corte): ENSO é um índice único por mês para todas as
    cidades e pode funcionar como "identificador de ano", favorecendo memorização de surtos.
    """
    from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, get_feature_columns, is_climate_feature
    from src.ml_pipeline.model_training import _expanding_window_splits, fit_predict_fold

    linhas = []
    for doenca in doencas:
        alvo = DOENCA_PARA_COL[doenca]
        for h in horizontes:
            df = preparar_dados(panel, doenca, h, ANO_HOLDOUT - 1)
            todas = get_feature_columns(df, doenca=doenca, usar_clima=True)
            sem = get_feature_columns(df, doenca=doenca, usar_clima=False)
            clima = [c for c in todas if is_climate_feature(c)]
            grupos = {
                "sem_clima": sem,
                "clima_completo": todas,
                "clima_sem_enso": sem + [c for c in clima if not c.startswith("enso_")],
                "so_enso": sem + [c for c in clima if c.startswith("enso_")],
                "so_temp_prec_local": sem + [c for c in clima if c.startswith(("temp_lag", "prec_lag", "prec_acum", "graus_dia"))],
            }
            for nome, feats in grupos.items():
                err, n = 0.0, 0
                for tr, te, _ in _expanding_window_splits(df["year"], 3, ANO_HOLDOUT - 1):
                    _, p = fit_predict_fold(df[tr], df[te], feats, alvo)
                    err += float((df.loc[te, alvo] - p).abs().sum())
                    n += int(te.sum())
                linhas.append({"doenca": doenca, "horizonte": h, "variante": nome, "n_features": len(feats), "mae": err / n})
                logger.info(f"Diagnóstico {doenca} h={h} {nome}: MAE={err / n:.3f}")
    out = pd.DataFrame(linhas)
    out["delta_vs_sem_clima_pct"] = out.groupby(["doenca", "horizonte"])["mae"].transform(
        lambda s: 100 * (s / s.iloc[0] - 1)
    )
    return out


# ------------------------------------------------------------------ gráfico
def plot_skill(res: pd.DataFrame, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    doencas = list(res["doenca"].unique())
    fig, axes = plt.subplots(1, len(doencas), figsize=(5.5 * len(doencas), 4), sharey=True, squeeze=False)
    estilos = {
        "xgb_clima_semcorte": ("#1f77b4", "-", "Com clima"),
        "xgb_semclima_semcorte": ("#ff7f0e", "-", "Sem clima"),
        "xgb_clima_p99": ("#1f77b4", ":", "Com clima + P99"),
        "xgb_semclima_p99": ("#ff7f0e", ":", "Sem clima + P99"),
        "sazonal": ("#7f7f7f", "--", "Sazonal (t−12)"),
    }
    for ax, d in zip(axes[0], doencas):
        for modelo, (cor, ls, lab) in estilos.items():
            s = res[(res["doenca"] == d) & (res["modelo"] == modelo)].sort_values("horizonte")
            ax.plot(s["horizonte"], s["skill_score"], ls, color=cor, marker="o", label=lab)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(d.capitalize())
        ax.set_xlabel("Horizonte (meses)")
        ax.set_xticks(sorted(res["horizonte"].unique()))
        ax.grid(alpha=0.3)
    axes[0][0].set_ylabel("Skill Score vs. persistência")
    axes[0][-1].legend(fontsize=8, frameon=False)
    fig.suptitle("Ganho sobre a persistência (OOF 2018–2024) — acima de 0 = agrega valor")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# ------------------------------------------------------------------ relatório
def _fmt(v, nd=3):
    return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{nd}f}"


def tabela_md(res: pd.DataFrame, doenca: str) -> str:
    r = res[res["doenca"] == doenca].sort_values(["horizonte", "modelo"])
    out = ["| h | Modelo | MAE | R² | MAE-surto (% pico) | Skill | AUC | Passa todos |",
           "|---|---|---|---|---|---|---|---|"]
    for _, x in r.iterrows():
        pct = 100 * x["mae_surto"] / x["pico_medio_surto"] if x["pico_medio_surto"] else np.nan
        out.append(
            f"| {x['horizonte']} | {x['modelo']} | {_fmt(x['mae'], 2)} | {_fmt(x['r2'])} | "
            f"{_fmt(x['mae_surto'], 1)} ({_fmt(pct, 0)}%) | {_fmt(x['skill_score'])} | "
            f"{_fmt(x['auc_risco_alto'])} | {'✅' if x['passa_todos'] else '❌'} |"
        )
    return "\n".join(out)


def run_analise(
    out_dir: Path = OUTPUT_EXPERIMENTO,
    com_shap: bool = True,
    panel: pd.DataFrame | None = None,
    diagnostico: bool = False,
):
    res = pd.read_csv(out_dir / "resultados.csv")
    doencas = [d for d in DOENCAS_EXPERIMENTO if d in set(res["doenca"])]
    horizontes = sorted(res["horizonte"].unique())

    efeito = tabela_efeito_clima(out_dir, doencas, horizontes)
    efeito.to_csv(out_dir / "efeito_clima.csv", index=False)
    plot_skill(res, out_dir / "skill_por_horizonte.png")

    decisoes = {d: decidir_config(res, d) for d in doencas}

    shap_txt = {}
    if com_shap:
        from src.ml_pipeline.data_ingestion import build_base_panel
        panel = panel if panel is not None else build_base_panel(BASE_DIR)
        for d in doencas:
            linhas = []
            for h in horizontes:
                rank = shap_clima(panel, d, h, decisoes[d]["corte_p99"])
                rank.to_csv(out_dir / f"shap_{d}_h{h}.csv", index=False)
                top_clima = rank[rank["clima"]].head(1)
                linhas.append(
                    f"| {h} | {rank['clima'].sum()} | {100 * rank.loc[rank['clima'], 'share'].sum():.1f}% | "
                    + (f"{top_clima['feature'].iloc[0]} (#{int(top_clima['rank'].iloc[0])})" if len(top_clima) else "—")
                    + f" | {', '.join(rank['feature'].head(5))} |"
                )
                decisoes[d].setdefault("shap", {})[f"h{h}"] = {
                    "pct_shap_clima": round(float(100 * rank.loc[rank["clima"], "share"].sum()), 2),
                    "melhor_feature_clima": top_clima["feature"].iloc[0] if len(top_clima) else None,
                    "rank_melhor_feature_clima": int(top_clima["rank"].iloc[0]) if len(top_clima) else None,
                }
            shap_txt[d] = (
                "| h | nº features clima | % do |SHAP| total vindo do clima | melhor feature de clima (rank) | top 5 |\n"
                "|---|---|---|---|---|\n" + "\n".join(linhas)
            )

    # ---------- relatório markdown ----------
    md = [
        "# Fase 2 — Análise do experimento (OOF 2018–2024, holdout 2025 intocado)\n",
        "Métricas calculadas no conjunto agregado de todos os folds de validação (expanding window). "
        "Surto = mês acima do P90 da própria cidade (treino); risco alto = acima da mediana da cidade (treino). "
        "Skill = ganho de MAE sobre a persistência no mesmo horizonte (casos[t−h]).\n",
        "Critérios: MAE < persistência · R² > 0,40 (dengue) · MAE-surto < 50% do pico médio · Skill > 0 · AUC > 0,75.\n",
        "![Skill por horizonte](skill_por_horizonte.png)\n",
    ]
    for d in doencas:
        dec = decisoes[d]
        ef = efeito[efeito["doenca"] == d]
        md += [f"\n## {d.capitalize()}\n", tabela_md(res, d), "\n",
               "### Efeito do clima (ΔMAE = com clima − sem clima; negativo = clima ajuda)\n",
               "| h | corte P99 | ΔMAE | IC 95% (bootstrap por cidade) | Δ% | Conclusão |",
               "|---|---|---|---|---|---|"]
        for _, x in ef.iterrows():
            concl = "clima ajuda" if x["clima_ajuda"] else ("clima piora" if x["clima_significativo"] else "sem diferença")
            md.append(
                f"| {x['horizonte']} | {'sim' if x['corte_p99'] else 'não'} | {x['delta_mae_clima']:+.3f} | "
                f"[{x['ic95_lo']:+.3f}, {x['ic95_hi']:+.3f}] | {x['delta_mae_pct']:+.1f}% | {concl} |"
            )
        if d in shap_txt:
            md += ["\n### SHAP do modelo com clima (treino 2015–2024, amostra 2022–2024)\n", shap_txt[d]]
        md += [
            "\n### Configuração sugerida pela regra pré-registrada\n",
            f"- **{dec['modelo']}** (clima={'sim' if dec['usar_clima'] else 'não'}, "
            f"corte P99={'sim' if dec['corte_p99'] else 'não'})",
            f"- Ganho médio de Skill com clima: {dec['ganho_skill_clima_medio']} (limiar {LIMIAR_SKILL_CLIMA})",
            f"- Corte P99: redução de MAE {dec['corte_reducao_mae_pct']}%, perda de R² {dec['corte_perda_r2']}",
        ]
    diag_path = out_dir / "diagnostico_clima_exploratorio.csv"
    if diagnostico:
        if panel is None:
            from src.ml_pipeline.data_ingestion import build_base_panel
            panel = build_base_panel(BASE_DIR)
        diagnostico_grupos_clima(panel, doencas).to_csv(diag_path, index=False)
    if diag_path.exists():
        dg = pd.read_csv(diag_path)
        md += ["\n## Diagnóstico exploratório: qual grupo de clima move o erro? (NÃO usado na decisão)\n",
               "MAE no OOF 2018–2024, sem corte. Δ% relativo ao modelo sem clima (negativo = melhora).\n",
               "| Doença | h | Variante | nº features | MAE | Δ% vs sem clima |", "|---|---|---|---|---|---|"]
        md += [f"| {x.doenca} | {x.horizonte} | {x.variante} | {x.n_features} | {x.mae:.3f} | "
               f"{x.delta_vs_sem_clima_pct:+.1f}% |" for x in dg.itertuples()]

    md += [
        "\n## Regra de decisão (pré-registrada)\n",
        f"1. Clima entra só se o Skill médio (3 horizontes) com clima superar o sem clima em > {LIMIAR_SKILL_CLIMA}.",
        f"2. Corte P99 entra só se reduzir o MAE médio em > {100 * LIMIAR_MAE_CORTE:.0f}% sem perder > {LIMIAR_R2_CORTE} de R².",
        "\n> A configuração acima é uma **sugestão**. Revise e confirme antes de rodar "
        "`python main.py teste-final --confirmar` — o holdout 2025 só pode ser usado uma vez.",
    ]
    (out_dir / "analise.md").write_text("\n".join(md), encoding="utf-8")

    cfg = {"confirmado_pelo_usuario": False, "regra": "ver analise_experimento.py", "doencas": decisoes}
    (out_dir / "config_escolhida.json").write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    logger.info(f"Análise gravada em {out_dir / 'analise.md'}")
    return decisoes, efeito


if __name__ == "__main__":
    configurar_log()
    run_analise()
