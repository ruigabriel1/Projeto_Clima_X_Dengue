import os
import sqlite3
import pandas as pd
import requests
import argparse
import logging
from tqdm import tqdm
from src.config import DATA_PROCESSED_DIR
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = DATA_PROCESSED_DIR / "dengue_analytics.db"

def get_ibge_7(code):
    s = str(code)
    weights = [1, 2, 1, 2, 1, 2]
    total = sum(
        (int(s[i]) * weights[i] // 10 + int(s[i]) * weights[i] % 10) 
        if int(s[i]) * weights[i] >= 10 else int(s[i]) * weights[i]
        for i in range(6)
    )
    dv = (10 - (total % 10)) % 10
    return str(code) + str(dv)

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
            
            for col in ['casos', 'casos_est', 'receptivo', 'umidmed', 'umidmax', 'umidmin']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            agg_rules = {
                'casos': 'sum',
                'casos_est': 'sum',
                'receptivo': 'mean',
                'umidmed': 'mean',
                'umidmax': 'mean',
                'umidmin': 'mean'
            }
            agg_rules = {k: v for k, v in agg_rules.items() if k in df.columns}
            df_grouped = df.groupby(['ANO', 'MES']).agg(agg_rules).reset_index()
            
            df_grouped = df_grouped.rename(columns={
                'casos': f'CASOS_{disease.upper()}',
                'casos_est': f'CASOS_EST_{disease.upper()}'
            })
            
            df_grouped['CODIGO_MUNICIPIO'] = geocode
            return df_grouped
    except Exception as e:
        logger.error(f"[SAÚDE - InfoDengue] Erro ao baixar {disease} para a cidade {geocode}: {e}")
    return pd.DataFrame()

def sleep_until_next_hour():
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=2, second=0, microsecond=0)
    sleep_seconds = (next_hour - now).total_seconds()
    logger.warning(f"[CLIMA - OpenMeteo] RATE LIMIT ATINGIDO! O servidor nos bloqueou por excesso de velocidade.")
    logger.warning(f"[CLIMA - OpenMeteo] MODO DORMINHOCO ATIVADO: O robô ficará pausado por {sleep_seconds/60:.1f} minutos (até as {next_hour.strftime('%H:%M')}).")
    logger.warning(f"[CLIMA - OpenMeteo] Ele acordará e continuará o download automaticamente. Você NÃO precisa aprovar nada.")
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
                logger.error(f"[CLIMA - OpenMeteo] Erro fatal {resp.status_code} para a cidade {geocode}")
                break
        except Exception as e:
            logger.error(f"[CLIMA - OpenMeteo] Timeout para a cidade {geocode}: {e}. Retentando em 10s...")
            time.sleep(10)
    return pd.DataFrame()

def process_saude(row):
    geocode = row['code_muni']
    geocode_7 = row['code_muni_7']
    lat = row['latitude']
    lon = row['longitude']
    
    df_dengue = fetch_infodengue(geocode_7, disease='dengue')
    df_zika = fetch_infodengue(geocode_7, disease='zika')
    df_chik = fetch_infodengue(geocode_7, disease='chikungunya')
    
    df_saude = df_dengue
    if not df_zika.empty:
        cols_to_use = ['ANO', 'MES', 'CASOS_ZIKA', 'CASOS_EST_ZIKA']
        cols_to_use = [c for c in cols_to_use if c in df_zika.columns] + ['ANO', 'MES']
        cols_to_use = list(set(cols_to_use))
        df_saude = pd.merge(df_saude, df_zika[cols_to_use], on=['ANO', 'MES'], how='outer')
        
    if not df_chik.empty:
        cols_to_use = ['ANO', 'MES', 'CASOS_CHIKUNGUNYA', 'CASOS_EST_CHIKUNGUNYA']
        cols_to_use = [c for c in cols_to_use if c in df_chik.columns] + ['ANO', 'MES']
        cols_to_use = list(set(cols_to_use))
        df_saude = pd.merge(df_saude, df_chik[cols_to_use], on=['ANO', 'MES'], how='outer')
    
    if df_saude.empty:
        return pd.DataFrame()
        
    df_saude['CODIGO_MUNICIPIO'] = geocode # override para 6 dígitos
    df_saude['LATITUDE'] = lat
    df_saude['LONGITUDE'] = lon
    df_saude['FAIXA_LATITUDE'] = row['faixa_latitude']
    df_saude['NOME_MUNICIPIO'] = row['name_muni']
    
    return df_saude

