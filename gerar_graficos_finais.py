import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import numpy as np
from pathlib import Path
import os

# Configurações de estilo
plt.style.use('ggplot')
sns.set_context("paper", font_scale=1.2)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.facecolor'] = '#f8f9fa'

# Diretórios
ROOT_DIR = Path(r"c:\Users\ruiga\OneDrive\Documents\Projeto_Clima_X_Dengue")
ML_OUTPUT = ROOT_DIR / "output" / "projecoes_regionais" / "ml_completo"
OUT_FOLDER = ROOT_DIR / "graficos_artigo_finais"
os.makedirs(OUT_FOLDER, exist_ok=True)

# 1. Carregar Dados Anuais para Gráfico de Cenários
df_anual = pd.read_csv(ML_OUTPUT / "projecao_ml_completa_municipios_anual.csv")
# Focar em São Carlos SC (421600) e período 2026-2030
df_anual = df_anual[(df_anual["code"] == 421600) & (df_anual["year"] >= 2026) & (df_anual["year"] <= 2030)]

ssp126 = df_anual[df_anual["scenario"] == "ssp126"].sort_values("year")
ssp245 = df_anual[df_anual["scenario"] == "ssp245"].sort_values("year")
ssp585 = df_anual[df_anual["scenario"] == "ssp585"].sort_values("year")

# Plot 1: Cenários com Envelope de Incerteza
fig, ax = plt.subplots(figsize=(10, 6))

if not ssp585.empty and not ssp126.empty:
    ax.fill_between(ssp126["year"], ssp126["pred_cases_ml"], ssp585["pred_cases_ml"], 
                    color="#3498db", alpha=0.15, label="Envelope de incerteza")

if not ssp126.empty:
    ax.plot(ssp126["year"], ssp126["pred_cases_ml"], color="#27ae60", marker="o", lw=3, label="Referência (linha de base)")
if not ssp245.empty:
    ax.plot(ssp245["year"], ssp245["pred_cases_ml"], color="#e67e22", marker="s", linestyle="--", lw=3, label="Intermediário (+0,6 °C / +3% precip.)")
if not ssp585.empty:
    ax.plot(ssp585["year"], ssp585["pred_cases_ml"], color="#c0392b", marker="D", linestyle="-.", lw=3, label="Intensificado (+1,2 °C / +6% precip.)")

ax.set_title("Projeção de Casos de Dengue por Cenário Climático\nSão Carlos (SC), 2026–2030", fontweight='bold', fontsize=14)
ax.set_xlabel("Ano", fontweight='bold')
ax.set_ylabel("Casos anuais projetados", fontweight='bold')
ax.set_xticks([2026, 2027, 2028, 2029, 2030])
ax.legend(loc="upper left")
plt.tight_layout()
fig.savefig(OUT_FOLDER / "grafico_cenarios_envelope.png", dpi=300)
plt.close(fig)


# 2. Carregar Dados Mensais para Sazonalidade
df_mensal = pd.read_csv(ML_OUTPUT / "projecao_ml_completa_municipios_mensal.csv")
df_mensal = df_mensal[(df_mensal["code"] == 421600) & (df_mensal["year"] >= 2026) & (df_mensal["year"] <= 2030) & (df_mensal["scenario"] == "ssp245")]

# Pegar temperatura média histórica do DB
DB_PATH = ROOT_DIR / "data" / "processed" / "dengue_analytics.db"
conn = sqlite3.connect(DB_PATH)
try:
    clima_df = pd.read_sql_query("SELECT MES as month, AVG(temp_media) as temp_media FROM ingestao_clima WHERE CODIGO_MUNICIPIO = 421600 GROUP BY MES", conn)
except Exception:
    clima_df = pd.DataFrame(columns=["month", "temp_media"])
conn.close()

# Agrupar projetado
proj_sazonal = df_mensal.groupby("month")["pred_cases_ml"].mean().reset_index()

if not proj_sazonal.empty and not clima_df.empty:
    df_saz = pd.merge(proj_sazonal, clima_df, on="month", how="inner")
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    meses_pt = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    x = np.arange(len(df_saz))
    
    # Encontrar o mês com mais casos para colorir de vermelho
    max_idx = df_saz["pred_cases_ml"].idxmax()
    colors = ["#3498db"] * len(df_saz)
    if max_idx is not np.nan:
        colors[max_idx] = "#e74c3c"
        
    ax1.bar(x, df_saz["pred_cases_ml"], color=colors, width=0.6, label="Casos Projetados (média 2026-2030)")
    ax1.set_xlabel("Mês", fontweight='bold')
    ax1.set_ylabel("Casos médios mensais", color="#2980b9", fontweight='bold')
    ax1.tick_params(axis='y', labelcolor="#2980b9")
    ax1.set_xticks(x)
    ax1.set_xticklabels([meses_pt[int(m)-1] for m in df_saz["month"]])
    
    ax2 = ax1.twinx()
    ax2.plot(x, df_saz["temp_media"], color="#c0392b", marker="o", lw=2, label="Temperatura média (°C)")
    ax2.set_ylabel("Temperatura média (°C)", color="#c0392b", fontweight='bold', rotation=270, labelpad=15)
    ax2.tick_params(axis='y', labelcolor="#c0392b")
    
    fig.suptitle("Distribuição Sazonal de Casos de Dengue (2026-2030, SSP245)\ne Temperatura Média Histórica", fontweight='bold', fontsize=14)
    
    # Juntar legendas
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False)
    
    plt.tight_layout()
    fig.savefig(OUT_FOLDER / "grafico_distribuicao_sazonal.png", dpi=300)
    plt.close(fig)

print(f"Gráficos gerados com sucesso na pasta: {OUT_FOLDER}")
