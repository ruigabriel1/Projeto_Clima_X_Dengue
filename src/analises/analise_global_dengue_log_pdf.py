#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISE GLOBAL: DENGUE LOG-TRANSFORMADO × VARIÁVEIS CLIMÁTICAS
================================================================

Objetivo: Análise estatística global (sem estratificação por latitude)
          usando dados de incidência de dengue com transformação logarítmica

Testes realizados:
- Estatísticas descritivas
- Teste de normalidade (Shapiro-Wilk)
- Correlações (Pearson/Spearman)
- Comparação entre fases ENSO (Kruskal-Wallis)
- Análise de regressão múltipla
"""

import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from datetime import datetime

# Estatística
from scipy import stats
from scipy.stats import shapiro, spearmanr, kruskal, mannwhitneyu
import statsmodels.api as sm

# Visualização
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings('ignore')

# ==================== CONFIGURAÇÕES ====================
BASE_DIR = Path(__file__).parent.parent.parent  # raiz do projeto
DADOS_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output" / "relatorios_latitude"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Estilo
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("=" * 80)
print("ANÁLISE GLOBAL: DENGUE LOG-TRANSFORMADO")
print("=" * 80)


# ==================== FUNÇÕES AUXILIARES ====================

def calcular_estatisticas_descritivas(df, var):
    """Calcula estatísticas descritivas completas."""
    data = df[var].dropna()
    
    return {
        'n': len(data),
        'media': np.mean(data),
        'mediana': np.median(data),
        'desvio_padrao': np.std(data),
        'minimo': np.min(data),
        'maximo': np.max(data),
        'q25': np.percentile(data, 25),
        'q75': np.percentile(data, 75),
        'iqr': np.percentile(data, 75) - np.percentile(data, 25)
    }


def teste_normalidade_completo(data, nome_var):
    """Testa normalidade com Shapiro-Wilk."""
    data_clean = data.dropna()
    
    if len(data_clean) < 3:
        return {'W': np.nan, 'p_value': np.nan, 'normal': False}
    
    try:
        W, p_value = shapiro(data_clean)
        return {'W': W, 'p_value': p_value, 'normal': p_value > 0.05}
    except:
        return {'W': np.nan, 'p_value': np.nan, 'normal': False}


# ==================== CARREGAMENTO DE DADOS ====================

def carregar_dados():
    """Carrega dados consolidados com transformação log."""
    print("\n[DADOS] Carregando dados consolidados...")
    
    # Verifica se existe a versão com log
    arquivo_log = DADOS_DIR / "dados_consolidados_com_log.csv"
    
    if arquivo_log.exists():
        print(f"  → Carregando: {arquivo_log.name}")
        df = pd.read_csv(arquivo_log)
    else:
        # Cria a partir dos dados consolidados
        print("  → Criando versão com log...")
        df = pd.read_csv(DADOS_DIR / "dados_consolidados.csv")
        df['dengue_log'] = np.log10(df['incidencia_dengue'] + 1)
        df.to_csv(arquivo_log, index=False)
        print(f"  ✓ Arquivo criado: {arquivo_log.name}")
    
    # Renomeia colunas para padronizar
    if 'dengue_log' not in df.columns and 'incidencia_dengue' in df.columns:
        df['dengue_log'] = np.log10(df['incidencia_dengue'] + 1)
    
    # Converte data
    df['data'] = pd.to_datetime(df['data'])
    
    # Carrega ONI se necessário (está vazio no arquivo consolidado)
    if df['oni_index'].isna().all():
        print("  [INFO] ONI vazio, carregando de elnino_lanina_2015-2024.csv...")
        df_oni = pd.read_csv(DADOS_DIR / "elnino_lanina_2015-2024.csv", sep=';', encoding='utf-8-sig')
        
        # Detecta coluna de ano (pode ter BOM)
        ano_col = [c for c in df_oni.columns if 'ANO' in c.upper()][0]
        
        # Transforma ONI de wide para long
        meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        
        oni_long = []
        for _, row in df_oni.iterrows():
            ano = row[ano_col]
            if pd.notna(ano) and str(ano).replace('.0', '').isdigit():
                ano = int(float(ano))
                for i, mes in enumerate(meses, 1):
                    if mes in row and pd.notna(row[mes]):
                        valor = str(row[mes]).replace(',', '.')
                        try:
                            oni_long.append({
                                'ano': ano,
                                'mes': i,
                                'oni_index': float(valor)
                            })
                        except:
                            pass
        
        df_oni_long = pd.DataFrame(oni_long)
        
        # Merge com dados principais
        if len(df_oni_long) > 0:
            df = df.merge(df_oni_long, on=['ano', 'mes'], how='left', suffixes=('', '_oni'))
            if 'oni_index_oni' in df.columns:
                df['oni_index'] = df['oni_index_oni'].fillna(df['oni_index'])
                df = df.drop('oni_index_oni', axis=1)
            print(f"  ✓ ONI carregado: {df['oni_index'].notna().sum()} valores")
    
    print(f"  [OK] {len(df)} registros carregados")
    print(f"  [INFO] Período: {df['data'].min()} a {df['data'].max()}")
    
    return df


# ==================== ANÁLISES ====================

def criar_pagina_visao_geral(pdf, df):
    """Página 1: Visão geral dos dados."""
    fig = plt.figure(figsize=(11, 8.5))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    fig.suptitle('ANÁLISE GLOBAL - Visão Geral dos Dados', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Estatísticas descritivas
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    
    stats_dengue = calcular_estatisticas_descritivas(df, 'dengue_log')
    stats_temp = calcular_estatisticas_descritivas(df, 'temp_media')
    stats_precip = calcular_estatisticas_descritivas(df, 'precipitacao')
    
    tabela_stats = [
        ['Variável', 'N', 'Média', 'Mediana', 'Desvio', 'Mín', 'Máx'],
        ['Dengue (log)', f"{stats_dengue['n']}", f"{stats_dengue['media']:.3f}", 
         f"{stats_dengue['mediana']:.3f}", f"{stats_dengue['desvio_padrao']:.3f}",
         f"{stats_dengue['minimo']:.3f}", f"{stats_dengue['maximo']:.3f}"],
        ['Temperatura', f"{stats_temp['n']}", f"{stats_temp['media']:.2f}", 
         f"{stats_temp['mediana']:.2f}", f"{stats_temp['desvio_padrao']:.2f}",
         f"{stats_temp['minimo']:.2f}", f"{stats_temp['maximo']:.2f}"],
        ['Precipitação', f"{stats_precip['n']}", f"{stats_precip['media']:.1f}", 
         f"{stats_precip['mediana']:.1f}", f"{stats_precip['desvio_padrao']:.1f}",
         f"{stats_precip['minimo']:.1f}", f"{stats_precip['maximo']:.1f}"]
    ]
    
    table = ax1.table(cellText=tabela_stats, cellLoc='center', loc='center',
                      bbox=[0.05, 0.0, 0.9, 1.0])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    for i in range(7):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Série temporal - Dengue
    ax2 = fig.add_subplot(gs[1, :])
    ax2.plot(df['data'], df['dengue_log'], linewidth=2, color='#d62728', marker='o', markersize=3)
    ax2.set_xlabel('Data', fontsize=10)
    ax2.set_ylabel('Dengue log10(x+1)', fontsize=10)
    ax2.set_title('Série Temporal: Incidência de Dengue (log)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Histograma
    ax3 = fig.add_subplot(gs[2, 0])
    ax3.hist(df['dengue_log'].dropna(), bins=30, color='#d62728', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Dengue (log)', fontsize=10)
    ax3.set_ylabel('Frequência', fontsize=10)
    ax3.set_title('Distribuição da Incidência', fontsize=11, fontweight='bold')
    ax3.axvline(df['dengue_log'].mean(), color='blue', linestyle='--', label='Média')
    ax3.axvline(df['dengue_log'].median(), color='green', linestyle='--', label='Mediana')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Boxplot
    ax4 = fig.add_subplot(gs[2, 1])
    ax4.boxplot(df['dengue_log'].dropna(), vert=True, patch_artist=True,
                boxprops=dict(facecolor='#d62728', alpha=0.7))
    ax4.set_ylabel('Dengue (log)', fontsize=10)
    ax4.set_title('Boxplot: Identificação de Outliers', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def criar_pagina_normalidade(pdf, df):
    """Página 2: Testes de normalidade."""
    fig = plt.figure(figsize=(11, 8.5))
    gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
    
    fig.suptitle('Testes de Normalidade', fontsize=16, fontweight='bold', y=0.98)
    
    # Teste para dengue_log
    norm_dengue = teste_normalidade_completo(df['dengue_log'], 'Dengue log')
    norm_temp = teste_normalidade_completo(df['temp_media'], 'Temperatura')
    norm_precip = teste_normalidade_completo(df['precipitacao'], 'Precipitação')
    
    # Tabela de resultados
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    
    tabela_norm = [
        ['Variável', 'W', 'p-valor', 'Normal?'],
        ['Dengue (log)', f"{norm_dengue['W']:.4f}", f"{norm_dengue['p_value']:.4e}", 
         'Sim' if norm_dengue['normal'] else 'Não'],
        ['Temperatura', f"{norm_temp['W']:.4f}", f"{norm_temp['p_value']:.4e}", 
         'Sim' if norm_temp['normal'] else 'Não'],
        ['Precipitação', f"{norm_precip['W']:.4f}", f"{norm_precip['p_value']:.4e}", 
         'Sim' if norm_precip['normal'] else 'Não']
    ]
    
    table = ax1.table(cellText=tabela_norm, cellLoc='center', loc='center',
                      bbox=[0.2, 0.0, 0.6, 1.0])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    for i in range(4):
        table[(0, i)].set_facecolor('#2196F3')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Q-Q plots
    from scipy.stats import probplot
    
    # Dengue
    ax2 = fig.add_subplot(gs[1, 0])
    probplot(df['dengue_log'].dropna(), dist="norm", plot=ax2)
    ax2.set_title('Q-Q Plot: Dengue (log)', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Temperatura
    ax3 = fig.add_subplot(gs[1, 1])
    probplot(df['temp_media'].dropna(), dist="norm", plot=ax3)
    ax3.set_title('Q-Q Plot: Temperatura', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Precipitação
    ax4 = fig.add_subplot(gs[2, 0])
    probplot(df['precipitacao'].dropna(), dist="norm", plot=ax4)
    ax4.set_title('Q-Q Plot: Precipitação', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Interpretação
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.axis('off')
    
    interpretacao = "INTERPRETAÇÃO:\n\n"
    interpretacao += "• Shapiro-Wilk testa H0: dados são normais\n"
    interpretacao += "• p > 0.05: não rejeitamos H0 (normal)\n"
    interpretacao += "• p < 0.05: rejeitamos H0 (não normal)\n\n"
    
    if not norm_dengue['normal']:
        interpretacao += "⚠ Dengue não é normal → usar testes\n  não-paramétricos (Spearman)\n"
    else:
        interpretacao += "✓ Dengue é normal → usar Pearson\n"
    
    ax5.text(0.05, 0.95, interpretacao, va='top', fontsize=10, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#fff3cd', alpha=0.8),
            transform=ax5.transAxes)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def criar_pagina_correlacoes(pdf, df):
    """Página 3: Análise de correlações."""
    fig = plt.figure(figsize=(11, 8.5))
    gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
    
    fig.suptitle('Análise de Correlações', fontsize=16, fontweight='bold', y=0.98)
    
    # Calcula correlações (Spearman para dados não-normais)
    vars_interesse = ['dengue_log', 'temp_media', 'temp_minima', 'temp_maxima', 
                      'precipitacao', 'oni_index']
    
    df_corr = df[vars_interesse].dropna()
    
    # Matriz de correlação Spearman
    corr_spearman = df_corr.corr(method='spearman')
    
    # Heatmap
    ax1 = fig.add_subplot(gs[0:2, 0])
    im = ax1.imshow(corr_spearman, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
    
    labels = ['Dengue\n(log)', 'Temp\nMédia', 'Temp\nMín', 'Temp\nMáx', 'Precip', 'ONI']
    ax1.set_xticks(range(len(labels)))
    ax1.set_yticks(range(len(labels)))
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_yticklabels(labels, fontsize=9)
    
    # Valores na matriz
    for i in range(len(corr_spearman)):
        for j in range(len(corr_spearman)):
            text = ax1.text(j, i, f'{corr_spearman.iloc[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=9)
    
    ax1.set_title('Matriz de Correlação (Spearman)', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
    
    # Tabela de correlações com dengue
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    
    corr_dengue = []
    for var in vars_interesse[1:]:  # Exclui dengue_log
        rho, p_val = spearmanr(df_corr['dengue_log'], df_corr[var])
        corr_dengue.append([var, f'{rho:.3f}', f'{p_val:.4f}', 
                           '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'])
    
    tabela_corr = [['Variável', 'ρ', 'p-valor', 'Sig.']] + corr_dengue
    
    table = ax2.table(cellText=tabela_corr, cellLoc='center', loc='center',
                      bbox=[0.0, 0.2, 1.0, 0.7])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    for i in range(4):
        table[(0, i)].set_facecolor('#FF9800')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Scatter plots
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.scatter(df_corr['temp_media'], df_corr['dengue_log'], alpha=0.5, s=30)
    ax3.set_xlabel('Temperatura Média (°C)', fontsize=9)
    ax3.set_ylabel('Dengue (log)', fontsize=9)
    ax3.set_title('Dengue × Temperatura', fontsize=10, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.scatter(df_corr['precipitacao'], df_corr['dengue_log'], alpha=0.5, s=30, color='blue')
    ax4.set_xlabel('Precipitação (mm)', fontsize=9)
    ax4.set_ylabel('Dengue (log)', fontsize=9)
    ax4.set_title('Dengue × Precipitação', fontsize=10, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.scatter(df_corr['oni_index'], df_corr['dengue_log'], alpha=0.5, s=30, color='green')
    ax5.set_xlabel('ONI Index', fontsize=9)
    ax5.set_ylabel('Dengue (log)', fontsize=9)
    ax5.set_title('Dengue × ONI (El Niño/La Niña)', fontsize=10, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def criar_pagina_enso(pdf, df):
    """Página 4: Comparação entre fases ENSO."""
    fig = plt.figure(figsize=(11, 8.5))
    gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
    
    fig.suptitle('Análise por Fase ENSO (El Niño / La Niña / Neutro)', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Separa por fase
    df_enso = df.dropna(subset=['fase_enso', 'dengue_log'])
    
    el_nino = df_enso[df_enso['fase_enso'] == 'El Niño']['dengue_log']
    la_nina = df_enso[df_enso['fase_enso'] == 'La Niña']['dengue_log']
    neutro = df_enso[df_enso['fase_enso'] == 'Neutro']['dengue_log']
    
    # Teste de Kruskal-Wallis
    if len(el_nino) > 0 and len(la_nina) > 0 and len(neutro) > 0:
        H, p_kruskal = kruskal(el_nino, la_nina, neutro)
    else:
        H, p_kruskal = np.nan, np.nan
    
    # Teste post-hoc Mann-Whitney
    if len(el_nino) > 0 and len(la_nina) > 0:
        U, p_mann = mannwhitneyu(el_nino, la_nina, alternative='two-sided')
    else:
        U, p_mann = np.nan, np.nan
    
    # Tabela de estatísticas
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    
    tabela_enso = [
        ['Fase ENSO', 'N', 'Média', 'Mediana', 'Desvio', 'Min', 'Max'],
        ['El Niño', f"{len(el_nino)}", f"{el_nino.mean():.3f}", f"{el_nino.median():.3f}",
         f"{el_nino.std():.3f}", f"{el_nino.min():.3f}", f"{el_nino.max():.3f}"],
        ['La Niña', f"{len(la_nina)}", f"{la_nina.mean():.3f}", f"{la_nina.median():.3f}",
         f"{la_nina.std():.3f}", f"{la_nina.min():.3f}", f"{la_nina.max():.3f}"],
        ['Neutro', f"{len(neutro)}", f"{neutro.mean():.3f}", f"{neutro.median():.3f}",
         f"{neutro.std():.3f}", f"{neutro.min():.3f}", f"{neutro.max():.3f}"]
    ]
    
    table = ax1.table(cellText=tabela_enso, cellLoc='center', loc='center',
                      bbox=[0.1, 0.0, 0.8, 1.0])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    for i in range(7):
        table[(0, i)].set_facecolor('#9C27B0')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Boxplot
    ax2 = fig.add_subplot(gs[1, 0])
    data_box = [el_nino, la_nina, neutro]
    bp = ax2.boxplot(data_box, labels=['El Niño', 'La Niña', 'Neutro'],
                     patch_artist=True)
    
    colors = ['#FF5722', '#2196F3', '#9E9E9E']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_ylabel('Dengue (log)', fontsize=10)
    ax2.set_title('Comparação entre Fases ENSO', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Violin plot (apenas para fases com dados)
    ax3 = fig.add_subplot(gs[1, 1])
    
    # Filtra apenas dados válidos
    data_box_valid = [d for d in data_box if len(d) > 0]
    labels_valid = []
    if len(el_nino) > 0:
        labels_valid.append('El Niño')
    if len(la_nina) > 0:
        labels_valid.append('La Niña')
    if len(neutro) > 0:
        labels_valid.append('Neutro')
    
    if len(data_box_valid) > 0:
        positions = list(range(1, len(data_box_valid) + 1))
        parts = ax3.violinplot(data_box_valid, positions=positions, showmeans=True, showmedians=True)
        
        ax3.set_xticks(positions)
        ax3.set_xticklabels(labels_valid)
        ax3.set_ylabel('Dengue (log)', fontsize=10)
        ax3.set_title('Distribuição por Fase ENSO', fontsize=11, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
    else:
        ax3.text(0.5, 0.5, 'Dados insuficientes', ha='center', va='center', transform=ax3.transAxes)
    
    # Testes estatísticos
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis('off')
    
    texto_testes = "TESTES ESTATÍSTICOS:\n\n"
    texto_testes += f"1. Kruskal-Wallis (comparação múltipla):\n"
    texto_testes += f"   H = {H:.4f}, p-valor = {p_kruskal:.4f}\n"
    
    if p_kruskal < 0.05:
        texto_testes += "   → Existe diferença significativa entre as fases ENSO\n\n"
    else:
        texto_testes += "   → Não há diferença significativa entre as fases\n\n"
    
    texto_testes += f"2. Mann-Whitney U (El Niño vs La Niña):\n"
    texto_testes += f"   U = {U:.4f}, p-valor = {p_mann:.4f}\n"
    
    if p_mann < 0.05:
        if el_nino.median() > la_nina.median():
            texto_testes += "   → El Niño tem incidência significativamente MAIOR\n"
        else:
            texto_testes += "   → La Niña tem incidência significativamente MAIOR\n"
    else:
        texto_testes += "   → Não há diferença significativa entre El Niño e La Niña\n"
    
    # Diferença percentual
    diff_perc = ((el_nino.mean() - la_nina.mean()) / la_nina.mean()) * 100
    texto_testes += f"\n3. Diferença percentual (médias):\n"
    texto_testes += f"   El Niño vs La Niña: {diff_perc:+.1f}%"
    
    ax4.text(0.05, 0.95, texto_testes, va='top', fontsize=10, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#e1f5fe', alpha=0.9),
            transform=ax4.transAxes)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def criar_pagina_regressao(pdf, df):
    """Página 5: Regressão múltipla."""
    fig = plt.figure(figsize=(11, 8.5))
    gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
    
    fig.suptitle('Modelo de Regressão Múltipla', fontsize=16, fontweight='bold', y=0.98)
    
    # Prepara dados
    vars_x = ['temp_media', 'precipitacao', 'oni_index']
    df_model = df[['dengue_log'] + vars_x].dropna()
    
    y = df_model['dengue_log']
    X = df_model[vars_x]
    X_const = sm.add_constant(X)
    
    # Ajusta modelo
    modelo = sm.OLS(y, X_const).fit()
    
    # Resumo do modelo
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    
    tabela_modelo = [
        ['Métrica', 'Valor'],
        ['R²', f'{modelo.rsquared:.4f}'],
        ['R² Ajustado', f'{modelo.rsquared_adj:.4f}'],
        ['F-statistic', f'{modelo.fvalue:.2f}'],
        ['p-valor (F)', f'{modelo.f_pvalue:.4e}'],
        ['AIC', f'{modelo.aic:.2f}'],
        ['BIC', f'{modelo.bic:.2f}']
    ]
    
    table = ax1.table(cellText=tabela_modelo, cellLoc='left', loc='center',
                      bbox=[0.3, 0.0, 0.4, 1.0])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    for i in range(2):
        table[(0, i)].set_facecolor('#673AB7')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Coeficientes
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.axis('off')
    
    coefs = modelo.params[1:]  # Exclui constante
    p_vals = modelo.pvalues[1:]
    
    tabela_coef = [['Variável', 'Coeficiente', 'p-valor', 'Sig.']]
    for var, coef, p in zip(vars_x, coefs, p_vals):
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
        tabela_coef.append([var, f'{coef:.6f}', f'{p:.4f}', sig])
    
    table2 = ax2.table(cellText=tabela_coef, cellLoc='center', loc='center',
                       bbox=[0.0, 0.2, 1.0, 0.7])
    table2.auto_set_font_size(False)
    table2.set_fontsize(10)
    table2.scale(1, 2)
    
    for i in range(4):
        table2[(0, i)].set_facecolor('#009688')
        table2[(0, i)].set_text_props(weight='bold', color='white')
    
    # Gráfico de coeficientes
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.barh(vars_x, coefs, color=['#FF9800', '#2196F3', '#4CAF50'], alpha=0.7)
    ax3.set_xlabel('Coeficiente', fontsize=10)
    ax3.set_title('Magnitude dos Coeficientes', fontsize=11, fontweight='bold')
    ax3.axvline(0, color='black', linestyle='--', linewidth=1)
    ax3.grid(True, alpha=0.3, axis='x')
    
    # Resíduos vs Preditos
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.scatter(modelo.fittedvalues, modelo.resid, alpha=0.5, s=30)
    ax4.axhline(0, color='red', linestyle='--', linewidth=2)
    ax4.set_xlabel('Valores Preditos', fontsize=10)
    ax4.set_ylabel('Resíduos', fontsize=10)
    ax4.set_title('Diagnóstico: Resíduos', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Q-Q plot dos resíduos
    ax5 = fig.add_subplot(gs[2, 1])
    from scipy.stats import probplot
    probplot(modelo.resid, dist="norm", plot=ax5)
    ax5.set_title('Q-Q Plot: Normalidade dos Resíduos', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def criar_pagina_conclusoes(pdf, df):
    """Página 6: Conclusões finais."""
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Título
    ax.text(0.5, 0.95, 'CONCLUSÕES E INTERPRETAÇÃO', 
            ha='center', fontsize=18, fontweight='bold', transform=ax.transAxes)
    
    # Linha decorativa
    ax.plot([0.2, 0.8], [0.92, 0.92], 'k-', linewidth=2, alpha=0.3, transform=ax.transAxes)
    
    # Recalcula estatísticas principais (usando mask comum para evitar problemas de tamanho)
    df_corr = df[['dengue_log', 'temp_media', 'precipitacao', 'oni_index']].dropna()
    
    if len(df_corr) > 3:
        corr_temp, p_temp = spearmanr(df_corr['dengue_log'], df_corr['temp_media'])
        corr_precip, p_precip = spearmanr(df_corr['dengue_log'], df_corr['precipitacao'])
        corr_oni, p_oni = spearmanr(df_corr['dengue_log'], df_corr['oni_index'])
    else:
        corr_temp, p_temp = 0, 1
        corr_precip, p_precip = 0, 1
        corr_oni, p_oni = 0, 1
    
    df_enso = df.dropna(subset=['fase_enso', 'dengue_log'])
    el_nino = df_enso[df_enso['fase_enso'] == 'El Niño']['dengue_log']
    la_nina = df_enso[df_enso['fase_enso'] == 'La Niña']['dengue_log']
    
    conclusoes = f"""
