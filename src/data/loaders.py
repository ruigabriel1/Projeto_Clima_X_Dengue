import pandas as pd
import geopandas as gpd
from pathlib import Path

def carregar_dados_brutos(nome_arquivo: str, sep=';', encoding='utf-8', **kwargs) -> pd.DataFrame:
    """Carrega dados da pasta data/raw"""
    from src.config import DATA_RAW_DIR
    caminho = DATA_RAW_DIR / nome_arquivo
    return pd.read_csv(caminho, sep=sep, encoding=encoding, **kwargs)

def carregar_dados_processados(nome_arquivo: str, sep=',', encoding='utf-8', **kwargs) -> pd.DataFrame:
    """Carrega dados da pasta data/processed"""
    from src.config import DATA_PROCESSED_DIR
    caminho = DATA_PROCESSED_DIR / nome_arquivo
    return pd.read_csv(caminho, sep=sep, encoding=encoding, **kwargs)

def carregar_geodados(nome_arquivo: str) -> gpd.GeoDataFrame:
    """Carrega shapefiles ou geojson da pasta data/geodados"""
    from src.config import DATA_GEODADOS_DIR
    caminho = DATA_GEODADOS_DIR / nome_arquivo
    return gpd.read_file(caminho)

def salvar_dados_processados(df: pd.DataFrame, nome_arquivo: str, index=False, **kwargs):
    """Salva dataframe na pasta data/processed"""
    from src.config import DATA_PROCESSED_DIR
    caminho = DATA_PROCESSED_DIR / nome_arquivo
    df.to_csv(caminho, index=index, **kwargs)
