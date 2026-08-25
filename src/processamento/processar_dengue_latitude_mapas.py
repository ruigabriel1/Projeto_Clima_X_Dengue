"""
Script para processar dados de dengue da região Sul do Brasil (2015-2024)
Gera CSVs por faixa de latitude e mapas de calor anuais
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import image as mpimg
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURAÇÃO =====
from src.config import BASE_DIR, DATA_RAW_DIR, OUTPUT_DIR, OUTPUT_CSVS_LATITUDE, OUTPUT_MAPAS_LATITUDE

ARQUIVO_DENGUE = str(DATA_RAW_DIR / "dengue_MENSAL.csv")
ARQUIVO_ROSA_VENTOS = str(DATA_RAW_DIR / "R_transparent.png")
PASTA_OUTPUT = str(OUTPUT_DIR)
PASTA_MAPAS = OUTPUT_MAPAS_LATITUDE
PASTA_CSVS = OUTPUT_CSVS_LATITUDE

# Faixas de latitude  
FAIXAS_LATITUDE = [
    (22.0, 23.0, "Faixa 1: 22.0°S – 23.0°S"),
    (23.0, 24.0, "Faixa 2: 23.0°S – 24.0°S"),
    (24.0, 25.5, "Faixa 3: 24.0°S – 25.5°S"),
    (25.5, 27.0, "Faixa 4: 25.5°S – 27.0°S"),
    (27.0, 28.0, "Faixa 5: 27.0°S – 28.0°S"),
    (28.0, 29.5, "Faixa 6: 28.0°S – 29.5°S"),
    (29.5, 31.0, "Faixa 7: 29.5°S – 31.0°S"),
    (31.0, 34.0, "Faixa 8: 31.0°S – 34.0°S")
]

def classificar_incidencia(valor):
    """Classifica incidência em categorias para visualização de Surtos Reais"""
    if pd.isna(valor) or valor < 0:
        return "Sem dados"
    elif valor == 0:
        return "Zero"
    elif valor < 50:
        return "1 a 49"
    elif valor < 500:
        return "50 a 499"
    elif valor < 2000:
        return "500 a 1.999"
    elif valor < 10000:
        return "2.000 a 9.999"
    else:
        return "> 10.000"

# Cores para os mapas (Paleta atualizada)
CORES_MAPA = {
    "Sem dados": "#f0f0f0",
    "Zero": "#ffffcc",
    "1 a 49": "#ffeda0",
    "50 a 499": "#feb24c",
    "500 a 1.999": "#fd8d3c",
    "2.000 a 9.999": "#f03b20",
    "> 10.000": "#bd0026"
}

print("=" * 70)
print("PROCESSAMENTO DE DADOS DE DENGUE - REGIÃO SUL DO BRASIL")
print("=" * 70)

# ===== ETAPA 1: CARREGAR E REESTRUTURAR DADOS =====
print("\n[1/5] Carregando dados do arquivo dengue_MENSAL.csv...")

# Ler o arquivo pulando 2 linhas de cabeçalho
df_raw = pd.read_csv(ARQUIVO_DENGUE, sep=';', encoding='latin-1', header=[0,1])

# Achatar os nomes das colunas multiníveis
df_raw.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df_raw.columns.values]

# Renomear as primeiras duas colunas
colunas = df_raw.columns.tolist()
colunas[0] = 'ANO'
colunas[1] = 'MES'
df_raw.columns = colunas

# Identificar colunas de municípios (códigos numéricos de 6 dígitos)
colunas_municipios = []
for col in df_raw.columns[2:]:
    # Extrair apenas dígitos
    col_limpo = ''.join(filter(str.isdigit, str(col)))
    if len(col_limpo) == 6:
        colunas_municipios.append((col, col_limpo))

print(f"    → Encontrados {len(colunas_municipios)} municípios")

# Transpor dados
print("    → Reestruturando dados...")

dados_reestruturados = []

for idx, row in df_raw.iterrows():
    ano = row['ANO']
    mes = row['MES']
    
    # Validar
    try:
        ano = int(ano)
        mes = int(mes)
    except (ValueError, TypeError):
        continue
    
    for col_original, cod_mun in colunas_municipios:
        casos = row[col_original]
        
        if pd.isna(casos):
            continue
        
        try:
            casos_int = max(0, int(float(casos)))
        except (ValueError, TypeError):
            continue
        
        dados_reestruturados.append({
            'CODIGO_MUNICIPIO': int(cod_mun),
            'ANO': ano,
            'MES': mes,
            'CASOS_DENGUE': casos_int
        })

df = pd.DataFrame(dados_reestruturados)
print(f"    ✓ Dados reestruturados: {len(df):,} registros")
print(f"    → Municípios únicos: {df['CODIGO_MUNICIPIO'].nunique()}")
print(f"    → Período: {df['ANO'].min()}-{df['ANO'].max()}")

# ===== ETAPA 2: ADICIONAR GEOLOCALIZAÇÃO =====
print("\n[2/5] Adicionando geolocalização dos municípios...")

try:
    print("    → Baixando dados geográficos com geobr...")
    import geobr
    
    gdf_municipios = geobr.read_municipality(year=2020)
    gdf_municipios['code_muni'] = gdf_municipios['code_muni'].astype(str).str[:6].astype(int)
    
    # Calcular centróides
    print("    → Calculando centróides...")
    gdf_municipios['latitude'] = gdf_municipios.geometry.centroid.y
    gdf_municipios['longitude'] = gdf_municipios.geometry.centroid.x
    
    # Filtrar região Sul
    gdf_sul = gdf_municipios[
        (gdf_municipios['code_muni'] >= 410000) & 
        (gdf_municipios['code_muni'] < 440000)
    ].copy()
    
    print(f"    ✓ Municípios da região Sul: {len(gdf_sul)}")
    
    # Merge
    geo_data = gdf_sul[['code_muni', 'name_muni', 'latitude', 'longitude', 'geometry']].copy()
    geo_data.columns = ['CODIGO_MUNICIPIO', 'NOME_MUNICIPIO', 'LATITUDE', 'LONGITUDE', 'geometry']
    
    df = df.merge(
        geo_data[['CODIGO_MUNICIPIO', 'NOME_MUNICIPIO', 'LATITUDE', 'LONGITUDE']], 
        on='CODIGO_MUNICIPIO', 
        how='left'
    )
    
    print(f"    ✓ Geolocalização adicionada: {(~df['LATITUDE'].isna()).sum():,} registros")
    
except Exception as e:
    print(f"    ⚠ Erro: {e}")
    print("    → Usando coordenadas estimadas...")
    df['LATITUDE'] = -(20 + (df['CODIGO_MUNICIPIO'] % 100000) / 10000)
    df['LONGITUDE'] = -(48 + (df['CODIGO_MUNICIPIO'] % 10000) / 1000)
    df['NOME_MUNICIPIO'] = "Município_" + df['CODIGO_MUNICIPIO'].astype(str)

# Remover sem coordenadas
df = df[df['LATITUDE'].notna()].copy()

# ===== ETAPA 3: CLASSIFICAR POR FAIXA DE LATITUDE =====
print("\n[3/5] Classificando municípios por faixa de latitude...")

def obter_faixa_latitude(lat):
    lat_abs = abs(lat)
    for i, (min_lat, max_lat, nome) in enumerate(FAIXAS_LATITUDE, 1):
        if min_lat <= lat_abs < max_lat:
            return i
    return None

df['FAIXA_LATITUDE'] = df['LATITUDE'].apply(obter_faixa_latitude)
df['CLASSIFICACAO_VISUAL'] = df['CASOS_DENGUE'].apply(classificar_incidencia)

df = df[df['FAIXA_LATITUDE'].notna()].copy()

print(f"    ✓ Classificação concluída: {len(df):,} registros")
for i in range(1, 9):
    count = (df['FAIXA_LATITUDE'] == i).sum()
    if count > 0:
        print(f"       {FAIXAS_LATITUDE[i-1][2]}: {count:,} registros")

# ===== ETAPA 4: GERAR ARQUIVOS XLSX POR FAIXA DE LATITUDE =====
print("\n[4/5] Gerando arquivos XLSX por faixa de latitude...")

for i in range(1, 9):
    df_faixa = df[df['FAIXA_LATITUDE'] == i].copy()
    
    if len(df_faixa) == 0:
        continue
    
    df_faixa = df_faixa.sort_values(['ANO', 'MES', 'CODIGO_MUNICIPIO'])
    
    municipios_unicos = df_faixa['CODIGO_MUNICIPIO'].nunique()
    casos_totais = df_faixa['CASOS_DENGUE'].sum()
    
    arquivo_xlsx = PASTA_CSVS / f"dengue_faixa_latitude_{i}.xlsx"
    
    # Salvar em XLSX com formatação
    with pd.ExcelWriter(arquivo_xlsx, engine='openpyxl') as writer:
        df_faixa.to_excel(writer, sheet_name=f'Faixa {i}', index=False)
        
        # Formatar colunas
        worksheet = writer.sheets[f'Faixa {i}']
        worksheet.column_dimensions['A'].width = 18  # CODIGO_MUNICIPIO
        worksheet.column_dimensions['B'].width = 8   # ANO
        worksheet.column_dimensions['C'].width = 8   # MES
        worksheet.column_dimensions['D'].width = 15  # CASOS_DENGUE
        worksheet.column_dimensions['E'].width = 30  # NOME_MUNICIPIO
        worksheet.column_dimensions['F'].width = 12  # LATITUDE
        worksheet.column_dimensions['G'].width = 12  # LONGITUDE
        worksheet.column_dimensions['H'].width = 18  # FAIXA_LATITUDE
        worksheet.column_dimensions['I'].width = 20  # CLASSIFICACAO_VISUAL
    
    print(f"    ✓ Faixa {i}: {municipios_unicos} municípios, {casos_totais:,} casos → {arquivo_xlsx.name}")

# ===== ETAPA 5: GERAR MAPAS DE CALOR ANUAIS =====
print("\n[5/5] Gerando mapas de calor anuais (2015-2024)...")

try:
    if 'gdf_sul' in locals():
        print("    → Gerando mapas com polígonos...")
        
        for ano in range(2015, 2025):
            df_ano = df[df['ANO'] == ano].groupby('CODIGO_MUNICIPIO').agg({
                'CASOS_DENGUE': 'sum'
            }).reset_index()
            
            if len(df_ano) == 0:
                continue
            
            df_ano['CLASSIFICACAO_VISUAL'] = df_ano['CASOS_DENGUE'].apply(classificar_incidencia)
            
            gdf_mapa = gdf_sul.merge(
                df_ano,
                left_on='code_muni',
                right_on='CODIGO_MUNICIPIO',
                how='left'
            )
            
            gdf_mapa['CLASSIFICACAO_VISUAL'] = gdf_mapa['CLASSIFICACAO_VISUAL'].fillna("Sem dados")
            
            fig, ax = plt.subplots(1, 1, figsize=(10, 14))
            
            # Definir fundo do oceano (azul claro)
            ax.set_facecolor('#a8d5f5')
            
            # Plotar países vizinhos em cinza (Paraguai, Argentina, Uruguai)
            try:
                # Carregar dados dos países da América do Sul
                import geopandas as gpd
                from shapely.geometry import box
                
                # Criar shapefiles simples para países vizinhos (aproximação)
                # Paraguai
                paraguai_bounds = box(-63, -28, -54, -19)
                # Argentina (parte sul)
                argentina_bounds = box(-74, -56, -53, -22)
                # Uruguai
                uruguai_bounds = box(-59, -35, -53, -30)
                
                # Plotar países vizinhos em cinza
                gdf_paraguai = gpd.GeoDataFrame([1], geometry=[paraguai_bounds], crs='EPSG:4326')
                gdf_argentina = gpd.GeoDataFrame([1], geometry=[argentina_bounds], crs='EPSG:4326')
                gdf_uruguai = gpd.GeoDataFrame([1], geometry=[uruguai_bounds], crs='EPSG:4326')
                
                gdf_paraguai.plot(ax=ax, color='#d3d3d3', edgecolor='#888888', linewidth=1, zorder=1)
                gdf_argentina.plot(ax=ax, color='#d3d3d3', edgecolor='#888888', linewidth=1, zorder=1)
                gdf_uruguai.plot(ax=ax, color='#d3d3d3', edgecolor='#888888', linewidth=1, zorder=1)
                
                # Adicionar labels dos países
                ax.text(-58, -23, 'Paraguai', fontsize=11, color='#666666', style='italic', 
                       ha='center', va='center', zorder=15)
                ax.text(-65, -40, 'Argentina', fontsize=11, color='#666666', style='italic',
                       ha='center', va='center', zorder=15)
                ax.text(-56, -32.5, 'Uruguai', fontsize=11, color='#666666', style='italic',
                       ha='center', va='center', zorder=15)
                ax.text(-42, -28, 'Oceano Atlântico', fontsize=11, color='#5a7fa8', style='italic',
                       ha='center', va='center', zorder=15)
            except:
                pass
            
            # Plotar região Sul com dados de dengue (sobre os países)
            for categoria in ["Sem dados", "0 a 9", "10 a 99", "100 a 299", "300 a 599", "> 600"]:
                gdf_cat = gdf_mapa[gdf_mapa['CLASSIFICACAO_VISUAL'] == categoria]
                if len(gdf_cat) > 0:
                    gdf_cat.plot(
                        ax=ax,
                        color=CORES_MAPA[categoria],
                        edgecolor='#444444',
                        linewidth=0.4,
                        label=categoria,
                        zorder=10
                    )
            
            ax.set_title(f'Incidência da Dengue do Ano {ano}', fontsize=16, fontweight='bold', pad=15)
            ax.axis('off')
            
            # Adicionar rosa dos ventos
            try:
                rosa_img = mpimg.imread(ARQUIVO_ROSA_VENTOS)
                ax_rosa = fig.add_axes([0.05, 0.85, 0.10, 0.10], zorder=30)
                ax_rosa.imshow(rosa_img)
                ax_rosa.axis('off')
            except:
                pass
            
            # Adicionar mapa de localização do Brasil (inset no canto superior direito)
            try:
                # Carregar estados do Brasil
                gdf_estados = geobr.read_state(year=2020)
                
                # Criar inset axes no canto superior direito
                ax_inset = fig.add_axes([0.75, 0.82, 0.20, 0.15], zorder=30)
                
                # Plotar todos os estados em cinza claro
                gdf_estados.plot(ax=ax_inset, color='#e0e0e0', edgecolor='#999999', linewidth=0.5)
                
                # Destacar região Sul (PR, SC, RS) em laranja
                estados_sul = gdf_estados[gdf_estados['abbrev_state'].isin(['PR', 'SC', 'RS'])]
                estados_sul.plot(ax=ax_inset, color='#ff9966', edgecolor='#333333', linewidth=0.8)
                
                ax_inset.set_xlim(-75, -33)
                ax_inset.set_ylim(-35, 5)
                ax_inset.axis('off')
                
                # Título do inset
                ax_inset.text(0.5, 1.05, 'Localização', transform=ax_inset.transAxes,
                            ha='center', fontsize=8, fontweight='bold')
            except:
                pass
            
            # Configurar legenda
            from matplotlib.patches import Rectangle
            legend_elements = []
            
            # Usar diretamente as chaves do dicionário CORES_MAPA na ordem em que foram definidas
            categorias = list(CORES_MAPA.keys())
            
            for cat in categorias:
                legend_elements.append(Rectangle((0,0),1,1, facecolor=CORES_MAPA[cat], edgecolor='#666666', linewidth=0.5, label=cat))
            
            leg = ax.legend(handles=legend_elements, title='Incidência dengue por 100 mil/hab', 
                          loc='lower left', fontsize=8, title_fontsize=7,
                          frameon=True, fancybox=False, shadow=False,
                          bbox_to_anchor=(0.01, 0.01))
            leg.get_frame().set_facecolor('white')
            leg.get_frame().set_edgecolor('black')
            leg.get_frame().set_linewidth(0.5)
            
            # Escala de barra no canto inferior direito
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            x_range = xlim[1] - xlim[0]
            y_range = ylim[1] - ylim[0]
            
            scale_x = xlim[1] - 0.25 * x_range
            scale_y = ylim[0] + 0.05 * y_range
            scale_length_km = 100
            scale_length_deg = scale_length_km / 111.0
            
            ax.plot([scale_x - scale_length_deg, scale_x], [scale_y, scale_y], 'k-', linewidth=3)
            ax.plot([scale_x - scale_length_deg, scale_x - scale_length_deg], [scale_y - 0.01*y_range, scale_y + 0.01*y_range], 'k-', linewidth=2)
            ax.plot([scale_x, scale_x], [scale_y - 0.01*y_range, scale_y + 0.01*y_range], 'k-', linewidth=2)
            ax.text(scale_x - scale_length_deg/2, scale_y - 0.03*y_range, f'{scale_length_km} km', 
                   ha='center', va='top', fontsize=8, fontweight='bold')
            
            # Fonte dos dados
            casos_ano = df_ano['CASOS_DENGUE'].sum()
            ax.text(0.98, 0.02, f'Fonte: DATASUS\nElaboração: NEDE/UFSM\nCasos: {casos_ano:,}', 
                   transform=ax.transAxes, fontsize=7, ha='right', va='bottom',
                   style='italic')
            
            arquivo_mapa = PASTA_MAPAS / f"mapa_dengue_{ano}.png"
            plt.tight_layout()
            plt.savefig(arquivo_mapa, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"    ✓ Mapa {ano}: {casos_ano:,} casos → {arquivo_mapa.name}")
    
    else:
        raise Exception("Shapefile não disponível")
    
except Exception as e:
    print(f"    → Gerando mapas de pontos...")
    
    for ano in range(2015, 2025):
        df_ano = df[df['ANO'] == ano].groupby(['CODIGO_MUNICIPIO', 'LATITUDE', 'LONGITUDE']).agg({
            'CASOS_DENGUE': 'sum'
        }).reset_index()
        
        if len(df_ano) == 0:
            continue
        
        df_ano['CLASSIFICACAO_VISUAL'] = df_ano['CASOS_DENGUE'].apply(classificar_incidencia)
        
        fig, ax = plt.subplots(1, 1, figsize=(10, 14))
        
        for categoria in ["0 a 9", "10 a 99", "100 a 299", "300 a 599", "> 600"]:
            df_cat = df_ano[df_ano['CLASSIFICACAO_VISUAL'] == categoria]
            if len(df_cat) > 0:
                sizes = np.where(df_cat['CASOS_DENGUE'] < 100, 60, 
                        np.where(df_cat['CASOS_DENGUE'] < 600, 120, 200))
                ax.scatter(
                    df_cat['LONGITUDE'],
                    df_cat['LATITUDE'],
                    c=CORES_MAPA[categoria],
                    s=sizes,
                    alpha=0.7,
                    edgecolors='#666666',
                    linewidth=0.5,
                    label=categoria
                )
        
        ax.set_title(f'Incidência da Dengue do Ano {ano}', fontsize=16, fontweight='bold')
        ax.set_xlabel('Longitude', fontsize=11)
        ax.set_ylabel('Latitude', fontsize=11)
        ax.grid(True, alpha=0.2, linestyle=':')
        
        # Adicionar rosa dos ventos
        try:
            rosa_img = mpimg.imread(ARQUIVO_ROSA_VENTOS)
            ax_rosa = fig.add_axes([0.08, 0.85, 0.10, 0.10], zorder=30)
            ax_rosa.imshow(rosa_img)
            ax_rosa.axis('off')
        except:
            pass
        
        # Legenda customizada
        from matplotlib.patches import Rectangle
        legend_elements = []
        
        categorias = list(CORES_MAPA.keys())
        
        for cat in categorias:
            legend_elements.append(Rectangle((0,0),1,1, facecolor=CORES_MAPA[cat], edgecolor='#666666', linewidth=0.5, label=cat))
        
        leg = ax.legend(handles=legend_elements, title='Incidência dengue por 100 mil/hab',
                      loc='lower left', fontsize=9, title_fontsize=8,
                      frameon=True, fancybox=False, shadow=False)
        leg.get_frame().set_facecolor('white')
        leg.get_frame().set_edgecolor('black')
        leg.get_frame().set_linewidth(0.5)
        
        casos_ano = df_ano['CASOS_DENGUE'].sum()
        ax.text(0.98, 0.02, f'Fonte: DATASUS\nElaboração: NEDE/UFSM\nCasos: {casos_ano:,}',
               transform=ax.transAxes, fontsize=7, ha='right', va='bottom', style='italic')
        
        arquivo_mapa = PASTA_MAPAS / f"mapa_dengue_{ano}.png"
        plt.tight_layout()
        plt.savefig(arquivo_mapa, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    ✓ Mapa {ano}: {casos_ano:,} casos → {arquivo_mapa.name}")

# ===== RESUMO FINAL =====
print("\n" + "=" * 70)
print("✅ PROCESSAMENTO CONCLUÍDO!")
print("=" * 70)
print(f"\n📊 Estatísticas Gerais:")
print(f"   • Registros processados: {len(df):,}")
print(f"   • Municípios únicos: {df['CODIGO_MUNICIPIO'].nunique()}")
print(f"   • Período: {df['ANO'].min()} - {df['ANO'].max()}")
print(f"   • Total de casos: {df['CASOS_DENGUE'].sum():,}")
print(f"\n📁 Arquivos Gerados:")
print(f"   • Arquivos XLSX por latitude: {PASTA_CSVS}/")
print(f"   • Mapas anuais: {PASTA_MAPAS}/")
print("=" * 70)
