"""Coleta isolada de São Carlos, SC — Clima + Saúde em 1 execução."""
import sqlite3
import pandas as pd
import requests
import logging
import time
from src.config import DATA_PROCESSED_DIR
import geopandas as gpd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = DATA_PROCESSED_DIR / "dengue_analytics.db"

# ====== Localizar São Carlos no Geopackage ======
logger.info("Localizando São Carlos, SC no geopackage...")
gdf = gpd.read_file("data/geodados/cache_municipios_sul.gpkg")
gdf['code_muni'] = gdf['code_muni'].astype(int)

# Filtrar São Carlos em SC pelo código IBGE exato (421600)
sao_carlos = gdf[gdf['code_muni'] == 421600]

if sao_carlos.empty:
    logger.error("São Carlos, SC não encontrado no geopackage!")
    exit(1)

row = sao_carlos.iloc[0]
code = int(row['code_muni'])
lat = row.geometry.centroid.y
lon = row.geometry.centroid.x
nome = row['name_muni']

# Calcular dígito verificador IBGE (7 dígitos)
s = str(code)
weights = [1, 2, 1, 2, 1, 2]
total = sum(
    (int(s[i]) * weights[i] // 10 + int(s[i]) * weights[i] % 10) 
    if int(s[i]) * weights[i] >= 10 else int(s[i]) * weights[i]
    for i in range(6)
)
dv = (10 - (total % 10)) % 10
code_7 = str(code) + str(dv)

# Faixa de latitude
FAIXAS = [(22.0,23.0,1),(23.0,24.0,2),(24.0,25.5,3),(25.5,27.0,4),
          (27.0,28.0,5),(28.0,29.5,6),(29.5,31.0,7),(31.0,34.0,8)]
faixa = None
for mn, mx, f in FAIXAS:
    if mn <= abs(lat) < mx:
        faixa = f
        break

logger.info(f"Município encontrado: {nome}")
logger.info(f"  Código IBGE 6d: {code} | 7d: {code_7}")
logger.info(f"  Lat: {lat:.4f} | Lon: {lon:.4f} | Faixa: {faixa}")

# ====== 1. Coleta CLIMA (Open-Meteo) ======
logger.info("=" * 50)
logger.info("[CLIMA] Baixando dados do Open-Meteo (2015-2025)...")
daily_vars = "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,windgusts_10m_max,soil_temperature_0_to_7cm_mean"
url_clima = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2015-01-01&end_date=2025-12-31&daily={daily_vars}&timezone=America%2FSao_Paulo"

resp = requests.get(url_clima, timeout=30)
if resp.status_code == 200:
    d = resp.json()
    daily = d['daily']
    df_clima = pd.DataFrame({
        'data': pd.to_datetime(daily['time']),
        'temp_media': daily.get('temperature_2m_mean', []),
        'temp_maxima': daily.get('temperature_2m_max', []),
        'temp_minima': daily.get('temperature_2m_min', []),
        'precipitacao': daily.get('precipitation_sum', []),
        'vel_vento_max': daily.get('windspeed_10m_max', []),
        'rajada_vento_max': daily.get('windgusts_10m_max', []),
        'temp_solo': daily.get('soil_temperature_0_to_7cm_mean', [])
    })
    df_clima['ANO'] = df_clima['data'].dt.year
    df_clima['MES'] = df_clima['data'].dt.month
    df_clima_mensal = df_clima.groupby(['ANO', 'MES']).agg({
        'temp_media': 'mean', 'temp_maxima': 'mean', 'temp_minima': 'mean',
        'precipitacao': 'sum', 'vel_vento_max': 'mean',
        'rajada_vento_max': 'mean', 'temp_solo': 'mean'
    }).reset_index()
    df_clima_mensal['CODIGO_MUNICIPIO'] = code
    df_clima_mensal['LATITUDE'] = lat
    df_clima_mensal['LONGITUDE'] = lon
    df_clima_mensal['FAIXA_LATITUDE'] = faixa
    df_clima_mensal['NOME_MUNICIPIO'] = nome
    logger.info(f"[CLIMA] OK: {len(df_clima_mensal)} registros mensais.")
else:
    logger.error(f"[CLIMA] Erro HTTP {resp.status_code}")
    df_clima_mensal = pd.DataFrame()

# ====== 2. Coleta SAÚDE (InfoDengue) ======
logger.info("=" * 50)
logger.info(f"[SAÚDE] Baixando dados do InfoDengue (geocode {code_7})...")

def fetch_disease(geocode_7, disease):
    url = f"https://info.dengue.mat.br/api/alertcity?geocode={geocode_7}&disease={disease}&format=json&ew_start=1&ew_end=53&ey_start=2015&ey_end=2025"
    r = requests.get(url, timeout=20)
    if r.status_code == 200:
        data = r.json()
        if data:
            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data_iniSE'], unit='ms')
            df['ANO'] = df['data'].dt.year
            df['MES'] = df['data'].dt.month
            for col in ['casos', 'casos_est']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
    return pd.DataFrame()

df_dengue = fetch_disease(code_7, 'dengue')
df_zika = fetch_disease(code_7, 'zika')
df_chik = fetch_disease(code_7, 'chikungunya')

# Agregar dengue
if not df_dengue.empty:
    agg = {'casos': 'sum', 'casos_est': 'sum'}
    agg = {k:v for k,v in agg.items() if k in df_dengue.columns}
    df_saude = df_dengue.groupby(['ANO','MES']).agg(agg).reset_index()
    df_saude = df_saude.rename(columns={'casos':'CASOS_DENGUE','casos_est':'CASOS_EST_DENGUE'})
else:
    df_saude = pd.DataFrame()

# Merge zika
if not df_zika.empty and not df_saude.empty:
    agg_z = {k:v for k,v in {'casos':'sum','casos_est':'sum'}.items() if k in df_zika.columns}
    df_z = df_zika.groupby(['ANO','MES']).agg(agg_z).reset_index()
    df_z = df_z.rename(columns={'casos':'CASOS_ZIKA','casos_est':'CASOS_EST_ZIKA'})
    df_saude = pd.merge(df_saude, df_z, on=['ANO','MES'], how='outer')

# Merge chikungunya
if not df_chik.empty and not df_saude.empty:
    agg_c = {k:v for k,v in {'casos':'sum','casos_est':'sum'}.items() if k in df_chik.columns}
    df_c = df_chik.groupby(['ANO','MES']).agg(agg_c).reset_index()
    df_c = df_c.rename(columns={'casos':'CASOS_CHIKUNGUNYA','casos_est':'CASOS_EST_CHIKUNGUNYA'})
    df_saude = pd.merge(df_saude, df_c, on=['ANO','MES'], how='outer')

if not df_saude.empty:
    df_saude['CODIGO_MUNICIPIO'] = code
    df_saude['LATITUDE'] = lat
    df_saude['LONGITUDE'] = lon
    df_saude['FAIXA_LATITUDE'] = faixa
    df_saude['NOME_MUNICIPIO'] = nome
    logger.info(f"[SAÚDE] OK: {len(df_saude)} registros mensais (Dengue + Zika + Chik).")
else:
    logger.info("[SAÚDE] Nenhum dado retornado.")

# ====== 3. Salvar no Banco ======
logger.info("=" * 50)
conn = sqlite3.connect(DB_PATH)

# Verificar se já existe no clima
try:
    existe_clima = conn.execute(f"SELECT COUNT(*) FROM ingestao_clima WHERE CODIGO_MUNICIPIO = {code}").fetchone()[0]
except:
    existe_clima = 0

if existe_clima > 0:
    logger.info(f"[DB] São Carlos já existe na tabela ingestao_clima ({existe_clima} registros). Pulando.")
else:
    if not df_clima_mensal.empty:
        df_clima_mensal.to_sql('ingestao_clima', conn, if_exists='append', index=False)
        logger.info(f"[DB] {len(df_clima_mensal)} registros de CLIMA salvos em ingestao_clima.")

# Verificar se já existe na saúde
try:
    existe_saude = conn.execute(f"SELECT COUNT(*) FROM ingestao_saude WHERE CODIGO_MUNICIPIO = {code}").fetchone()[0]
except:
    existe_saude = 0

if existe_saude > 0:
    logger.info(f"[DB] São Carlos já existe na tabela ingestao_saude ({existe_saude} registros). Pulando.")
else:
    if not df_saude.empty:
        df_saude.to_sql('ingestao_saude', conn, if_exists='append', index=False)
        logger.info(f"[DB] {len(df_saude)} registros de SAÚDE salvos em ingestao_saude.")

# Contagem final
for t in ['ingestao_saude', 'ingestao_clima']:
    c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    d = conn.execute(f"SELECT COUNT(DISTINCT CODIGO_MUNICIPIO) FROM {t}").fetchone()[0]
    logger.info(f"[DB] Tabela {t}: {c} registros totais, {d} cidades.")

conn.close()
logger.info("=" * 50)
logger.info("COLETA DE SÃO CARLOS, SC CONCLUÍDA COM SUCESSO!")
