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
