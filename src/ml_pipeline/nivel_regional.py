"""
Nível regional (protocolo v7, candidata N): prevê o total de casos de cada UF e redistribui entre as cidades.

Para cada doença e horizonte h, um GLM quasi-Poisson (escala de Pearson), empilhando PR, SC e RS:

    log E[T_uf,t] = log(pop_uf,t / 100 mil) + α_uf + Σ_{k=1,2} [a_k·sen(2πk·m_t/12) + b_k·cos(2πk·m_t/12)]
                    + β1·log(T_uf,t−h + 1) + β2·rt_uf,t−h + β3·incid_acum24_uf,t−h  [+ β4·novidade_uf,t−h (S)]

Reconciliação: previsão da cidade × T̂_uf ÷ soma das previsões das cidades da UF no mês (a ordem das cidades
dentro da UF não muda). Sem tuning. Um fold com menos de MIN_MESES_UF meses completos por UF no treino, ou
uma UF-mês com algum preditor ausente, não é reconciliado (fator 1).

`prever` usa só numpy (os coeficientes ficam em JSON no metadata), para a API não depender do statsmodels.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL, PREFIXOS

UF_POR_PREFIXO = {"41": "PR", "42": "SC", "43": "RS"}
UFS = ("PR", "SC", "RS")
MIN_MESES_UF = 24
ESCALA_ACUM = 1000.0   # incid_acum24 por 100 mil ÷ 1000 (mesmo modelo, melhor condicionamento numérico)


def _t(year, month):
    return np.asarray(year, dtype=int) * 12 + np.asarray(month, dtype=int) - 1


def serie_uf(panel: pd.DataFrame, doenca: str) -> pd.DataFrame:
    """Total mensal por UF (casos, população, Rt médio ponderado pela população) numa grade mensal completa."""
    alvo = DOENCA_PARA_COL[doenca]
    rtc = f"{PREFIXOS[alvo]}_rt_medio"
    d = panel[panel[alvo].notna() & (panel["populacao"] > 0)].copy()
    d["uf"] = d["code"].astype(str).str[:2].map(UF_POR_PREFIXO)
    d = d[d["uf"].notna()]
    d["t"] = _t(d["year"], d["month"])
    if rtc in d.columns:
        w = d["populacao"].where(d[rtc].notna())
        d["_rtw"], d["_w"] = d[rtc] * w, w
    else:
        d["_rtw"], d["_w"] = np.nan, np.nan
    g = d.groupby(["uf", "t"]).agg(T=(alvo, "sum"), pop=("populacao", "sum"), _rtw=("_rtw", "sum"), _w=("_w", "sum"))
    g["rt_uf"] = np.where(g["_w"] > 0, g["_rtw"] / g["_w"].replace(0, np.nan), np.nan)
    partes = []
    for uf, x in g.drop(columns=["_rtw", "_w"]).reset_index().groupby("uf"):
        grade = pd.DataFrame({"t": np.arange(x["t"].min(), x["t"].max() + 1)})
        partes.append(grade.merge(x, on="t", how="left").assign(uf=uf))
    s = pd.concat(partes, ignore_index=True)
    s["year"], s["month"] = s["t"] // 12, s["t"] % 12 + 1
    return s[["uf", "t", "year", "month", "T", "pop", "rt_uf"]]


def novidade_sorotipo(sorotipo: pd.DataFrame, h: int) -> pd.DataFrame:
    """
    novidade_uf,t−h = 1 − Σ_s p_s(3 meses até t−h) · p_s(36 meses anteriores a essa janela).
    Devolvida indexada pelo mês-alvo t. NaN se uma das janelas não tiver caso sorotipado.
    """
    cols = ["n_denv1", "n_denv2", "n_denv3", "n_denv4"]
    partes = []
    for uf, x in sorotipo.groupby("UF"):
        x = x.assign(t=_t(x["ANO"], x["MES"])).set_index("t")[cols].sort_index()
        x = x.reindex(np.arange(x.index.min(), x.index.max() + 1), fill_value=0)
        rec = x.rolling(3, min_periods=3).sum()
        ant = x.shift(3).rolling(36, min_periods=36).sum()
        prec = rec.div(rec.sum(axis=1).replace(0, np.nan), axis=0)
        pant = ant.div(ant.sum(axis=1).replace(0, np.nan), axis=0)
        nov = 1 - (prec * pant).sum(axis=1, min_count=4)
        partes.append(pd.DataFrame({"uf": uf, "t": nov.index + h, "novidade": nov.values}))
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=["uf", "t", "novidade"])


def desenho(serie: pd.DataFrame, h: int, sorotipo: pd.DataFrame | None = None) -> pd.DataFrame:
    """Uma linha por UF × mês-alvo t, com os preditores medidos em t−h (sem vazamento)."""
    partes = []
    for uf, x in serie.sort_values("t").groupby("uf"):
        x = x.copy()
        x["x_logT"] = np.log(x["T"].shift(h) + 1)
        x["x_rt"] = x["rt_uf"].shift(h)
        acum = x["T"].rolling(24, min_periods=24).sum()
        x["x_acum24"] = (acum / x["pop"] * 1e5).shift(h) / ESCALA_ACUM
        partes.append(x)
    des = pd.concat(partes, ignore_index=True)
    des["offset"] = np.log(des["pop"] / 1e5)
    for k in (1, 2):
        des[f"s{k}"] = np.sin(2 * np.pi * k * des["month"] / 12)
        des[f"c{k}"] = np.cos(2 * np.pi * k * des["month"] / 12)
    if sorotipo is not None:
        des = des.merge(novidade_sorotipo(sorotipo, h), on=["uf", "t"], how="left")
    return des


def nomes_coef(com_s: bool) -> list[str]:
    return [f"a_{u}" for u in UFS] + ["s1", "c1", "s2", "c2", "x_logT", "x_rt", "x_acum24"] + (["novidade"] if com_s else [])


def _matriz(des: pd.DataFrame, nomes: list[str]) -> np.ndarray:
    cols = []
    for n in nomes:
        cols.append((des["uf"] == n[2:]).astype(float).to_numpy() if n.startswith("a_") else des[n].to_numpy(float))
    return np.column_stack(cols)


def _completas(des: pd.DataFrame, nomes: list[str]) -> np.ndarray:
    X = _matriz(des, nomes)
    return np.isfinite(X).all(axis=1) & np.isfinite(des["offset"].to_numpy(float))


def ajustar(des: pd.DataFrame, treino: np.ndarray, com_s: bool = False) -> dict | None:
    """GLM quasi-Poisson nos meses de treino completos; None se alguma UF tiver < MIN_MESES_UF meses."""
    import statsmodels.api as sm
    nomes = nomes_coef(com_s)
    ok = np.asarray(treino, bool) & _completas(des, nomes) & des["T"].notna().to_numpy()
    n_uf = des.loc[ok, "uf"].value_counts()
    if any(n_uf.get(u, 0) < MIN_MESES_UF for u in UFS):
        return None
    d = des[ok]
    fit = sm.GLM(d["T"].to_numpy(float), _matriz(d, nomes), family=sm.families.Poisson(),
                 offset=d["offset"].to_numpy(float)).fit(scale="X2")
    return {"nomes": nomes, "coef": [float(c) for c in fit.params], "escala": float(fit.scale),
            "n": int(ok.sum()), "treino_ate": int(d["t"].max())}


def prever(modelo: dict | None, des: pd.DataFrame) -> np.ndarray:
    """T̂ por linha do desenho; NaN onde falta preditor ou não há modelo (→ fator 1 na reconciliação)."""
    if modelo is None:
        return np.full(len(des), np.nan)
    nomes = modelo["nomes"]
    X = _matriz(des, nomes)
    with np.errstate(invalid="ignore", over="ignore"):
        out = np.exp(X @ np.asarray(modelo["coef"]) + des["offset"].to_numpy(float))
    out[~_completas(des, nomes)] = np.nan
    return out


def reconciliar(cidades: pd.DataFrame, total_uf: pd.DataFrame, col: str = "pred") -> tuple[np.ndarray, np.ndarray]:
    """
    cidades: code, year, month, `col`. total_uf: uf, year, month, T_hat.
    Devolve (previsão reconciliada, fator). Fator 1 onde T_hat é NaN ou a soma das cidades é 0.
    """
    uf = cidades["code"].astype(str).str[:2].map(UF_POR_PREFIXO).to_numpy()
    yr, mo = cidades["year"].to_numpy(int), cidades["month"].to_numpy(int)
    soma = cidades[col].groupby([uf, yr, mo]).transform("sum").to_numpy(float)
    chave = pd.DataFrame({"uf": uf, "year": yr, "month": mo})
    tu = total_uf[["uf", "year", "month", "T_hat"]].astype({"year": int, "month": int})
    th = chave.merge(tu, on=["uf", "year", "month"], how="left")["T_hat"].to_numpy(float)
    fator = np.where(np.isfinite(th) & (soma > 0), th / np.where(soma > 0, soma, 1.0), 1.0)
    return cidades[col].to_numpy(float) * fator, fator
