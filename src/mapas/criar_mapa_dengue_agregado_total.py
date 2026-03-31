"""
Script para criar mapa de incidência total de dengue (2015-2024)
Segue o padrão visual dos outros mapas do projeto
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import image as mpimg
from matplotlib.patches import Rectangle
import geopandas as gpd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
plt.ioff()

# Configurar caminhos
base_path = Path(__file__).parent.parent.parent  # raiz do projeto
output_dir = base_path / "output" / "mapas"
output_dir.mkdir(parents=True, exist_ok=True)

# Cores padronizadas (mesmo esquema dos outros mapas)
CORES_MAPA = {
    "Sem dados": "#f0f0f0",
    "0 a 999": "#ffffcc",
    "1000 a 4999": "#ffeda0",
    "5000 a 9999": "#feb24c",
    "10000 a 19999": "#f03b20",
    "> 20000": "#bd0026"
}

def classificar_incidencia(valor):
    """Classifica incidência em categorias visuais (casos totais agregados)"""
    if pd.isna(valor) or valor < 0:
        return "Sem dados"
    elif valor < 1000:
        return "0 a 999"
    elif valor < 5000:
        return "1000 a 4999"
    elif valor < 10000:
        return "5000 a 9999"
    elif valor < 20000:
        return "10000 a 19999"
    else:
        return "> 20000"

def criar_mapa_dengue_total():
    """Cria mapa de incidência total de dengue 2015-2024"""
    
    print("\n" + "="*80)
    print("CRIANDO MAPA DE INCIDENCIA TOTAL DE DENGUE (2015-2024)")
    print("="*80)
    
    # 1. Carregar dados
    print("\n[1/5] Carregando dados de dengue...")
    arquivo_dengue = base_path / "data" / "raw" / "dengue_MENSAL.csv"
    
    df_dengue = pd.read_csv(arquivo_dengue, sep=';', decimal=',', encoding='latin1')
    
    # Remover linhas de cabeçalho duplicadas
    df_dengue = df_dengue[~df_dengue.iloc[:, 0].isin(['municipio', 'year'])].copy()
    
    # Converter primeira coluna para ano
    df_dengue['ANO'] = pd.to_numeric(df_dengue.iloc[:, 0], errors='coerce')
    
    # Filtrar 2015-2024
    df_filtrado = df_dengue[(df_dengue['ANO'] >= 2015) & (df_dengue['ANO'] <= 2024)].copy()
    
    print(f"  -> Total de registros no periodo: {len(df_filtrado):,}")
    
    # 2. Calcular incidência total por município
    print("\n[2/5] Calculando incidencia total por municipio...")
    
    # Códigos dos municípios estão nas colunas (a partir da coluna 3)
    colunas_municipios = df_dengue.columns[3:]
    
    incidencia_total = []
    total_casos_geral = 0
    
    for col in colunas_municipios:
        try:
            codigo_mun = float(col)
            
            # Somar todos os casos do município no período
            casos_totais = 0
            for idx, row in df_filtrado.iterrows():
                try:
                    valor = pd.to_numeric(row[col], errors='coerce')
                    if pd.notna(valor):
                        casos_totais += valor
                except:
                    pass
            
            if casos_totais > 0:
                incidencia_total.append({
                    'CODIGO_MUNICIPIO': int(codigo_mun),
                    'CASOS_TOTAIS': casos_totais
                })
                total_casos_geral += casos_totais
        except:
            pass
    
    df_incidencia = pd.DataFrame(incidencia_total)
    
    # Calcular incidência média anual aproximada (casos totais / 10 anos)
    # Isso dará valores mais próximos do padrão visual esperado
    df_incidencia['INCIDENCIA_MEDIA_ANUAL'] = df_incidencia['CASOS_TOTAIS'] / 10.0
    
    # Adicionar classificação visual baseada nos casos totais
    df_incidencia['CLASSIFICACAO_VISUAL'] = df_incidencia['CASOS_TOTAIS'].apply(classificar_incidencia)
    
    print(f"  -> Total de municipios processados: {len(df_incidencia):,}")
    print(f"  -> Total de casos somados: {total_casos_geral:,.0f}")
    
    # Top 10 por incidência média anual
    print(f"\n  Top 10 municipios com maior incidencia media anual:")
    top10 = df_incidencia.nlargest(10, 'INCIDENCIA_MEDIA_ANUAL')
    for _, row in top10.iterrows():
        print(f"    {int(row['CODIGO_MUNICIPIO'])}: {row['INCIDENCIA_MEDIA_ANUAL']:,.1f} casos/ano (total: {row['CASOS_TOTAIS']:,.0f})")
    
    # 3. Carregar dados geoespaciais
    print("\n[3/5] Carregando dados geoespaciais...")
    
    cache_file = base_path / "cache_municipios_sul.gpkg"
    
    if cache_file.exists():
        gdf_sul = gpd.read_file(cache_file)
        print(f"  -> Municipios no shapefile: {len(gdf_sul):,}")
    else:
        print("  ! Cache de geodados nao encontrado!")
        print("  Execute primeiro: python scripts/criar_cache_geodados.py")
        return
    
    # 4. Mesclar dados
    print("\n[4/5] Mesclando dados...")
    
    # Mesclar com geodados
    gdf_mapa = gdf_sul.merge(
        df_incidencia,
        left_on='code_muni',
        right_on='CODIGO_MUNICIPIO',
        how='left'
    )
    
    gdf_mapa['CLASSIFICACAO_VISUAL'] = gdf_mapa['CLASSIFICACAO_VISUAL'].fillna("Sem dados")
    
    print(f"  -> Municipios com dados: {len(gdf_mapa[gdf_mapa['CLASSIFICACAO_VISUAL'] != 'Sem dados']):,}")
    
    # Distribuição por categoria
    print(f"\n  Distribuicao por categoria:")
    for cat in ["0 a 999", "1000 a 4999", "5000 a 9999", "10000 a 19999", "> 20000"]:
        count = len(gdf_mapa[gdf_mapa['CLASSIFICACAO_VISUAL'] == cat])
        if count > 0:
            print(f"    {cat}: {count} municipios")
    
    # 5. Criar mapa
    print("\n[5/5] Criando mapa...")
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 14))
    ax.set_facecolor('#a8d5f5')  # Fundo azul oceano
    
    # Plotar por categoria (mesma ordem dos outros mapas)
    for cat in ["Sem dados", "0 a 999", "1000 a 4999", "5000 a 9999", "10000 a 19999", "> 20000"]:
        gdf_cat = gdf_mapa[gdf_mapa['CLASSIFICACAO_VISUAL'] == cat]
        if len(gdf_cat) > 0:
            gdf_cat.plot(
                ax=ax,
                color=CORES_MAPA[cat],
                edgecolor='#444444',
                linewidth=0.4,
                label=cat,
                zorder=10
            )
    
    # Título
    ax.set_title('Incidencia Total da Dengue (2015-2024)', 
                 fontsize=16, fontweight='bold', pad=15)
    
    # Adicionar linhas de latitude
    ylim = ax.get_ylim()
    xlim = ax.get_xlim()
    
    # Linhas de latitude a cada 1 grau (aproximadamente)
    lat_min = int(ylim[0])
    lat_max = int(ylim[1]) + 1
    
    for lat in range(lat_min, lat_max):
        if lat % 1 == 0:  # Linhas a cada 1 grau
            ax.axhline(y=lat, color='black', linewidth=0.5, linestyle='--', alpha=0.4, zorder=20)
            # Adicionar label da latitude
            ax.text(xlim[1] + 0.1, lat, f'{abs(lat):.1f}°S', 
                   fontsize=7, va='center', ha='left')
    
    ax.axis('off')
    
    # Rosa dos ventos
    try:
        arquivo_rosa = base_path / "data" / "raw" / "R_transparent.png"
        if arquivo_rosa.exists():
            rosa = mpimg.imread(arquivo_rosa)
            ax_rosa = fig.add_axes([0.05, 0.85, 0.10, 0.10], zorder=30)
            ax_rosa.imshow(rosa)
            ax_rosa.axis('off')
    except:
        pass
    
    # Legenda (mesmo estilo dos outros mapas)
    leg_elem = []
    for cat in ["0 a 999", "1000 a 4999", "5000 a 9999", "10000 a 19999", "> 20000"]:
        leg_elem.append(Rectangle((0,0), 1, 1, facecolor=CORES_MAPA[cat], 
                                  edgecolor='#666666', linewidth=0.5, label=cat))
    
    leg = ax.legend(handles=leg_elem, title='Casos totais dengue (2015-2024)',
                   loc='lower left', fontsize=8, title_fontsize=7,
                   frameon=True, fancybox=False, shadow=False,
                   bbox_to_anchor=(0.01, 0.01))
    leg.get_frame().set_facecolor('white')
    leg.get_frame().set_edgecolor('black')
    leg.get_frame().set_linewidth(0.5)
    
    # Escala gráfica (mesmo estilo dos outros mapas)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]
    
    scale_x = xlim[1] - 0.25 * x_range
    scale_y = ylim[0] + 0.05 * y_range
    scale_length_km = 100
    scale_length_deg = scale_length_km / 111.0
    
    ax.plot([scale_x - scale_length_deg, scale_x], [scale_y, scale_y], 'k-', linewidth=3)
    ax.plot([scale_x - scale_length_deg, scale_x - scale_length_deg], 
           [scale_y - 0.01*y_range, scale_y + 0.01*y_range], 'k-', linewidth=2)
    ax.plot([scale_x, scale_x], 
           [scale_y - 0.01*y_range, scale_y + 0.01*y_range], 'k-', linewidth=2)
    ax.text(scale_x - scale_length_deg/2, scale_y - 0.03*y_range, f'{scale_length_km} km',
           ha='center', va='top', fontsize=8, fontweight='bold')
    
    # Informações (mesmo estilo dos outros mapas)
    ax.text(0.98, 0.02, 
           f'Fonte: DATASUS\nElaboracao: NEDE/UFSM\nCasos totais: {total_casos_geral:,.0f}\nPeriodo: 2015-2024',
           transform=ax.transAxes, fontsize=7, ha='right', va='bottom',
           style='italic')
    
    # Salvar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo_saida = output_dir / f"mapa_dengue_agregado_2015_2024_{timestamp}.png"
    
    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"\n  OK Mapa salvo: {arquivo_saida}")
    
    # Salvar CSV com ambos os valores
    arquivo_csv = output_dir / "dengue_agregado_2015_2024.csv"
    df_incidencia.to_csv(arquivo_csv, index=False)
    print(f"  OK Dados salvos: {arquivo_csv}")
    
    print("\n" + "="*80)
    print("OK MAPA DE DENGUE AGREGADO CRIADO COM SUCESSO!")
    print("="*80)
    print(f"\nArquivo: {arquivo_saida}")
    print(f"Total de casos: {total_casos_geral:,.0f}")
    print(f"Municipios: {len(df_incidencia):,}")
    print()

if __name__ == "__main__":
    criar_mapa_dengue_total()