PRINCIPAIS ACHADOS:

1. TRANSFORMAÇÃO LOGARÍTMICA
   ✓ Uso de log10(x+1) reduz assimetria e outliers
   ✓ Facilita análises estatísticas e interpretação

2. CORRELAÇÕES COM DENGUE (Spearman ρ)
   • Temperatura: ρ = {corr_temp:.3f} (p = {p_temp:.4f})
     {'→ Correlação SIGNIFICATIVA' if p_temp < 0.05 else '→ Não significativa'}
   
   • Precipitação: ρ = {corr_precip:.3f} (p = {p_precip:.4f})
     {'→ Correlação SIGNIFICATIVA' if p_precip < 0.05 else '→ Não significativa'}
   
   • ONI Index: ρ = {corr_oni:.3f} (p = {p_oni:.4f})
     {'→ Correlação SIGNIFICATIVA' if p_oni < 0.05 else '→ Não significativa'}

3. EFEITO ENSO
   • El Niño: média = {el_nino.mean():.3f} (log)
   • La Niña: média = {la_nina.mean():.3f} (log)
   • Diferença: {((el_nino.mean() - la_nina.mean()) / la_nina.mean() * 100):+.1f}%

4. MODELO DE REGRESSÃO
   • Variáveis climáticas explicam parte da variação
   • Outros fatores não climáticos são importantes
   • Recomenda-se análise por latitude (heterogeneidade espacial)

