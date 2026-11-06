"""
Experimento v6 (docs/PROTOCOLO_V6.md) — responde H6a (formulação), H6b (vizinhos), H6c (imunidade longa).

Base B0 = configuração da v5.1 por doença. Variantes (uma passada, mesmos folds):
    B0       offset log(pop/100 mil), features da v5.1
    A        offset log(casos[t−h] + 1), features da v5.1
    B0_V, B0_L, A_V, A_L   = B0/A + vizinhos (V) ou + imunidade longa (L)
Regra sequencial: A × B0 define a formulação F; depois V × F e L × F, cada um isolado.
Validação: todos os meses consolidados (2015-01 a 2026-09); expanding window, folds 2018–2026.

Trava de pré-registro: com dados reais, o experimento só roda se docs/PROTOCOLO_V6.md estiver commitado e
sem alterações locais; o hash do commit vai para o meta.json.

Saídas em output/experimento_v6/: resultados.csv, efeitos.csv, decisao.json, relatorio.md,
oof_<doenca>_h<h>.csv.gz, meta.json
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import BASE_DIR, DOENCAS_EXPERIMENTO, HORIZONTES, OUTPUT_DIR
from src.ml_pipeline.analise_experimento import bootstrap_delta_mae
from src.ml_pipeline.experimento_horizontes import configurar_log, git_commit
from src.ml_pipeline.experimento_v5 import EPS_INCID, OUT_V5, Q_RISCO_V5, calibrar_temporal, metricas
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, PREFIXOS, build_ml_features, get_feature_columns
from src.ml_pipeline.model_training import XGB_PARAMS, _expanding_window_splits, fit_predict_fold, limiares_por_cidade

logger = logging.getLogger(__name__)

OUT_V6 = OUTPUT_DIR / "experimento_v6"
PROTOCOLO = BASE_DIR / "docs" / "PROTOCOLO_V6.md"
ANO_MIN_TESTE = 2018
ANOS_POS_EPIDEMIA = (2025, 2026)
VARIANTES = {   # nome: (offset_persistencia, vizinhos, imunidade_longa)
    "B0": (False, False, False), "A": (True, False, False),
    "B0_V": (False, True, False), "B0_L": (False, False, True),
    "A_V": (True, True, False), "A_L": (True, False, True),
}


class ProtocoloNaoRegistrado(RuntimeError):
    pass


def protocolo_registrado(path: Path = PROTOCOLO) -> str:
    """Hash do último commit que tocou o protocolo; erro se não houver ou se houver alteração local."""
    rel = str(path.relative_to(BASE_DIR)).replace("\\", "/")
    h = subprocess.run(["git", "log", "-1", "--format=%H", "--", rel], cwd=BASE_DIR,
                       capture_output=True, text=True).stdout.strip()
    sujo = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=BASE_DIR).returncode != 0
    if not h or sujo:
        raise ProtocoloNaoRegistrado(f"{rel} precisa estar commitado (e sem alterações) antes de rodar o experimento v6.")
    return h


def base_v51(exp_v5: Path = OUT_V5) -> dict:
    """Configuração da v5.1 por doença (decisão pré-registrada da v5)."""
    dec = json.loads((exp_v5 / "decisao.json").read_text(encoding="utf-8"))
    return {d: {"clima": "parcimonioso" if i["clima"] else "nenhum", "suscetibilidade": bool(i["suscetibilidade"])}
            for d, i in dec.items()}


def preparar(panel: pd.DataFrame, doenca: str, h: int) -> pd.DataFrame:
    df = build_ml_features(panel, doenca=doenca, horizonte=h).dropna(subset=[DOENCA_PARA_COL[doenca]])
    return df[df["populacao"].notna() & (df["populacao"] > 0)].reset_index(drop=True)


def features_variantes(df: pd.DataFrame, doenca: str, base: dict) -> dict[str, list[str]]:
    return {n: get_feature_columns(df, doenca=doenca, clima=base["clima"], suscetibilidade=base["suscetibilidade"],
                                   vizinhos=v, imunidade_longa=l)
            for n, (_, v, l) in VARIANTES.items()}


def rodar(df: pd.DataFrame, doenca: str, h: int, base: dict, ano_max: int) -> tuple[pd.DataFrame, dict]:
    alvo = DOENCA_PARA_COL[doenca]
    col_p = f"{PREFIXOS[alvo]}_lag{h}"
    feats = features_variantes(df, doenca, base)      # seleção ANTES de qualquer coluna auxiliar
    df = df.assign(_incid=df[alvo] / df["populacao"] * 1e5)
    partes = []
    for tr, te, ano in _expanding_window_splits(df["year"], 3, ano_max):
        if ano < ANO_MIN_TESTE:
            continue
        d_tr, d_te = df[tr], df[te]
        t0 = time.time()
        parte = pd.DataFrame({
            "code": d_te["code"].values, "year": d_te["year"].values, "month": d_te["month"].values,
            "pop": d_te["populacao"].to_numpy(float), "y_true": d_te[alvo].to_numpy(float),
            "y_persistencia": d_te[col_p].to_numpy(float),
            "p75_incid": limiares_por_cidade(d_tr, d_te["code"], "_incid", Q_RISCO_V5),
        })
        for n, (persist, _, _) in VARIANTES.items():
            _, pred = fit_predict_fold(d_tr, d_te, feats[n], alvo, use_pop_offset=not persist,
                                       offset_persistencia=col_p if persist else None)
            parte[f"pred_{n}"] = pred
        partes.append(parte)
        logger.info(f"  v6 {doenca} h={h} fold {ano}: {len(d_te)} linhas, {time.time() - t0:.1f}s")
    oof = pd.concat(partes, ignore_index=True)
    oof["risco_alto"] = (oof["y_true"] / oof["pop"] * 1e5 > oof["p75_incid"]).astype(int)
    for n in [*VARIANTES, "persistencia"]:
        col = "y_persistencia" if n == "persistencia" else f"pred_{n}"
        oof[f"escore_{n}"] = (oof[col].fillna(0) / oof["pop"] * 1e5) / (oof["p75_incid"] + EPS_INCID)
        oof[f"prob_{n}"] = calibrar_temporal(oof, f"escore_{n}")
    return oof, feats


def tabela(oof: pd.DataFrame, doenca: str, h: int, periodo: str) -> list[dict]:
    linhas = []
    for n in [*VARIANTES, "persistencia"]:
        col = "y_persistencia" if n == "persistencia" else f"pred_{n}"
        m = metricas(oof, col, f"escore_{n}", f"prob_{n}")
        m["razao_previsto_real"] = float(oof[col].fillna(0).sum() / max(oof["y_true"].sum(), 1))
        linhas.append({"doenca": doenca, "horizonte": h, "periodo": periodo, "modelo": n, **m})
    return linhas


def efeito(oof: pd.DataFrame, doenca: str, h: int, passo: str, com: str, sem: str) -> dict:
    d, lo, hi = bootstrap_delta_mae(oof, f"pred_{com}", f"pred_{sem}")
    return {"doenca": doenca, "horizonte": h, "passo": passo, "com": com, "sem": sem, "delta_mae": d,
            "ic95_lo": lo, "ic95_hi": hi, "delta_pct": 100 * d / (oof["y_true"] - oof[f"pred_{sem}"]).abs().mean(),
            "reduz_erro": bool(hi < 0)}


def decidir(efeitos_por_doenca: dict[str, pd.DataFrame]) -> dict:
    """Regra sequencial do protocolo: adota se IC 95% < 0 em ≥ 2 dos 3 horizontes."""
    dec = {}
    for d, ef in efeitos_por_doenca.items():
        def adota(passo):
            return bool(ef.loc[ef["passo"] == passo, "reduz_erro"].sum() >= 2)
        f = "A" if adota("A_vs_B0") else "B0"
        v, l = adota(f"V_vs_{f}"), adota(f"L_vs_{f}")
        dec[d] = {"formulacao": f, "offset": "persistencia" if f == "A" else "pop", "vizinhos": v,
                  "imunidade_longa": l, "modelo": f + ("_V" if v else "") + ("_L" if l else "")}
    return dec


def run(panel: pd.DataFrame | None = None, out_dir: Path = OUT_V6, doencas=DOENCAS_EXPERIMENTO,
        horizontes=HORIZONTES, base: dict | None = None, exigir_registro: bool = True) -> tuple:
    t0 = time.time()
    registro = protocolo_registrado() if exigir_registro else None
    out_dir.mkdir(parents=True, exist_ok=True)
    if panel is None:
        from src.ml_pipeline.data_ingestion import build_base_panel
        from src.prediction_service.data_fetcher import remover_meses_nao_consolidados
        panel = remover_meses_nao_consolidados(build_base_panel(BASE_DIR))
    base = base or base_v51()
    ano_max = int(panel["year"].max())
    res, efeitos, meta_feats = [], {}, {}
    for doenca in doencas:
        ef_d = []
        for h in horizontes:
            logger.info(f"=== v6 {doenca} h={h} ===")
            oof, feats = rodar(preparar(panel, doenca, h), doenca, h, base[doenca], ano_max)
            oof.to_csv(out_dir / f"oof_{doenca}_h{h}.csv.gz", index=False)
            meta_feats[f"{doenca}_h{h}"] = feats
            res += tabela(oof, doenca, h, f"dev_{ANO_MIN_TESTE}_{ano_max}")
            for ano in ANOS_POS_EPIDEMIA:
                if (oof["year"] == ano).any():
                    res += tabela(oof[oof["year"] == ano], doenca, h, f"pos_epidemia_{ano}")
            ef_d += [efeito(oof, doenca, h, "A_vs_B0", "A", "B0")]
            for f in ("B0", "A"):
                ef_d += [efeito(oof, doenca, h, f"V_vs_{f}", f"{f}_V", f),
                         efeito(oof, doenca, h, f"L_vs_{f}", f"{f}_L", f)]
        efeitos[doenca] = pd.DataFrame(ef_d)
    resultados, ef = pd.DataFrame(res), pd.concat(efeitos.values(), ignore_index=True)
    dec = decidir(efeitos)
    resultados.to_csv(out_dir / "resultados.csv", index=False)
    ef.to_csv(out_dir / "efeitos.csv", index=False)
    (out_dir / "decisao.json").write_text(json.dumps(dec, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "relatorio.md").write_text(relatorio(resultados, ef, dec), encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({
        "executado_em": time.strftime("%Y-%m-%d %H:%M:%S"), "git_commit": git_commit(),
        "protocolo_commit": registro, "duracao_min": round((time.time() - t0) / 60, 1),
        "anos": [int(panel.year.min()), ano_max], "base_v51": base, "xgb_params": XGB_PARAMS,
        "features": meta_feats,
    }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    logger.info(f"Experimento v6 concluído → {out_dir}")
    return resultados, ef, dec


OUT_MODELOS_V6 = OUTPUT_DIR / "models" / "final_v6"


def treinar_producao(panel: pd.DataFrame | None = None, exp_dir: Path = OUT_V6, out_dir: Path = OUT_MODELOS_V6,
                     horizontes=HORIZONTES, base: dict | None = None) -> dict:
    """
    Modelo v6 do modo sombra: configuração decidida em decisao.json, treinada com todos os meses consolidados.
    Mesmo formato de metadata da v5.1 (o Preditor lê os dois), com "offset" indicando a formulação.
    Calibrador e intervalo vêm do OOF da variante decidida; se a combinação final (ex.: A_V_L) não existir
    no OOF, usam a formulação F (registrado no metadata).
    """
    import joblib
    from sklearn.isotonic import IsotonicRegression

    from src.ml_pipeline.alerta_risco import FAIXAS_PROB
    from src.ml_pipeline.modelo_final import calibrar_intervalo

    if panel is None:
        from src.ml_pipeline.data_ingestion import build_base_panel
        from src.prediction_service.data_fetcher import remover_meses_nao_consolidados
        panel = remover_meses_nao_consolidados(build_base_panel(BASE_DIR))
    dec = json.loads((exp_dir / "decisao.json").read_text(encoding="utf-8"))
    base = base or base_v51()
    todas = {}
    for doenca, i in dec.items():
        alvo = DOENCA_PARA_COL[doenca]
        col_lag = lambda h: f"{PREFIXOS[alvo]}_lag{h}"  # noqa: E731
        dest = out_dir / doenca
        dest.mkdir(parents=True, exist_ok=True)
        obs = panel.dropna(subset=[alvo]).sort_values(["year", "month"])
        ini, fim = obs.iloc[[0, -1]][["year", "month"]].astype(int).values
        meta = {"versao": "v6", "doenca": doenca, "modelo": i["modelo"], "offset": i["offset"],
                "vizinhos": i["vizinhos"], "imunidade_longa": i["imunidade_longa"], **base[doenca],
                "treinado_em": time.strftime("%Y-%m-%d %H:%M:%S"), "git_commit": git_commit(),
                "anos_treino": [int(ini[0]), int(fim[0])], "periodo_treino": f"{ini[0]}-{ini[1]:02d} a {fim[0]}-{fim[1]:02d}",
                "xgb_params": XGB_PARAMS, "q_risco": Q_RISCO_V5, "eps_incid": EPS_INCID,
                "faixas_probabilidade": FAIXAS_PROB, "horizontes": {}}
        for h in horizontes:
            df = preparar(panel, doenca, h)
            feats = get_feature_columns(df, doenca=doenca, clima=base[doenca]["clima"],
                                        suscetibilidade=base[doenca]["suscetibilidade"],
                                        vizinhos=i["vizinhos"], imunidade_longa=i["imunidade_longa"])
            persist = i["offset"] == "persistencia"
            model, _ = fit_predict_fold(df, df.iloc[:1], feats, alvo, use_pop_offset=not persist,
                                        offset_persistencia=col_lag(h) if persist else None)
            joblib.dump(model, dest / f"h{h}.joblib")
            oof = pd.read_csv(exp_dir / f"oof_{doenca}_h{h}.csv.gz", dtype={"code": str})
            ref = i["modelo"] if f"pred_{i['modelo']}" in oof.columns else i["formulacao"]
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof[f"escore_{ref}"].fillna(0), oof["risco_alto"])
            joblib.dump(iso, dest / f"h{h}_calibrador.joblib")
            meta["horizontes"][f"h{h}"] = {
                "arquivo": f"h{h}.joblib", "calibrador": f"h{h}_calibrador.joblib", "features": feats,
                "calibracao_de": ref, "intervalo_contagem": calibrar_intervalo(oof["y_true"], oof[f"pred_{ref}"]),
            }
            logger.info(f"v6 produção {doenca} h={h}: {i['modelo']}, {len(feats)} features, offset {i['offset']}")
        hist = panel.dropna(subset=[alvo]).assign(_inc=lambda x: x[alvo] / x["populacao"] * 1e5)
        q = hist.groupby("code").agg(p75_incid=("_inc", lambda s: s.quantile(Q_RISCO_V5)),
                                     meses_com_caso=(alvo, lambda s: int((s > 0).sum())),
                                     nome=("city_name", "last"), populacao=("populacao", "last"))
        meta["cidades"] = {str(c): {"nome": r.nome, "populacao": int(r.populacao), "p75_incid": float(r.p75_incid),
                                    "meses_com_caso": int(r.meses_com_caso)} for c, r in q.iterrows()}
        (dest / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        todas[doenca] = meta
    return todas


def relatorio(res: pd.DataFrame, ef: pd.DataFrame, dec: dict) -> str:
    def f(v, n=3):
        return "—" if pd.isna(v) else f"{v:.{n}f}"
    md = ["# Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)\n",
          "Folds 2018–2026 (2025 e 2026 já foram testes únicos; aqui são desenvolvimento). "
          "A decisão usa só o período completo; os anos pós-epidemia são descritivos.\n"]
    for d in dec:
        md += [f"\n## {d.capitalize()}\n",
               "| período | h | modelo | MAE | Skill | AUC | Brier skill | previsto ÷ real |",
               "|---|---|---|---|---|---|---|---|"]
        for x in res[res.doenca == d].sort_values(["periodo", "horizonte", "modelo"]).itertuples():
            md.append(f"| {x.periodo} | {x.horizonte} | {x.modelo} | {f(x.mae, 2)} | {f(x.skill)} | {f(x.auc)} | "
                      f"{f(getattr(x, 'brier_skill', np.nan))} | {f(x.razao_previsto_real, 2)} |")
        md += ["\n### Efeitos (ΔMAE com − sem, IC 95% bootstrap por município)\n",
               "| h | passo | ΔMAE | IC 95% | Δ% | reduz erro? |", "|---|---|---|---|---|---|"]
        for x in ef[ef.doenca == d].itertuples():
            md.append(f"| {x.horizonte} | {x.passo} | {x.delta_mae:+.3f} | [{x.ic95_lo:+.3f}, {x.ic95_hi:+.3f}] | "
                      f"{x.delta_pct:+.1f}% | {'sim' if x.reduz_erro else 'não'} |")
        i = dec[d]
        md.append(f"\n**Decisão (regra pré-registrada):** formulação = `{i['formulacao']}` (offset {i['offset']}); "
                  f"vizinhos = {'entra' if i['vizinhos'] else 'fica de fora'}; imunidade longa = "
                  f"{'entra' if i['imunidade_longa'] else 'fica de fora'} → `{i['modelo']}`")
    return "\n".join(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Experimento v6 (protocolo pré-registrado)")
    ap.add_argument("--doenca", choices=list(DOENCAS_EXPERIMENTO) + ["todas"], default="todas")
    a = ap.parse_args(argv)
    configurar_log()
    run(doencas=DOENCAS_EXPERIMENTO if a.doenca == "todas" else (a.doenca,))


if __name__ == "__main__":
    main()
