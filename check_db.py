import sqlite3
conn = sqlite3.connect('data/processed/dengue_analytics.db')
print('=== TABELAS ===')
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
for r in cur.fetchall():
    print(f'  {r[0]}')
print()
print('=== CONTAGENS ===')
for t in ['ingestao_saude', 'ingestao_clima', 'ingestao_enso']:
    try:
        c = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        d = conn.execute(f'SELECT COUNT(DISTINCT CODIGO_MUNICIPIO) FROM {t}').fetchone()[0]
        print(f'  {t}: {c} registros, {d} cidades')
    except:
        print(f'  {t}: NAO EXISTE')
conn.close()
