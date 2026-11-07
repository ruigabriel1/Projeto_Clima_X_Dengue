"""Idempotência e política de preservação do histórico na atualização incremental."""
import sqlite3
from datetime import date

import pandas as pd

from src.processamento import atualizacao_incremental as ai


def _banco(tmp_path):
    db = tmp_path / "t.db"
    hist = pd.DataFrame({
        "ANO": [2025, 2025], "MES": [11, 12], "CASOS_DENGUE": [10.0, 20.0],
        "CODIGO_MUNICIPIO": [410690, 410690], "LATITUDE": [-25.4] * 2, "LONGITUDE": [-49.3] * 2,
        "FAIXA_LATITUDE": [2, 2], "NOME_MUNICIPIO": ["Curitiba"] * 2,
    })
    with sqlite3.connect(db) as c:
        hist.to_sql("ingestao_saude", c, index=False)
    return db


def _coletor_falso(cidade, hoje):
    # A fonte "revisou" 2025 (casos diferentes) e traz 2026 até o mês corrente (incompleto)
    df = pd.DataFrame({
        "ANO": [2025, 2025, 2026, 2026, 2026], "MES": [11, 12, 1, 2, 3],
        "CASOS_DENGUE": [999.0, 999.0, 5.0, 7.0, 1.0], "NIVEL_DENGUE": [1, 2, 3, 4, 1],
    })
    for c in ("CODIGO_MUNICIPIO", "LATITUDE", "LONGITUDE", "FAIXA_LATITUDE", "NOME_MUNICIPIO"):
        df[c] = cidade[c]
    return ai._meses_fechados(df, hoje)


def test_rodar_duas_vezes_nao_duplica_e_preserva_historico(tmp_path, monkeypatch):
    db = _banco(tmp_path)
    monkeypatch.setitem(ai.COLETORES, "infodengue", _coletor_falso)
    monkeypatch.setitem(ai.PAUSA, "infodengue", 0)
    hoje = date(2026, 3, 15)

    ai.atualizar("infodengue", "r1", hoje=hoje, db_path=db)
    ai.atualizar("infodengue", "r2", hoje=hoje, db_path=db)   # nova rodada: reprocessa tudo

    with sqlite3.connect(db) as c:
        df = pd.read_sql("SELECT * FROM ingestao_saude ORDER BY ANO, MES", c)
    assert len(df) == 4                                    # 2 históricas + jan/fev 2026 (mar incompleto)
    assert not df.duplicated(["CODIGO_MUNICIPIO", "ANO", "MES"]).any()
    h = df[df.ANO == 2025]
    assert h["CASOS_DENGUE"].tolist() == [10.0, 20.0]      # histórico preservado
    assert h["NIVEL_DENGUE"].tolist() == [1, 2]            # mas recebe o alerta
    assert h["INGERIDO_EM"].isna().all()
    n = df[df.ANO == 2026]
    assert n["CASOS_DENGUE"].tolist() == [5.0, 7.0] and n["INGERIDO_EM"].notna().all()


def test_retoma_rodada_interrompida(tmp_path, monkeypatch):
    db = _banco(tmp_path)
    chamadas = []
    monkeypatch.setitem(ai.COLETORES, "infodengue", lambda c, h: chamadas.append(1) or _coletor_falso(c, h))
    monkeypatch.setitem(ai.PAUSA, "infodengue", 0)
    ai.atualizar("infodengue", "r1", hoje=date(2026, 3, 15), db_path=db)
    ai.atualizar("infodengue", "r1", hoje=date(2026, 3, 15), db_path=db)   # mesma rodada: nada a fazer
    assert len(chamadas) == 1


