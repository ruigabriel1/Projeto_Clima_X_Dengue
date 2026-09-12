import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import os

# 1. Obter dados reais de 2015 a 2025
conn = sqlite3.connect('data/processed/dengue_analytics.db')
df_real = pd.read_sql_query(
    "SELECT ANO as year, SUM(CASOS_DENGUE) as real_cases FROM ingestao_saude WHERE CODIGO_MUNICIPIO = 421600 GROUP BY ANO ORDER BY ANO",
    conn
)
conn.close()

# 2. Obter previsões de teste (2022 a 2024)
try:
    df_test = pd.read_csv('output/projecoes_regionais/ml_completo/backtest_ml_completo.csv')
    df_test_anual = df_test.groupby('year')['pred_cases_ml'].sum().reset_index()
except Exception as e:
    df_test_anual = pd.DataFrame(columns=['year', 'pred_cases_ml'])

# 3. Obter previsão final (2025)
try:
    df_2025 = pd.read_csv('output/projecoes_regionais/ml_completo/projecao_ml_completa_municipios_anual.csv')
    pred_2025 = df_2025[(df_2025['code'] == 421600) & (df_2025['scenario'] == 'ssp245')]['pred_cases_ml'].values[0]
except Exception as e:
    pred_2025 = 0

# Consolidar previsões
df_pred = pd.DataFrame({'year': [2025], 'pred_cases_ml': [pred_2025]})
df_pred = pd.concat([df_test_anual, df_pred], ignore_index=True)

# Merge para o plot
df_plot = pd.merge(df_real, df_pred, on='year', how='left')

# Setup Plot (estética moderna)
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

# Barras Reais (2015 a 2025)
ax.bar(df_plot['year'] - 0.2, df_plot['real_cases'], width=0.4, color='#3498db', alpha=0.8, label='Casos Reais Observados')

# Barras Previstas (2022 a 2025)
valid_pred = df_plot.dropna(subset=['pred_cases_ml'])
ax.bar(valid_pred['year'] + 0.2, valid_pred['pred_cases_ml'], width=0.4, color='#e74c3c', alpha=0.9, label='Previsão do ML (XGBoost)')

# Estilização
ax.set_title('Validação do Machine Learning: São Carlos (SC)\nComparação Real vs Previsão', fontsize=14, pad=20, color='white')
ax.set_ylabel('Total de Casos de Dengue / Ano', fontsize=12)
ax.set_xticks(df_plot['year'])
ax.grid(axis='y', linestyle='--', alpha=0.3)
ax.legend(loc='upper left')

# Anotações para o pico de 2024 e queda de 2025
val_2024_real = df_plot[df_plot['year'] == 2024]['real_cases'].values[0]
val_2024_pred = valid_pred[valid_pred['year'] == 2024]['pred_cases_ml'].values[0] if 2024 in valid_pred['year'].values else 0

val_2025_real = df_plot[df_plot['year'] == 2025]['real_cases'].values[0]
val_2025_pred = valid_pred[valid_pred['year'] == 2025]['pred_cases_ml'].values[0] if 2025 in valid_pred['year'].values else 0

ax.annotate(f'Pico Real:\n{int(val_2024_real)}', xy=(2024 - 0.2, val_2024_real), xytext=(2024 - 1.5, val_2024_real),
            arrowprops=dict(facecolor='white', arrowstyle='->'), color='white', fontweight='bold')

ax.annotate(f'Previsão Queda:\n{int(val_2025_pred)}', xy=(2025 + 0.2, val_2025_pred), xytext=(2025 + 0.5, val_2025_pred + 200),
            arrowprops=dict(facecolor='#e74c3c', arrowstyle='->'), color='#e74c3c', fontweight='bold')

plt.tight_layout()
os.makedirs('scratch', exist_ok=True)
plt.savefig('scratch/valida_sc.png')
print('Gráfico salvo em scratch/valida_sc.png')
