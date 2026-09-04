"""
Script para gerar mapas de faixas de latitude com incidência de dengue
Cria mapas anuais (2015-2023) com design consistente baseado no Mapa_latitude2.png (2024)
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

# Faixas de latitude (8 faixas da região Sul)
FAIXAS_LATITUDE = [
    {"num": 1, "min": 22.0, "max": 23.0, "label": "Faixa 1: 22.0°S – 23.0°S"},
    {"num": 2, "min": 23.0, "max": 24.0, "label": "Faixa 2: 23.0°S – 24.0°S"},
    {"num": 3, "min": 24.0, "max": 25.5, "label": "Faixa 3: 24.0°S – 25.5°S"},
    {"num": 4, "min": 25.5, "max": 27.0, "label": "Faixa 4: 25.5°S – 27.0°S"},
    {"num": 5, "min": 27.0, "max": 28.0, "label": "Faixa 5: 27.0°S – 28.0°S"},
    {"num": 6, "min": 28.0, "max": 29.5, "label": "Faixa 6: 28.0°S – 29.5°S"},
    {"num": 7, "min": 29.5, "max": 31.0, "label": "Faixa 7: 29.5°S – 31.0°S"},
    {"num": 8, "min": 31.0, "max": 34.0, "label": "Faixa 8: 31.0°S – 34.0°S"}
]

# Classificação de cores por incidência
CLASSIFICACAO_CORES = [
    {"min": 0, "max": 10, "cor": "#FFFFCC", "label": "0 a 9"},
    {"min": 10, "max": 100, "cor": "#FFEDA0", "label": "10 a 99"},
    {"min": 100, "max": 300, "cor": "#FEB24C", "label": "100 a 299"},
    {"min": 300, "max": 600, "cor": "#F03B20", "label": "300 a 599"},
    {"min": 600, "max": float('inf'), "cor": "#BD0026", "label": "> 600"}
]

def classificar_incidencia(valor):
    """Retorna cor baseada na incidência de dengue"""
    if pd.isna(valor) or valor < 0:
        return "#E0E0E0"  # Cinza para sem dados
    
    for classe in CLASSIFICACAO_CORES:
        if classe["min"] <= valor < classe["max"]:
            return classe["cor"]
    
    return CLASSIFICACAO_CORES[-1]["cor"]  # Maior categoria

def carregar_dados_faixas(ano):
    """Carrega dados de todas as faixas de latitude para um ano específico"""
    dados_ano = []
    
    for faixa in FAIXAS_LATITUDE:
        arquivo = PASTA_CSVS / f"dengue_faixa_latitude_{faixa['num']}.csv"
        
        if not arquivo.exists():
            print(f"    ⚠ Arquivo não encontrado: {arquivo.name}")
            continue
        
        df = pd.read_csv(arquivo)
        
        # Filtrar pelo ano
        df_ano = df[df['ANO'] == ano].copy()
        
        if len(df_ano) == 0:
            continue
        
        # Agregar casos por município
        df_agregado = df_ano.groupby('CODIGO_MUNICIPIO').agg({
            'CASOS_DENGUE': 'sum',
            'FAIXA_LATITUDE': 'first',
            'LATITUDE': 'first',
            'LONGITUDE': 'first',
            'NOME_MUNICIPIO': 'first'
        }).reset_index()
        
        dados_ano.append(df_agregado)
    
    if not dados_ano:
        return None
    
    # Concatenar todos os dados
    df_completo = pd.concat(dados_ano, ignore_index=True)
    return df_completo

def calcular_media_por_faixa(df):
    """Calcula a média de casos de dengue por faixa de latitude"""
    if df is None or len(df) == 0:
        return None
    
    medias = df.groupby('FAIXA_LATITUDE').agg({
        'CASOS_DENGUE': 'mean'
    }).reset_index()
    
    medias.columns = ['FAIXA_LATITUDE', 'MEDIA_CASOS']
    return medias

def gerar_mapa_faixas(ano):
    """Gera mapa de barras horizontais com as faixas de latitude"""
    print(f"\n[{ano}] Gerando mapa de faixas de latitude...")
    
    # Carregar dados do ano
    df_ano = carregar_dados_faixas(ano)
    
    if df_ano is None:
        print(f"    ⚠ Nenhum dado encontrado para {ano}")
        return
    
    # Calcular médias por faixa
    medias = calcular_media_por_faixa(df_ano)
    
    if medias is None:
        print(f"    ⚠ Não foi possível calcular médias para {ano}")
        return
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Configuração do gráfico
    faixas_presentes = []
    cores_faixas = []
    valores_medias = []
    labels_faixas = []
    
    for faixa in FAIXAS_LATITUDE:
        media_row = medias[medias['FAIXA_LATITUDE'] == faixa['num']]
        
        if len(media_row) > 0:
            media_valor = media_row['MEDIA_CASOS'].values[0]
            valores_medias.append(media_valor)
            cores_faixas.append(classificar_incidencia(media_valor))
            labels_faixas.append(faixa['label'])
            faixas_presentes.append(faixa['num'])
        else:
            valores_medias.append(0)
            cores_faixas.append("#E0E0E0")
            labels_faixas.append(faixa['label'])
            faixas_presentes.append(faixa['num'])
    
    # Criar barras horizontais
    y_pos = np.arange(len(labels_faixas))
    bars = ax.barh(y_pos, valores_medias, color=cores_faixas, edgecolor='black', linewidth=1.2)
    
    # Adicionar valores nas barras
    for i, (bar, valor) in enumerate(zip(bars, valores_medias)):
        if valor > 0:
            ax.text(valor + max(valores_medias) * 0.02, bar.get_y() + bar.get_height()/2, 
                   f'{valor:.1f}', 
                   va='center', ha='left', fontsize=10, fontweight='bold')
    
    # Configurar eixos
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels_faixas, fontsize=11)
    ax.set_xlabel('Incidência Média de Dengue (casos por 100 mil habitantes)', fontsize=12, fontweight='bold')
    ax.set_title(f'Incidência de Dengue por Faixa de Latitude - Ano {ano}', 
                fontsize=16, fontweight='bold', pad=20)
    
    # Grade
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.8)
    ax.set_axisbelow(True)
    
    # Limites do eixo x
    max_valor = max(valores_medias) if valores_medias else 100
    ax.set_xlim(0, max_valor * 1.15)
    
    # Legenda de cores
    legend_elements = []
    for classe in CLASSIFICACAO_CORES:
        patch = mpatches.Patch(facecolor=classe['cor'], edgecolor='black', 
                              linewidth=0.5, label=classe['label'])
        legend_elements.append(patch)
    
    ax.legend(handles=legend_elements, 
             title='Classificação de Incidência\n(casos por 100 mil hab)', 
             loc='lower right', fontsize=10, title_fontsize=10,
             frameon=True, fancybox=False, shadow=False)
    
    # Informações adicionais
    total_casos = df_ano['CASOS_DENGUE'].sum()
    num_municipios = df_ano['CODIGO_MUNICIPIO'].nunique()
    
    info_texto = f'Total de casos: {total_casos:,}\nMunicípios: {num_municipios}\nFonte: DATASUS\nElaboração: NEDE/UFSM'
    ax.text(0.02, 0.98, info_texto, transform=ax.transAxes,
           fontsize=9, verticalalignment='top', 
           bbox=dict(boxstyle='round', facecolor='white', edgecolor='black', alpha=0.8))
    
    # Salvar
    arquivo_saida = PASTA_OUTPUT / f"mapa_faixas_latitude_{ano}.png"
    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"    ✓ Mapa salvo: {arquivo_saida.name}")
    print(f"    → Total de casos: {total_casos:,}")
    print(f"    → Municípios: {num_municipios}")
    print(f"    → Média geral: {df_ano['CASOS_DENGUE'].mean():.2f}")

def main():
    """Função principal para gerar todos os mapas"""
    print("=" * 80)
    print("GERAÇÃO DE MAPAS DE FAIXAS DE LATITUDE - INCIDÊNCIA DE DENGUE")
    print("=" * 80)
    
    # Verificar arquivos de entrada
    print("\n[INFO] Verificando arquivos de entrada...")
    arquivos_encontrados = 0
    for i in range(1, 9):
        arquivo = PASTA_CSVS / f"dengue_faixa_latitude_{i}.csv"
        if arquivo.exists():
            arquivos_encontrados += 1
            print(f"    ✓ {arquivo.name}")
        else:
            print(f"    ✗ {arquivo.name} - NÃO ENCONTRADO")
    
    print(f"\n    Total de arquivos encontrados: {arquivos_encontrados}/8")
    
    if arquivos_encontrados == 0:
        print("\n⚠ ERRO: Nenhum arquivo CSV encontrado!")
        return
    
    # Gerar mapas para cada ano
    print("\n[PROCESSAMENTO] Gerando mapas por ano...")
    anos_processados = 0
    
    for ano in range(2015, 2024):  # 2015 a 2023
        try:
            gerar_mapa_faixas(ano)
            anos_processados += 1
        except Exception as e:
            print(f"    ⚠ Erro ao processar {ano}: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumo final
    print("\n" + "=" * 80)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
    print("=" * 80)
    print(f"\n📊 Resumo:")
    print(f"   • Anos processados: {anos_processados}/9")
    print(f"   • Pasta de saída: {PASTA_OUTPUT}")
    print(f"   • Arquivos gerados: mapa_faixas_latitude_YYYY.png")
    print("=" * 80)

if __name__ == "__main__":
    main()
