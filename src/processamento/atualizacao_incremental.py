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
  - InfoDengue: as últimas 12 semanas (casos, casos_est, Rt, p_rt1...) de dengue e chikungunya são copiadas
    em `ingestao_infodengue_snapshot` com a data da coleta. Só acrescenta; é o registro do que se sabia
    em cada data (o InfoDengue recalcula o histórico).

Uso:
  python -m src.processamento.atualizacao_incremental --alvo todos
  python -m src.processamento.atualizacao_incremental --alvo infodengue --limite 5
"""
from __future__ import annotations

import argparse
import logging
import os
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
TABELAS = {"infodengue": "ingestao_saude", "openmeteo": "ingestao_clima",
           "backfill-infodengue": "ingestao_saude", "backfill-openmeteo": "ingestao_clima"}
# Colunas que podem ser acrescentadas a meses já gravados com ANO < ANO_CORTE (casos e clima nunca):
# o alerta NIVEL_* (benchmark) e, pelo protocolo v7, o Rt estimado pelo InfoDengue.
COLS_RT = [f"{c}_{d}" for d in ("DENGUE", "CHIKUNGUNYA") for c in ("RT_MEDIO", "RT_ULT", "P_RT1")]
COLS_HISTORICO = {"ingestao_saude": ["NIVEL_DENGUE", "NIVEL_CHIKUNGUNYA", "NIVEL_ZIKA", *COLS_RT],
                  "ingestao_clima": []}

# Backfill do protocolo v7: anos anteriores à série dos experimentos v4–v6, só inserção.
ANO_INICIO_SERIE = 2015
BACKFILL_SAUDE = (2010, 2014)                     # dengue; chikungunya sem vigilância antes de 2015
BACKFILL_CLIMA = ("2009-07-01", "2014-12-31")     # 6 meses antes, para as defasagens de jan/2010
PAUSA = {"infodengue": 0.3, "openmeteo": 1.0, "backfill-infodengue": 0.3, "backfill-openmeteo": 1.0}
TABELA_SNAPSHOT = "ingestao_infodengue_snapshot"
DOENCAS_SNAPSHOT = ("dengue", "chikungunya")   # zika fora do projeto


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
    tmp = f"_tmp_upsert_{tabela}_{os.getpid()}"   # único por processo: ingestões em paralelo no mesmo banco
    df.to_sql(tmp, conn, if_exists="replace", index=False)
    cols = [c for c in df.columns if c not in CHAVES]
    on = " AND ".join(f"{tabela}.{k} = s.{k}" for k in CHAVES)

    def sets(cs):
        return ", ".join(f'"{c}" = s."{c}"' for c in cs)

    hist = [c for c in COLS_HISTORICO.get(tabela, []) if c in cols]
    if hist:
        conn.execute(f"UPDATE {tabela} SET {sets(hist)} FROM {tmp} AS s WHERE {on} AND {tabela}.ANO < {ano_corte}")
    conn.execute(f"UPDATE {tabela} SET {sets(cols)} FROM {tmp} AS s WHERE {on} AND {tabela}.ANO >= {ano_corte}")
    todas = ", ".join(f'"{c}"' for c in df.columns)
    cur = conn.execute(
        f"INSERT INTO {tabela} ({todas}) SELECT {todas} FROM {tmp} AS s "
        f"WHERE s.ANO >= {ano_corte} AND NOT EXISTS (SELECT 1 FROM {tabela} WHERE {on})"
    )
    conn.execute(f"DROP TABLE {tmp}")
    return {"inseridas": cur.rowcount}


def inserir_historico(conn: sqlite3.Connection, tabela: str, df: pd.DataFrame,
                      ano_limite: int = ANO_INICIO_SERIE) -> dict:
    """Backfill: só INSERE meses com ANO < ano_limite que ainda não existem. Nunca faz UPDATE."""
    if df.empty:
        return {"inseridas": 0}
    df = df[df["ANO"] < ano_limite].copy()
    if df.empty:
        return {"inseridas": 0}
    df["INGERIDO_EM"] = datetime.now().isoformat(timespec="seconds")
    preparar_esquema(conn, tabela, list(df.columns))
    tmp = f"_tmp_backfill_{tabela}_{os.getpid()}"
    df.to_sql(tmp, conn, if_exists="replace", index=False)
    on = " AND ".join(f"{tabela}.{k} = s.{k}" for k in CHAVES)
    todas = ", ".join(f'"{c}"' for c in df.columns)
    cur = conn.execute(f"INSERT INTO {tabela} ({todas}) SELECT {todas} FROM {tmp} AS s "
                       f"WHERE s.ANO < {ano_limite} AND NOT EXISTS (SELECT 1 FROM {tabela} WHERE {on})")
    conn.execute(f"DROP TABLE {tmp}")
    return {"inseridas": cur.rowcount}


def _meses_fechados(df: pd.DataFrame, hoje: date) -> pd.DataFrame:
    return df[(df["ANO"] * 12 + df["MES"]) < (hoje.year * 12 + hoje.month)]


# ------------------------------------------------------------------ coletas por cidade
def coletar_saude(cidade: pd.Series, hoje: date):
    """Série mensal da cidade (para ingestao_saude) e cópia das últimas semanas (para o snapshot)."""
    cod7 = ing.get_ibge_7(int(cidade["CODIGO_MUNICIPIO"]))
    from concurrent.futures import ThreadPoolExecutor

    doencas = ("dengue", "chikungunya", "zika")
    with ThreadPoolExecutor(max_workers=3) as ex:   # 3 chamadas simultâneas por cidade
        semanais = list(ex.map(lambda d: ing.fetch_infodengue_semanal(cod7, disease=d, start_year=2015,
                                                                      end_year=hoje.year), doencas))
    snaps = []
    for doenca, s in zip(doencas, semanais):
        if doenca in DOENCAS_SNAPSHOT and not s.empty:
            sn = ing.snapshot_semanal(s)
            sn["DOENCA"] = doenca
            snaps.append(sn)
    snapshot = pd.concat(snaps, ignore_index=True) if snaps else pd.DataFrame()
    if not snapshot.empty:
        snapshot["CODIGO_MUNICIPIO"] = int(cidade["CODIGO_MUNICIPIO"])
    series = [ing.agregar_infodengue_mensal(s, cod7, d) for d, s in zip(doencas, semanais)]
    partes = []
    for doenca, d in zip(doencas, series):
        if not d.empty:
            if doenca != "dengue":   # receptividade/umidade vêm só da série de dengue (como na ingestão original)
                d = d[[c for c in d.columns if c in ("ANO", "MES") or c.endswith(doenca.upper())]]
            partes.append(d.drop(columns=["CODIGO_MUNICIPIO"], errors="ignore"))
    extras = {TABELA_SNAPSHOT: snapshot}
    if not partes:
        return pd.DataFrame(), extras
    df = partes[0]
    for p in partes[1:]:
        df = df.merge(p, on=["ANO", "MES"], how="outer")
    for c in ("CODIGO_MUNICIPIO", "LATITUDE", "LONGITUDE", "FAIXA_LATITUDE", "NOME_MUNICIPIO"):
        df[c] = cidade[c]
    return _meses_fechados(df, hoje), extras


def gravar_snapshot(conn: sqlite3.Connection, snap: pd.DataFrame, coletado_em: date) -> int:
    """
    Guarda a cópia das últimas semanas como a API as entregou nesta data (só acrescenta).
    O InfoDengue recalcula o histórico, então esta é a única forma de saber, no futuro, o que se sabia na
    época (necessário para avaliar um nowcast). Rodar de novo no mesmo dia não duplica.
    """
    if snap is None or snap.empty:
        return 0
    s = snap.copy()
    s["COLETADO_EM"] = coletado_em.isoformat()
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {TABELA_SNAPSHOT} (CODIGO_MUNICIPIO INTEGER, DOENCA TEXT, SE INTEGER, "
        "DATA_INI_SE TEXT, casos REAL, casos_est REAL, casos_est_min REAL, casos_est_max REAL, Rt REAL, "
        "p_rt1 REAL, versao_modelo TEXT, COLETADO_EM TEXT)")
    conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{TABELA_SNAPSHOT} ON {TABELA_SNAPSHOT} "
                 "(CODIGO_MUNICIPIO, DOENCA, SE, COLETADO_EM)")
    cols = ["CODIGO_MUNICIPIO", "DOENCA", "SE", "DATA_INI_SE", *ing.COLS_SNAPSHOT, "COLETADO_EM"]
    s = s[cols].dropna(subset=["SE"])
    s["SE"] = s["SE"].astype(int)
    ph = ", ".join("?" for _ in cols)
    antes = conn.total_changes
    conn.executemany(f"INSERT OR IGNORE INTO {TABELA_SNAPSHOT} ({', '.join(cols)}) VALUES ({ph})",
                     s.astype(object).where(s.notna(), None).itertuples(index=False, name=None))
    return conn.total_changes - antes


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


def coletar_saude_historico(cidade: pd.Series, hoje: date) -> pd.DataFrame:
    """Backfill v7: dengue de 2010–2014 (casos, receptividade, umidade, alerta, Rt). Sem chik/zika."""
    cod7 = ing.get_ibge_7(int(cidade["CODIGO_MUNICIPIO"]))
    a0, a1 = BACKFILL_SAUDE
    df = ing.fetch_infodengue(cod7, disease="dengue", start_year=a0, end_year=a1)
    if df.empty:
        return df
    df = df[(df["ANO"] >= a0) & (df["ANO"] <= a1)].drop(columns=["CODIGO_MUNICIPIO"])
    for c in ("CODIGO_MUNICIPIO", "LATITUDE", "LONGITUDE", "FAIXA_LATITUDE", "NOME_MUNICIPIO"):
        df[c] = cidade[c]
    return df


def coletar_clima_historico(cidade: pd.Series, hoje: date) -> pd.DataFrame:
    """Backfill v7: clima de 2009-07 a 2014-12, mesmas variáveis e agregação mensal da série atual."""
    ini, fim = BACKFILL_CLIMA
    df = ing.fetch_clima(cidade["LATITUDE"], cidade["LONGITUDE"], int(cidade["CODIGO_MUNICIPIO"]),
                         start_date=ini, end_date=fim)
    if df.empty:
        return df
    for c in ("LATITUDE", "LONGITUDE", "FAIXA_LATITUDE", "NOME_MUNICIPIO"):
        df[c] = cidade[c]
    return df


COLETORES = {"infodengue": coletar_saude, "openmeteo": coletar_clima,
             "backfill-infodengue": coletar_saude_historico, "backfill-openmeteo": coletar_clima_historico}
GRAVAR = {"backfill-infodengue": inserir_historico, "backfill-openmeteo": inserir_historico}


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

    total = n_snap = 0
    for i, (_, cidade) in enumerate(pendentes.iterrows(), 1):
        res = COLETORES[alvo](cidade, hoje)
        df, extras = res if isinstance(res, tuple) else (res, {})
        with sqlite3.connect(db_path, timeout=120) as conn:
            total += GRAVAR.get(alvo, upsert)(conn, tabela, df)["inseridas"]
            n_snap += gravar_snapshot(conn, extras.get(TABELA_SNAPSHOT), hoje)
            conn.execute("INSERT INTO ingestao_progresso VALUES (?, ?, ?, ?)",
                         (alvo, rodada, int(cidade["CODIGO_MUNICIPIO"]), datetime.now().isoformat(timespec="seconds")))
        if i % 50 == 0:
            logger.info(f"[{alvo}] {i}/{len(pendentes)} cidades, {total} linhas novas")
        time.sleep(PAUSA[alvo])
    logger.info(f"[{alvo}] concluído: {total} linhas novas" + (f", {n_snap} semanas no snapshot" if n_snap else ""))


def atualizar_enso():
    df = ing.ingest_noaa_enso(start_year=2015)
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("ingestao_enso", conn, if_exists="replace", index=False)
    logger.info(f"[noaa] ingestao_enso: {len(df)} meses")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Atualização incremental idempotente do banco")
    ap.add_argument("--alvo", choices=["infodengue", "openmeteo", "noaa", "todos", "backfill", "backfill-infodengue",
                                       "backfill-openmeteo", "backfill-populacao"], required=True,
                    help="backfill = protocolo v7: dengue 2010–2014, clima 2009-07..2014-12 e população (só insere)")
    ap.add_argument("--rodada", default=date.today().isoformat(), help="Identificador para retomar")
    ap.add_argument("--limite", type=int, default=None, help="Processar só N cidades (teste)")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", force=True)
    alvos = {"todos": ["noaa", "infodengue", "openmeteo"],
             "backfill": ["backfill-populacao", "backfill-infodengue", "backfill-openmeteo"]}.get(args.alvo, [args.alvo])
    for a in alvos:
        if a == "noaa":
            atualizar_enso()
        elif a == "backfill-populacao":
            from src.processamento.ingestor_ibge_populacao import backfill_populacao
            backfill_populacao()
        else:
            atualizar(a, args.rodada, args.limite)


if __name__ == "__main__":
    main()
