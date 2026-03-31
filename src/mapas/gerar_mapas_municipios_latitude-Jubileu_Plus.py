"""
Script para gerar mapas de municípios por latitude (2015-2023)
Design idêntico ao mapa de 2024 com polígonos coloridos por incidência
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')  # Usar backend não-interativo
import matplotlib.pyplot as plt
from matplotlib import image as mpimg
from matplotlib.patches import Rectangle
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
plt.ioff()  # Desligar modo interativo

# ===== CONFIGURAÇÃO =====
PASTA_BASE = Path(__file__).parent.parent.parent  # raiz do projeto
PASTA_CSVS = PASTA_BASE / "output" / "csvs_latitude"
PASTA_OUTPUT = PASTA_BASE / "output" / "mapas_latitude"
ARQUIVO_ROSA_VENTOS = PASTA_BASE / "data" / "raw" / "R_transparent.png"

PASTA_OUTPUT.mkdir(parents=True, exist_ok=True)

# Cores para classificação de incidência (igual ao mapa de referência)
CORES_MAPA = {
    "Sem dados": "#f0f0f0",
    "0 a 9": "#ffffcc",
    "10 a 99": "#ffeda0",
    "100 a 299": "#feb24c",
    "300 a 599": "#f03b20",
    "> 600": "#bd0026"
}

def classificar_incidencia(valor):
    """Classifica incidência em categorias"""
    if pd.isna(valor) or valor < 0:
        return "Sem dados"
    elif valor < 10:
        return "0 a 9"
    elif valor < 100:
        return "10 a 99"
    elif valor < 300:
        return "100 a 299"
    elif valor < 600:
        return "300 a 599"
    else:
        return "> 600"

def carregar_geodados():
    """Carrega dados geográficos dos municípios da região Sul"""
    print("\n[INFO] Carregando dados geograficos...")
    
    # Verificar se há cache
    cache_file = PASTA_BASE / "data" / "geodados" / "cache_geodados_sul.gpkg"
    
    if cache_file.exists():
        print("    > Usando cache local...")
        try:
            gdf_sul = gpd.read_file(cache_file)
            print(f"    OK {len(gdf_sul)} municipios carregados do cache")
            return gdf_sul
        except:
            print("    AVISO: Cache corrompido, baixando novamente...")
    
    try:
        import geobr
        
        print("    > Baixando dados do geobr (pode demorar)...")
        
        # Carregar municípios do Brasil
        gdf_municipios = geobr.read_municipality(year=2020)
        gdf_municipios['code_muni'] = gdf_municipios['code_muni'].astype(str).str[:6].astype(int)
        
        # Filtrar região Sul (PR=41, SC=42, RS=43)
        gdf_sul = gdf_municipios[
            (gdf_municipios['code_muni'] >= 410000) & 
            (gdf_municipios['code_muni'] < 440000)
        ].copy()
        
        print(f"    OK {len(gdf_sul)} municipios da regiao Sul carregados")
        
        # Salvar cache
        print("    > Salvando cache para uso futuro...")
        gdf_sul.to_file(cache_file, driver='GPKG')
        print("    OK Cache salvo")
        
        return gdf_sul
        
    except Exception as e:
        print(f"    AVISO: Erro ao carregar geodados: {e}")
        import traceback
        traceback.print_exc()
        return None

def carregar_dados_ano(ano):
    """Carrega e agrega dados de dengue para um ano específico"""
    dados_ano = []
    
    for i in range(1, 9):
        arquivo = PASTA_CSVS / f"dengue_faixa_latitude_{i}.csv"
        
        if not arquivo.exists():
            continue
        
        df = pd.read_csv(arquivo)
        df_ano = df[df['ANO'] == ano].copy()
        
        if len(df_ano) > 0:
            dados_ano.append(df_ano)
    
    if not dados_ano:
        return None
    
    # Concatenar e agregar por município
    df_completo = pd.concat(dados_ano, ignore_index=True)
    
    df_agregado = df_completo.groupby('CODIGO_MUNICIPIO').agg({
        'CASOS_DENGUE': 'sum',
        'NOME_MUNICIPIO': 'first',
        'LATITUDE': 'first',
        'LONGITUDE': 'first'
    }).reset_index()
    
    return df_agregado

def carregar_dados_consolidado(anos):
    """Carrega e agrega dados de dengue para múltiplos anos"""
    dados_todos = []
    
    for i in range(1, 9):
        arquivo = PASTA_CSVS / f"dengue_faixa_latitude_{i}.csv"
        
        if not arquivo.exists():
            continue
        
        df = pd.read_csv(arquivo)
        df_anos = df[df['ANO'].isin(anos)].copy()
        
        if len(df_anos) > 0:
            dados_todos.append(df_anos)
    
    if not dados_todos:
        return None
    
    # Concatenar e agregar por município
    df_completo = pd.concat(dados_todos, ignore_index=True)
    
    df_agregado = df_completo.groupby('CODIGO_MUNICIPIO').agg({
        'CASOS_DENGUE': 'sum',
        'NOME_MUNICIPIO': 'first',
        'LATITUDE': 'first',
        'LONGITUDE': 'first'
    }).reset_index()
    
    return df_agregado

def gerar_mapa_municipios(ano, gdf_sul):
    """Gera mapa de municípios coloridos por incidência"""
    print(f"\n[{ano}] Gerando mapa de municipios...")
    
    # Carregar dados do ano
    df_ano = carregar_dados_ano(ano)
    
    if df_ano is None or gdf_sul is None:
        print(f"    AVISO: Dados insuficientes para {ano}")
        return
    
    # Classificar incidência
    df_ano['CLASSIFICACAO_VISUAL'] = df_ano['CASOS_DENGUE'].apply(classificar_incidencia)
    
    # Merge com geodados
    gdf_mapa = gdf_sul.merge(
        df_ano,
        left_on='code_muni',
        right_on='CODIGO_MUNICIPIO',
        how='left'
    )
    
    gdf_mapa['CLASSIFICACAO_VISUAL'] = gdf_mapa['CLASSIFICACAO_VISUAL'].fillna("Sem dados")
    
    # Criar figura com fundo branco
    fig, ax = plt.subplots(1, 1, figsize=(10, 14), facecolor='white')
    
    # Fundo do mapa (cinza claro)
    ax.set_facecolor('#d9d9d9')
    
    # Plotar municípios por categoria de incidência
    for categoria in ["Sem dados", "0 a 9", "10 a 99", "100 a 299", "300 a 599", "> 600"]:
        gdf_cat = gdf_mapa[gdf_mapa['CLASSIFICACAO_VISUAL'] == categoria]
        if len(gdf_cat) > 0:
            gdf_cat.plot(
                ax=ax,
                color=CORES_MAPA[categoria],
                edgecolor='#666666',
                linewidth=0.3,
                label=categoria,
                zorder=10
            )
    
    # Título
    ax.set_title(f'Incidência da Dengue do Ano {ano}', 
                fontsize=16, fontweight='bold', pad=15)
    
    # Obter limites antes de desligar os eixos
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    # Remover eixos
    ax.axis('off')
    
    # Adicionar linhas de latitude pontilhadas com números
    latitudes = [22, 23, 24, 25.5, 27, 28, 29.5, 31, 34]
    
    for lat in latitudes:
        # Linha pontilhada horizontal
        ax.axhline(-lat, color='black', linestyle='--', linewidth=1.0, alpha=0.6, 
                  zorder=15, dashes=(5, 3))
        
        # Número da latitude no lado esquerdo
        ax.text(xlim[0], -lat, f'  {lat:.1f}°S', 
               fontsize=10, va='center', ha='left', fontweight='bold',
               color='black',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                        edgecolor='black', linewidth=1.0, alpha=0.95),
               zorder=20)
    
    # Rosa dos ventos
    try:
        if ARQUIVO_ROSA_VENTOS.exists():
            rosa_img = mpimg.imread(ARQUIVO_ROSA_VENTOS)
            ax_rosa = fig.add_axes([0.11, 0.92, 0.08, 0.08], zorder=30)
            ax_rosa.imshow(rosa_img)
            ax_rosa.axis('off')
    except:
        pass
    
    # Legenda
    legend_elements = []
    for cat in ["0 a 9", "10 a 99", "100 a 299", "300 a 599", "> 600"]:
        legend_elements.append(
            Rectangle((0,0), 1, 1, facecolor=CORES_MAPA[cat], 
                     edgecolor='black', linewidth=0.5, label=cat)
        )
    
    leg = ax.legend(
        handles=legend_elements, 
        title='Incidência dengue por 100 mil/hab',
        loc='lower left', 
        fontsize=8, 
        title_fontsize=8,
        frameon=True, 
        fancybox=False, 
        shadow=False,
        bbox_to_anchor=(0.07, 0.07)
    )
    leg.get_frame().set_facecolor('white')
    leg.get_frame().set_edgecolor('black')
    leg.get_frame().set_linewidth(0.5)
    
    # Escala de barra
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]
    scale_x = xlim[1] - 0.20 * x_range
    scale_y = ylim[0] + 0.05 * y_range
    scale_length_km = 100
    scale_length_deg = scale_length_km / 111.0
    
    ax.plot([scale_x - scale_length_deg, scale_x], [scale_y, scale_y], 
           'k-', linewidth=3, zorder=20)
    ax.plot([scale_x - scale_length_deg, scale_x - scale_length_deg], 
           [scale_y - 0.15, scale_y + 0.15], 'k-', linewidth=2, zorder=20)
    ax.plot([scale_x, scale_x], 
           [scale_y - 0.15, scale_y + 0.15], 'k-', linewidth=2, zorder=20)
    ax.text(scale_x - scale_length_deg/2, scale_y - 0.4, 
           f'{scale_length_km} km', ha='center', va='top', 
           fontsize=8, fontweight='bold', zorder=20)
    
    # Informações
    total_casos = df_ano['CASOS_DENGUE'].sum()
    ax.text(0.98, 0.02, 
           f'Fonte: DATASUS\nElaboração: NEDE/UFSM\nCasos: {total_casos:,}',
           transform=ax.transAxes, fontsize=7, ha='right', va='bottom',
           style='italic',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                    edgecolor='black', linewidth=0.5, alpha=0.9))
    
    # Salvar
    arquivo_saida = PASTA_OUTPUT / f"mapa_municipios_latitude_{ano}.png"
    plt.tight_layout(pad=0.1)
    plt.savefig(arquivo_saida, dpi=300, bbox_inches='tight', facecolor='white', 
                edgecolor='none', pad_inches=0.1)
    plt.close(fig)  # Fechar a figura específica
    plt.close('all')  # Garantir que todas as figuras sejam fechadas
    
    print(f"    OK Mapa salvo: {arquivo_saida.name}")
    print(f"    > Total de casos: {total_casos:,}")
    print(f"    > Municipios: {len(df_ano)}")

def gerar_mapa_consolidado(anos, gdf_sul):
    """Gera mapa consolidado com soma de todos os anos"""
    print(f"\n[CONSOLIDADO 2015-2024] Gerando mapa...")
    
    # Carregar dados consolidados
    df_consolidado = carregar_dados_consolidado(anos)
    
    if df_consolidado is None or gdf_sul is None:
        print(f"    AVISO: Dados insuficientes para consolidado")
        return
    
    # Classificar incidência
    df_consolidado['CLASSIFICACAO_VISUAL'] = df_consolidado['CASOS_DENGUE'].apply(classificar_incidencia)
    
    # Merge com geodados
    gdf_mapa = gdf_sul.merge(
        df_consolidado,
        left_on='code_muni',
        right_on='CODIGO_MUNICIPIO',
        how='left'
    )
    
    gdf_mapa['CLASSIFICACAO_VISUAL'] = gdf_mapa['CLASSIFICACAO_VISUAL'].fillna("Sem dados")
    
    # Criar figura com fundo branco
    fig, ax = plt.subplots(1, 1, figsize=(10, 14), facecolor='white')
    
    # Fundo do mapa (cinza claro)
    ax.set_facecolor('#d9d9d9')
    
    # Plotar municípios por categoria de incidência
    for categoria in ["Sem dados", "0 a 9", "10 a 99", "100 a 299", "300 a 599", "> 600"]:
        gdf_cat = gdf_mapa[gdf_mapa['CLASSIFICACAO_VISUAL'] == categoria]
        if len(gdf_cat) > 0:
            gdf_cat.plot(
                ax=ax,
                color=CORES_MAPA[categoria],
                edgecolor='#666666',
                linewidth=0.3,
                label=categoria,
                zorder=10
            )
    
    # Título
    ax.set_title(f'Incidencia da Dengue - Consolidado 2015-2024', 
                fontsize=16, fontweight='bold', pad=15)
    
    # Obter limites antes de desligar os eixos
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    # Remover eixos
    ax.axis('off')
    
    # Adicionar linhas de latitude pontilhadas com números
    latitudes = [22, 23, 24, 25.5, 27, 28, 29.5, 31, 34]
    
    for lat in latitudes:
        # Linha pontilhada horizontal
        ax.axhline(-lat, color='black', linestyle='--', linewidth=1.0, alpha=0.6, 
                  zorder=15, dashes=(5, 3))
        
        # Número da latitude no lado esquerdo
        ax.text(xlim[0], -lat, f'  {lat:.1f}°S', 
               fontsize=10, va='center', ha='left', fontweight='bold',
               color='black',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                        edgecolor='black', linewidth=1.0, alpha=0.95),
               zorder=20)
    
    # Rosa dos ventos
    try:
        if ARQUIVO_ROSA_VENTOS.exists():
            rosa_img = mpimg.imread(ARQUIVO_ROSA_VENTOS)
            ax_rosa = fig.add_axes([0.11, 0.92, 0.08, 0.08], zorder=30)
            ax_rosa.imshow(rosa_img)
            ax_rosa.axis('off')
    except:
        pass
    
    # Legenda
    legend_elements = []
    for cat in ["0 a 9", "10 a 99", "100 a 299", "300 a 599", "> 600"]:
        legend_elements.append(
            Rectangle((0,0), 1, 1, facecolor=CORES_MAPA[cat], 
                     edgecolor='black', linewidth=0.5, label=cat)
        )
    
    leg = ax.legend(
        handles=legend_elements, 
        title='Incidencia dengue por 100 mil/hab',
        loc='lower left', 
        fontsize=8, 
        title_fontsize=8,
        frameon=True, 
        fancybox=False, 
        shadow=False,
        bbox_to_anchor=(0.07, 0.07)
    )
    leg.get_frame().set_facecolor('white')
    leg.get_frame().set_edgecolor('black')
    leg.get_frame().set_linewidth(0.5)
    
    # Escala de barra
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]
    scale_x = xlim[1] - 0.20 * x_range
    scale_y = ylim[0] + 0.05 * y_range
    scale_length_km = 100
    scale_length_deg = scale_length_km / 111.0
    
    ax.plot([scale_x - scale_length_deg, scale_x], [scale_y, scale_y], 
           'k-', linewidth=3, zorder=20)
    ax.plot([scale_x - scale_length_deg, scale_x - scale_length_deg], 
           [scale_y - 0.15, scale_y + 0.15], 'k-', linewidth=2, zorder=20)
    ax.plot([scale_x, scale_x], 
           [scale_y - 0.15, scale_y + 0.15], 'k-', linewidth=2, zorder=20)
    ax.text(scale_x - scale_length_deg/2, scale_y - 0.4, 
           f'{scale_length_km} km', ha='center', va='top', 
           fontsize=8, fontweight='bold', zorder=20)
    
    # Total de casos (para exibição no console)
    total_casos = df_consolidado['CASOS_DENGUE'].sum()
    
    # Salvar
    arquivo_saida = PASTA_OUTPUT / f"mapa_municipios_latitude_CONSOLIDADO_2015_2024.png"
    plt.tight_layout(pad=0.1)
    plt.savefig(arquivo_saida, dpi=300, bbox_inches='tight', facecolor='white', 
                edgecolor='none', pad_inches=0.1)
    plt.close(fig)
    plt.close('all')
    
    print(f"    OK Mapa consolidado salvo: {arquivo_saida.name}")
    print(f"    > Total de casos (2015-2024): {total_casos:,}")
    print(f"    > Municipios: {len(df_consolidado)}")

def main():
    """Função principal"""
    print("=" * 80)
    print("GERACAO DE MAPAS DE MUNICIPIOS POR LATITUDE - DENGUE (2015-2024)")
    print("=" * 80)
    
    # Carregar geodados uma vez
    gdf_sul = carregar_geodados()
    
    if gdf_sul is None:
        print("\nERRO: Nao foi possivel carregar os dados geograficos")
        print("Instalando geobr...")
        import subprocess
        subprocess.run(['pip', 'install', 'geobr'], check=True)
        gdf_sul = carregar_geodados()
        
        if gdf_sul is None:
            print("\nERRO CRITICO: Impossivel continuar sem geodados")
            return
    
    # Gerar mapas para cada ano
    print("\n[PROCESSAMENTO] Gerando mapas por ano...")
    anos_processados = 0
    
    for ano in range(2015, 2025):  # Incluindo 2024
        try:
            gerar_mapa_municipios(ano, gdf_sul)
            anos_processados += 1
        except Exception as e:
            print(f"    AVISO: Erro ao processar {ano}: {e}")
            import traceback
            traceback.print_exc()
    
    # Gerar mapa consolidado
    print("\n[CONSOLIDADO] Gerando mapa com soma de todos os anos...")
    try:
        gerar_mapa_consolidado(list(range(2015, 2025)), gdf_sul)
    except Exception as e:
        print(f"    AVISO: Erro ao processar consolidado: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumo
    print("\n" + "=" * 80)
    print("OK PROCESSAMENTO CONCLUIDO!")
    print("=" * 80)
    print(f"\nResumo:")
    print(f"   - Anos processados: {anos_processados}/10")
    print(f"   - Mapa consolidado: 2015-2024")
    print(f"   - Pasta de saida: {PASTA_OUTPUT}")
    print(f"   - Arquivos: mapa_municipios_latitude_YYYY.png")
    print("=" * 80)

if __name__ == "__main__":
    main()
