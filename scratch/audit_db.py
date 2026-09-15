import sqlite3
conn = sqlite3.connect('data/processed/dengue_analytics.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("=== AUDITORIA DO BANCO DE DADOS ===")
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    print(f"  {t[0]}: {count} registros")
print()
# Cidades distintas
for tbl in ['ingestao_saude', 'ingestao_clima', 'ingestao_enso']:
    try:
        if tbl == 'ingestao_enso':
            r = conn.execute(f"SELECT MIN(ANO), MAX(ANO) FROM {tbl}").fetchone()
            print(f"  {tbl}: {r[0]} a {r[1]}")
        else:
            r = conn.execute(f"SELECT COUNT(DISTINCT CODIGO_MUNICIPIO) FROM {tbl}").fetchone()
            print(f"  {tbl}: {r[0]} cidades distintas")
    except:
        pass
conn.close()
