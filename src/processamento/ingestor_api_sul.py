import os
import sqlite3
import pandas as pd
import requests
import geobr
import logging
from tqdm import tqdm
from src.config import DATA_PROCESSED_DIR
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = DATA_PROCESSED_DIR / "dengue_analytics.db"

FAIXAS_LATITUDE = [
    (22.0, 23.0, 1), (23.0, 24.0, 2), (24.0, 25.5, 3), (25.5, 27.0, 4),
    (27.0, 28.0, 5), (28.0, 29.5, 6), (29.5, 31.0, 7), (31.0, 34.0, 8)
]

def obter_faixa_latitude(lat):
    lat_abs = abs(lat)
    for min_lat, max_lat, faixa in FAIXAS_LATITUDE:
        if min_lat <= lat_abs < max_lat:
            return faixa
    return None

def fetch_infodengue(geocode, disease='dengue', start_year=2015, end_year=2025):
    url = f"https://info.dengue.mat.br/api/alertcity?geocode={geocode}&disease={disease}&format=json&ew_start=1&ew_end=53&ey_start={start_year}&ey_end={end_year}"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if not data: return pd.DataFrame()
            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data_iniSE'], unit='ms')
            df['ANO'] = df['data'].dt.year
            df['MES'] = df['data'].dt.month
            
            # Agrupar mensalmente. 
            # Receptivo e umidade pegamos a média do mês.
            agg_rules = {
                'casos': 'sum',
                'casos_est': 'sum',
                'receptivo': 'mean',
                'umidmed': 'mean',
                'umidmax': 'mean',
                'umidmin': 'mean'
            }
            # Evita erro se a chave não existir na API para alguma doença
            agg_rules = {k: v for k, v in agg_rules.items() if k in df.columns}
            
            df_grouped = df.groupby(['ANO', 'MES']).agg(agg_rules).reset_index()
            
            # Renomear para incluir a doença nos casos
            df_grouped = df_grouped.rename(columns={
                'casos': f'CASOS_{disease.upper()}',
                'casos_est': f'CASOS_EST_{disease.upper()}'
            })
            
            df_grouped['CODIGO_MUNICIPIO'] = geocode
            return df_grouped
    except Exception as e:
        logger.error(f"Error fetching {disease} for {geocode}: {e}")
    return pd.DataFrame()

def sleep_until_next_hour():
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=2, second=0, microsecond=0)
    sleep_seconds = (next_hour - now).total_seconds()
    logger.warning(f"Rate limit atingido! Pausando por {sleep_seconds/60:.1f} minutos até as {next_hour.strftime('%H:%M')}.")
    time.sleep(sleep_seconds)

def fetch_clima(lat, lon, geocode, start_year=2015, end_year=2025):
    daily_vars = "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,windgusts_10m_max,soil_temperature_0_to_7cm_mean"
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_year}-01-01&end_date={end_year}-12-31&daily={daily_vars}&timezone=America%2FSao_Paulo"
    
    while True:
        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                d = resp.json()
                if 'daily' not in d: return pd.DataFrame()
                
                daily_data = d['daily']
                df = pd.DataFrame({
                    'data': pd.to_datetime(daily_data['time']),
                    'temp_media': daily_data.get('temperature_2m_mean', []),
                    'temp_maxima': daily_data.get('temperature_2m_max', []),
                    'temp_minima': daily_data.get('temperature_2m_min', []),
                    'precipitacao': daily_data.get('precipitation_sum', []),
                    'vel_vento_max': daily_data.get('windspeed_10m_max', []),
                    'rajada_vento_max': daily_data.get('windgusts_10m_max', []),
                    'temp_solo': daily_data.get('soil_temperature_0_to_7cm_mean', [])
                })
                
                df['ANO'] = df['data'].dt.year
                df['MES'] = df['data'].dt.month
                df_grouped = df.groupby(['ANO', 'MES']).agg({
                    'temp_media': 'mean',
                    'temp_maxima': 'mean',
                    'temp_minima': 'mean',
                    'precipitacao': 'sum',
                    'vel_vento_max': 'mean',
                    'rajada_vento_max': 'mean',
                    'temp_solo': 'mean'
                }).reset_index()
                
                df_grouped['CODIGO_MUNICIPIO'] = geocode
                return df_grouped
            elif resp.status_code == 429:
                sleep_until_next_hour()
                continue
            else:
                logger.error(f"Erro {resp.status_code} clima para {geocode}")
                break
        except Exception as e:
            logger.error(f"Timeout clima para {geocode}: {e}")
            time.sleep(10)
    return pd.DataFrame()

