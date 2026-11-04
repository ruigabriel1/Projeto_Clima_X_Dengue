"""DLNM: a base de spline e a recuperação de um efeito climático simulado conhecido."""
import numpy as np
import pandas as pd
import pytest

pytest.importorskip("pyfixest")

from src.analise_efeito import dlnm  # noqa: E402

BETA = 0.10          # +10% de risco por °C, só no lag 1


def _painel_sintetico(seed=0):
    rng = np.random.default_rng(seed)
    linhas = []
    choque_ano = {a: rng.normal(0, 0.5) for a in range(2015, 2023)}     # choques interanuais comuns
    for c in range(60):
        code = f"4{c % 3 + 1}{c:04d}"
        base = rng.normal(2.0, 0.5)
        temps = []
        for a in range(2015, 2023):
            for m in range(1, 13):
                temps.append((a, m, 20 + 5 * np.sin(2 * np.pi * m / 12) + rng.normal(0, 1.5)))
        for i, (a, m, t) in enumerate(temps):
            t_lag1 = temps[i - 1][2] if i else np.nan
            mu = np.exp(base + 0.8 * np.cos(2 * np.pi * m / 12) + choque_ano[a]
                        + (BETA * (t_lag1 - 20) if i else 0))
            linhas.append({"code": code, "year": a, "month": m, "temp_media": t,
                           "precipitacao": max(0, rng.normal(120, 40)), "populacao": 100_000,
                           "dengue_cases": rng.poisson(mu), "chik_cases": 0})
    return pd.DataFrame(linhas)


def test_spline_natural_e_linear_fora_dos_nos():
    x = np.linspace(0, 10, 200)
    s = dlnm.SplineNatural(x)
    assert s.gl == 4
    B = s.base(np.array([11.0, 12.0, 13.0]))       # além da fronteira: segunda derivada nula (linear)
    assert np.allclose(np.diff(B, n=2, axis=0), 0, atol=1e-8)


def test_recupera_rr_simulado():
    p = _painel_sintetico()
    d, splines = dlnm.preparar(p, "dengue")
    fit = dlnm.ajustar(d, "principal")
    p50, p90 = np.quantile(d["temp_media"], [0.5, 0.9])
    rr = dlnm.rr_acumulado(fit, "temp_media", splines["temp_media"], np.array([p90]), p50)["rr"].iloc[0]
    esperado = np.exp(BETA * (p90 - p50))
    assert rr == pytest.approx(esperado, rel=0.10)
    lags = dlnm.rr_por_lag(fit, "temp_media", splines["temp_media"], p90, p50)
    assert lags.loc[lags["rr"].sub(1).abs().idxmax(), "lag"] == 1          # o efeito está no lag certo