# ------------------------------------------------------------------ cópias semanais do InfoDengue (v7, Fase 0)
def _semanal_falso(cod7, disease="dengue", start_year=2015, end_year=2026):
    datas = pd.date_range("2026-01-04", periods=14, freq="7D")
    base = {"dengue": 10, "chikungunya": 1, "zika": 0}[disease]
    return pd.DataFrame({
        "data_iniSE": datas.astype("int64") // 10**6, "data": datas,
        "SE": [202601 + i for i in range(14)], "casos": [base + i for i in range(14)],
        "casos_est": [base + i + 0.5 for i in range(14)], "casos_est_min": 0.0, "casos_est_max": 99.0,
        "Rt": 1.1, "p_rt1": 0.7, "versao_modelo": "2026-04-10", "nivel": 1, "receptivo": 1,
        "umidmed": 80.0, "umidmax": 90.0, "umidmin": 70.0,
    })


def test_snapshot_guarda_ultimas_semanas_e_nao_duplica(tmp_path, monkeypatch):
    db = _banco(tmp_path)
    monkeypatch.setattr(ai.ing, "fetch_infodengue_semanal", _semanal_falso)
    monkeypatch.setitem(ai.PAUSA, "infodengue", 0)
    hoje = date(2026, 4, 15)
    ai.atualizar("infodengue", "r1", hoje=hoje, db_path=db)
    ai.atualizar("infodengue", "r2", hoje=hoje, db_path=db)          # mesmo dia: não duplica
    ai.atualizar("infodengue", "r3", hoje=date(2026, 4, 22), db_path=db)   # outra data: nova cópia
    with sqlite3.connect(db) as c:
        s = pd.read_sql(f"SELECT * FROM {ai.TABELA_SNAPSHOT}", c)
        m = pd.read_sql("SELECT * FROM ingestao_saude WHERE ANO = 2026 ORDER BY MES", c)
    assert set(s["DOENCA"]) == {"dengue", "chikungunya"}             # zika fora
    assert len(s) == 2 * 12 * 2                                      # 2 doenças × 12 semanas × 2 datas
    d = s[(s.DOENCA == "dengue") & (s.COLETADO_EM == "2026-04-15")].sort_values("SE")
    assert d["SE"].tolist() == [202603 + i for i in range(12)]       # as 12 mais recentes
    assert d["Rt"].eq(1.1).all() and d["versao_modelo"].eq("2026-04-10").all()
    # a série mensal continua a mesma de antes (jan = 4 semanas que começam em janeiro)
    assert m.loc[m.MES == 1, "CASOS_DENGUE"].item() == 10 + 11 + 12 + 13


def test_agregacao_mensal_igual_a_fetch_infodengue():
    from src.processamento import ingestor_api_sul as ing
    sem = _semanal_falso(4106902)
    a = ing.agregar_infodengue_mensal(sem, 4106902, "dengue")
    assert {"CASOS_DENGUE", "CASOS_EST_DENGUE", "NIVEL_DENGUE", "receptivo"} <= set(a.columns)
    assert a["CASOS_DENGUE"].sum() == sem["casos"].sum()
    assert ing.agregar_infodengue_mensal(pd.DataFrame(), 1).empty


# ------------------------------------------------------------------ backfill e Rt (v7, Fase 2)
def _banco_2015(tmp_path):
    db = tmp_path / "b.db"
    hist = pd.DataFrame({
        "ANO": [2014, 2015], "MES": [12, 1], "CASOS_DENGUE": [3.0, 4.0],
        "CODIGO_MUNICIPIO": [410690, 410690], "LATITUDE": [-25.4] * 2, "LONGITUDE": [-49.3] * 2,
        "FAIXA_LATITUDE": [2, 2], "NOME_MUNICIPIO": ["Curitiba"] * 2,
    })
    with sqlite3.connect(db) as c:
        hist.to_sql("ingestao_saude", c, index=False)
    return db