5. LIMITAÇÕES
   • Dados agregados temporalmente (perdas de padrões sazonais)
   • Ausência de variáveis socioeconômicas
   • Lag temporal não considerado nesta análise global

RECOMENDAÇÕES:
→ Análise estratificada por latitude (ver relatório específico)
→ Incluir lags temporais (1-3 meses)
→ Considerar variáveis socioeconômicas
→ Validar modelos com dados independentes
    """
    
    ax.text(0.05, 0.85, conclusoes, va='top', fontsize=10, family='monospace',
            transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.9))
    
    # Rodapé
    ax.text(0.5, 0.02, f'Relatório gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
            ha='center', fontsize=9, color='#666666', transform=ax.transAxes)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


# ==================== FUNÇÃO PRINCIPAL ====================

def main():
    """Função principal."""
    try:
        # Carrega dados
        df = carregar_dados()
        
        # Gera PDF
        print("\n[PDF] Gerando relatório PDF...")
        pdf_path = OUTPUT_DIR / f"analise_global_dengue_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        with PdfPages(pdf_path) as pdf:
            print("  [1/6] Visão geral...")
            criar_pagina_visao_geral(pdf, df)
            
            print("  [2/6] Normalidade...")
            criar_pagina_normalidade(pdf, df)
            
            print("  [3/6] Correlações...")
            criar_pagina_correlacoes(pdf, df)
            
            print("  [4/6] Análise ENSO...")
            criar_pagina_enso(pdf, df)
            
            print("  [5/6] Regressão...")
            criar_pagina_regressao(pdf, df)
            
            print("  [6/6] Conclusões...")
            criar_pagina_conclusoes(pdf, df)
        
        print(f"\n✓ PDF gerado com sucesso!")
        print(f"  [FILE] {pdf_path}")
        
        # Salva dados processados
        csv_path = OUTPUT_DIR / "dados_analise_global.csv"
        df.to_csv(csv_path, index=False)
        print(f"  [CSV] {csv_path}")
        
        print("\n" + "=" * 80)
        print("ANÁLISE GLOBAL CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
