"""
Pipeline ETL para criação do Data Warehouse Analítico (SQLite).
Lê arquivos CSV da camada Silver e materializa tabelas para consumo analítico e Machine Learning.
"""

import sqlite3
import logging
from pathlib import Path

# Ajuste do path para rodar da raiz
import sys
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def build_dw():
    db_path = BASE_DIR / 'data' / 'processed' / 'dengue_analytics.db'
    logger.info(f"Iniciando construção do Data Warehouse em: {db_path}")

    # Reutilizar a lógica existente para carregar os dados base (csvs_latitude)
    from src.processamento.motor_lote_modelagem_v2_por_latitude import build_base_panel
    panel, lookup = build_base_panel(BASE_DIR)

    # Conexão com o banco (cria se não existir)
    conn = sqlite3.connect(db_path)

    # ==========================================
    # CAMADA SILVER (Star Schema / Dimensões e Fatos)
    # ==========================================
    logger.info("Criando tabela Silver: dim_municipio")
    dim_mun = lookup.copy()
    dim_mun = dim_mun.rename(columns={'lat_faixa_id': 'regiao_latitude_id'})
    dim_mun.to_sql('dim_municipio', conn, if_exists='replace', index=False)

    logger.info("Criando tabela Silver: fato_epidemiologica")
    fato_epi = panel[['code', 'year', 'month', 'dengue_cases']].copy()
    fato_epi.to_sql('fato_epidemiologica', conn, if_exists='replace', index=False)

    logger.info("Criando tabela Silver: fato_climatica")
    fato_clim = panel[['code', 'year', 'month', 'temp_media', 'precipitacao']].copy()
    fato_clim.to_sql('fato_climatica', conn, if_exists='replace', index=False)

    logger.info("Criando tabela Silver: fato_oceanica")
    fato_oc = panel[['year', 'month', 'enso']].drop_duplicates().copy()
    fato_oc.to_sql('fato_oceanica', conn, if_exists='replace', index=False)

    # ==========================================
    # CAMADA GOLD (Feature Store / One Big Table)
    # ==========================================
    logger.info("Construindo tabela Gold: gold_painel_ml (Feature Engineering)...")
    df = panel.copy()
    
    # Ordenar rigorosamente para garantir lags temporais corretos
    df = df.sort_values(['code', 'year', 'month']).reset_index(drop=True)

    # Features Climáticas
    df['temp_lag3'] = df.groupby('code')['temp_media'].shift(3)
    df['prec_lag3'] = df.groupby('code')['precipitacao'].shift(3)
    df['enso_lag3'] = df.groupby('code')['enso'].shift(3)

    # Features Epidemiológicas
    df['casos_lag1'] = df.groupby('code')['dengue_cases'].shift(1)
    df['casos_lag12'] = df.groupby('code')['dengue_cases'].shift(12)

    # Proxy Populacional
    max_hist = df.groupby('code')['dengue_cases'].max().rename('max_historico')
    df = df.merge(max_hist, on='code', how='left')

    # Limpeza para ML (remove nulos gerados pelos lags)
    gold_df = df.dropna().copy()
    
    # Salvar a "One Big Table" na camada Gold
    gold_df.to_sql('gold_painel_ml', conn, if_exists='replace', index=False)
    
    logger.info(f"Sucesso! Tabela gold_painel_ml materializada com {len(gold_df):,} registros.")
    
    # Índices SQL para acelerar as consultas
    logger.info("Criando índices de performance no SQLite...")
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gold_code ON gold_painel_ml(code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gold_year ON gold_painel_ml(year);")
    conn.commit()

    conn.close()
    logger.info("Data Warehouse concluído e pronto para uso.")

if __name__ == "__main__":
    build_dw()