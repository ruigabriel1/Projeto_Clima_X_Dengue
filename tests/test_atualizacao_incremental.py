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
