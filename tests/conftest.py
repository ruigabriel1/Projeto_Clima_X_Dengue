"""Fixtures compartilhados: painel sintético (não depende do banco)."""
import numpy as np
import pandas as pd
import pytest


# =============================================
# Fixture: painel sintético mínimo (multi-doença)
# =============================================
@pytest.fixture
def mini_panel():
    """Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças."""
    np.random.seed(42)
    rows = []
    for code in ["100001", "200002"]:
        for y in [2018, 2019, 2020, 2021, 2022, 2023]:
            for m in range(1, 13):
                rows.append({
                    "code": code,
                    "year": y,
                    "month": m,
                    "dengue_cases": np.random.poisson(50),
                    "chik_cases": np.random.poisson(10),
                    "zika_cases": np.random.poisson(3),
                    "temp_media": 20 + np.random.randn() * 3,
                    "temp_maxima": 28 + np.random.randn() * 2,
                    "temp_minima": 14 + np.random.randn() * 2,
                    "precipitacao": max(0, 100 + np.random.randn() * 40),
                    "umidmed": min(100, max(30, 70 + np.random.randn() * 10)),
                    "enso": np.random.choice([-0.5, 0.0, 0.5, 1.0]),
                    "receptivo": np.random.choice([0, 1, 2]),
                    "populacao": 50000 + np.random.randint(-5000, 5000),
                    "latitude": -28.5 if code == "100001" else -25.0,
                })
    return pd.DataFrame(rows)