def process_municipality(row):
    geocode = row['code_muni']
    geocode_7 = row['code_muni_7']
    lat = row['latitude']
    lon = row['longitude']
    
    # Doenças
    df_dengue = fetch_infodengue(geocode_7, disease='dengue')
    df_zika = fetch_infodengue(geocode_7, disease='zika')
    df_chik = fetch_infodengue(geocode_7, disease='chikungunya')
    
    # Merge das 3 doenças
    df_saude = df_dengue
    if not df_zika.empty:
        # Pega so os casos de zika para não duplicar umidade/receptivo
        cols_to_use = ['ANO', 'MES', 'CASOS_ZIKA', 'CASOS_EST_ZIKA']
        cols_to_use = [c for c in cols_to_use if c in df_zika.columns]
        cols_to_use += ['ANO', 'MES'] # ensure join keys
        cols_to_use = list(set(cols_to_use))
        df_saude = pd.merge(df_saude, df_zika[cols_to_use], on=['ANO', 'MES'], how='outer')
        
    if not df_chik.empty:
        cols_to_use = ['ANO', 'MES', 'CASOS_CHIKUNGUNYA', 'CASOS_EST_CHIKUNGUNYA']
        cols_to_use = [c for c in cols_to_use if c in df_chik.columns]
        cols_to_use += ['ANO', 'MES']
        cols_to_use = list(set(cols_to_use))
        df_saude = pd.merge(df_saude, df_chik[cols_to_use], on=['ANO', 'MES'], how='outer')
    
    if not df_saude.empty:
        df_saude['CODIGO_MUNICIPIO'] = geocode # override para 6 dígitos
    
    # Clima
    df_clima = fetch_clima(lat, lon, geocode)
    
    if df_saude.empty or df_clima.empty:
        return pd.DataFrame()
    
    # Final Merge
    df_merged = pd.merge(df_saude, df_clima, on=['CODIGO_MUNICIPIO', 'ANO', 'MES'], how='outer')
    df_merged['LATITUDE'] = lat
    df_merged['LONGITUDE'] = lon
    df_merged['FAIXA_LATITUDE'] = row['faixa_latitude']
    df_merged['NOME_MUNICIPIO'] = row['name_muni']
    
    return df_merged

def main():
    import geopandas as gpd
    logger.info("Carregando municípios do Sul...")
    gdf_municipios = gpd.read_file("data/geodados/cache_municipios_sul.gpkg")
    gdf_municipios['code_muni_7'] = gdf_municipios['code_muni'].astype(str)
    gdf_municipios['code_muni'] = gdf_municipios['code_muni_7'].str[:6].astype(int)
    gdf_municipios['latitude'] = gdf_municipios.geometry.centroid.y
    gdf_municipios['longitude'] = gdf_municipios.geometry.centroid.x
    
    gdf_sul = gdf_municipios[(gdf_municipios['code_muni'] >= 410000) & (gdf_municipios['code_muni'] < 440000)].copy()
    gdf_sul['faixa_latitude'] = gdf_sul['latitude'].apply(obter_faixa_latitude)
    gdf_sul = gdf_sul.dropna(subset=['faixa_latitude'])
    
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    processed_cities = set()
    try:
        df_existente = pd.read_sql_query("SELECT DISTINCT CODIGO_MUNICIPIO FROM ingestao_api", conn)
        processed_cities = set(df_existente['CODIGO_MUNICIPIO'])
        logger.info(f"Retomando progresso: {len(processed_cities)} cidades já processadas no banco.")
    except:
        logger.info("Tabela ingestao_api ainda não existe (nova ingestão).")
        
    gdf_pendentes = gdf_sul[~gdf_sul['code_muni'].isin(processed_cities)]
    
    logger.info(f"Total pendentes para baixar: {len(gdf_pendentes)}")
    
    for _, row in tqdm(gdf_pendentes.iterrows(), total=len(gdf_pendentes), desc="Ingestão Chunking"):
        df_res = process_municipality(row)
        if not df_res.empty:
            df_res.to_sql('ingestao_api', conn, if_exists='append', index=False)
        time.sleep(1) # pausa anti-rate limit basica
        
    conn.close()
    logger.info("Ingestão 2015-2025 concluída com as novas variáveis!")

if __name__ == '__main__':
    main()