def process_clima(row):
    geocode = row['code_muni']
    lat = row['latitude']
    lon = row['longitude']
    
    df_clima = fetch_clima(lat, lon, geocode)
    if df_clima.empty:
        return pd.DataFrame()
        
    df_clima['LATITUDE'] = lat
    df_clima['LONGITUDE'] = lon
    df_clima['FAIXA_LATITUDE'] = row['faixa_latitude']
    df_clima['NOME_MUNICIPIO'] = row['name_muni']
    
    return df_clima

def main():
    parser = argparse.ArgumentParser(description="Ingestor de APIs (Dupla Personalidade)")
    parser.add_argument('--alvo', type=str, choices=['infodengue', 'openmeteo'], required=True, help="Qual API baixar: infodengue ou openmeteo")
    args = parser.parse_args()
    
    alvo = args.alvo
    tabela_alvo = 'ingestao_saude' if alvo == 'infodengue' else 'ingestao_clima'
    process_func = process_saude if alvo == 'infodengue' else process_clima
    
    logger.info(f"=== INICIANDO ROBÔ ALVO: {alvo.upper()} ===")
    logger.info(f"Os dados serão salvos na tabela '{tabela_alvo}' do banco {DB_PATH.name}")

    import geopandas as gpd
    gdf_municipios = gpd.read_file("data/geodados/cache_municipios_sul.gpkg")
    gdf_municipios['code_muni'] = gdf_municipios['code_muni'].astype(int)
    gdf_municipios['code_muni_7'] = gdf_municipios['code_muni'].apply(get_ibge_7)
    gdf_municipios['latitude'] = gdf_municipios.geometry.centroid.y
    gdf_municipios['longitude'] = gdf_municipios.geometry.centroid.x
    
    gdf_sul = gdf_municipios[(gdf_municipios['code_muni'] >= 410000) & (gdf_municipios['code_muni'] < 440000)].copy()
    gdf_sul['faixa_latitude'] = gdf_sul['latitude'].apply(obter_faixa_latitude)
    gdf_sul = gdf_sul.dropna(subset=['faixa_latitude'])
    
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    processed_cities = set()
    try:
        df_existente = pd.read_sql_query(f"SELECT DISTINCT CODIGO_MUNICIPIO FROM {tabela_alvo}", conn)
        processed_cities = set(df_existente['CODIGO_MUNICIPIO'])
        logger.info(f"Retomando progresso: {len(processed_cities)} cidades já estão na tabela {tabela_alvo}.")
    except Exception:
        logger.info(f"Tabela {tabela_alvo} ainda não existe (nova ingestão).")
        
    gdf_pendentes = gdf_sul[~gdf_sul['code_muni'].isin(processed_cities)]
    logger.info(f"Total pendentes para baixar no alvo {alvo.upper()}: {len(gdf_pendentes)}")
    
    for _, row in tqdm(gdf_pendentes.iterrows(), total=len(gdf_pendentes), desc=f"Ingestão {alvo.upper()}"):
        df_res = process_func(row)
        if not df_res.empty:
            df_res.to_sql(tabela_alvo, conn, if_exists='append', index=False)
        pausa = 0.5 if alvo == 'infodengue' else 20.0
        time.sleep(pausa) # Pausa estendida para burlar limite da Open-Meteo
        
    conn.close()
    logger.info(f"=== INGESTÃO {alvo.upper()} 2015-2025 CONCLUÍDA ===")

if __name__ == '__main__':
    main()
