import pandas as pd

# Ler dados
df = pd.read_csv('output/csvs_latitude/dengue_faixa_latitude_6.csv')

# Filtrar janeiro de 2015
jan2015 = df[(df['ANO'] == 2015) & (df['MES'] == 1)]

print("=" * 80)
print("ANÁLISE DETALHADA: FAIXA 6 - JANEIRO 2015")
print("=" * 80)

# Identificar estado pelo código do município (2 primeiros dígitos)
jan2015['ESTADO'] = jan2015['CODIGO_MUNICIPIO'].astype(str).str[:2]

print("\n📊 DADOS POR ESTADO:")
print("-" * 80)
for estado in sorted(jan2015['ESTADO'].unique()):
    dados_estado = jan2015[jan2015['ESTADO'] == estado]
    soma_casos = dados_estado['CASOS_DENGUE'].sum()
    media = dados_estado['CASOS_DENGUE'].mean()
    print(f"\nEstado (código {estado}):")
    print(f"  • Municípios: {len(dados_estado)}")
    print(f"  • Total casos: {soma_casos}")
    print(f"  • Média: {media:.4f}")
    
    # Mostrar municípios com casos
    com_casos = dados_estado[dados_estado['CASOS_DENGUE'] > 0]
    if len(com_casos) > 0:
        print(f"  • Municípios com casos:")
        for _, row in com_casos.iterrows():
            print(f"    - {row['NOME_MUNICIPIO']}: {row['CASOS_DENGUE']} casos")

print("\n" + "=" * 80)
print("TOTAL GERAL:")
print("=" * 80)
print(f"Municípios: {len(jan2015)}")
print(f"Soma de casos: {jan2015['CASOS_DENGUE'].sum()}")
print(f"Média: {jan2015['CASOS_DENGUE'].mean():.4f}")

# Verificar se média de 0.3069 vem de algum subconjunto específico
print("\n" + "=" * 80)
print("TESTANDO HIPÓTESES PARA MÉDIA 0.3069:")
print("=" * 80)

# Hipótese 1: Média ponderada ou algo específico
target = 0.3069
municipios_diversos = [147, 145, 146, 144]  # Testando diferentes números de municípios

for n_mun in municipios_diversos:
    casos_necessarios = target * n_mun
    print(f"Se fossem {n_mun} municípios → precisaria de {casos_necessarios:.2f} casos (temos 45)")
