#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatórios Individuais por Latitude
Cria um PDF separado para cada faixa de latitude com análises completas
Similar ao relatório original mas focado em cada latitude
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy import stats
from pathlib import Path
from datetime import datetime

# Configurações
BASE_DIR = Path(__file__).parent.parent.parent  # raiz do projeto
MEDIAS_DIR = BASE_DIR / "output" / "medias_latitude"
OUTPUT_DIR = BASE_DIR / "output" / "relatorios_latitude"
DADOS_ONI = BASE_DIR / "data" / "raw" / "elnino_lanina_2015-2024.csv"

# Cria diretório de saída
OUTPUT_DIR.mkdir(exist_ok=True)

# Configura matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (11, 8.5)
plt.rcParams['font.size'] = 10

def carregar_todos_dados():
    """Carrega todos os dados de forma consolidada (reutilizando lógica do outro script)"""
    print("  Carregando dados consolidados...")
    
    # 1. Dengue
    df_dengue = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais.csv")
    df_dengue = df_dengue[['FAIXA_LATITUDE', 'ANO', 'MES', 'MEDIA_LOG_CASOS_DENGUE']]
    df_dengue.columns = ['LATITUDE', 'ANO', 'MES', 'incidencia_dengue']
    
    # 2. Temperaturas
    df_temp_max = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais_temp_maxima.csv")
    df_temp_med = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais_temp_media.csv")
    df_temp_min = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais_temp_minima.csv")
    
    df_temp = df_temp_max[['FAIXA_LATITUDE', 'ANO', 'MES', 'MEDIA_TEMP_MAXIMA']].copy()
    df_temp.columns = ['LATITUDE', 'ANO', 'MES', 'temp_maxima']
    df_temp['temp_media'] = df_temp_med['MEDIA_TEMP_MEDIA'].values
    df_temp['temp_minima'] = df_temp_min['MEDIA_TEMP_MINIMA'].values
    
    # 3. Precipitação
    df_prec = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais_precipitacao.csv")
    df_prec = df_prec[['FAIXA_LATITUDE', 'ANO', 'MES', 'MEDIA_PRECIPITACAO_MENSAL']]
    df_prec.columns = ['LATITUDE', 'ANO', 'MES', 'precipitacao']
    
    # 4. ONI
    df_oni = pd.read_csv(DADOS_ONI, sep=';', encoding='utf-8', decimal=',')
    df_oni = df_oni.loc[:, ~df_oni.columns.str.contains('^Unnamed')]
    df_oni.rename(columns={df_oni.columns[0]: 'ANO'}, inplace=True)
    
    meses_cols = [col for col in df_oni.columns if col != 'ANO']
    df_oni_long = pd.melt(df_oni, id_vars=['ANO'], value_vars=meses_cols, var_name='MES_NOME', value_name='ONI')
    
    # Converte vírgula para ponto em ONI (caso seja string)
    if df_oni_long['ONI'].dtype == 'object':
        df_oni_long['ONI'] = df_oni_long['ONI'].str.replace(',', '.').astype(float)
    
    meses_map = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    df_oni_long['MES'] = df_oni_long['MES_NOME'].str.lower().map(meses_map)
    df_oni_long = df_oni_long.dropna(subset=['ANO', 'MES', 'ONI'])
    df_oni_long['ANO'] = df_oni_long['ANO'].astype(int)
    df_oni_long['MES'] = df_oni_long['MES'].astype(int)
    df_oni_long = df_oni_long[['ANO', 'MES', 'ONI']]
    
    # Merge tudo
    df = df_dengue.merge(df_temp, on=['LATITUDE', 'ANO', 'MES'], how='inner')
    df = df.merge(df_prec[['LATITUDE', 'ANO', 'MES', 'precipitacao']], on=['LATITUDE', 'ANO', 'MES'], how='left')
    df = df.merge(df_oni_long, on=['ANO', 'MES'], how='left')
    
    # Data
    df['data'] = pd.to_datetime(df['ANO'].astype(str) + '-' + df['MES'].astype(str) + '-01')
    
    # Estação
    def definir_estacao(mes):
        if mes in [12, 1, 2]:
            return 'Verao'
        elif mes in [3, 4, 5]:
            return 'Outono'
        elif mes in [6, 7, 8]:
            return 'Inverno'
        else:
            return 'Primavera'
    
    df['estacao'] = df['MES'].apply(definir_estacao)
    
    # Categoriza ONI (El Niño/La Niña/Normal)
    def categorizar_oni(valor):
        if pd.isna(valor):
            return 'Desconhecido'
        elif valor >= 0.5:
            return 'El Niño'
        elif valor <= -0.5:
            return 'La Niña'
        else:
            return 'Normal'
    
    df['fase_oni'] = df['ONI'].apply(categorizar_oni)
    
    print(f"    {len(df)} registros consolidados")
    return df

