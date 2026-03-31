"""
Script para criar painel comparativo de todos os anos (2015-2023)
Gera uma visualização única com todos os mapas de faixas de latitude
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURAÇÃO =====
PASTA_BASE = Path(__file__).parent.parent.parent  # raiz do projeto
PASTA_CSVS = PASTA_BASE / "output" / "csvs_latitude"
PASTA_OUTPUT = PASTA_BASE / "output" / "mapas_latitude"
PASTA_OUTPUT.mkdir(parents=True, exist_ok=True)

# Faixas de latitude
FAIXAS_LATITUDE = [
    {"num": 1, "min": 22.0, "max": 23.0, "label": "Faixa 1"},
    {"num": 2, "min": 23.0, "max": 24.0, "label": "Faixa 2"},
    {"num": 3, "min": 24.0, "max": 25.5, "label": "Faixa 3"},
    {"num": 4, "min": 25.5, "max": 27.0, "label": "Faixa 4"},
    {"num": 5, "min": 27.0, "max": 28.0, "label": "Faixa 5"},
    {"num": 6, "min": 28.0, "max": 29.5, "label": "Faixa 6"},
    {"num": 7, "min": 29.5, "max": 31.0, "label": "Faixa 7"},
    {"num": 8, "min": 31.0, "max": 34.0, "label": "Faixa 8"}
]

# Classificação de cores
CLASSIFICACAO_CORES = [
    {"min": 0, "max": 10, "cor": "#FFFFCC"},
    {"min": 10, "max": 100, "cor": "#FFEDA0"},
    {"min": 100, "max": 300, "cor": "#FEB24C"},
    {"min": 300, "max": 600, "cor": "#F03B20"},
    {"min": 600, "max": float('inf'), "cor": "#BD0026"}
]

def classificar_incidencia(valor):
    """Retorna cor baseada na incidência"""
    if pd.isna(valor) or valor < 0:
        return "#E0E0E0"
    
    for classe in CLASSIFICACAO_CORES:
        if classe["min"] <= valor < classe["max"]:
            return classe["cor"]
    
    return CLASSIFICACAO_CORES[-1]["cor"]

def carregar_dados_faixas(ano):
    """Carrega dados de todas as faixas para um ano"""
    dados_ano = []
    
    for faixa in FAIXAS_LATITUDE:
        arquivo = PASTA_CSVS / f"dengue_faixa_latitude_{faixa['num']}.csv"
        
        if not arquivo.exists():
            continue
        
        df = pd.read_csv(arquivo)
        df_ano = df[df['ANO'] == ano].copy()
        
        if len(df_ano) == 0:
            continue
        
        df_agregado = df_ano.groupby('CODIGO_MUNICIPIO').agg({
            'CASOS_DENGUE': 'sum',
            'FAIXA_LATITUDE': 'first'
        }).reset_index()
        
        dados_ano.append(df_agregado)
    
    if not dados_ano:
        return None
    
    return pd.concat(dados_ano, ignore_index=True)

def calcular_medias_todos_anos():
    """Calcula médias de todas as faixas para todos os anos"""
    anos = range(2015, 2024)
    dados_completos = []
    
    for ano in anos:
        df_ano = carregar_dados_faixas(ano)
        
        if df_ano is None:
            continue
        
        medias = df_ano.groupby('FAIXA_LATITUDE').agg({
            'CASOS_DENGUE': 'mean'
        }).reset_index()
        
        medias['ANO'] = ano
        dados_completos.append(medias)
    
    if not dados_completos:
        return None
    
    df_final = pd.concat(dados_completos, ignore_index=True)
    return df_final

def gerar_painel_comparativo():
    """Gera painel com comparação de todos os anos"""
    print("\n[PAINEL COMPARATIVO] Gerando visualização multi-anual...")
    
    # Carregar dados
    df_completo = calcular_medias_todos_anos()
    
    if df_completo is None:
        print("    ⚠ Não foi possível carregar os dados")
        return
    
    # Criar figura com subplots
    anos = sorted(df_completo['ANO'].unique())
    n_anos = len(anos)
    
    # Grid 3x3 para acomodar 9 anos
    fig, axes = plt.subplots(3, 3, figsize=(20, 16))
    axes = axes.flatten()
    
    # Valor máximo para normalizar todos os gráficos
    max_valor_global = df_completo['CASOS_DENGUE'].max()
    
    for idx, ano in enumerate(anos):
        ax = axes[idx]
        df_ano = df_completo[df_completo['ANO'] == ano]
        
        # Preparar dados
        valores = []
        cores = []
        labels = []
        
        for faixa in FAIXAS_LATITUDE:
            media_row = df_ano[df_ano['FAIXA_LATITUDE'] == faixa['num']]
            
            if len(media_row) > 0:
                valor = media_row['CASOS_DENGUE'].values[0]
                valores.append(valor)
                cores.append(classificar_incidencia(valor))
            else:
                valores.append(0)
                cores.append("#E0E0E0")
            
            labels.append(faixa['label'])
        
        # Plotar barras
        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, valores, color=cores, edgecolor='black', linewidth=0.8)
        
        # Adicionar valores
        for i, (bar, valor) in enumerate(zip(bars, valores)):
            if valor > 0:
                ax.text(valor + max_valor_global * 0.02, bar.get_y() + bar.get_height()/2,
                       f'{valor:.0f}', va='center', ha='left', fontsize=8)
        
        # Configurar eixos
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlim(0, max_valor_global * 1.15)
        ax.set_title(f'{ano}', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.2, linestyle='--')
        ax.set_axisbelow(True)
        
        # Total de casos no ano
        total = df_completo[df_completo['ANO'] == ano]['CASOS_DENGUE'].sum()
        ax.text(0.98, 0.02, f'Total: {total:.0f}',
               transform=ax.transAxes, fontsize=8, ha='right', va='bottom',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # Título principal
    fig.suptitle('Evolução da Incidência de Dengue por Faixa de Latitude (2015-2023)',
                fontsize=18, fontweight='bold', y=0.995)
    
    # Legenda global
    legend_elements = []
    labels_legenda = ["0-9", "10-99", "100-299", "300-599", ">600"]
    for i, classe in enumerate(CLASSIFICACAO_CORES):
        patch = mpatches.Patch(facecolor=classe['cor'], edgecolor='black',
                              linewidth=0.5, label=labels_legenda[i])
        legend_elements.append(patch)
    
    fig.legend(handles=legend_elements,
              title='Incidência (casos/100 mil hab)',
              loc='lower center', ncol=5, fontsize=10, title_fontsize=11,
              bbox_to_anchor=(0.5, -0.02), frameon=True)
    
    # Ajustar layout
    plt.tight_layout(rect=[0, 0.02, 1, 0.99])
    
    # Salvar
    arquivo_saida = PASTA_OUTPUT / "painel_comparativo_2015_2023.png"
    plt.savefig(arquivo_saida, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"    ✓ Painel salvo: {arquivo_saida.name}")
    print(f"    → Anos incluídos: {len(anos)}")
    print(f"    → Faixas de latitude: 8")

def gerar_grafico_evolucao_temporal():
    """Gera gráfico de linha mostrando evolução temporal por faixa"""
    print("\n[EVOLUÇÃO TEMPORAL] Gerando gráfico de tendências...")
    
    # Carregar dados
    df_completo = calcular_medias_todos_anos()
    
    if df_completo is None:
        print("    ⚠ Não foi possível carregar os dados")
        return
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Cores para cada faixa
    cores_faixas = plt.cm.tab10(np.linspace(0, 1, 8))
    
    # Plotar linha para cada faixa
    for i, faixa in enumerate(FAIXAS_LATITUDE):
        df_faixa = df_completo[df_completo['FAIXA_LATITUDE'] == faixa['num']]
        
        if len(df_faixa) > 0:
            df_faixa_sorted = df_faixa.sort_values('ANO')
            ax.plot(df_faixa_sorted['ANO'], df_faixa_sorted['CASOS_DENGUE'],
                   marker='o', linewidth=2.5, markersize=6,
                   label=faixa['label'], color=cores_faixas[i])
    
    # Configurar gráfico
    ax.set_xlabel('Ano', fontsize=13, fontweight='bold')
    ax.set_ylabel('Incidência Média (casos por 100 mil hab)', fontsize=13, fontweight='bold')
    ax.set_title('Evolução Temporal da Incidência de Dengue por Faixa de Latitude',
                fontsize=16, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax.legend(loc='upper left', fontsize=10, frameon=True, shadow=False)
    
    # Eixo x com todos os anos
    anos = sorted(df_completo['ANO'].unique())
    ax.set_xticks(anos)
    ax.set_xticklabels(anos, rotation=45)
    
    # Adicionar informações
    ax.text(0.98, 0.02, 'Fonte: DATASUS\nElaboração: NEDE/UFSM',
           transform=ax.transAxes, fontsize=9, ha='right', va='bottom',
           style='italic', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Salvar
    arquivo_saida = PASTA_OUTPUT / "evolucao_temporal_faixas_latitude.png"
    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"    ✓ Gráfico salvo: {arquivo_saida.name}")
    print(f"    → Linhas plotadas: {len(FAIXAS_LATITUDE)}")

def main():
    """Função principal"""
    print("=" * 80)
    print("GERAÇÃO DE PAINÉIS COMPARATIVOS - ANÁLISE MULTI-ANUAL")
    print("=" * 80)
    
    try:
        gerar_painel_comparativo()
        gerar_grafico_evolucao_temporal()
        
        print("\n" + "=" * 80)
        print("✅ PAINÉIS GERADOS COM SUCESSO!")
        print("=" * 80)
        print(f"\n📁 Arquivos criados em: {PASTA_OUTPUT}")
        print("   • painel_comparativo_2015_2023.png")
        print("   • evolucao_temporal_faixas_latitude.png")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n⚠ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
