"""
Atualização incremental e idempotente do banco (InfoDengue, Open-Meteo, NOAA).

Política (preserva a reprodutibilidade dos experimentos já publicados):
  - Meses com ANO < ANO_CORTE (padrão 2026) que já existem: só recebem as colunas de alerta
    NIVEL_* (benchmark). Casos e clima históricos NÃO são sobrescritos.
  - Meses com ANO ≥ ANO_CORTE: inseridos ou atualizados por completo (o InfoDengue revisa
    as semanas recentes), com INGERIDO_EM = data/hora da ingestão.
  - Só meses FECHADOS (anteriores ao mês corrente) são gravados.
  - Upsert por (CODIGO_MUNICIPIO, ANO, MES), garantido por índice UNIQUE: rodar de novo não duplica.
  - Progresso por cidade em `ingestao_progresso`; uma rodada interrompida retoma de onde parou.

Uso:
  python -m src.processamento.atualizacao_incremental --alvo todos
  python -m src.processamento.atualizacao_incremental --alvo infodengue --limite 5
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta

import pandas as pd

from src.config import DB_PATH
from src.processamento import ingestor_api_sul as ing

logger = logging.getLogger(__name__)

ANO_CORTE = 2026
CHAVES = ["CODIGO_MUNICIPIO", "ANO", "MES"]
TABELAS = {"infodengue": "ingestao_saude", "openmeteo": "ingestao_clima"}
COLS_HISTORICO = {"ingestao_saude": ["NIVEL_DENGUE", "NIVEL_CHIKUNGUNYA", "NIVEL_ZIKA"], "ingestao_clima": []}
PAUSA = {"infodengue": 0.3, "openmeteo": 1.0}


# ------------------------------------------------------------------ esquema
def preparar_esquema(conn: sqlite3.Connection, tabela: str, colunas: list[str]):
    """Adiciona colunas que faltam (sem perda de dados) e garante índice UNIQUE nas chaves."""
    existentes = {r[1] for r in conn.execute(f"PRAGMA table_info({tabela})")}
    for c in colunas:
        if c not in existentes:
            tipo = "TEXT" if c in ("INGERIDO_EM", "NOME_MUNICIPIO") else "REAL"
            conn.execute(f'ALTER TABLE {tabela} ADD COLUMN "{c}" {tipo}')
            logger.info(f"{tabela}: coluna {c} adicionada")
    conn.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{tabela}_chave ON {tabela} (CODIGO_MUNICIPIO, ANO, MES)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS ingestao_progresso (alvo TEXT, rodada TEXT, codigo INTEGER, concluido_em TEXT)"
    )


def upsert(conn: sqlite3.Connection, tabela: str, df: pd.DataFrame, ano_corte: int = ANO_CORTE) -> dict:
    """Aplica a política de upsert do módulo. Retorna contagens."""
    if df.empty:
        return {"inseridas": 0}
    df = df.copy()
    df["INGERIDO_EM"] = datetime.now().isoformat(timespec="seconds")
    preparar_esquema(conn, tabela, list(df.columns))
    df.to_sql("_tmp_upsert", conn, if_exists="replace", index=False)
    cols = [c for c in df.columns if c not in CHAVES]
    on = " AND ".join(f"{tabela}.{k} = s.{k}" for k in CHAVES)

    def sets(cs):
        return ", ".join(f'"{c}" = s."{c}"' for c in cs)

    hist = [c for c in COLS_HISTORICO.get(tabela, []) if c in cols]
    if hist:
        conn.execute(f"UPDATE {tabela} SET {sets(hist)} FROM _tmp_upsert AS s WHERE {on} AND {tabela}.ANO < {ano_corte}")
    conn.execute(f"UPDATE {tabela} SET {sets(cols)} FROM _tmp_upsert AS s WHERE {on} AND {tabela}.ANO >= {ano_corte}")
    todas = ", ".join(f'"{c}"' for c in df.columns)
    cur = conn.execute(
        f"INSERT INTO {tabela} ({todas}) SELECT {todas} FROM _tmp_upsert AS s "
        f"WHERE s.ANO >= {ano_corte} AND NOT EXISTS (SELECT 1 FROM {tabela} WHERE {on})"
    )
    conn.execute("DROP TABLE _tmp_upsert")
    return {"inseridas": cur.rowcount}


def _meses_fechados(df: pd.DataFrame, hoje: date) -> pd.DataFrame:
    return df[(df["ANO"] * 12 + df["MES"]) < (hoje.year * 12 + hoje.month)]


# ------------------------------------------------------------------ coletas por cidade
def coletar_saude(cidade: pd.Series, hoje: date) -> pd.DataFrame:
    cod7 = ing.get_ibge_7(int(cidade["CODIGO_MUNICIPIO"]))
    from concurrent.futures import ThreadPoolExecutor

    doencas = ("dengue", "chikungunya", "zika")
    with ThreadPoolExecutor(max_workers=3) as ex:   # 3 chamadas simultâneas por cidade
        series = list(ex.map(lambda d: ing.fetch_infodengue(cod7, disease=d, start_year=2015, end_year=hoje.year), doencas))
    partes = []
    for doenca, d in zip(doencas, series):
        if not d.empty:
            if doenca != "dengue":   # receptividade/umidade vêm só da série de dengue (como na ingestão original)
                d = d[[c for c in d.columns if c in ("ANO", "MES") or c.endswith(doenca.upper())]]
            partes.append(d.drop(columns=["CODIGO_MUNICIPIO"], errors="ignore"))
    if not partes:
        return pd.DataFrame()
    df = partes[0]
    for p in partes[1:]:
        df = df.merge(p, on=["ANO", "MES"], how="outer")
    for c in ("CODIGO_MUNICIPIO", "LATITUDE", "LONGITUDE", "FAIXA_LATITUDE", "NOME_MUNICIPIO"):
        df[c] = cidade[c]
    return _meses_fechados(df, hoje)


def coletar_clima(cidade: pd.Series, hoje: date) -> pd.DataFrame:
    # O arquivo do Open-Meteo (ERA5) tem ~5 dias de atraso; pede até o fim do último mês fechado.
    fim = date(hoje.year, hoje.month, 1) - timedelta(days=1)
    df = ing.fetch_clima(cidade["LATITUDE"], cidade["LONGITUDE"], int(cidade["CODIGO_MUNICIPIO"]),
                         start_date=f"{ANO_CORTE}-01-01", end_date=fim.isoformat())
    if df.empty:
        return df
    for c in ("LATITUDE", "LONGITUDE", "FAIXA_LATITUDE", "NOME_MUNICIPIO"):
        df[c] = cidade[c]
    return _meses_fechados(df, hoje)


COLETORES = {"infodengue": coletar_saude, "openmeteo": coletar_clima}


# ------------------------------------------------------------------ orquestração
def cidades_do_banco(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT CODIGO_MUNICIPIO, MAX(LATITUDE) LATITUDE, MAX(LONGITUDE) LONGITUDE, "
        "MAX(FAIXA_LATITUDE) FAIXA_LATITUDE, MAX(NOME_MUNICIPIO) NOME_MUNICIPIO "
        "FROM ingestao_saude GROUP BY CODIGO_MUNICIPIO ORDER BY CODIGO_MUNICIPIO", conn)


def atualizar(alvo: str, rodada: str, limite: int | None = None, hoje: date | None = None, db_path=DB_PATH):
    hoje = hoje or date.today()
    tabela = TABELAS[alvo]
    with sqlite3.connect(db_path, timeout=120) as conn:
        cidades = cidades_do_banco(conn)
        preparar_esquema(conn, tabela, [])
        feitas = {r[0] for r in conn.execute(
            "SELECT codigo FROM ingestao_progresso WHERE alvo = ? AND rodada = ?", (alvo, rodada))}
    pendentes = cidades[~cidades["CODIGO_MUNICIPIO"].isin(feitas)]
    if limite:
        pendentes = pendentes.head(limite)
    logger.info(f"[{alvo}] rodada {rodada}: {len(feitas)} feitas, {len(pendentes)} pendentes")

    total = 0
    for i, (_, cidade) in enumerate(pendentes.iterrows(), 1):
        df = COLETORES[alvo](cidade, hoje)
        with sqlite3.connect(db_path, timeout=120) as conn:
            total += upsert(conn, tabela, df)["inseridas"]
            conn.execute("INSERT INTO ingestao_progresso VALUES (?, ?, ?, ?)",
                         (alvo, rodada, int(cidade["CODIGO_MUNICIPIO"]), datetime.now().isoformat(timespec="seconds")))
        if i % 50 == 0:
            logger.info(f"[{alvo}] {i}/{len(pendentes)} cidades, {total} linhas novas")
        time.sleep(PAUSA[alvo])
    logger.info(f"[{alvo}] concluído: {total} linhas novas")


def atualizar_enso():
    df = ing.ingest_noaa_enso(start_year=2015)
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("ingestao_enso", conn, if_exists="replace", index=False)
    logger.info(f"[noaa] ingestao_enso: {len(df)} meses")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Atualização incremental idempotente do banco")
    ap.add_argument("--alvo", choices=["infodengue", "openmeteo", "noaa", "todos"], required=True)
    ap.add_argument("--rodada", default=date.today().isoformat(), help="Identificador para retomar")
    ap.add_argument("--limite", type=int, default=None, help="Processar só N cidades (teste)")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", force=True)
    alvos = ["noaa", "infodengue", "openmeteo"] if args.alvo == "todos" else [args.alvo]
    for a in alvos:
        if a == "noaa":
            atualizar_enso()
        else:
            atualizar(a, args.rodada, args.limite)


if __name__ == "__main__":
    main()
