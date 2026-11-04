"""
Fase 3 — Teste final no ano de 2025 (docs/PLANO_EXPERIMENTO_FINAL.md).

  - Usa a configuração de output/experimento/config_escolhida.json (Fase 2).
  - Treina em 2015–2024 e testa em 2025, nos 3 horizontes, com as 5 métricas.
  - Reporta junto as métricas de desenvolvimento (OOF 2018–2024) para detectar overfitting
    à validação. Nada é ajustado depois.
  - O holdout só pode ser usado UMA vez: exige --confirmar e grava uma trava
    (teste_final_2025.lock). Rodar de novo exige --forcar e fica registrado no relatório.

Saídas: output/experimento/teste_final_2025.{json,md}, oof_2025_<doenca>_h<h>.csv.gz
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import pandas as pd

from src.config import ANO_HOLDOUT, BASE_DIR, HORIZONTES, OUTPUT_EXPERIMENTO
from src.ml_pipeline.experimento_horizontes import (
    CLIP_PERCENTIL, configurar_log, git_commit, nome_config, preparar_dados,
)
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, PREFIXOS, get_feature_columns
from src.ml_pipeline.metricas import Q_RISCO, Q_SURTO, avaliar_criterios, calcular_metricas
from src.ml_pipeline.model_training import fit_predict_fold, limiares_por_cidade

logger = logging.getLogger(__name__)

LOCK_NAME = "teste_final_2025.lock"
# Queda considerada relevante entre validação e teste (sinal de overfitting à validação)
QUEDA_SKILL_RELATIVA = 0.5
QUEDA_R2_ABSOLUTA = 0.15


class HoldoutJaUsado(RuntimeError):
    pass


def carregar_config(out_dir: Path) -> dict:
    path = out_dir / "config_escolhida.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} não existe. Rode a Fase 2: python main.py analise")
    return json.loads(path.read_text(encoding="utf-8"))


def avaliar_2025(panel: pd.DataFrame, doenca: str, h: int, usar_clima: bool, corte: bool):
    """Treina em anos < ANO_HOLDOUT e avalia em ANO_HOLDOUT. Retorna (métricas modelo, baselines, oof)."""
    alvo = DOENCA_PARA_COL[doenca]
    p = PREFIXOS[alvo]
    df = preparar_dados(panel, doenca, h, ANO_HOLDOUT)
    tr, te = df[df["year"] < ANO_HOLDOUT], df[df["year"] == ANO_HOLDOUT]
    if te.empty:
        raise ValueError(f"Sem dados de {ANO_HOLDOUT} para {doenca}.")
    feats = get_feature_columns(df, doenca=doenca, usar_clima=usar_clima)
    _, pred = fit_predict_fold(tr, te, feats, alvo, CLIP_PERCENTIL if corte else None)

    oof = pd.DataFrame({
        "code": te["code"].values, "year": te["year"].values, "month": te["month"].values,
        "y_true": te[alvo].to_numpy(float),
        "y_pred": pred,
        "y_persistencia": te[f"{p}_lag{h}"].to_numpy(float),
        "y_sazonal": te[f"{p}_lag12"].to_numpy(float),
        "limiar_surto": limiares_por_cidade(tr, te["code"], alvo, Q_SURTO),
        "limiar_risco": limiares_por_cidade(tr, te["code"], alvo, Q_RISCO),
    })
    args = (oof["y_persistencia"], oof["limiar_surto"], oof["limiar_risco"])
    m = calcular_metricas(oof["y_true"], oof["y_pred"], *args)
    base = {
        "persistencia": calcular_metricas(oof["y_true"], oof["y_persistencia"], *args),
        "sazonal": calcular_metricas(oof["y_true"], oof["y_sazonal"], *args),
    }
    return m, base, oof


def run_teste_final(
    out_dir: Path = OUTPUT_EXPERIMENTO,
    confirmar: bool = False,
    forcar: bool = False,
    panel: pd.DataFrame | None = None,
) -> dict:
    lock = out_dir / LOCK_NAME
    if lock.exists() and not forcar:
        raise HoldoutJaUsado(
            f"O teste em {ANO_HOLDOUT} já foi executado em {lock.read_text(encoding='utf-8').strip()}. "
            "Reusar o holdout invalida o teste. Use --forcar só se souber o que está fazendo."
        )
    if not confirmar:
        raise PermissionError(
            "O teste final usa o holdout uma única vez. Revise output/experimento/analise.md e "
            "config_escolhida.json e rode com --confirmar."
        )

    cfg = carregar_config(out_dir)
    dev = pd.read_csv(out_dir / "resultados.csv")
    if panel is None:
        from src.ml_pipeline.data_ingestion import build_base_panel
        panel = build_base_panel(BASE_DIR)

    relatorio = {
        "executado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_commit": git_commit(),
        "ano_teste": ANO_HOLDOUT,
        "reexecucao_forcada": bool(lock.exists()),
        "doencas": {},
    }
    for doenca, dec in cfg["doencas"].items():
        nome = nome_config(dec["usar_clima"], dec["corte_p99"])
        relatorio["doencas"][doenca] = {"modelo": nome, "horizontes": {}}
        for h in HORIZONTES:
            logger.info(f"Teste {ANO_HOLDOUT}: {doenca} h={h} ({nome})")
            m, base, oof = avaliar_2025(panel, doenca, h, dec["usar_clima"], dec["corte_p99"])
            oof.to_csv(out_dir / f"oof_{ANO_HOLDOUT}_{doenca}_h{h}.csv.gz", index=False)
            d = dev[(dev["doenca"] == doenca) & (dev["horizonte"] == h) & (dev["modelo"] == nome)]
            dev_m = d.iloc[0].to_dict() if len(d) else {}
            queda_skill = (
                dev_m.get("skill_score", 0) > 0
                and m["skill_score"] < (1 - QUEDA_SKILL_RELATIVA) * dev_m["skill_score"]
            )
            queda_r2 = dev_m.get("r2") is not None and (dev_m["r2"] - m["r2"]) > QUEDA_R2_ABSOLUTA
            relatorio["doencas"][doenca]["horizontes"][f"h{h}"] = {
                "teste_2025": m,
                "criterios_2025": avaliar_criterios(m, doenca),
                "baselines_2025": base,
                "validacao_2018_2024": {k: dev_m.get(k) for k in ("mae", "r2", "mae_surto", "skill_score", "auc_risco_alto")},
                "queda_relevante_vs_validacao": bool(queda_skill or queda_r2),
            }

    (out_dir / "teste_final_2025.json").write_text(
        json.dumps(relatorio, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    (out_dir / "teste_final_2025.md").write_text(_markdown(relatorio), encoding="utf-8")
    lock.write_text(relatorio["executado_em"], encoding="utf-8")
    logger.info(f"Teste final gravado em {out_dir / 'teste_final_2025.md'}")
    return relatorio


def _markdown(rel: dict) -> str:
    md = [f"# Fase 3 — Teste final em {rel['ano_teste']} (executado {rel['executado_em']})\n"]
    if rel["reexecucao_forcada"]:
        md.append("> ⚠️ Reexecução forçada: o holdout já tinha sido usado antes.\n")
    for doenca, d in rel["doencas"].items():
        md += [f"\n## {doenca.capitalize()} — {d['modelo']}\n",
               "| h | MAE 2025 (val.) | R² 2025 (val.) | MAE-surto/pico | Skill 2025 (val.) | AUC 2025 | MAE persist. | Passa | Queda vs val. |",
               "|---|---|---|---|---|---|---|---|---|"]
        for h, x in d["horizontes"].items():
            t, v, c = x["teste_2025"], x["validacao_2018_2024"], x["criterios_2025"]
            frac = t["mae_surto"] / t["pico_medio_surto"] if t["pico_medio_surto"] else float("nan")
            md.append(
                f"| {h[1:]} | {t['mae']:.2f} ({v['mae'] or float('nan'):.2f}) | {t['r2']:.3f} ({v['r2'] or float('nan'):.3f}) | "
                f"{frac:.0%} | {t['skill_score']:.3f} ({v['skill_score'] or float('nan'):.3f}) | {t['auc_risco_alto']:.3f} | "
                f"{t['mae_persistencia']:.2f} | {'✅' if c['passa_todos'] else '❌'} | "
                f"{'⚠️ sim' if x['queda_relevante_vs_validacao'] else 'não'} |"
            )
    md.append("\nResultados reportados sem nenhum ajuste posterior ao teste.")
    return "\n".join(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description=f"Fase 3 — teste único em {ANO_HOLDOUT}")
    ap.add_argument("--confirmar", action="store_true", help="Confirma que a configuração foi revisada")
    ap.add_argument("--forcar", action="store_true", help="Reexecuta mesmo com a trava (fica registrado)")
    args = ap.parse_args(argv)
    configurar_log()
    run_teste_final(confirmar=args.confirmar, forcar=args.forcar)


if __name__ == "__main__":
    main()
