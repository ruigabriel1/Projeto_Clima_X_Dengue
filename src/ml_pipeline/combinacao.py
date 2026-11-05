"""
Combinação modelo + persistência (docs/PROTOCOLO_V5.md, desvio de 2026-11-04, noite).

    casos_comb = w · casos_modelo + (1 − w) · casos[t−h],   w ∈ {0,0; 0,1; …; 1,0}

- Validação (OOF 2018–2024): o peso do ano Y é escolhido só com os anos < Y (cross-fitting temporal);
  2018 usa w = 1 (modelo puro), por não ter passado.
- 2025 (segunda validação, já vista) usa o peso escolhido com 2018–2024.
- Peso final (produção e teste de 2026): escolhido com 2018–2025.
- O escore de risco vem da incidência combinada, com a mesma calibração isotônica temporal.
- Regra: a combinação substitui o modelo puro se reduzir o MAE com IC 95% < 0 em ≥ 2 dos 3 horizontes.

Saídas em output/experimento_v5/: combinacao.csv, combinacao_efeitos.csv, combinacao.json, combinacao.md
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import HORIZONTES
from src.ml_pipeline.analise_experimento import bootstrap_delta_mae
from src.ml_pipeline.experimento_v5 import ANO_FIM_DEV, EPS_INCID, OUT_V5, calibrar_temporal, metricas

logger = logging.getLogger(__name__)

PESOS = np.round(np.arange(0.0, 1.0001, 0.1), 1)


def combinar(modelo, persistencia, w) -> np.ndarray:
    """w · modelo + (1 − w) · persistência; persistência ausente conta como zero casos. w pode ser vetor."""
    w = np.asarray(w, float)
    return w * np.asarray(modelo, float) + (1 - w) * np.nan_to_num(np.asarray(persistencia, float))


def escolher_peso(y, modelo, persistencia) -> float:
    """Peso com menor MAE na grade; empate fica com o maior peso do modelo."""
    y = np.asarray(y, float)
    maes = [np.mean(np.abs(y - combinar(modelo, persistencia, w))) for w in PESOS]
    melhor = min(maes)
    return float(max(w for w, m in zip(PESOS, maes) if np.isclose(m, melhor)))


def pesos_cross_fit(oof: pd.DataFrame, col_modelo: str) -> dict[int, float]:
    """Peso por ano de teste, escolhido só com os anos anteriores."""
    out = {}
    for ano in sorted(oof["year"].unique()):
        ant = oof[oof["year"] < ano]
        out[int(ano)] = 1.0 if ant.empty else escolher_peso(ant["y_true"], ant[col_modelo], ant["y_persistencia"])
    return out


def aplicar(oof: pd.DataFrame, col_modelo: str) -> tuple[pd.DataFrame, dict]:
    """Acrescenta peso_comb, pred_comb, escore_comb e prob_comb ao OOF. Retorna (oof, pesos por ano)."""
    dev = oof[oof["year"] <= ANO_FIM_DEV]
    pesos = pesos_cross_fit(dev, col_modelo)
    apos_dev = escolher_peso(dev["y_true"], dev[col_modelo], dev["y_persistencia"])   # usado em 2025
    oof = oof.copy()
    oof["peso_comb"] = oof["year"].map(lambda a: pesos.get(int(a), apos_dev)).astype(float)
    oof["pred_comb"] = combinar(oof[col_modelo], oof["y_persistencia"], oof["peso_comb"])
    oof["escore_comb"] = (oof["pred_comb"] / oof["pop"] * 1e5) / (oof["p75_incid"] + EPS_INCID)
    oof["prob_comb"] = calibrar_temporal(oof, "escore_comb")
    return oof, {**pesos, "apos_dev": apos_dev}


def run(exp_dir: Path = OUT_V5, horizontes=HORIZONTES) -> dict:
    dec = json.loads((exp_dir / "decisao.json").read_text(encoding="utf-8"))
    linhas, efeitos, saida = [], [], {}
    for doenca, info in dec.items():
        mod = info["modelo"]
        col = f"pred_{mod}"
        saida[doenca] = {"modelo_base": mod, "horizontes": {}}
        for h in horizontes:
            oof = pd.read_csv(exp_dir / f"oof_{doenca}_h{h}.csv.gz", dtype={"code": str})
            oof, pesos = aplicar(oof, col)
            oof.to_csv(exp_dir / f"oof_{doenca}_h{h}.csv.gz", index=False)
            dev, v25 = oof[oof["year"] <= ANO_FIM_DEV], oof[oof["year"] > ANO_FIM_DEV]
            for periodo, g in (("dev_2018_2024", dev), ("validacao_2025_ja_vista", v25)):
                if g.empty:
                    continue
                for previsor, cp, ce, cpr in (("modelo", col, f"escore_{mod}", f"prob_{mod}"),
                                              ("combinacao", "pred_comb", "escore_comb", "prob_comb"),
                                              ("persistencia", "y_persistencia", "escore_persistencia", "prob_persistencia")):
                    linhas.append({"doenca": doenca, "horizonte": h, "periodo": periodo, "previsor": previsor,
                                   **metricas(g, cp, ce, cpr)})
            d, lo, hi = bootstrap_delta_mae(dev, "pred_comb", col)
            efeitos.append({"doenca": doenca, "horizonte": h, "delta_mae": d, "ic95_lo": lo, "ic95_hi": hi,
                            "delta_pct": 100 * d / (dev["y_true"] - dev[col]).abs().mean(), "reduz_erro": bool(hi < 0)})
            final = escolher_peso(oof["y_true"], oof[col], oof["y_persistencia"])   # 2018–2025 → produção e 2026
            saida[doenca]["horizontes"][f"h{h}"] = {"pesos_cross_fit": pesos, "peso_final": final}
            logger.info(f"Combinação {doenca} h={h}: pesos={pesos} final={final} ΔMAE={d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    ef = pd.DataFrame(efeitos)
    for doenca in saida:
        saida[doenca]["usar_combinacao"] = bool(ef.loc[ef["doenca"] == doenca, "reduz_erro"].sum() >= 2)
    res = pd.DataFrame(linhas)
    res.to_csv(exp_dir / "combinacao.csv", index=False)
    ef.to_csv(exp_dir / "combinacao_efeitos.csv", index=False)
    (exp_dir / "combinacao.json").write_text(json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8")
    (exp_dir / "combinacao.md").write_text(relatorio(res, ef, saida), encoding="utf-8")
    return saida


def relatorio(res: pd.DataFrame, ef: pd.DataFrame, saida: dict) -> str:
    def f(v, n=3):
        return "—" if pd.isna(v) else f"{v:.{n}f}"
    md = ["# Combinação modelo + persistência (desvio pré-registrado de 2026-11-04)\n",
          "Pesos escolhidos só com anos anteriores (cross-fitting temporal). 2025 já foi visto na v4.\n"]
    for d, s in saida.items():
        md += [f"\n## {d.capitalize()} (modelo base `{s['modelo_base']}`)\n",
               "| período | h | previsor | MAE | Skill | MAE incid. (mediana) | AUC | Brier skill |", "|---|---|---|---|---|---|---|---|"]
        for x in res[res.doenca == d].sort_values(["periodo", "horizonte", "previsor"]).itertuples():
            md.append(f"| {x.periodo} | {x.horizonte} | {x.previsor} | {f(x.mae, 2)} | {f(x.skill)} | "
                      f"{f(x.mae_incid_mediana_cidades, 1)} | {f(x.auc)} | {f(getattr(x, 'brier_skill', np.nan))} |")
        md += ["\n| h | peso final do modelo (2018–2025) | ΔMAE combinação − modelo (dev) | IC 95% | reduz erro? |",
               "|---|---|---|---|---|"]
        for x in ef[ef.doenca == d].itertuples():
            w = s["horizontes"][f"h{x.horizonte}"]["peso_final"]
            md.append(f"| {x.horizonte} | {w:.1f} | {x.delta_mae:+.3f} ({x.delta_pct:+.1f}%) | "
                      f"[{x.ic95_lo:+.3f}, {x.ic95_hi:+.3f}] | {'sim' if x.reduz_erro else 'não'} |")
        md.append(f"\n**Decisão:** {'a combinação substitui o modelo puro' if s['usar_combinacao'] else 'fica o modelo puro'}.")
    return "\n".join(md)


if __name__ == "__main__":
    from src.ml_pipeline.experimento_horizontes import configurar_log
    configurar_log()
    print(json.dumps(run(), indent=2, ensure_ascii=False))
