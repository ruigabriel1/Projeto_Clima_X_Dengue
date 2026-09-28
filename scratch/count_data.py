import sqlite3, pandas as pd
conn = sqlite3.connect('data/processed/dengue_analytics.db')
total_saude = pd.read_sql('SELECT COUNT(*) as n FROM ingestao_saude', conn).iloc[0,0]
total_clima = pd.read_sql('SELECT COUNT(*) as n FROM ingestao_clima', conn).iloc[0,0]
sc = pd.read_sql("SELECT COUNT(*) as n FROM ingestao_saude WHERE CODIGO_MUNICIPIO = 421600", conn).iloc[0,0]
print(f'Total saude: {total_saude}')
print(f'Total clima: {total_clima}')
print(f'Sao Carlos ONLY: {sc}')
conn.close()