def test_backfill_so_insere_meses_antigos_inexistentes(tmp_path, monkeypatch):
    db = _banco_2015(tmp_path)

    def falso(cidade, hoje):
        df = pd.DataFrame({"ANO": [2013, 2014, 2015], "MES": [5, 12, 1], "CASOS_DENGUE": [7.0, 999.0, 999.0],
                           "RT_MEDIO_DENGUE": [1.2, 1.3, 1.4]})
        for c in ("CODIGO_MUNICIPIO", "LATITUDE", "LONGITUDE", "FAIXA_LATITUDE", "NOME_MUNICIPIO"):
            df[c] = cidade[c]
        return df

    monkeypatch.setitem(ai.COLETORES, "backfill-infodengue", falso)
    monkeypatch.setitem(ai.PAUSA, "backfill-infodengue", 0)
    ai.atualizar("backfill-infodengue", "b1", db_path=db)
    ai.atualizar("backfill-infodengue", "b2", db_path=db)
    with sqlite3.connect(db) as c:
        df = pd.read_sql("SELECT * FROM ingestao_saude ORDER BY ANO, MES", c)
    assert len(df) == 3 and not df.duplicated(["CODIGO_MUNICIPIO", "ANO", "MES"]).any()
    assert df["CASOS_DENGUE"].tolist() == [7.0, 3.0, 4.0]     # 2013 inserido; 2014 e 2015 intocados
    assert df["RT_MEDIO_DENGUE"].isna().tolist() == [False, True, True]   # backfill nunca faz UPDATE


def test_rt_acrescentado_ao_historico_sem_mudar_casos(tmp_path):
    db = _banco_2015(tmp_path)
    novo = pd.DataFrame({"ANO": [2015], "MES": [1], "CASOS_DENGUE": [999.0], "RT_MEDIO_DENGUE": [0.8],
                         "P_RT1_DENGUE": [0.1], "CODIGO_MUNICIPIO": [410690]})
    with sqlite3.connect(db) as c:
        ai.upsert(c, "ingestao_saude", novo)
        r = pd.read_sql("SELECT * FROM ingestao_saude WHERE ANO = 2015", c).iloc[0]
    assert r["CASOS_DENGUE"] == 4.0 and r["RT_MEDIO_DENGUE"] == 0.8 and r["P_RT1_DENGUE"] == 0.1


def test_agregacao_do_rt():
    from src.processamento import ingestor_api_sul as ing
    sem = _semanal_falso(1)
    sem["Rt"] = [0.5 + 0.1 * i for i in range(14)]
    sem["p_rt1"] = [0.1 * (i % 10) for i in range(14)]
    a = ing.agregar_infodengue_mensal(sem, 1, "dengue").set_index("MES")
    jan = sem[sem["data"].dt.month == 1]
    assert abs(a.loc[1, "RT_MEDIO_DENGUE"] - jan["Rt"].mean()) < 1e-9
    assert abs(a.loc[1, "RT_ULT_DENGUE"] - jan["Rt"].iloc[-1]) < 1e-9
    assert abs(a.loc[1, "P_RT1_DENGUE"] - jan["p_rt1"].mean()) < 1e-9


def test_backfill_populacao_so_insere(tmp_path):
    from src.processamento.ingestor_ibge_populacao import backfill_populacao
    db = _banco_2015(tmp_path)
    with sqlite3.connect(db) as c:
        pd.DataFrame({"CODIGO_MUNICIPIO": ["410690"], "ANO": [2015], "POPULACAO": [100]}).to_sql(
            "ingestao_populacao", c, index=False)
    chamadas = []

    def fetch(cod7, anos):
        chamadas.append(list(anos))
        return pd.DataFrame({"CODIGO_MUNICIPIO": cod7[:6], "ANO": anos, "POPULACAO": [90] * len(anos)})

    assert backfill_populacao([2009, 2011], db_path=db, pausa=0, fetch=fetch) == 2
    assert backfill_populacao([2009, 2011], db_path=db, pausa=0, fetch=fetch) == 0   # nada falta
    with sqlite3.connect(db) as c:
        p = pd.read_sql("SELECT * FROM ingestao_populacao ORDER BY ANO", c)
    assert p["ANO"].tolist() == [2009, 2011, 2015] and p.loc[p.ANO == 2015, "POPULACAO"].item() == 100
    assert chamadas == [[2009, 2011]]
