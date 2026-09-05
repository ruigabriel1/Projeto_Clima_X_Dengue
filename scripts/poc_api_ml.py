import os
import requests
import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys
from datetime import datetime

# Força a saída para UTF-8 no Windows para suportar emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# Garante que a pasta output exista
os.makedirs("output", exist_ok=True)

# ---------------------------------------------------------
# 1. PARAMETRIZAÇÃO
# ---------------------------------------------------------
GEOCODE = "4101507" # Arapongas - PR
LAT = -23.4167
LON = -51.425
ANO_INICIO = 2015
ANO_FIM = 2024

print(f"🌍 Iniciando PoC de Ingestão e ML para Arapongas (IBGE: {GEOCODE})")

# ---------------------------------------------------------
# 2. INGESTÃO API: InfoDengue (Dados de Saúde)
# ---------------------------------------------------------
print("📥 1/4 - Baixando casos de Dengue da API InfoDengue (FIOCRUZ/FGV)...")
url_dengue = f"https://info.dengue.mat.br/api/alertcity?geocode={GEOCODE}&disease=dengue&format=json&ew_start=1&ew_end=53&ey_start={ANO_INICIO}&ey_end={ANO_FIM}"
response = requests.get(url_dengue)
if response.status_code == 200:
    dados_dengue = response.json()
    df_dengue = pd.DataFrame(dados_dengue)
    # Extrair a data de inicio da semana epidemiológica e converter (InfoDengue retorna em milissegundos)
    df_dengue['data'] = pd.to_datetime(df_dengue['data_iniSE'], unit='ms')
    df_dengue['ano'] = df_dengue['data'].dt.year
    df_dengue['mes'] = df_dengue['data'].dt.month
    
    # Agrupar por ano e mês para termos a visão MENSAL (igual ao seu DB)
    dengue_mensal = df_dengue.groupby(['ano', 'mes'])['casos'].sum().reset_index()
    print(f"   ✅ Sucesso! {len(dengue_mensal)} meses de dados históricos de saúde resgatados.")
else:
    print(f"Erro na API InfoDengue: {response.status_code}")
    sys.exit(1)

# ---------------------------------------------------------
# 3. INGESTÃO API: Open-Meteo (Dados de Clima)
# ---------------------------------------------------------
print("📥 2/4 - Baixando histórico climático da API Open-Meteo...")
url_clima = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={ANO_INICIO}-01-01&end_date={ANO_FIM}-12-31&daily=temperature_2m_mean,precipitation_sum&timezone=America%2FSao_Paulo"
response = requests.get(url_clima)
if response.status_code == 200:
    dados_clima = response.json()
    df_clima = pd.DataFrame({
        'data': pd.to_datetime(dados_clima['daily']['time']),
        'temp_media': dados_clima['daily']['temperature_2m_mean'],
        'precipitacao': dados_clima['daily']['precipitation_sum']
    })
    df_clima['ano'] = df_clima['data'].dt.year
    df_clima['mes'] = df_clima['data'].dt.month
    
    # Agrupar mensalmente
    clima_mensal = df_clima.groupby(['ano', 'mes']).agg(
        temp_media=('temp_media', 'mean'),
        precipitacao=('precipitacao', 'sum')
    ).reset_index()
    print(f"   ✅ Sucesso! Clima histórico resgatado e sumarizado mensalmente.")
else:
    print(f"Erro na API Open-Meteo: {response.status_code}")
    sys.exit(1)


# ---------------------------------------------------------
# 4. ENGENHARIA DE FEATURES (Merge e Lags)
# ---------------------------------------------------------
print("⚙️  3/4 - Fundindo os dados e criando lags (atrasos climáticos)...")
df_final = pd.merge(dengue_mensal, clima_mensal, on=['ano', 'mes'], how='inner')
df_final = df_final.sort_values(by=['ano', 'mes']).reset_index(drop=True)
df_final['data'] = pd.to_datetime(df_final['ano'].astype(str) + '-' + df_final['mes'].astype(str) + '-01')

# Criar defasagem de 3 meses (Lag-3) para dar tempo de o mosquito procriar e a doença eclodir
df_final['temp_lag3'] = df_final['temp_media'].shift(3)
df_final['prec_lag3'] = df_final['precipitacao'].shift(3)

# Removemos as 3 primeiras linhas que ficaram com NaN por causa do Shift
df_final = df_final.dropna().reset_index(drop=True)


# ---------------------------------------------------------
# 5. TREINAMENTO DO XGBOOST (Com visualização no terminal)
# ---------------------------------------------------------
print("\n🧠 4/4 - Treinando algoritmo XGBoost com monitoramento ao vivo...")
features = ['mes', 'temp_lag3', 'prec_lag3']
target = 'casos'

# Separar dados: Treino (2015-2023) e Validação (2024)
train_mask = df_final['ano'] < 2024
val_mask = df_final['ano'] == 2024

