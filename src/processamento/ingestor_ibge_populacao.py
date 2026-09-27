"""
ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API SIDRA)
e salva na tabela 'ingestao_populacao' do banco SQLite.

Uso:
  python src/processamento/ingestor_ibge_populacao.py --codigo 4216008
  python src/processamento/ingestor_ibge_populacao.py  (todos os municípios do Sul)
"""
import os
import sqlite3
import argparse
import logging
import requests
import pandas as pd
import time
from src.config import DATA_PROCESSED_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = DATA_PROCESSED_DIR / "dengue_analytics.db"

ANOS = list(range(2015, 2026))


def fetch_populacao_ibge(codigo_ibge_7: str) -> pd.DataFrame:
    """Busca população estimada do IBGE via API SIDRA (tabela 6579)."""
    periodos = ",".join(str(a) for a in ANOS)
    url = (
        f"https://apisidra.ibge.gov.br/values/t/6579/n6/{codigo_ibge_7}"
        f"/v/9324/p/{periodos}/f/n"
    )
    logger.info(f"[IBGE] Requisitando população para município {codigo_ibge_7}...")

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if len(data) <= 1:
        logger.warning(f"[IBGE] Nenhum dado retornado para {codigo_ibge_7}.")
        return pd.DataFrame()

    records = []
    for r in data[1:]:  # Pula o header
        valor = r.get("V", "")
        ano = r.get("D3N", "")
        if valor and valor != "-" and ano:
            records.append({
                "CODIGO_MUNICIPIO": codigo_ibge_7[:6],  # 6 dígitos (padrão do projeto)
                "ANO": int(ano),
                "POPULACAO": int(valor),
            })

    df = pd.DataFrame(records)
    logger.info(f"[IBGE] {len(df)} registros de população obtidos para {codigo_ibge_7}.")
    return df


def get_ibge_7(code):
    """Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos."""
    s = str(code)
    weights = [1, 2, 1, 2, 1, 2]
    total = sum(
        (int(s[i]) * weights[i] // 10 + int(s[i]) * weights[i] % 10)
        if int(s[i]) * weights[i] >= 10 else int(s[i]) * weights[i]
        for i in range(6)
    )
    dv = (10 - (total % 10)) % 10
    return str(code) + str(dv)


def main():
    parser = argparse.ArgumentParser(description="Ingestor de População do IBGE (API SIDRA)")
    parser.add_argument(
        "--codigo", type=str, default=None,
        help="Código IBGE 7 dígitos de um município específico (ex: 4216008 para São Carlos/SC)"
    )
    args = parser.parse_args()

    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # Garante que a tabela existe
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ingestao_populacao (
            CODIGO_MUNICIPIO TEXT,
            ANO INTEGER,
            POPULACAO INTEGER
        )
    """)

    if args.codigo:
        # Modo: município específico
        df = fetch_populacao_ibge(args.codigo)
        if not df.empty:
            # Remove dados antigos desse município antes de inserir
            conn.execute(
                "DELETE FROM ingestao_populacao WHERE CODIGO_MUNICIPIO = ?",
                (args.codigo[:6],)
            )
            df.to_sql("ingestao_populacao", conn, if_exists="append", index=False)
            logger.info(f"[IBGE] Salvo {len(df)} registros para {args.codigo} na tabela ingestao_populacao.")
    else:
        # Modo: todos os municípios já presentes no banco (ingestao_saude)
        logger.info("[IBGE] Modo completo: buscando população para todos os municípios do banco...")
        try:
            df_cidades = pd.read_sql_query(
                "SELECT DISTINCT CODIGO_MUNICIPIO FROM ingestao_saude", conn
            )
        except Exception:
            logger.error("Tabela ingestao_saude não encontrada. Rode o ingestor de saúde primeiro.")
            conn.close()
            return

        # Verificar quais já foram baixados
        try:
            df_existente = pd.read_sql_query(
                "SELECT DISTINCT CODIGO_MUNICIPIO FROM ingestao_populacao", conn
            )
            ja_baixados = set(df_existente["CODIGO_MUNICIPIO"].astype(str))
        except Exception:
            ja_baixados = set()

        codigos = df_cidades["CODIGO_MUNICIPIO"].astype(str).unique().tolist()
        pendentes = [c for c in codigos if c not in ja_baixados]
        logger.info(f"[IBGE] {len(ja_baixados)} já baixados, {len(pendentes)} pendentes.")

        for i, code_6 in enumerate(pendentes):
            code_7 = get_ibge_7(code_6)
            try:
                df = fetch_populacao_ibge(code_7)
                if not df.empty:
                    df.to_sql("ingestao_populacao", conn, if_exists="append", index=False)
                time.sleep(0.3)  # Respeitar rate limit do IBGE
            except Exception as e:
                logger.error(f"[IBGE] Erro para {code_7}: {e}")

            if (i + 1) % 50 == 0:
                logger.info(f"[IBGE] Progresso: {i + 1}/{len(pendentes)}")

    # Relatório final
    try:
        count = conn.execute("SELECT COUNT(*) FROM ingestao_populacao").fetchone()[0]
        cidades = conn.execute("SELECT COUNT(DISTINCT CODIGO_MUNICIPIO) FROM ingestao_populacao").fetchone()[0]
        logger.info(f"[IBGE] Tabela ingestao_populacao: {count} registros, {cidades} municípios.")
    except Exception:
        pass

    conn.close()
    logger.info("=== INGESTÃO IBGE CONCLUÍDA ===")


if __name__ == "__main__":
    main()
