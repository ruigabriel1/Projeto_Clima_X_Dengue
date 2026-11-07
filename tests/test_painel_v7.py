"""Painel com histórico estendido e Rt (protocolo v7): o padrão continua sendo o painel dos experimentos v4–v6."""
import sqlite3

import numpy as np
import pandas as pd

from src.ml_pipeline.data_ingestion import build_base_panel


def _raiz(tmp_path):
    db = tmp_path / "data" / "processed"
    db.mkdir(parents=True)
    meses = [(a, m) for a in (2013, 2014, 2015, 2016) for m in range(1, 13)]
    saude = pd.DataFrame([{"ANO": a, "MES": m, "CODIGO_MUNICIPIO": 410690, "CASOS_DENGUE": float(m),
                           "CASOS_CHIKUNGUNYA": (1.0 if a >= 2015 else np.nan), "RT_MEDIO_DENGUE": 1.0,
                           "RT_ULT_DENGUE": 1.1, "P_RT1_DENGUE": 0.5, "umidmed": 80.0, "LATITUDE": -25.4,
                           "LONGITUDE": -49.3, "FAIXA_LATITUDE": 2, "NOME_MUNICIPIO": "Curitiba"}
                          for a, m in meses if a >= 2014])
    clima = pd.DataFrame([{"ANO": a, "MES": m, "CODIGO_MUNICIPIO": 410690, "temp_media": 20.0 + m,
                           "precipitacao": 100.0} for a, m in meses])
    pop = pd.DataFrame({"CODIGO_MUNICIPIO": ["410690"] * 3, "ANO": [2013, 2015, 2016], "POPULACAO": [10, 20, 30]})
    with sqlite3.connect(db / "dengue_analytics.db") as c:
        saude.to_sql("ingestao_saude", c, index=False)
        clima.to_sql("ingestao_clima", c, index=False)
        pop.to_sql("ingestao_populacao", c, index=False)
    return tmp_path


def test_padrao_igual_ao_painel_dos_experimentos(tmp_path):
    p = build_base_panel(_raiz(tmp_path))
    assert p["year"].min() == 2015 and len(p) == 24
    assert not [c for c in p.columns if "rt" in c.lower().split("_")]      # Rt fora por padrão
    assert "RT_MEDIO_DENGUE" not in p.columns and "dengue_rt_medio" not in p.columns


def test_historico_estendido_com_rt_e_meses_de_aquecimento(tmp_path):
    p = build_base_panel(_raiz(tmp_path), ano_min=2014, incluir_rt=True)
    assert {"dengue_rt_medio", "dengue_rt_ult", "dengue_prt1"} <= set(p.columns)
    aq = p[p["year"] == 2013]                       # clima de 2013 sem casos: só para as defasagens
    assert len(aq) == 12 and aq["dengue_cases"].isna().all() and aq["temp_media"].notna().all()
    assert (aq["city_name"] == "Curitiba").all()
    assert len(p[p["year"] >= 2014]) == 36 and p[p["year"] >= 2014]["dengue_cases"].notna().all()
    assert p.loc[p["year"] == 2014, "chik_cases"].isna().all()   # sem vigilância antes de 2015
    assert p.loc[p["year"] == 2014, "populacao"].notna().all()   # interpolada entre 2013 e 2015
