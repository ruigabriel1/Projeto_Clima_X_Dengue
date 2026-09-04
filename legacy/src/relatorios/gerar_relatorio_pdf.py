#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório PDF - Análise Estatística Dengue
Gera relatório visual com testes estatísticos e gráficos
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy import stats
from pathlib import Path
from datetime import datetime

# Configurações
ARQUIVO_DADOS = Path(__file__).parent.parent.parent / "data" / "processed" / "dados_consolidados.csv"
ARQUIVO_PDF = Path(__file__).parent.parent.parent / "output" / "relatorio_analise_dengue.pdf"

# Configura matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (11, 8.5)
plt.rcParams['font.size'] = 10

def carregar_dados():
    """Carrega dados consolidados"""
    df = pd.read_csv(ARQUIVO_DADOS, parse_dates=['data'])
    print(f"✓ Dados carregados: {len(df)} registros")
    print(f"  Colunas: {list(df.columns)}")
    return df

def criar_pagina_capa(pdf, df):
    """Cria página de capa do relatório"""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Título
    ax.text(0.5, 0.8, 'RELATÓRIO DE ANÁLISE ESTATÍSTICA', 
            ha='center', fontsize=24, fontweight='bold')
    ax.text(0.5, 0.75, 'Dengue e Fatores Climáticos', 
            ha='center', fontsize=18)
    
    # Informações
    periodo = f"{df['data'].min().strftime('%B/%Y')} - {df['data'].max().strftime('%B/%Y')}"
    ax.text(0.5, 0.6, f'Período: {periodo}', ha='center', fontsize=14)
    ax.text(0.5, 0.55, f'Total de Registros: {len(df)}', ha='center', fontsize=14)
    
    # Metodologia
    ax.text(0.5, 0.45, 'Metodologia: Testes Não-Paramétricos', 
            ha='center', fontsize=16, fontweight='bold')
    ax.text(0.1, 0.37, '• Teste de Shapiro-Wilk (Normalidade)', fontsize=12)
    ax.text(0.1, 0.33, '• Correlação de Spearman', fontsize=12)
    ax.text(0.1, 0.29, '• Teste de Mann-Whitney U', fontsize=12)
    ax.text(0.1, 0.25, '• Teste de Kruskal-Wallis', fontsize=12)
    
    # Nota importante sobre LAG
    ax.text(0.5, 0.18, 'IMPORTANTE: Análise com LAG Temporal', 
            ha='center', fontsize=14, fontweight='bold', color='red')
    ax.text(0.05, 0.13, 'Os casos de dengue apresentam atraso de 2-3 meses após condições climáticas', 
            ha='left', fontsize=10, style='italic', wrap=True)
    ax.text(0.05, 0.10, 'favoráveis. Por isso, usamos LAG de 3 meses nas correlações clima-dengue.', 
            ha='left', fontsize=10, style='italic')
    
    # Data
    ax.text(0.5, 0.05, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 
            ha='center', fontsize=10, style='italic')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_tabela_estatisticas(pdf, df):
    """Cria tabela com estatísticas descritivas"""
    fig, axes = plt.subplots(2, 1, figsize=(11, 8.5))
    
    # Estatísticas
    variaveis = ['temp_media', 'temp_minima', 'temp_maxima', 'incidencia_dengue', 'precipitacao']
    stats_df = df[variaveis].describe().T
    
    # Tabela 1: Estatísticas Básicas
    ax1 = axes[0]
    ax1.axis('off')
    ax1.text(0.5, 0.95, 'ESTATÍSTICAS DESCRITIVAS', 
             ha='center', fontsize=16, fontweight='bold', transform=ax1.transAxes)
    
    table_data = [['Variável', 'Média', 'Desvio Padrão', 'Mínimo', 'Máximo']]
    nomes = {
        'temp_media': 'Temp. Média (°C)',
        'temp_minima': 'Temp. Mínima (°C)',
        'temp_maxima': 'Temp. Máxima (°C)',
        'incidencia_dengue': 'Incidência de Dengue',
        'precipitacao': 'Precipitação (mm)'
    }
    
    for var in variaveis:
        table_data.append([
            nomes[var],
            f"{stats_df.loc[var, 'mean']:.2f}",
            f"{stats_df.loc[var, 'std']:.2f}",
            f"{stats_df.loc[var, 'min']:.2f}",
            f"{stats_df.loc[var, 'max']:.2f}"
        ])
    
    table1 = ax1.table(cellText=table_data, cellLoc='center', loc='center',
                       bbox=[0.1, 0.3, 0.8, 0.6])
    table1.auto_set_font_size(False)
    table1.set_fontsize(10)
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
    
    table_data2 = [['Variável', 'Estatística W', 'p-valor', 'Distribuição']]
    
    for var in variaveis:
        dados = df[var].dropna()
        if len(dados) > 3:
            w_stat, p_value = stats.shapiro(dados)
            distribuicao = 'Normal' if p_value > 0.05 else 'Não Normal'
            table_data2.append([
                nomes[var],
                f"{w_stat:.4f}",
                f"{p_value:.4f}",
                distribuicao
            ])
    
    table2 = ax2.table(cellText=table_data2, cellLoc='center', loc='center',
                       bbox=[0.1, 0.3, 0.8, 0.6])
    table2.auto_set_font_size(False)
    table2.set_fontsize(10)
    table2.scale(1, 2)
    
    for i in range(4):
        table2[(0, i)].set_facecolor('#2196F3')
        table2[(0, i)].set_text_props(weight='bold', color='white')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_matriz_correlacao(pdf, df):
    """Cria matriz de correlação de Spearman COM LAG 3 MESES"""
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Usar variáveis COM LAG 3 meses (correlações corretas!) - INCLUINDO TEMP MÍNIMA
    variaveis = ['temp_media_lag3', 'temp_minima_lag3', 'temp_maxima_lag3', 'precipitacao_lag3', 'incidencia_dengue']
    df_vars = df[variaveis].dropna()
    
    # Calcula correlação de Spearman
    corr_matrix = df_vars.corr(method='spearman')
    
    # Plot
    im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
    
    # Configurações
    ax.set_xticks(range(len(variaveis)))
    ax.set_yticks(range(len(variaveis)))
    nomes = ['Temp.Média\n(lag 3m)', 'Temp.Mínima\n(lag 3m)', 'Temp.Máxima\n(lag 3m)', 'Precipitação\n(lag 3m)', 'Incidência\nDengue']
    ax.set_xticklabels(nomes)
    ax.set_yticklabels(nomes)
    
    # Adiciona valores
    for i in range(len(variaveis)):
        for j in range(len(variaveis)):
            text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                          ha="center", va="center", color="black", fontweight='bold')
    
    ax.set_title('MATRIZ DE CORRELAÇÃO DE SPEARMAN\n(Incidência de Dengue vs Clima com LAG 3 meses)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Barra de cor
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Coeficiente de Correlação', rotation=270, labelpad=20)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_graficos_scatter(pdf, df):
    """Cria gráficos de dispersão COM LAG TEMPORAL"""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle('ANÁLISE DE DISPERSÃO: Incidência de Dengue vs Variáveis Climáticas', 
                 fontsize=14, fontweight='bold')
    
    # Usar variáveis climáticas (incluindo temperatura mínima COM LAG)
    variaveis = [
        ('temp_media_lag3', 'Temp. Média 3 meses antes (°C)'),
        ('temp_minima_lag3', 'Temp. Mínima 3 meses antes (°C)'),
        ('temp_maxima_lag3', 'Temp. Máxima 3 meses antes (°C)'),
        ('precipitacao_lag3', 'Precipitação 3 meses antes (mm)')
    ]
    
    for idx, (var, label) in enumerate(variaveis):
        ax = axes[idx // 2, idx % 2]
        
        # Remove NaN
        mask = df[var].notna() & df['incidencia_dengue'].notna()
        x = df.loc[mask, var]
        y = df.loc[mask, 'incidencia_dengue']
        
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
        
        # Texto formatado corretamente (rho com sig, p-valor separado)
        texto = f'ρ = {rho:.3f}{sig}\np = {p_val:.4f}'
        ax.text(0.05, 0.95, texto, 
                transform=ax.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_xlabel(label)
        ax.set_ylabel('Incidência de Dengue')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_boxplots_sazonais(pdf, df):
    """Cria boxplots por estação do ano"""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle('ANÁLISE SAZONAL: Distribuição por Estação do Ano', 
                 fontsize=16, fontweight='bold')
    
    variaveis = [
        ('temp_media', 'Temperatura Média (°C)'),
        ('incidencia_dengue', 'Incidência de Dengue'),
        ('precipitacao', 'Precipitação (mm)'),
        ('temp_maxima', 'Temperatura Máxima (°C)')
    ]
    
    estacoes_ordem = ['Verão', 'Outono', 'Inverno', 'Primavera']
    
    for idx, (var, label) in enumerate(variaveis):
        ax = axes[idx // 2, idx % 2]
        
        # Prepara dados
        dados_estacao = [df[df['estacao'] == est][var].dropna() for est in estacoes_ordem]
        
        # Boxplot
        bp = ax.boxplot(dados_estacao, tick_labels=estacoes_ordem, patch_artist=True)
        
        # Cores
        cores = ['#FF6B6B', '#FFA500', '#4ECDC4', '#95E1D3']
        for patch, cor in zip(bp['boxes'], cores):
            patch.set_facecolor(cor)
            patch.set_alpha(0.7)
        
        ax.set_ylabel(label)
        ax.grid(True, axis='y', alpha=0.3)
        
        # Teste Kruskal-Wallis
        if len([d for d in dados_estacao if len(d) > 0]) >= 2:
            h_stat, p_val = stats.kruskal(*[d for d in dados_estacao if len(d) > 0])
            ax.text(0.5, 0.98, f'Kruskal-Wallis: H={h_stat:.2f}, p={p_val:.4f}', 
                    transform=ax.transAxes, ha='center', fontsize=9,
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def criar_serie_temporal(pdf, df):
    """Cria gráfico de série temporal"""
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True)
    fig.suptitle('SÉRIE TEMPORAL: Evolução das Variáveis ao Longo do Tempo', 
                 fontsize=16, fontweight='bold')
    
    # Temperatura
    axes[0].plot(df['data'], df['temp_media'], label='Média', color='red', linewidth=2)
    axes[0].fill_between(df['data'], df['temp_minima'], df['temp_maxima'], 
                         alpha=0.3, color='orange', label='Amplitude (Min-Max)')
    axes[0].set_ylabel('Temperatura (°C)')
    axes[0].legend(loc='upper right')
    axes[0].grid(True, alpha=0.3)
    
    # Precipitação
    axes[1].bar(df['data'], df['precipitacao'], width=20, alpha=0.7, color='steelblue')
    axes[1].set_ylabel('Precipitação (mm)')
    axes[1].grid(True, alpha=0.3)
    
    # Incidência de Dengue
    axes[2].plot(df['data'], df['incidencia_dengue'], color='darkred', linewidth=2, marker='o', markersize=4)
    axes[2].set_ylabel('Incidência de Dengue')
    axes[2].set_xlabel('Data')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def main():
    """Função principal"""
    print("=" * 80)
    print("GERADOR DE RELATÓRIO PDF - ANÁLISE ESTATÍSTICA DENGUE")
    print("=" * 80)
    
    # Carrega dados
    print("\n📊 Carregando dados...")
    df = carregar_dados()
    
    # Cria PDF
    print(f"\n📄 Gerando relatório PDF...")
    ARQUIVO_PDF.parent.mkdir(exist_ok=True)
    
    with PdfPages(ARQUIVO_PDF) as pdf:
        print("  → Página 1: Capa")
        criar_pagina_capa(pdf, df)
        
        print("  → Página 2: Estatísticas Descritivas")
        criar_tabela_estatisticas(pdf, df)
        
        print("  → Página 3: Matriz de Correlação")
        criar_matriz_correlacao(pdf, df)
        
        print("  → Página 4: Gráficos de Dispersão")
        criar_graficos_scatter(pdf, df)
        
        print("  → Página 5: Análise Sazonal")
        criar_boxplots_sazonais(pdf, df)
        
        print("  → Página 6: Série Temporal")
        criar_serie_temporal(pdf, df)
    
    print(f"\n✅ Relatório gerado com sucesso!")
    print(f"   📁 Arquivo: {ARQUIVO_PDF}")
    print("=" * 80)

if __name__ == "__main__":
    main()