def carregar_dados_latitude(num_lat):
    """
    Filtra dados para uma latitude específica e cria lags
    
    Args:
        num_lat: Número da latitude (1-8)
        
    Returns:
        DataFrame com dados da latitude e lags criados
    """
    df_completo = carregar_todos_dados()
    
    # Filtra latitude
    df = df_completo[df_completo['LATITUDE'] == num_lat].copy()
    df = df.sort_values('data').reset_index(drop=True)
    
    # Cria LAGs
    for lag in [1, 2, 3]:
        df[f'temp_media_lag{lag}'] = df['temp_media'].shift(lag)
        df[f'temp_minima_lag{lag}'] = df['temp_minima'].shift(lag)
        df[f'temp_maxima_lag{lag}'] = df['temp_maxima'].shift(lag)
        df[f'precipitacao_lag{lag}'] = df['precipitacao'].shift(lag)
        df[f'ONI_lag{lag}'] = df['ONI'].shift(lag)
    
    print(f"    {len(df)} registros para Latitude {num_lat}")
    return df

def criar_pagina_capa(pdf, df, num_lat):
    """Cria página de capa do relatório"""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Título
    ax.text(0.5, 0.8, 'RELATORIO DE ANALISE ESTATISTICA', 
            ha='center', fontsize=24, fontweight='bold')
    ax.text(0.5, 0.75, f'Dengue e Fatores Climaticos - Latitude {num_lat}', 
            ha='center', fontsize=18)
    
    # Informações
    periodo = f"{df['data'].min().strftime('%B/%Y')} - {df['data'].max().strftime('%B/%Y')}"
    ax.text(0.5, 0.6, f'Periodo: {periodo}', ha='center', fontsize=14)
    ax.text(0.5, 0.55, f'Total de Registros: {len(df)}', ha='center', fontsize=14)
    
    # Estatísticas da latitude
    ax.text(0.5, 0.48, f'ESTATISTICAS DA LATITUDE {num_lat}', 
            ha='center', fontsize=14, fontweight='bold')
    
    incidencia_media = df['incidencia_dengue'].mean()
    temp_media = df['temp_media'].mean()
    precip_media = df['precipitacao'].mean()
    
    ax.text(0.1, 0.40, f'Incidencia Media: {incidencia_media:.2f}', fontsize=12)
    ax.text(0.1, 0.36, f'Temperatura Media: {temp_media:.2f} graus C', fontsize=12)
    ax.text(0.1, 0.32, f'Precipitacao Media: {precip_media:.2f} mm', fontsize=12)
    
    # Metodologia
    ax.text(0.5, 0.25, 'Metodologia: Testes Nao-Parametricos', 
            ha='center', fontsize=16, fontweight='bold')
    ax.text(0.1, 0.19, '- Teste de Shapiro-Wilk (Normalidade)', fontsize=12)
    ax.text(0.1, 0.16, '- Correlacao de Spearman', fontsize=12)
    ax.text(0.1, 0.13, '- Teste de Kruskal-Wallis (Sazonal)', fontsize=12)
    ax.text(0.1, 0.10, '- Analise com LAG Temporal (1, 2 e 3 meses)', fontsize=12)
    
    # Data
    ax.text(0.5, 0.05, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 
            ha='center', fontsize=10, style='italic')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_tabela_estatisticas(pdf, df, num_lat):
    """Cria tabela com estatísticas descritivas"""
    fig, axes = plt.subplots(3, 1, figsize=(11, 11))
    
    # Estatísticas - Verifica se ONI existe
    variaveis = ['temp_media', 'temp_minima', 'temp_maxima', 'incidencia_dengue', 'precipitacao']
    if 'ONI' in df.columns and df['ONI'].notna().sum() > 3:
        variaveis.append('ONI')
    
    stats_df = df[variaveis].describe().T
    
    # Tabela 1: Estatísticas Básicas
    ax1 = axes[0]
    ax1.axis('off')
    ax1.text(0.5, 0.95, f'ESTATISTICAS DESCRITIVAS - LATITUDE {num_lat}', 
             ha='center', fontsize=16, fontweight='bold', transform=ax1.transAxes)
    
    table_data = [['Variavel', 'Media', 'Desvio Padrao', 'Minimo', 'Maximo']]
    nomes = {
        'temp_media': 'Temp. Media (graus C)',
        'temp_minima': 'Temp. Minima (graus C)',
        'temp_maxima': 'Temp. Maxima (graus C)',
        'incidencia_dengue': 'Incidencia de Dengue',
        'precipitacao': 'Precipitacao (mm)',
        'ONI': 'Indice ONI (El Nino/La Nina)'
    }
    
    for var in variaveis:
        if var in stats_df.index:  # Verificação extra de segurança
            table_data.append([
                nomes.get(var, var),
                f"{stats_df.loc[var, 'mean']:.2f}",
                f"{stats_df.loc[var, 'std']:.2f}",
                f"{stats_df.loc[var, 'min']:.2f}",
                f"{stats_df.loc[var, 'max']:.2f}"
            ])
    
    table1 = ax1.table(cellText=table_data, cellLoc='center', loc='center',
                       bbox=[0.05, 0.25, 0.9, 0.65])
    table1.auto_set_font_size(False)
    table1.set_fontsize(9)
    table1.scale(1, 2)
    
    # Header em negrito
    for i in range(5):
        table1[(0, i)].set_facecolor('#4CAF50')
        table1[(0, i)].set_text_props(weight='bold', color='white')
    
    # Tabela 2: Teste de Normalidade
    ax2 = axes[1]
    ax2.axis('off')
    ax2.text(0.5, 0.95, 'TESTE DE NORMALIDADE (Shapiro-Wilk)', 
             ha='center', fontsize=16, fontweight='bold', transform=ax2.transAxes)
    
    table_data2 = [['Variavel', 'Estatistica W', 'p-valor', 'Distribuicao']]
    
    for var in variaveis:
        dados = df[var].dropna()
        if len(dados) > 3:
            w_stat, p_value = stats.shapiro(dados)
            distribuicao = 'Normal' if p_value > 0.05 else 'Nao Normal'
            table_data2.append([
                nomes[var],
                f"{w_stat:.4f}",
                f"{p_value:.4f}",
                distribuicao
            ])
    
    table2 = ax2.table(cellText=table_data2, cellLoc='center', loc='center',
                       bbox=[0.1, 0.25, 0.8, 0.65])
    table2.auto_set_font_size(False)
    table2.set_fontsize(9)
    table2.scale(1, 2)
    
    for i in range(4):
        table2[(0, i)].set_facecolor('#2196F3')
        table2[(0, i)].set_text_props(weight='bold', color='white')
    
    # Tabela 3: Análise Categórica do ONI (El Niño/La Niña/Normal)
    if 'fase_oni' in df.columns:
        ax3 = axes[2]
        ax3.axis('off')
        ax3.text(0.5, 0.95, 'ANALISE DE FASES ONI (El Nino/La Nina/Normal)', 
                 ha='center', fontsize=16, fontweight='bold', transform=ax3.transAxes)
        
        # Contagem de frequências
        contagem_oni = df['fase_oni'].value_counts().sort_index()
        total = len(df)
        
        table_data3 = [['Fase', 'Frequencia', 'Percentual', 'Criterio']]
        
        ordem_fases = ['El Niño', 'Normal', 'La Niña']
        criterios = {
            'El Niño': 'ONI >= +0.5C',
            'Normal': '-0.49C <= ONI <= +0.49C',
            'La Niña': 'ONI <= -0.5C'
        }
        
        for fase in ordem_fases:
            if fase in contagem_oni.index:
                freq = contagem_oni[fase]
                perc = (freq / total) * 100
                table_data3.append([
                    fase,
                    f"{freq}",
                    f"{perc:.1f}%",
                    criterios[fase]
                ])
        
        # Adiciona total
        table_data3.append(['TOTAL', f"{total}", '100.0%', ''])
        
        table3 = ax3.table(cellText=table_data3, cellLoc='center', loc='center',
                           bbox=[0.1, 0.2, 0.8, 0.7])
        table3.auto_set_font_size(False)
        table3.set_fontsize(10)
        table3.scale(1, 2.2)
        
        # Header
        for i in range(4):
            table3[(0, i)].set_facecolor('#FF9800')
            table3[(0, i)].set_text_props(weight='bold', color='white')
        
        # Linha de total em destaque
        for i in range(4):
            table3[(len(table_data3)-1, i)].set_facecolor('#FFF3E0')
            table3[(len(table_data3)-1, i)].set_text_props(weight='bold')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_matriz_correlacao(pdf, df, num_lat):
    """Cria matriz de correlação de Spearman COM LAG 3 MESES"""
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Usar variáveis COM LAG 3 meses (incluindo ONI)
    variaveis = ['temp_media_lag3', 'temp_minima_lag3', 'temp_maxima_lag3', 
                 'precipitacao_lag3', 'ONI_lag3', 'incidencia_dengue']
    df_vars = df[variaveis].dropna()
    
    if len(df_vars) < 3:
        ax.text(0.5, 0.5, 'Dados insuficientes para matriz de correlacao', 
                ha='center', va='center', fontsize=14)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        return
    
    # Calcula correlação de Spearman
    corr_matrix = df_vars.corr(method='spearman')
    
    # Plot
    im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
    
    # Configurações
    ax.set_xticks(range(len(variaveis)))
    ax.set_yticks(range(len(variaveis)))
    nomes = ['Temp.Media\n(lag 3m)', 'Temp.Minima\n(lag 3m)', 'Temp.Maxima\n(lag 3m)', 
             'Precipitacao\n(lag 3m)', 'ONI\n(lag 3m)', 'Incidencia\nDengue']
    ax.set_xticklabels(nomes, fontsize=9)
    ax.set_yticklabels(nomes, fontsize=9)
    
    # Adiciona valores
    for i in range(len(variaveis)):
        for j in range(len(variaveis)):
            text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                          ha="center", va="center", color="black", fontweight='bold', fontsize=9)
    
    ax.set_title(f'MATRIZ DE CORRELACAO DE SPEARMAN - LATITUDE {num_lat}\n(Incidencia de Dengue vs Clima com LAG 3 meses)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Barra de cor
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Coeficiente de Correlacao', rotation=270, labelpad=20)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_graficos_scatter(pdf, df, num_lat):
    """Cria gráficos de dispersão COM LAG TEMPORAL"""
    fig, axes = plt.subplots(3, 2, figsize=(11, 11))
    fig.suptitle(f'ANALISE DE DISPERSAO - LATITUDE {num_lat}\nIncidencia de Dengue vs Variaveis Climaticas', 
                 fontsize=14, fontweight='bold')
    
    # Usar variáveis climáticas COM LAG (incluindo ONI)
    variaveis = [
        ('temp_media_lag3', 'Temp. Media 3 meses antes (graus C)'),
        ('temp_minima_lag3', 'Temp. Minima 3 meses antes (graus C)'),
        ('temp_maxima_lag3', 'Temp. Maxima 3 meses antes (graus C)'),
        ('precipitacao_lag3', 'Precipitacao 3 meses antes (mm)'),
        ('ONI_lag3', 'ONI 3 meses antes (El Nino/La Nina)'),
        ('temp_media_lag2', 'Temp. Media 2 meses antes (graus C)')
    ]
    
    for idx, (var, label) in enumerate(variaveis):
        ax = axes[idx // 2, idx % 2]
        
        # Remove NaN
        mask = df[var].notna() & df['incidencia_dengue'].notna()
        x = df.loc[mask, var]
        y = df.loc[mask, 'incidencia_dengue']
        
        if len(x) < 3:
            ax.text(0.5, 0.5, 'Dados insuficientes', ha='center', va='center')
            ax.set_xlabel(label)
            ax.set_ylabel('Incidencia de Dengue')
            continue
        
        # Scatter
        ax.scatter(x, y, alpha=0.6, s=50, color='steelblue')
        
        # Linha de tendência
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "r--", alpha=0.8, linewidth=2)
        
        # Correlação
        rho, p_val = stats.spearmanr(x, y)
        
        # Interpretação da correlação
        if p_val < 0.001:
            sig = '***'
        elif p_val < 0.01:
            sig = '**'
        elif p_val < 0.05:
            sig = '*'
        else:
            sig = ''
        
        # Texto formatado
        texto = f'rho = {rho:.3f}{sig}\np = {p_val:.4f}'
        ax.text(0.05, 0.95, texto, 
                transform=ax.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_xlabel(label, fontsize=9)
        ax.set_ylabel('Incidencia de Dengue', fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_boxplots_sazonais(pdf, df, num_lat):
    """Cria boxplots por estação do ano"""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle(f'ANALISE SAZONAL - LATITUDE {num_lat}\nDistribuicao por Estacao do Ano', 
                 fontsize=14, fontweight='bold')
    
    variaveis = [
        ('temp_media', 'Temperatura Media (graus C)'),
        ('incidencia_dengue', 'Incidencia de Dengue'),
        ('precipitacao', 'Precipitacao (mm)'),
        ('ONI', 'Indice ONI (El Nino/La Nina)')
    ]
    
    estacoes_ordem = ['Verao', 'Outono', 'Inverno', 'Primavera']
    
    for idx, (var, label) in enumerate(variaveis):
        ax = axes[idx // 2, idx % 2]
        
        # Prepara dados
        dados_estacao = [df[df['estacao'] == est][var].dropna() for est in estacoes_ordem]
        
        # Verifica se há dados
        if all(len(d) == 0 for d in dados_estacao):
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center')
            ax.set_ylabel(label)
            continue
        
        # Boxplot
        bp = ax.boxplot(dados_estacao, tick_labels=estacoes_ordem, patch_artist=True)
        
        # Cores
        cores = ['#FF6B6B', '#FFA500', '#4ECDC4', '#95E1D3']
        for patch, cor in zip(bp['boxes'], cores):
            patch.set_facecolor(cor)
            patch.set_alpha(0.7)
        
        ax.set_ylabel(label, fontsize=10)
        ax.grid(True, axis='y', alpha=0.3)
        
        # Testes estatísticos: Kruskal-Wallis E Levene
        dados_validos = [d for d in dados_estacao if len(d) > 0]
        if len(dados_validos) >= 2:
            # Kruskal-Wallis (diferenças entre medianas)
            h_stat, p_kw = stats.kruskal(*dados_validos)
            
            # Levene (homogeneidade de variâncias)
            w_stat, p_lev = stats.levene(*dados_validos)
            
            # Mostra ambos os testes
            texto = f'Kruskal-Wallis: H={h_stat:.2f}, p={p_kw:.4f}\nLevene: W={w_stat:.2f}, p={p_lev:.4f}'
            ax.text(0.5, 0.98, texto, 
                    transform=ax.transAxes, ha='center', fontsize=7,
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_serie_temporal(pdf, df, num_lat):
    """Cria gráfico de série temporal"""
    fig, axes = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
    fig.suptitle(f'SERIE TEMPORAL - LATITUDE {num_lat}\nEvolucao das Variaveis ao Longo do Tempo', 
                 fontsize=14, fontweight='bold')
    
    # Temperatura
    axes[0].plot(df['data'], df['temp_media'], label='Media', color='red', linewidth=2)
    axes[0].fill_between(df['data'], df['temp_minima'], df['temp_maxima'], 
                         alpha=0.3, color='orange', label='Amplitude (Min-Max)')
    axes[0].set_ylabel('Temperatura (graus C)', fontsize=10)
    axes[0].legend(loc='upper right', fontsize=8)
    axes[0].grid(True, alpha=0.3)
    
    # Precipitação
    axes[1].bar(df['data'], df['precipitacao'], width=20, alpha=0.7, color='steelblue')
    axes[1].set_ylabel('Precipitacao (mm)', fontsize=10)
    axes[1].grid(True, alpha=0.3)
    
    # ONI (El Niño/La Niña)
    axes[2].plot(df['data'], df['ONI'], color='purple', linewidth=2, marker='o', markersize=3)
    axes[2].axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='El Nino')
    axes[2].axhline(y=-0.5, color='blue', linestyle='--', alpha=0.5, label='La Nina')
    axes[2].axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    axes[2].set_ylabel('Indice ONI', fontsize=10)
    axes[2].legend(loc='upper right', fontsize=8)
    axes[2].grid(True, alpha=0.3)
    
    # Incidência de Dengue
    axes[3].plot(df['data'], df['incidencia_dengue'], color='darkred', linewidth=2, marker='o', markersize=4)
    axes[3].set_ylabel('Incidencia de Dengue\n(log10+1)', fontsize=10)
    axes[3].set_xlabel('Data', fontsize=10)
    axes[3].grid(True, alpha=0.3)
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_analise_lag(pdf, df, num_lat):
    """Cria análise comparativa de diferentes LAGs"""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle(f'ANALISE DE LAG TEMPORAL - LATITUDE {num_lat}\nComparacao de Correlacoes com Diferentes Lags', 
                 fontsize=14, fontweight='bold')
    
    # Variáveis para testar
    variaveis_base = ['temp_media', 'temp_maxima', 'precipitacao', 'ONI']
    titulos = ['Temperatura Media', 'Temperatura Maxima', 'Precipitacao', 'Indice ONI']
    
    for idx, (var_base, titulo) in enumerate(zip(variaveis_base, titulos)):
        ax = axes[idx // 2, idx % 2]
        
        lags = [0, 1, 2, 3]
        correlacoes = []
        p_values = []
        
        for lag in lags:
            if lag == 0:
                var = var_base
            else:
                var = f'{var_base}_lag{lag}'
            
            mask = df[var].notna() & df['incidencia_dengue'].notna()
            if mask.sum() > 3:
                rho, p_val = stats.spearmanr(df.loc[mask, var], df.loc[mask, 'incidencia_dengue'])
                correlacoes.append(rho)
                p_values.append(p_val)
            else:
                correlacoes.append(np.nan)
                p_values.append(np.nan)
        
        # Plot barras
        cores = ['red' if p < 0.05 else 'gray' for p in p_values]
        bars = ax.bar(lags, correlacoes, color=cores, alpha=0.7)
        
        # Linha no zero
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        
        # Marca o lag ótimo
        if not all(np.isnan(correlacoes)):
            abs_corrs = [abs(c) if not np.isnan(c) else 0 for c in correlacoes]
            best_lag = lags[abs_corrs.index(max(abs_corrs))]
            ax.text(best_lag, correlacoes[best_lag], f'Otimo\n(lag {best_lag})', 
                   ha='center', va='bottom' if correlacoes[best_lag] > 0 else 'top',
                   fontsize=8, fontweight='bold', color='darkgreen')
        
        ax.set_xlabel('Lag (meses)', fontsize=9)
        ax.set_ylabel('Correlacao de Spearman (rho)', fontsize=9)
        ax.set_title(titulo, fontsize=11, fontweight='bold')
        ax.set_xticks(lags)
        ax.grid(True, axis='y', alpha=0.3)
        ax.set_ylim(-1, 1)
    
    # Legenda
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='red', alpha=0.7, label='p < 0.05 (significativo)'),
                      Patch(facecolor='gray', alpha=0.7, label='p >= 0.05 (nao significativo)')]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2, fontsize=9, 
              bbox_to_anchor=(0.5, -0.02))
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def gerar_relatorio_latitude(num_lat):
    """
    Gera relatório completo para uma latitude específica
    
    Args:
        num_lat: Número da latitude (1-8)
    """
    print(f"\n[Latitude {num_lat}] Gerando relatorio...")
    
    # Carrega dados
    df = carregar_dados_latitude(num_lat)
    
    # Nome do arquivo de saída
    pdf_path = OUTPUT_DIR / f"Relatorio_Latitude_{num_lat}.pdf"
    
    # Gera PDF
    with PdfPages(pdf_path) as pdf:
        print(f"  Pag 1: Capa")
        criar_pagina_capa(pdf, df, num_lat)
        
        print(f"  Pag 2: Estatisticas Descritivas")
        criar_tabela_estatisticas(pdf, df, num_lat)
        
        print(f"  Pag 3: Matriz de Correlacao")
        criar_matriz_correlacao(pdf, df, num_lat)
        
        print(f"  Pag 4: Graficos de Dispersao")
        criar_graficos_scatter(pdf, df, num_lat)
        
        print(f"  Pag 5: Analise Sazonal")
        criar_boxplots_sazonais(pdf, df, num_lat)
        
        print(f"  Pag 6: Serie Temporal")
        criar_serie_temporal(pdf, df, num_lat)
        
        print(f"  Pag 7: Analise de LAG")
        criar_analise_lag(pdf, df, num_lat)
    
    print(f"  [OK] {pdf_path.name}")
    return pdf_path

def main():
    """Função principal"""
    print("=" * 80)
    print("GERADOR DE RELATORIOS INDIVIDUAIS POR LATITUDE")
    print("=" * 80)
    
    print(f"\nDiretorio de saida: {OUTPUT_DIR}")
    
    # Gera relatório para cada latitude
    pdfs_gerados = []
    
    for lat in range(1, 9):
        try:
            pdf_path = gerar_relatorio_latitude(lat)
            pdfs_gerados.append(pdf_path)
        except Exception as e:
            print(f"  [ERRO] Latitude {lat}: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumo
    print("\n" + "=" * 80)
    print(f"[OK] {len(pdfs_gerados)} RELATORIOS GERADOS COM SUCESSO!")
    print("=" * 80)
    
    print("\nArquivos criados:")
    for pdf in pdfs_gerados:
        print(f"  - {pdf.name}")
    
    print(f"\nLocalizacao: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
