"""
Módulo responsável por construir o painel base a partir do banco de dados (SQLite).
Separa a preocupação de IO e queries SQL da lógica do modelo.
"""
import sqlite3
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

def build_base_panel(root_dir: Path, modo: str = "regional") -> pd.DataFrame:
    db_path = root_dir / "data" / "processed" / "dengue_analytics.db"
    
    logger.info("build_base_panel -> Lendo tabelas desacopladas do SQLite (Saúde + Clima + ENSO)")
    
    if not db_path.exists():
        raise FileNotFoundError(f"Banco da API não encontrado em {db_path}. Execute os robôs de ingestão.")
        
    conn = sqlite3.connect(db_path)
    
    try:
        df_saude = pd.read_sql_query("SELECT * FROM ingestao_saude", conn)
        logger.info(f"Tabela de Saúde lida: {len(df_saude)} registros.")
    except Exception:
        df_saude = pd.DataFrame()
        
    try:
        df_clima = pd.read_sql_query("SELECT * FROM ingestao_clima", conn)
        logger.info(f"Tabela de Clima lida: {len(df_clima)} registros.")
    except Exception:
        df_clima = pd.DataFrame()
        
    conn.close()
    
    if df_saude.empty and df_clima.empty:
        raise ValueError("Nenhuma tabela tem dados. Rode o ingestor primeiro.")
        
    if not df_saude.empty and not df_clima.empty:
        cols_to_drop = ['LATITUDE', 'LONGITUDE', 'FAIXA_LATITUDE', 'NOME_MUNICIPIO']
        df_clima = df_clima.drop(columns=[c for c in cols_to_drop if c in df_clima.columns])
        panel = pd.merge(df_saude, df_clima, on=['CODIGO_MUNICIPIO', 'ANO', 'MES'], how='outer')
    else:
        panel = df_saude if not df_saude.empty else df_clima
    
    rename_map = {
        "CODIGO_MUNICIPIO": "code",
        "NOME_MUNICIPIO": "city_name",
        "ANO": "year",
        "MES": "month",
        "LATITUDE": "latitude",
        "LONGITUDE": "longitude",
        "FAIXA_LATITUDE": "lat_faixa_id",
        "temp_media": "temp_media",
        "temp_maxima": "temp_maxima",
        "temp_minima": "temp_minima",
        "precipitacao": "precipitacao",
        "CASOS_DENGUE": "dengue_cases",
        "ENSO": "enso"
    }
    panel = panel.rename(columns={k: v for k, v in rename_map.items() if k in panel.columns})
    
    if "code" in panel.columns:
        panel["code"] = panel["code"].astype(str).str.extract(r"(\d{6})", expand=False)
        
    # Assegurar que ENSO existe (pode vir nulo de alguns joins)
    if "enso" not in panel.columns:
        panel["enso"] = 0.0
        
    return panel