X_train = df_final.loc[train_mask, features]
y_train = df_final.loc[train_mask, target]
X_val = df_final.loc[val_mask, features]
y_val = df_final.loc[val_mask, target]

# Instanciando o modelo mais robusto
model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    objective='reg:squarederror',
    random_state=42
)

# Treinamento com verbose para mostrar a queda do erro em tempo real
model.fit(
    X_train, y_train,
    eval_set=[(X_train, y_train), (X_val, y_val)],
    verbose=10  # Mostra logs a cada 10 árvores
)

# Faz a predição para o histórico inteiro (para plotar o gráfico)
df_final['casos_preditos'] = np.maximum(model.predict(df_final[features]), 0) # Não permite casos negativos


# ---------------------------------------------------------
# 6. SIMULAÇÃO E ELEGIBILIDADE PARA 2025
# ---------------------------------------------------------
print("\n🔮 Gerando Previsão para 2025 (Cenário Climático Médio)...")
clima_2025 = clima_mensal.drop(columns=['ano']).groupby('mes').mean(numeric_only=True).reset_index() # Clima médio histórico
df_2025 = pd.DataFrame({'ano': 2025, 'mes': range(1, 13)})
df_2025 = pd.merge(df_2025, clima_2025, on='mes', how='left')

# Precisamos do Lag-3 usando os ultimos meses de 2024 e os de 2025
# (Para simplificar a PoC, vamos apenas aplicar o lag simulado sobre o clima de 2025 mesmo)
df_2025['temp_lag3'] = df_2025['temp_media'].shift(3).bfill()
df_2025['prec_lag3'] = df_2025['precipitacao'].shift(3).bfill()

# Prevê os casos de 2025
df_2025['casos_preditos'] = np.maximum(model.predict(df_2025[features]), 0)
df_2025['data'] = pd.to_datetime(df_2025['ano'].astype(str) + '-' + df_2025['mes'].astype(str) + '-01')


# --- VERIFICAÇÃO DE ELEGIBILIDADE (LIMITE EPIDÊMICO) ---
# Q95 histórico
limite_epidemia_q95 = np.percentile(df_final['casos'], 95)
pico_2025 = df_2025['casos_preditos'].max()
total_2025 = df_2025['casos_preditos'].sum()

print("-" * 50)
print(f"📊 RELATÓRIO DE ELEGIBILIDADE - ARAPONGAS/PR (2025)")
print(f"   Limite Epidêmico (Q95 histórico): {limite_epidemia_q95:.0f} casos/mês")
print(f"   Pico Previsto (2025): {pico_2025:.0f} casos no mês {df_2025.loc[df_2025['casos_preditos'].idxmax(), 'mes']}")
print(f"   Total Anual Previsto: {total_2025:.0f} casos")

if pico_2025 > limite_epidemia_q95:
    print("\n🚨 ALERTA VERMELHO: O município ESTÁ ELEGÍVEL para intervenção emergencial.")
    print("   A previsão matemática quebrou o teto de 95% do histórico.")
else:
    print("\n🟢 NORMAL: O município NÃO ESTÁ elegível para alerta emergencial.")
    print("   A previsão se mantém abaixo do teto epidêmico histórico.")
print("-" * 50)


# ---------------------------------------------------------
# 7. EXPORTAÇÃO DO GRÁFICO (Visualização de Time)
# ---------------------------------------------------------
plt.figure(figsize=(14, 6))

# Real (Azul)
plt.plot(df_final['data'], df_final['casos'], label='Real (InfoDengue)', color='blue', alpha=0.6, linewidth=2)

# Treinamento e Validação (Laranja)
plt.plot(df_final['data'], df_final['casos_preditos'], label='XGBoost Fit/Previsto', color='darkorange', linestyle='--', linewidth=2)

# Projeção 2025 (Vermelho)
plt.plot(df_2025['data'], df_2025['casos_preditos'], label='Projeção 2025', color='red', linewidth=3)

# Linha de Alerta Q95
plt.axhline(y=limite_epidemia_q95, color='darkred', linestyle=':', label='Limite Epidêmico (Q95)')

plt.title('Dengue Data as a Product: Real vs Previsto (XGBoost) - Arapongas/PR', fontsize=14, fontweight='bold')
plt.xlabel('Data')
plt.ylabel('Casos Mensais')
plt.legend()
plt.grid(True, alpha=0.3)
plt.gca().xaxis.set_major_locator(mdates.YearLocator())
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

grafico_path = os.path.join("output", "poc_xgboost_forecast.png")
plt.savefig(grafico_path, dpi=150, bbox_inches='tight')
plt.close()

print(f"\n📈 Gráfico gerado com sucesso em: {grafico_path}")
print("   Você poderá abrir esta imagem para ver o desenvolvimento temporal do algoritmo.")
