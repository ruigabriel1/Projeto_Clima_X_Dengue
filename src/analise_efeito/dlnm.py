"""
DLNM — efeito defasado e não linear do clima sobre a incidência (docs/PROTOCOLO_V5.md, H1).

Modelo (Poisson condicional, pyfixest.fepois):
    casos ~ cb(temp) + cb(prec) + log1p(casos t−1) | cidade×mês-calendário + UF×ano,
    offset = log(pop), erro padrão agrupado por município.

  - EF cidade×mês-calendário: sazonalidade própria de cada cidade (o clima "típico" do mês sai do efeito).
  - EF UF×ano: choques interanuais comuns (sorotipo, imunidade regional, vigilância, ENSO). É o que impede
    que o efeito do clima seja, na verdade, "qual ano foi" — o problema visto no experimento preditivo.
  - Cross-basis: spline natural no valor (nós internos P10/P50/P90, fronteiras no mín./máx. → 4 g.l.)
    × lags 0..3 meses sem restrição → 16 coeficientes por variável.

Resultados: RR acumulado (lags 0–3) por valor vs. a mediana, curva lag-resposta no P90, tabela P10/P90,
e sensibilidades (sem EF UF×ano; sem termo autorregressivo). Período 2015–2025 (2026 fora).
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import BASE_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)

OUT_DLNM = OUTPUT_DIR / "dlnm"
LAG_MAX = 3
ANO_MAX = 2025
ALVOS = {"dengue": "dengue_cases", "chikungunya": "chik_cases"}
VARIAVEIS = {"temp_media": "Temperatura média mensal (°C)", "precipitacao": "Precipitação mensal (mm)"}
ESPECIFICACOES = {
    "principal": {"fe": "code^month + uf^year", "ar": True},
    "sem_ef_ano": {"fe": "code^month", "ar": True},
    "sem_autorregressivo": {"fe": "code^month + uf^year", "ar": False},
}


# ------------------------------------------------------------------ base de spline natural
class SplineNatural:
    """Base de spline cúbica natural (ESL eq. 5.4–5.5), sem intercepto. len(base) = n_nós − 1."""

    def __init__(self, x: np.ndarray, quantis=(0.10, 0.50, 0.90)):
        x = np.asarray(x, float)
        x = x[np.isfinite(x)]
        self.nos = np.concatenate([[x.min()], np.quantile(x, quantis), [x.max()]])

    def _d(self, x, k):
        nk, nK = self.nos[k], self.nos[-1]
        return (np.maximum(x - nk, 0) ** 3 - np.maximum(x - nK, 0) ** 3) / (nK - nk)

    def base(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, float)
        K = len(self.nos)
        cols = [x] + [self._d(x, k) - self._d(x, K - 2) for k in range(K - 2)]
        return np.column_stack(cols)

    @property
    def gl(self) -> int:
        return len(self.nos) - 1


def cross_basis(df: pd.DataFrame, var: str, spline: SplineNatural, lag_max: int = LAG_MAX) -> pd.DataFrame:
    """Colunas cb_<var>_b<j>_l<l> = B_j(x_{t−l}) por cidade (df ordenado por code, year, month)."""
    g = df.groupby("code", sort=False)[var]
    cols = {}
    for l in range(lag_max + 1):
        xl = g.shift(l).to_numpy(float)
        B = spline.base(np.nan_to_num(xl, nan=np.nanmedian(df[var])))
        B[~np.isfinite(xl)] = np.nan
        for j in range(B.shape[1]):
            cols[f"cb_{var}_b{j}_l{l}"] = B[:, j]
    return pd.DataFrame(cols, index=df.index)


# ------------------------------------------------------------------ ajuste
def preparar(panel: pd.DataFrame, doenca: str) -> tuple[pd.DataFrame, dict]:
    alvo = ALVOS[doenca]
    d = panel[(panel["year"] <= ANO_MAX)].sort_values(["code", "year", "month"]).reset_index(drop=True)
    d = d[d["populacao"].notna() & (d["populacao"] > 0)].copy()
    d["uf"] = d["code"].astype(str).str[:2]
    d["y"] = d[alvo]
    d["log_pop"] = np.log(d["populacao"])
    d["ar_log1p"] = np.log1p(d.groupby("code", sort=False)["y"].shift(1))
    splines = {v: SplineNatural(d[v].to_numpy()) for v in VARIAVEIS}
    cbs = [cross_basis(d, v, splines[v]) for v in VARIAVEIS]
    d = pd.concat([d] + cbs, axis=1)
    cols = [c for cb in cbs for c in cb.columns]
    d = d.dropna(subset=["y", "ar_log1p"] + cols)
    return d, splines


def ajustar(d: pd.DataFrame, espec: str):
    import pyfixest as pf

    cfg = ESPECIFICACOES[espec]
    cbcols = [c for c in d.columns if c.startswith("cb_")]
    rhs = " + ".join(cbcols + (["ar_log1p"] if cfg["ar"] else []))
    return pf.fepois(f"y ~ {rhs} | {cfg['fe']}", data=d, offset="log_pop", vcov={"CRV1": "code"})


# ------------------------------------------------------------------ RR
def _coef_cov(fit, var: str, gl: int):
    nomes = [f"cb_{var}_b{j}_l{l}" for l in range(LAG_MAX + 1) for j in range(gl)]
    b = fit.coef()[nomes].to_numpy()
    V = fit._vcov
    idx = [list(fit.coef().index).index(n) for n in nomes]
    return b, V[np.ix_(idx, idx)]


def rr_acumulado(fit, var: str, spline: SplineNatural, grade: np.ndarray, ref: float) -> pd.DataFrame:
    """RR acumulado (soma dos lags 0..L) de cada valor da grade vs. ref, com IC 95%."""
    gl = spline.gl
    b, V = _coef_cov(fit, var, gl)
    dB = spline.base(grade) - spline.base(np.array([ref]))        # (n, gl)
    G = np.tile(dB, (1, LAG_MAX + 1))                              # mesma diferença em todos os lags
    lrr = G @ b
    se = np.sqrt(np.einsum("ij,jk,ik->i", G, V, G))
    return pd.DataFrame({"valor": grade, "rr": np.exp(lrr), "ic_lo": np.exp(lrr - 1.96 * se), "ic_hi": np.exp(lrr + 1.96 * se)})


def rr_por_lag(fit, var: str, spline: SplineNatural, valor: float, ref: float) -> pd.DataFrame:
    gl = spline.gl
    b, V = _coef_cov(fit, var, gl)
    dB = (spline.base(np.array([valor])) - spline.base(np.array([ref])))[0]
    linhas = []
    for l in range(LAG_MAX + 1):
        g = np.zeros(len(b))
        g[l * gl:(l + 1) * gl] = dB
        lrr, se = g @ b, float(np.sqrt(g @ V @ g))
        linhas.append({"lag": l, "rr": np.exp(lrr), "ic_lo": np.exp(lrr - 1.96 * se), "ic_hi": np.exp(lrr + 1.96 * se)})
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ execução
def run(panel: pd.DataFrame | None = None, out_dir: Path = OUT_DLNM, doencas=tuple(ALVOS), especs=tuple(ESPECIFICACOES)):
    out_dir.mkdir(parents=True, exist_ok=True)
    if panel is None:
        from src.ml_pipeline.data_ingestion import build_base_panel
        panel = build_base_panel(BASE_DIR)
    panel = panel[panel["year"] <= ANO_MAX]
    tabela, curvas, lags = [], [], []
    for doenca in doencas:
        d, splines = preparar(panel, doenca)
        for espec in especs:
            t0 = time.time()
            fit = ajustar(d, espec)
            logger.info(f"DLNM {doenca}/{espec}: n={fit._N}, {time.time() - t0:.0f}s")
            for var in VARIAVEIS:
                x = d[var]
                p10, p50, p90 = np.quantile(x, [0.10, 0.50, 0.90])
                grade = np.linspace(*np.quantile(x, [0.01, 0.99]), 60)
                cur = rr_acumulado(fit, var, splines[var], grade, p50).assign(doenca=doenca, especificacao=espec, variavel=var)
                curvas.append(cur)
                pts = rr_acumulado(fit, var, splines[var], np.array([p10, p90]), p50)
                for rotulo, (_, r) in zip(("P10", "P90"), pts.iterrows()):
                    tabela.append({"doenca": doenca, "especificacao": espec, "variavel": var, "ponto": rotulo,
                                   "valor": round(r.valor, 2), "referencia_mediana": round(p50, 2),
                                   "rr": r.rr, "ic_lo": r.ic_lo, "ic_hi": r.ic_hi, "n_obs": int(fit._N)})
                lags.append(rr_por_lag(fit, var, splines[var], p90, p50).assign(doenca=doenca, especificacao=espec, variavel=var))
    tab, cur, lag = pd.DataFrame(tabela), pd.concat(curvas), pd.concat(lags)
    tab.to_csv(out_dir / "rr_p10_p90.csv", index=False)
    cur.to_csv(out_dir / "curvas_exposicao_resposta.csv", index=False)
    lag.to_csv(out_dir / "curvas_lag_resposta_p90.csv", index=False)
    plotar(cur, lag, out_dir)
    (out_dir / "relatorio.md").write_text(relatorio(tab), encoding="utf-8")
    logger.info(f"DLNM concluído → {out_dir}")
    return tab


def plotar(cur: pd.DataFrame, lag: pd.DataFrame, out_dir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for doenca in cur["doenca"].unique():
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        for i, var in enumerate(VARIAVEIS):
            ax = axes[0, i]
            for espec, estilo in (("principal", "-"), ("sem_ef_ano", "--")):
                c = cur[(cur.doenca == doenca) & (cur.variavel == var) & (cur.especificacao == espec)]
                ax.plot(c.valor, c.rr, estilo, color="#1f4e79" if espec == "principal" else "#c0504d",
                        label="Principal (EF UF×ano)" if espec == "principal" else "Sem EF de ano")
                if espec == "principal":
                    ax.fill_between(c.valor, c.ic_lo, c.ic_hi, color="#1f4e79", alpha=0.15)
            ax.axhline(1, color="black", lw=0.8)
            ax.set_xlabel(VARIAVEIS[var]); ax.set_ylabel("RR acumulado (lags 0–3) vs. mediana")
            ax.legend(fontsize=8, frameon=False)
            ax = axes[1, i]
            lg = lag[(lag.doenca == doenca) & (lag.variavel == var) & (lag.especificacao == "principal")]
            ax.errorbar(lg.lag, lg.rr, yerr=[lg.rr - lg.ic_lo, lg.ic_hi - lg.rr], fmt="o-", color="#1f4e79", capsize=3)
            ax.axhline(1, color="black", lw=0.8)
            ax.set_xticks(range(LAG_MAX + 1)); ax.set_xlabel("Defasagem (meses)"); ax.set_ylabel("RR no P90 vs. mediana")
        fig.suptitle(f"{doenca.capitalize()} — efeito do clima (DLNM, Poisson condicional, 2015–2025)")
        fig.tight_layout()
        fig.savefig(out_dir / f"dlnm_{doenca}.png", dpi=130)
        plt.close(fig)


def relatorio(tab: pd.DataFrame) -> str:
    md = ["# DLNM — efeito do clima sobre a incidência (2015–2025)\n",
          "RR acumulado nos lags 0–3 meses, no P10 e no P90 da variável, em relação à mediana. "
          "Principal: EF cidade×mês + UF×ano, termo autorregressivo, offset log(pop), EP agrupado por município.\n",
          "| Doença | Especificação | Variável | Ponto | Valor | Mediana | RR | IC 95% |", "|---|---|---|---|---|---|---|---|"]
    for x in tab.itertuples():
        md.append(f"| {x.doenca} | {x.especificacao} | {x.variavel} | {x.ponto} | {x.valor} | {x.referencia_mediana} | "
                  f"{x.rr:.3f} | [{x.ic_lo:.3f}, {x.ic_hi:.3f}] |")
    md.append("\n![dengue](dlnm_dengue.png)\n![chikungunya](dlnm_chikungunya.png)")
    return "\n".join(md)


def main(argv=None):
    from src.ml_pipeline.experimento_horizontes import configurar_log
    ap = argparse.ArgumentParser(description="DLNM do efeito do clima (protocolo v5, H1)")
    ap.add_argument("--doenca", choices=list(ALVOS) + ["todas"], default="todas")
    a = ap.parse_args(argv)
    configurar_log()
    run(doencas=tuple(ALVOS) if a.doenca == "todas" else (a.doenca,))


if __name__ == "__main__":
    main()
