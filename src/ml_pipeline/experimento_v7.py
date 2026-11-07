"""
Experimento v7 (docs/PROTOCOLO_V7.md) — H7a (histórico 2010+), H7b (Rt), H7c (nível regional), H7d (sorotipo).

Base F = decisão da v6 por doença (dengue: offset de persistência; chikungunya: B0 = v5.1).
Variantes do modelo por cidade (uma passada, mesmos folds de teste 2018–2026):
    F, F_R (+ Rt)                       e, só dengue, F_H, F_HR (treino a partir de 2010)
Pós-processamento por variante v: v_N (reconciliação com o GLM do total da UF) e v_NS (N + sorotipo, só dengue
e só se o portão de cobertura passar). Também o "teto": v reconciliada com o total REAL da UF (oráculo,
descritivo).
Regra sequencial: H × F → F′; R × F′ → F″; N × F″; S × N. Adota se ΔMAE com IC 95% < 0 em ≥ 2 dos 3 horizontes
e ΔAUC ≥ −0,01 em cada um desses horizontes.

O alvo de risco (P75 da cidade) é o mesmo para todas as variantes: anos de treino do fold a partir de 2015.
Trava de pré-registro: só roda com dados reais se docs/PROTOCOLO_V7.md estiver commitado e sem alterações.

Saídas em output/experimento_v7/ (cópia dos resultados em docs/resultados_v7/).
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sqlite3
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import BASE_DIR, DB_PATH, DOENCAS_EXPERIMENTO, HORIZONTES, OUTPUT_DIR
from src.ml_pipeline import nivel_regional as nr
from src.ml_pipeline.analise_experimento import bootstrap_delta_mae
from src.ml_pipeline.experimento_horizontes import configurar_log, git_commit
from src.ml_pipeline.experimento_v5 import EPS_INCID, Q_RISCO_V5, calibrar_temporal, metricas
from src.ml_pipeline.experimento_v6 import OUT_V6, base_v51, preparar, protocolo_registrado
from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, PREFIXOS, get_feature_columns
from src.ml_pipeline.model_training import XGB_PARAMS, _expanding_window_splits, fit_predict_fold, limiares_por_cidade

logger = logging.getLogger(__name__)

OUT_V7 = OUTPUT_DIR / "experimento_v7"
DOCS_V7 = BASE_DIR / "docs" / "resultados_v7"
PROTOCOLO = BASE_DIR / "docs" / "PROTOCOLO_V7.md"
ANO_MIN_TESTE = 2018
ANOS_POS_EPIDEMIA = (2025, 2026)
ANO_HISTORICO = 2010
ANO_SERIE = 2015
LIMIAR_AUC = -0.01
PORTAO = {"min_casos": 10, "frac_janelas": 0.70, "anos": (2015, 2025)}
CHAVES = ["code", "year", "month"]


def variantes_cidade(doenca: str) -> dict[str, tuple[bool, bool]]:
    """nome: (histórico 2010+, Rt)."""
    v = {"F": (False, False), "F_R": (False, True)}
    if doenca == "dengue":
        v |= {"F_H": (True, False), "F_HR": (True, True)}
    return v


def com_rt(v: str) -> str:
    return {"F": "F_R", "F_H": "F_HR"}[v]


def base_v6(exp_v6: Path = OUT_V6) -> dict:
    """Base F: configuração da v5.1 (clima, suscetibilidade) + formulação decidida na v6."""
    dec6 = json.loads((exp_v6 / "decisao.json").read_text(encoding="utf-8"))
    b = base_v51()
    return {d: {**b[d], "offset": dec6[d]["offset"]} for d in dec6}


# ------------------------------------------------------------------ portão do sorotipo
def carregar_sorotipo(db_path=DB_PATH) -> pd.DataFrame | None:
    try:
        with sqlite3.connect(db_path) as c:
            return pd.read_sql("SELECT * FROM ingestao_sorotipo", c)
    except Exception:
        return None


def portao_sorotipo(sorotipo: pd.DataFrame | None) -> dict:
    """Só cobertura: fração das janelas UF × 3 meses (inteiras em 2015–2025) com ≥ 10 casos sorotipados."""
    a0, a1 = PORTAO["anos"]
    if sorotipo is None or sorotipo.empty:
        return {"passa": False, "motivo": "tabela ingestao_sorotipo ausente ou vazia", **PORTAO}
    ts = np.arange(a0 * 12, (a1 + 1) * 12)
    por_uf, janelas = {}, []
    for uf in nr.UFS:
        x = sorotipo[sorotipo["UF"] == uf].assign(t=lambda d: d["ANO"] * 12 + d["MES"] - 1)
        n = x.set_index("t")["n_testados"].reindex(ts, fill_value=0)
        j = n.rolling(3, min_periods=3).sum().dropna() >= PORTAO["min_casos"]
        por_uf[uf] = round(float(j.mean()), 3)
        janelas.append(j)
    frac = float(pd.concat(janelas).mean())
    return {"passa": bool(frac >= PORTAO["frac_janelas"]), "frac_janelas_ok": round(frac, 3), "por_uf": por_uf,
            "casos_sorotipados_2015_2025": int(sorotipo.loc[sorotipo["ANO"].between(a0, a1), "n_testados"].sum()),
            **PORTAO}


# ------------------------------------------------------------------ painéis
def paineis(doencas) -> dict[str, pd.DataFrame]:
    from src.ml_pipeline.data_ingestion import build_base_panel
    from src.prediction_service.data_fetcher import remover_meses_nao_consolidados
    p = {"2015": remover_meses_nao_consolidados(build_base_panel(BASE_DIR, ano_min=ANO_SERIE, incluir_rt=True))}
    if "dengue" in doencas:
        p["2010"] = remover_meses_nao_consolidados(build_base_panel(BASE_DIR, ano_min=ANO_HISTORICO, incluir_rt=True))
    return p


def _feats(df, doenca, base, rt):
    return get_feature_columns(df, doenca=doenca, clima=base["clima"], suscetibilidade=base["suscetibilidade"], rt=rt)


# ------------------------------------------------------------------ uma doença × horizonte
def rodar(paineis_: dict, doenca: str, h: int, base: dict, ano_max: int, sorotipo: pd.DataFrame | None,
          usar_s: bool) -> tuple[pd.DataFrame, dict, dict]:
    alvo = DOENCA_PARA_COL[doenca]
    col_p = f"{PREFIXOS[alvo]}_lag{h}"
    persist = base["offset"] == "persistencia"
    dfs = {"2015": preparar(paineis_["2015"], doenca, h)}
    if doenca == "dengue":
        dfs["2010"] = preparar(paineis_["2010"], doenca, h)
    var = variantes_cidade(doenca)
    feats = {n: _feats(dfs["2010" if hist else "2015"], doenca, base, rt) for n, (hist, rt) in var.items()}
    df15 = dfs["2015"].assign(_incid=lambda x: x[alvo] / x["populacao"] * 1e5)

    partes = []
    for tr, te, ano in _expanding_window_splits(df15["year"], 3, ano_max):
        if ano < ANO_MIN_TESTE:
            continue
        t0 = time.time()
        d_tr15, d_te15 = df15[tr], df15[te]
        parte = pd.DataFrame({
            "code": d_te15["code"].values, "year": d_te15["year"].values, "month": d_te15["month"].values,
            "pop": d_te15["populacao"].to_numpy(float), "y_true": d_te15[alvo].to_numpy(float),
            "y_persistencia": d_te15[col_p].to_numpy(float),
            "p75_incid": limiares_por_cidade(d_tr15, d_te15["code"], "_incid", Q_RISCO_V5),
        })
        for n, (hist, _) in var.items():
            dfv = dfs["2010" if hist else "2015"]
            d_tr = dfv[dfv["year"] < ano]
            d_te = d_te15[CHAVES].merge(dfv[dfv["year"] == ano], on=CHAVES, how="left")
            if d_te[alvo].isna().any():
                raise RuntimeError(f"{n}: {int(d_te[alvo].isna().sum())} linhas de teste sem par no painel {hist}")
            _, pred = fit_predict_fold(d_tr, d_te, feats[n], alvo, use_pop_offset=not persist,
                                       offset_persistencia=col_p if persist else None)
            parte[f"pred_{n}"] = pred
        partes.append(parte)
        logger.info(f"  v7 {doenca} h={h} fold {ano}: {len(d_te15)} linhas, {time.time() - t0:.1f}s")
    oof = pd.concat(partes, ignore_index=True)

    # ---- N (e S): GLM do total da UF, ajustado fold a fold só com meses anteriores ao ano de teste
    serie = nr.serie_uf(paineis_["2010" if doenca == "dengue" else "2015"], doenca)
    des = nr.desenho(serie, h, sorotipo if usar_s else None)
    totais, glm = {"N": [], "NS": []}, {}
    for ano in sorted(oof["year"].unique()):
        alvo_ano = des["year"] == ano
        for k, s in (("N", False), ("NS", True)):
            if s and not usar_s:
                continue
            m = nr.ajustar(des, (des["year"] < ano).to_numpy(), com_s=s)
            glm[f"{k}_{ano}"] = m
            totais[k].append(des.loc[alvo_ano, ["uf", "year", "month"]].assign(T_hat=nr.prever(m, des[alvo_ano])))
    real = oof.assign(uf=oof["code"].astype(str).str[:2].map(nr.UF_POR_PREFIXO)).groupby(
        ["uf", "year", "month"], as_index=False)["y_true"].sum().rename(columns={"y_true": "T_hat"})
    for n in var:
        oof[f"pred_{n}_N"], oof[f"fator_{n}_N"] = nr.reconciliar(oof, pd.concat(totais["N"]), f"pred_{n}")
        if usar_s:
            oof[f"pred_{n}_NS"], _ = nr.reconciliar(oof, pd.concat(totais["NS"]), f"pred_{n}")
        oof[f"pred_{n}_teto"], _ = nr.reconciliar(oof, real, f"pred_{n}")

    oof["risco_alto"] = (oof["y_true"] / oof["pop"] * 1e5 > oof["p75_incid"]).astype(int)
    for n in modelos(oof):
        col = "y_persistencia" if n == "persistencia" else f"pred_{n}"
        oof[f"escore_{n}"] = (oof[col].fillna(0) / oof["pop"] * 1e5) / (oof["p75_incid"] + EPS_INCID)
        oof[f"prob_{n}"] = calibrar_temporal(oof, f"escore_{n}")
    resumo_glm = {k: (None if m is None else {"n": m["n"], "coef": dict(zip(m["nomes"], np.round(m["coef"], 4))),
                                              "escala": round(m["escala"], 2)}) for k, m in glm.items()}
    return oof, feats, resumo_glm


def modelos(oof: pd.DataFrame) -> list[str]:
    return [c[5:] for c in oof.columns if c.startswith("pred_")] + ["persistencia"]


def tabela(oof: pd.DataFrame, doenca: str, h: int, periodo: str) -> list[dict]:
    linhas = []
    for n in modelos(oof):
        col = "y_persistencia" if n == "persistencia" else f"pred_{n}"
        m = metricas(oof, col, f"escore_{n}", f"prob_{n}")
        m["razao_previsto_real"] = float(oof[col].fillna(0).sum() / max(oof["y_true"].sum(), 1))
        linhas.append({"doenca": doenca, "horizonte": h, "periodo": periodo, "modelo": n, **m})
    return linhas


def efeito(oof: pd.DataFrame, doenca: str, h: int, passo: str, com: str, sem: str) -> dict:
    d, lo, hi = bootstrap_delta_mae(oof, f"pred_{com}", f"pred_{sem}")
    auc = {n: metricas(oof, f"pred_{n}", f"escore_{n}", f"prob_{n}")["auc"] for n in (com, sem)}
    return {"doenca": doenca, "horizonte": h, "passo": passo, "com": com, "sem": sem, "delta_mae": d,
            "ic95_lo": lo, "ic95_hi": hi, "delta_pct": 100 * d / (oof["y_true"] - oof[f"pred_{sem}"]).abs().mean(),
            "reduz_erro": bool(hi < 0), "auc_com": auc[com], "auc_sem": auc[sem], "delta_auc": auc[com] - auc[sem]}


def passos(doenca: str, usar_s: bool) -> list[tuple[str, str, str]]:
    """(passo, com, sem): todas as comparações que a regra sequencial pode precisar."""
    p = [("R_vs_F", "F_R", "F")]
    cidade = ["F", "F_R"]
    if doenca == "dengue":
        p += [("H_vs_F", "F_H", "F"), ("R_vs_F_H", "F_HR", "F_H")]
        cidade += ["F_H", "F_HR"]
    p += [(f"N_vs_{v}", f"{v}_N", v) for v in cidade]
    if usar_s:
        p += [(f"S_vs_{v}_N", f"{v}_NS", f"{v}_N") for v in cidade]
    return p


def adota(ef: pd.DataFrame, passo: str) -> bool:
    """Regra dupla: IC 95% do ΔMAE < 0 em ≥ 2 horizontes e ΔAUC ≥ −0,01 em cada um desses horizontes."""
    e = ef[(ef["passo"] == passo) & ef["reduz_erro"]]
    return bool(len(e) >= 2 and (e["delta_auc"] >= LIMIAR_AUC).all())


def decidir(efeitos_por_doenca: dict[str, pd.DataFrame], base: dict, usar_s: dict[str, bool]) -> dict:
    dec = {}
    for d, ef in efeitos_por_doenca.items():
        hist = d == "dengue" and adota(ef, "H_vs_F")
        f1 = "F_H" if hist else "F"
        rt = adota(ef, f"R_vs_{f1}")
        f2 = com_rt(f1) if rt else f1
        n = adota(ef, f"N_vs_{f2}")
        s = bool(n and usar_s.get(d) and adota(ef, f"S_vs_{f2}_N"))
        dec[d] = {"historico_2010": hist, "rt": rt, "nivel_regional": n, "sorotipo": s,
                  "offset": base[d]["offset"], "ano_min": ANO_HISTORICO if hist else ANO_SERIE,
                  "cidade": f2, "modelo": f2 + ("_NS" if s else "_N" if n else "")}
    return dec


# ------------------------------------------------------------------ execução
def run(paineis_: dict | None = None, out_dir: Path = OUT_V7, doencas=DOENCAS_EXPERIMENTO, horizontes=HORIZONTES,
        base: dict | None = None, sorotipo: pd.DataFrame | None = None, exigir_registro: bool = True,
        docs_dir: Path | None = DOCS_V7) -> tuple:
    t0 = time.time()
    registro = protocolo_registrado(PROTOCOLO) if exigir_registro else None
    out_dir.mkdir(parents=True, exist_ok=True)
    if sorotipo is None and exigir_registro:
        sorotipo = carregar_sorotipo()
    portao = portao_sorotipo(sorotipo)
    # o portão é gravado ANTES de qualquer modelo (protocolo: S só é avaliado se passar)
    for d in [out_dir] + ([docs_dir] if docs_dir else []):
        d.mkdir(parents=True, exist_ok=True)
        (d / "portao_sorotipo.json").write_text(json.dumps(portao, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Portão do sorotipo: {portao}")
    paineis_ = paineis_ or paineis(doencas)
    base = base or base_v6()
    ano_max = int(paineis_["2015"]["year"].max())
    usar_s = {d: bool(d == "dengue" and portao["passa"]) for d in doencas}
    res, efeitos, meta_feats, meta_glm = [], {}, {}, {}
    for doenca in doencas:
        ef_d = []
        for h in horizontes:
            logger.info(f"=== v7 {doenca} h={h} ===")
            oof, feats, glm = rodar(paineis_, doenca, h, base[doenca], ano_max, sorotipo, usar_s[doenca])
            oof.to_csv(out_dir / f"oof_{doenca}_h{h}.csv.gz", index=False)
            meta_feats[f"{doenca}_h{h}"], meta_glm[f"{doenca}_h{h}"] = feats, glm
            res += tabela(oof, doenca, h, f"dev_{ANO_MIN_TESTE}_{ano_max}")
            for ano in ANOS_POS_EPIDEMIA:
                if (oof["year"] == ano).any():
                    res += tabela(oof[oof["year"] == ano], doenca, h, f"pos_epidemia_{ano}")
            ef_d += [efeito(oof, doenca, h, p, c, s) for p, c, s in passos(doenca, usar_s[doenca])]
        efeitos[doenca] = pd.DataFrame(ef_d)
    resultados, ef = pd.DataFrame(res), pd.concat(efeitos.values(), ignore_index=True)
    dec = decidir(efeitos, base, usar_s)
    resultados.to_csv(out_dir / "resultados.csv", index=False)
    ef.to_csv(out_dir / "efeitos.csv", index=False)
    (out_dir / "decisao.json").write_text(json.dumps(dec, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "relatorio.md").write_text(relatorio(resultados, ef, dec, portao), encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({
        "executado_em": time.strftime("%Y-%m-%d %H:%M:%S"), "git_commit": git_commit(),
        "protocolo_commit": registro, "duracao_min": round((time.time() - t0) / 60, 1),
        "anos": {k: [int(p["year"].min()), int(p["year"].max())] for k, p in paineis_.items()},
        "base": base, "xgb_params": XGB_PARAMS, "portao_sorotipo": portao, "features": meta_feats, "glm": meta_glm,
    }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    if docs_dir:
        for f in ("resultados.csv", "efeitos.csv", "decisao.json", "relatorio.md", "meta.json"):
            shutil.copy(out_dir / f, docs_dir / f)
    logger.info(f"Experimento v7 concluído → {out_dir}")
    return resultados, ef, dec


OUT_MODELOS_V7 = OUTPUT_DIR / "models" / "final_v7"


def treinar_producao(paineis_: dict | None = None, exp_dir: Path = OUT_V7, out_dir: Path = OUT_MODELOS_V7,
                     horizontes=HORIZONTES, base: dict | None = None, sorotipo: pd.DataFrame | None = None) -> dict:
    """
    Modelo v7 do modo sombra: configuração de decisao.json treinada com todos os meses consolidados.
    Mesmo formato de metadata da v5.1/v6; com nível regional, cada horizonte leva os coeficientes do GLM
    (ajustado em todos os meses) em "nivel_regional". Calibrador e intervalo vêm do OOF da variante decidida.
    O limiar de risco (P75) usa os meses a partir de 2015, como na v5.1/v6 e no experimento.
    """
    import joblib
    from sklearn.isotonic import IsotonicRegression

    from src.ml_pipeline.alerta_risco import FAIXAS_PROB
    from src.ml_pipeline.modelo_final import calibrar_intervalo

    dec = json.loads((exp_dir / "decisao.json").read_text(encoding="utf-8"))
    paineis_ = paineis_ or paineis(tuple(dec))
    base = base or base_v6()
    todas = {}
    for doenca, i in dec.items():
        alvo = DOENCA_PARA_COL[doenca]
        persist = i["offset"] == "persistencia"
        panel = paineis_["2010" if i["historico_2010"] else "2015"]
        dest = out_dir / doenca
        dest.mkdir(parents=True, exist_ok=True)
        obs = panel.dropna(subset=[alvo]).sort_values(["year", "month"])
        ini, fim = obs.iloc[[0, -1]][["year", "month"]].astype(int).values
        meta = {"versao": "v7", "doenca": doenca, "modelo": i["modelo"], "offset": i["offset"],
                "historico_2010": i["historico_2010"], "rt": i["rt"], "nivel_regional": i["nivel_regional"],
                "sorotipo": i["sorotipo"], "incluir_rt": True, **{k: base[doenca][k] for k in ("clima", "suscetibilidade")},
                "treinado_em": time.strftime("%Y-%m-%d %H:%M:%S"), "git_commit": git_commit(),
                "anos_treino": [int(ini[0]), int(fim[0])], "periodo_treino": f"{ini[0]}-{ini[1]:02d} a {fim[0]}-{fim[1]:02d}",
                "xgb_params": XGB_PARAMS, "q_risco": Q_RISCO_V5, "eps_incid": EPS_INCID,
                "faixas_probabilidade": FAIXAS_PROB, "horizontes": {}}
        serie = nr.serie_uf(paineis_["2010" if doenca == "dengue" else "2015"], doenca) if i["nivel_regional"] else None
        for h in horizontes:
            col_p = f"{PREFIXOS[alvo]}_lag{h}"
            df = preparar(panel, doenca, h)
            feats = _feats(df, doenca, base[doenca], i["rt"])
            model, _ = fit_predict_fold(df, df.iloc[:1], feats, alvo, use_pop_offset=not persist,
                                        offset_persistencia=col_p if persist else None)
            joblib.dump(model, dest / f"h{h}.joblib")
            oof = pd.read_csv(exp_dir / f"oof_{doenca}_h{h}.csv.gz", dtype={"code": str})
            ref = i["modelo"]
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof[f"escore_{ref}"].fillna(0), oof["risco_alto"])
            joblib.dump(iso, dest / f"h{h}_calibrador.joblib")
            hm = {"arquivo": f"h{h}.joblib", "calibrador": f"h{h}_calibrador.joblib", "features": feats,
                  "calibracao_de": ref, "intervalo_contagem": calibrar_intervalo(oof["y_true"], oof[f"pred_{ref}"])}
            if i["nivel_regional"]:
                des = nr.desenho(serie, h, sorotipo if i["sorotipo"] else None)
                glm = nr.ajustar(des, np.ones(len(des), bool), com_s=i["sorotipo"])
                if glm is None:
                    raise RuntimeError(f"GLM regional sem meses suficientes ({doenca}, h={h})")
                hm["nivel_regional"] = glm
            meta["horizontes"][f"h{h}"] = hm
            logger.info(f"v7 produção {doenca} h={h}: {i['modelo']}, {len(feats)} features, offset {i['offset']}")
        p15 = paineis_["2015"]
        hist = p15.dropna(subset=[alvo]).assign(_inc=lambda x: x[alvo] / x["populacao"] * 1e5)
        q = hist.groupby("code").agg(p75_incid=("_inc", lambda s: s.quantile(Q_RISCO_V5)),
                                     meses_com_caso=(alvo, lambda s: int((s > 0).sum())),
                                     nome=("city_name", "last"), populacao=("populacao", "last"))
        meta["cidades"] = {str(c): {"nome": r.nome, "populacao": int(r.populacao), "p75_incid": float(r.p75_incid),
                                    "meses_com_caso": int(r.meses_com_caso)} for c, r in q.iterrows()}
        (dest / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        todas[doenca] = meta
    return todas


def relatorio(res: pd.DataFrame, ef: pd.DataFrame, dec: dict, portao: dict) -> str:
    def f(v, n=3):
        return "—" if pd.isna(v) else f"{v:.{n}f}"
    md = ["# Experimento v7 — histórico 2010+, Rt, nível regional e sorotipo (protocolo v7)\n",
          "Folds de teste 2018–2026. A decisão usa só o período completo; anos pós-epidemia e o teto "
          "(total regional REAL, oráculo) são descritivos.\n",
          f"**Portão do sorotipo:** {'passou' if portao['passa'] else 'não passou'} "
          f"(fração de janelas UF × 3 meses com ≥ {portao['min_casos']} casos sorotipados: "
          f"{portao.get('frac_janelas_ok', '—')}; exigido {portao['frac_janelas']}).\n"]
    for d in dec:
        md += [f"\n## {d.capitalize()}\n",
               "| período | h | modelo | MAE | Skill | AUC | Brier skill | previsto ÷ real |",
               "|---|---|---|---|---|---|---|---|"]
        for x in res[res.doenca == d].sort_values(["periodo", "horizonte", "modelo"]).itertuples():
            md.append(f"| {x.periodo} | {x.horizonte} | {x.modelo} | {f(x.mae, 2)} | {f(x.skill)} | {f(x.auc)} | "
                      f"{f(getattr(x, 'brier_skill', np.nan))} | {f(x.razao_previsto_real, 2)} |")
        md += ["\n### Efeitos (com − sem; IC 95% bootstrap por município)\n",
               "| h | passo | ΔMAE | IC 95% | Δ% | ΔAUC | reduz erro? |", "|---|---|---|---|---|---|---|"]
        for x in ef[ef.doenca == d].itertuples():
            md.append(f"| {x.horizonte} | {x.passo} | {x.delta_mae:+.3f} | [{x.ic95_lo:+.3f}, {x.ic95_hi:+.3f}] | "
                      f"{x.delta_pct:+.1f}% | {x.delta_auc:+.3f} | {'sim' if x.reduz_erro else 'não'} |")
        i = dec[d]
        md.append(f"\n**Decisão (regra pré-registrada):** histórico 2010+ = {'entra' if i['historico_2010'] else 'fica de fora'}; "
                  f"Rt = {'entra' if i['rt'] else 'fica de fora'}; nível regional = "
                  f"{'entra' if i['nivel_regional'] else 'fica de fora'}; sorotipo = "
                  f"{'entra' if i['sorotipo'] else 'fica de fora'} → `{i['modelo']}`")
    return "\n".join(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Experimento v7 (protocolo pré-registrado)")
    ap.add_argument("--doenca", choices=list(DOENCAS_EXPERIMENTO) + ["todas"], default="todas")
    a = ap.parse_args(argv)
    configurar_log()
    run(doencas=DOENCAS_EXPERIMENTO if a.doenca == "todas" else (a.doenca,))


if __name__ == "__main__":
    main()
