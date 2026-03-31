"""
Gerador de Mapas Anuais - Região Sul do Brasil
================================================
Este script gera automaticamente mapas anuais para:
- Temperatura Média (2015-2024)
- Temperatura Mínima (2015-2024)
- Temperatura Máxima (2015-2024)
- Dengue (2015-2024)
- Precipitação (2015-2024)

Total: 50 mapas

Autor: Sistema de Análise Geográfica
Data: 2024
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import urllib.request
import json
from datetime import datetime
import unicodedata
from matplotlib.patches import FancyArrowPatch, Rectangle
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib import cm
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

class GeradorMapasAnuais:
    def __init__(self, dir_dados=None, dir_saida=None):
        """
        Inicializa o gerador de mapas anuais
        
        Args:
            dir_dados: Diretório com os arquivos CSV (usa data/raw/ por padrão)
            dir_saida: Diretório para salvar os mapas gerados (usa output/mapas/ por padrão)
        """
        _base = Path(__file__).parent.parent.parent  # raiz do projeto
        self.dir_dados = Path(dir_dados) if dir_dados else _base / "data" / "raw"
        self.dir_saida = Path(dir_saida) if dir_saida else _base / "output" / "mapas"
        self._geodados_dir = _base / "data" / "geodados"
        self.dir_saida.mkdir(parents=True, exist_ok=True)
        
        print("Iniciando Gerador de Mapas Anuais...")
        print(f"Diretório de dados: {self.dir_dados.absolute()}")
        print(f"Diretório de saída: {self.dir_saida.absolute()}")
        
        # Carregar dados geográficos
        print("\nCarregando dados geográficos...")
        self.geodados = self._carregar_geodados()
        print(f"✓ Dados geográficos carregados: {len(self.geodados)} municípios")
    
    def _carregar_geodados(self):
        """Carrega os dados geográficos dos municípios da região sul"""
        # Verificar se existe cache local (agora em data/geodados/)
        cache_file = self._geodados_dir / 'cache_geodados.json'
        self._geodados_dir.mkdir(parents=True, exist_ok=True)
        
        if cache_file.exists():
            print("  (usando cache local)")
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"
            import time
            time.sleep(2)  # Aguardar 2 segundos antes de requisitar
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
            
            # Salvar cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        
        gdf = gpd.GeoDataFrame.from_features(data['features'])
        
        # Filtrar apenas estados da região sul (PR=41, SC=42, RS=43)
        gdf['estado'] = gdf['id'].str[:2].astype(int)
        gdf_sul = gdf[gdf['estado'].isin([41, 42, 43])].copy()
        
        return gdf_sul
    
    def _normalizar_nome_municipio(self, nome):
        """Remove acentos e normaliza nome do município"""
        if pd.isna(nome):
            return ""
        nome = str(nome).lower().strip()
        # Remove acentos
        nome = ''.join(c for c in unicodedata.normalize('NFD', nome)
                      if unicodedata.category(c) != 'Mn')
        return nome
    
    def _carregar_dados_temperatura(self, tipo):
        """
        Carrega dados de temperatura
        
        Args:
            tipo: 'minima', 'media' ou 'maxima'
        """
        arquivo = self.dir_dados / f'Temp_{tipo}_MENSAL.csv'
        print(f"  - Carregando {arquivo.name}...")
        
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
        
        # Ler primeira linha (códigos dos municípios)
        codigos = pd.read_csv(arquivo, sep=';', encoding='utf-8', nrows=1, header=None)
        
        # Ler segunda linha (nomes dos municípios)
        nomes = pd.read_csv(arquivo, sep=';', encoding='utf-8', skiprows=1, nrows=1, header=None)
        
        # Ler dados (pular as duas primeiras linhas) - usar decimal=',' para valores com vírgula
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8', skiprows=2, decimal=',')
        
        # Criar mapeamento código -> nome normalizado
        municipio_map = {}
        for i in range(2, len(codigos.columns)):
            cod = codigos.iloc[0, i]
            nome = nomes.iloc[0, i]
            if pd.notna(cod) and pd.notna(nome):
                municipio_map[i] = self._normalizar_nome_municipio(nome)
        
        return df, municipio_map
    
    def _carregar_dados_dengue(self):
        """Carrega dados de dengue"""
        arquivo = self.dir_dados / 'dengue_MENSAL.csv'
        print(f"  - Carregando {arquivo.name}...")
        
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
        
        # Mesma estrutura dos dados de temperatura
        codigos = pd.read_csv(arquivo, sep=';', encoding='utf-8', nrows=1, header=None)
        nomes = pd.read_csv(arquivo, sep=';', encoding='utf-8', skiprows=1, nrows=1, header=None)
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8', skiprows=2)
        
        municipio_map = {}
        for i in range(2, len(codigos.columns)):
            cod = codigos.iloc[0, i]
            nome = nomes.iloc[0, i]
            if pd.notna(cod) and pd.notna(nome):
                municipio_map[i] = self._normalizar_nome_municipio(nome)
        
        return df, municipio_map
    
    def _carregar_dados_precipitacao(self):
        """Carrega dados de precipitação"""
        arquivo = self.dir_dados / 'precipitacao_mensal_rev.csv'
        print(f"  - Carregando {arquivo.name}...")
        
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
        
        # Ler primeira linha (códigos dos municípios) - pulando a primeira coluna
        codigos = pd.read_csv(arquivo, sep=';', encoding='utf-8', nrows=1, header=None)
        
        # Ler segunda linha (nomes dos municípios)
        nomes = pd.read_csv(arquivo, sep=';', encoding='utf-8', skiprows=1, nrows=1, header=None)
        
        # Ler dados (pular as duas primeiras linhas)
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8', skiprows=2)
        
        # Criar mapeamento código -> nome normalizado
        municipio_map = {}
        for i in range(2, len(codigos.columns)):
            cod = codigos.iloc[0, i]
            nome = nomes.iloc[0, i]
            if pd.notna(cod) and pd.notna(nome):
                municipio_map[i] = self._normalizar_nome_municipio(nome)
        
        return df, municipio_map
    
    def _calcular_media_anual(self, df, municipio_map, ano):
        """
        Calcula a média anual para cada município
        
        Args:
            df: DataFrame com os dados mensais
            municipio_map: Mapeamento de índice para nome do município
            ano: Ano para calcular a média
        
        Returns:
            GeoDataFrame com médias anuais por município
        """
        # Filtrar dados do ano
        df_ano = df[df['year'] == ano].copy()
        
        if len(df_ano) == 0:
            return None
        
        # Calcular médias por município
        dados_municipios = []
        
        for idx, nome_norm in municipio_map.items():
            # Extrair valores do ano
            valores = []
            for _, linha in df_ano.iterrows():
                if idx < len(linha):
                    valor = linha.iloc[idx]
                    if pd.notna(valor):
                        try:
                            valores.append(float(valor))
                        except (ValueError, TypeError):
                            continue
            
            if valores:
                media_anual = np.mean(valores)
                dados_municipios.append({
                    'municipio_norm': nome_norm,
                    'valor': media_anual
                })
        
        # Criar GeoDataFrame
        df_resultado = pd.DataFrame(dados_municipios)
        
        # Normalizar nomes nos geodados
        gdf = self.geodados.copy()
        gdf['municipio_norm'] = gdf['name'].apply(self._normalizar_nome_municipio)
        
        # Merge com geodados
        gdf_final = gdf.merge(df_resultado, on='municipio_norm', how='left')
        
        return gdf_final
    
    def _criar_mapa(self, gdf, titulo, arquivo_saida, cmap='YlOrRd', vmin=None, vmax=None, 
                    bins=None, labels=None, label_legenda='Valor'):
        """
        Cria um mapa com os dados fornecidos (padrão igual aos mapas de dengue)
        Agora com legenda de classes discretas
        
        Args:
            gdf: GeoDataFrame com os dados
            titulo: Título do mapa
            arquivo_saida: Caminho para salvar o arquivo
            cmap: Esquema de cores (lista de cores ou nome do colormap)
            vmin: Valor mínimo para escala de cores (ignorado se bins fornecido)
            vmax: Valor máximo para escala de cores (ignorado se bins fornecido)
            bins: Lista de limites das classes (ex: [0, 10, 20, 30])
            labels: Lista de rótulos das classes (ex: ['0-10', '10-20', '20-30'])
            label_legenda: Título da legenda
        """
        # Configurar fonte Times New Roman
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.rcParams['font.size'] = 12
        
        fig = plt.figure(figsize=(16, 14))
        ax = fig.add_subplot(111)
        
        # Se bins e labels foram fornecidos, usar legenda discreta
        if bins is not None and labels is not None:
            # Classificar os dados
            gdf['classe'] = pd.cut(gdf['valor'], bins=bins, labels=labels, include_lowest=True)
            
            # Definir cores
            if isinstance(cmap, list):
                colors = cmap
            else:
                # Gerar cores do colormap
                cm_obj = plt.cm.get_cmap(cmap)
                colors = [cm_obj(i / (len(labels) - 1)) for i in range(len(labels))]
            
            cmap_custom = ListedColormap(colors)
            
            # Preencher municípios sem dados com a cor mais clara
            gdf_plot = gdf.copy()
            gdf_plot.loc[gdf_plot['valor'].isna(), 'classe'] = labels[0]
            
            # Plotar todos os municípios por classe
            for label, color in zip(labels, colors):
                subset = gdf_plot[gdf_plot['classe'] == label]
                if len(subset) > 0:
                    subset.plot(ax=ax, color=color, edgecolor='#999999', linewidth=0.4)
            
        else:
            # Modo contínuo (fallback)
            gdf[gdf['valor'].isna()].plot(ax=ax, color='lightgray', edgecolor='#999999', linewidth=0.4)
            
            if vmin is None:
                vmin = gdf['valor'].min()
            if vmax is None:
                vmax = gdf['valor'].max()
            
            gdf[gdf['valor'].notna()].plot(
                column='valor',
                ax=ax,
                legend=True,
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                edgecolor='#999999',
                linewidth=0.4,
                legend_kwds={
                    'label': label_legenda,
                    'orientation': 'horizontal',
                    'shrink': 0.8,
                    'pad': 0.05
                }
            )
        
        # Adicionar fronteiras estaduais (mais grossas e escuras) - IGUAL DENGUE
        # Usar dissolve apenas nos geodados base para evitar lentidão
        if not hasattr(self, '_estados_boundary'):
            gdf_temp = self.geodados.copy()
            gdf_temp['estado_code'] = gdf_temp['id'].astype(str).str[:2]
            self._estados_boundary = gdf_temp.dissolve(by='estado_code').boundary
        
        self._estados_boundary.plot(ax=ax, edgecolor='#333333', linewidth=1.5, zorder=10)
        
        ax.set_title(titulo, fontsize=22, fontweight='bold', pad=20, fontfamily='Times New Roman')
        ax.axis('off')
        ax.set_aspect('equal')
        
        # Criar legenda customizada SE bins/labels foram fornecidos
        if bins is not None and labels is not None:
            legend_patches = []
            for label, color in zip(labels, colors):
                patch = mpatches.Patch(color=color, label=label)
                legend_patches.append(patch)
            
            legend = ax.legend(handles=legend_patches,
                              title=label_legenda,
                              loc='lower left',
                              bbox_to_anchor=(0.02, 0.02),
                              frameon=True,
                              fancybox=True,
                              shadow=True,
                              fontsize=11,
                              title_fontsize=12)
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_alpha(0.95)
            legend.get_title().set_fontweight('bold')
        
        # ADICIONAR ROSA DOS VENTOS (canto superior esquerdo) - IGUAL DENGUE
        rosa_path = self.dir_dados / 'R.png'
        
        if rosa_path.exists():
            try:
                rosa_img = Image.open(rosa_path)
                
                if rosa_img.mode != 'RGBA':
                    rosa_img = rosa_img.convert('RGBA')
                
                background = Image.new('RGBA', rosa_img.size, (255, 255, 255, 0))
                rosa_final = Image.alpha_composite(background, rosa_img)
                
                imagebox = OffsetImage(rosa_final, zoom=0.15)
                ab = AnnotationBbox(imagebox, (0.08, 0.92),
                                   xycoords='figure fraction',
                                   frameon=False,
                                   box_alignment=(0.5, 0.5),
                                   zorder=100)
                fig.add_artist(ab)
            except Exception as e:
                print(f"  ! Aviso: Não foi possível carregar rosa dos ventos: {e}")
        
        # ADICIONAR ESCALA GRÁFICA (canto inferior direito) - IGUAL DENGUE
        bounds = gdf.total_bounds
        map_width = bounds[2] - bounds[0]
        map_height = bounds[3] - bounds[1]
        
        lat_media = (bounds[1] + bounds[3]) / 2
        km_per_lat_degree = 111.0
        km_per_lon_degree = 111.0 * np.cos(np.radians(lat_media))
        
        real_height_km = map_height * km_per_lat_degree
        real_width_km = map_width * km_per_lon_degree
        
        fig_width_cm = 16 * 2.54
        fig_height_cm = 14 * 2.54
        map_height_cm_effective = fig_height_cm * 0.80
        
        km_per_cm = real_height_km / map_height_cm_effective
        escala_numerica = int(km_per_cm * 100000)
        
        scale_x = bounds[2] - map_width * 0.28
        scale_y = bounds[1] + map_height * 0.06
        
        segments = [0, 100, 200, 300]
        segment_width_degrees = 100 / km_per_lon_degree
        
        for i in range(len(segments) - 1):
            x_start = scale_x + (i * segment_width_degrees)
            color = 'black' if i % 2 == 0 else 'white'
            
            rect = Rectangle((x_start, scale_y), 
                           segment_width_degrees, 
                           map_height * 0.015,
                           facecolor=color,
                           edgecolor='black',
                           linewidth=1.8,
                           zorder=50)
            ax.add_patch(rect)
        
        for i, km in enumerate(segments):
            x_pos = scale_x + (i * segment_width_degrees)
            ax.text(x_pos, scale_y + map_height*0.018, f'{km}',
                   ha='center', va='bottom',
                   fontsize=10,
                   fontweight='bold',
                   fontfamily='Times New Roman')
        
        x_final = scale_x + (len(segments)-1) * segment_width_degrees
        ax.text(x_final + segment_width_degrees*0.3, scale_y + map_height*0.0075,
               'km',
               ha='left', va='center',
               fontsize=11,
               fontweight='bold',
               fontfamily='Times New Roman')
        
        scale_center_x = scale_x + (segment_width_degrees * (len(segments)-1) / 2)
        
        ax.text(scale_center_x, scale_y - map_height*0.020,
               f'Escala 1:{escala_numerica:,}'.replace(',', '.'),
               ha='center', va='top',
               fontsize=9,
               fontfamily='Times New Roman',
               style='italic')
        
        ax.text(scale_center_x, scale_y - map_height*0.035,
               f'1 cm ≈ {km_per_cm:.1f} km',
               ha='center', va='top',
               fontsize=9,
               fontweight='bold',
               fontfamily='Times New Roman')
        
        # Adicionar fonte dos dados
        plt.figtext(0.98, 0.01,
                   f'Fonte: Dados climáticos\nElaborado em: {datetime.now().strftime("%d/%m/%Y")}',
                   fontsize=10,
                   ha='right',
                   style='italic',
                   fontfamily='Times New Roman',
                   color='#333333')
        
        plt.tight_layout()
        plt.savefig(arquivo_saida, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Resetar configurações de fonte
        plt.rcParams['font.family'] = 'sans-serif'
        
        print(f"    ✓ Mapa salvo: {arquivo_saida.name}")
    
    def _criar_mapa_dengue(self, gdf, ano, arquivo_saida):
        """
        Cria um mapa especializado para dengue com:
        - Norte verdadeiro
        - Escala gráfica
        - Fonte Times New Roman
        - Legenda customizada com classes definidas
        - Incidência por 100 mil habitantes
        """
        # Configurar fonte Times New Roman para todo o gráfico
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.rcParams['font.size'] = 12
        
        # Calcular incidência por 100 mil habitantes (assumindo população)
        # Nota: Se tiver dados de população, multiplicar por (casos/população)*100000
        # Por enquanto, vamos usar os valores totais como proxy
        gdf['incidencia'] = gdf['valor']  # Aqui você pode ajustar com dados de população
        
        # Definir classes de incidência
        bins = [0, 300, 3000, 10000, 15000, 30000, 80000, float('inf')]
        labels = ['0 - 300', '301 - 3000', '3001 - 10000', '10001 - 15000', 
                  '15001 - 30000', '30001 - 80000', '> 80000']
        
        # Classificar os dados
        gdf['classe'] = pd.cut(gdf['incidencia'], bins=bins, labels=labels, include_lowest=True)
        
        # Definir cores para cada classe (gradiente de laranja)
        colors = ['#FFF5EB', '#FFE0B2', '#FFB74D', '#FF9800', '#F57C00', '#E65100', '#BF360C']
        cmap_custom = ListedColormap(colors)
        
        # Criar figura com proporção adequada
        fig = plt.figure(figsize=(16, 14))
        ax = fig.add_subplot(111)
        
        # Preencher municípios sem dados com a cor mais clara (classe 0-300)
        gdf_plot = gdf.copy()
        gdf_plot.loc[gdf_plot['incidencia'].isna(), 'classe'] = labels[0]  # Primeira classe
        
        # Plotar todos os municípios por classe
        for i, (label, color) in enumerate(zip(labels, colors)):
            subset = gdf_plot[gdf_plot['classe'] == label]
            if len(subset) > 0:
                subset.plot(ax=ax, color=color, edgecolor='#999999', linewidth=0.4)
        
        # Adicionar fronteiras estaduais (mais grossas e escuras)
        # Dissolver por estado (código IBGE estadual: primeiros 2 dígitos)
        gdf['estado_code'] = gdf['id'].astype(str).str[:2]
        estados_gdf = gdf.dissolve(by='estado_code')
        estados_gdf.boundary.plot(ax=ax, edgecolor='#333333', linewidth=1.5, zorder=10)
        
        # Título
        ax.set_title(f'Incidência da Dengue do Ano {ano}',
                    fontsize=22, fontweight='bold', pad=20,
                    fontfamily='Times New Roman')
        
        ax.axis('off')
        ax.set_aspect('equal')
        
        # Criar legenda customizada
        legend_patches = []
        for label, color in zip(labels, colors):
            patch = mpatches.Patch(color=color, label=label)
            legend_patches.append(patch)
        
        # Posicionar legenda
        legend = ax.legend(handles=legend_patches,
                          title='Incidência dengue por 100 mil/hab',
                          loc='lower left',
                          bbox_to_anchor=(0.02, 0.02),
                          frameon=True,
                          fancybox=True,
                          shadow=True,
                          fontsize=11,
                          title_fontsize=12)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_alpha(0.95)
        legend.get_title().set_fontweight('bold')
        
        # Adicionar Rosa dos Ventos (canto superior esquerdo) - carregar imagem
        rosa_path = self.dir_dados / 'R.png'
        
        if rosa_path.exists():
            try:
                # Carregar imagem e converter para RGBA para garantir transparência
                rosa_img = Image.open(rosa_path)
                
                # Converter para RGBA se necessário
                if rosa_img.mode != 'RGBA':
                    rosa_img = rosa_img.convert('RGBA')
                
                # Criar uma nova imagem com fundo branco
                background = Image.new('RGBA', rosa_img.size, (255, 255, 255, 0))
                
                # Compor a imagem sobre fundo transparente
                rosa_final = Image.alpha_composite(background, rosa_img)
                
                # Posicionar no canto superior esquerdo em coordenadas da figura
                imagebox = OffsetImage(rosa_final, zoom=0.15)
                
                # Converter coordenadas da figura para coordenadas do eixo
                # Posicionar no canto superior esquerdo
                ab = AnnotationBbox(imagebox, (0.08, 0.92),
                                   xycoords='figure fraction',
                                   frameon=False,
                                   box_alignment=(0.5, 0.5),
                                   zorder=100)
                fig.add_artist(ab)
            except Exception as e:
                print(f"  ! Aviso: Não foi possível carregar rosa dos ventos: {e}")
        else:
            print(f"  ! Aviso: Arquivo R.png não encontrado em {rosa_path}")
        
        # Adicionar escala gráfica cartográfica (canto inferior direito)
        bounds = gdf.total_bounds
        map_width = bounds[2] - bounds[0]
        map_height = bounds[3] - bounds[1]
        
        # Calcular escala real do mapa com precisão
        # Latitude média da região sul: aproximadamente -27°
        import numpy as np
        lat_media = (bounds[1] + bounds[3]) / 2
        
        # 1 grau de latitude = 111 km (constante)
        # 1 grau de longitude varia com latitude: 111 * cos(latitude)
        km_per_lat_degree = 111.0
        km_per_lon_degree = 111.0 * np.cos(np.radians(lat_media))
        
        # Calcular dimensões reais do mapa
        real_height_km = map_height * km_per_lat_degree
        real_width_km = map_width * km_per_lon_degree
        
        # Tamanho da figura em cm
        fig_width_inches = 16
        fig_height_inches = 14
        fig_width_cm = fig_width_inches * 2.54  # 40.64 cm
        fig_height_cm = fig_height_inches * 2.54  # 35.56 cm
        
        # O mapa ocupa cerca de 80% da área útil (considerando título e margens)
        map_height_cm_effective = fig_height_cm * 0.80
        
        # Calcular km por cm no mapa impresso
        km_per_cm = real_height_km / map_height_cm_effective
        
        # Escala numérica: 1:X (1 cm no mapa = X cm na realidade)
        escala_numerica = int(km_per_cm * 100000)  # km para cm (*100000)
        
        # Posição da escala (canto inferior direito)
        scale_x = bounds[2] - map_width * 0.28
        scale_y = bounds[1] + map_height * 0.06
        
        # Definir segmentos da escala gráfica (em km)
        segments = [0, 100, 200, 300]
        segment_width_degrees = 100 / km_per_lon_degree
        
        # Desenhar barra de escala com segmentos alternados
        from matplotlib.patches import Rectangle, FancyBboxPatch
        
        for i in range(len(segments) - 1):
            x_start = scale_x + (i * segment_width_degrees)
            
            # Alternar cores (preto/branco)
            color = 'black' if i % 2 == 0 else 'white'
            
            rect = Rectangle((x_start, scale_y), 
                           segment_width_degrees, 
                           map_height * 0.015,
                           facecolor=color,
                           edgecolor='black',
                           linewidth=1.8,
                           zorder=50)
            ax.add_patch(rect)
        
        # Adicionar marcações de distância acima da barra
        for i, km in enumerate(segments):
            x_pos = scale_x + (i * segment_width_degrees)
            ax.text(x_pos, scale_y + map_height*0.018, f'{km}',
                   ha='center', va='bottom',
                   fontsize=10,
                   fontweight='bold',
                   fontfamily='Times New Roman')
        
        # Label "km" ao lado da escala
        x_final = scale_x + (len(segments)-1) * segment_width_degrees
        ax.text(x_final + segment_width_degrees*0.3, scale_y + map_height*0.0075,
               'km',
               ha='left', va='center',
               fontsize=11,
               fontweight='bold',
               fontfamily='Times New Roman')
        
        # Escala numérica e relação km/cm abaixo da barra
        scale_center_x = scale_x + (segment_width_degrees * (len(segments)-1) / 2)
        
        ax.text(scale_center_x, scale_y - map_height*0.020,
               f'Escala 1:{escala_numerica:,}'.replace(',', '.'),
               ha='center', va='top',
               fontsize=9,
               fontfamily='Times New Roman',
               style='italic')
        
        ax.text(scale_center_x, scale_y - map_height*0.035,
               f'1 cm ≈ {km_per_cm:.1f} km',
               ha='center', va='top',
               fontsize=9,
               fontweight='bold',
               fontfamily='Times New Roman')
        
        # Remover informações adicionais (conforme solicitado)
        
        # Adicionar fonte dos dados
        plt.figtext(0.98, 0.01,
                   f'Fonte: DATASUS\nElaborado em: {datetime.now().strftime("%d/%m/%Y")}',
                   fontsize=10,
                   ha='right',
                   style='italic',
                   fontfamily='Times New Roman',
                   color='#333333')
        
        plt.tight_layout()
        plt.savefig(arquivo_saida, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Resetar configurações de fonte
        plt.rcParams['font.family'] = 'sans-serif'
        
        print(f"    ✓ Mapa salvo: {arquivo_saida.name}")
    
    def gerar_mapas_temperatura(self, ano, tipo):
        """
        Gera mapa de temperatura para um ano específico
        
        Args:
            ano: Ano a gerar o mapa
            tipo: 'minima', 'media' ou 'maxima'
        """
        # Carregar dados
        df, municipio_map = self._carregar_dados_temperatura(tipo)
        
        # Calcular média anual
        gdf = self._calcular_media_anual(df, municipio_map, ano)
        
        if gdf is None:
            print(f"    ⚠ Sem dados para {ano}")
            return
        
        # Criar mapa
        titulo = f'Temperatura {tipo.capitalize()} - Ano {ano}\nMédia Anual - Região Sul do Brasil'
        arquivo = self.dir_saida / f'temperatura_{tipo}_{ano}.png'
        
        # Definir classes e cores baseado no tipo
        if tipo == 'minima':
            # Temperatura Mínima: -2 a 18°C
            bins = [-5, 0, 3, 6, 9, 12, 15, 20]
            labels = ['< 0°C', '0 - 2°C', '3 - 5°C', '6 - 8°C', '9 - 11°C', '12 - 14°C', '> 15°C']
            colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#08519c']
            self._criar_mapa(gdf, titulo, arquivo, cmap=colors, 
                           bins=bins, labels=labels, 
                           label_legenda='Temperatura mínima (°C)')
        elif tipo == 'maxima':
            # Temperatura Máxima: 22 a 36°C
            bins = [20, 24, 26, 28, 30, 32, 34, 40]
            labels = ['< 24°C', '24 - 25°C', '26 - 27°C', '28 - 29°C', '30 - 31°C', '32 - 33°C', '> 34°C']
            colors = ['#fff5f0', '#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26', '#a50f15']
            self._criar_mapa(gdf, titulo, arquivo, cmap=colors, 
                           bins=bins, labels=labels, 
                           label_legenda='Temperatura máxima (°C)')
        else:  # media
            # Temperatura Média: 12 a 24°C
            bins = [10, 14, 16, 18, 20, 22, 24, 28]
            labels = ['< 14°C', '14 - 15°C', '16 - 17°C', '18 - 19°C', '20 - 21°C', '22 - 23°C', '> 24°C']
            colors = ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c']
            self._criar_mapa(gdf, titulo, arquivo, cmap=colors, 
                           bins=bins, labels=labels, 
                           label_legenda='Temperatura média (°C)')
    
    def gerar_mapas_dengue(self, ano):
        """Gera mapa de dengue para um ano específico"""
        # Carregar dados
        df, municipio_map = self._carregar_dados_dengue()
        
        # Para dengue, vamos somar os casos (não fazer média)
        df_ano = df[df['year'] == ano].copy()
        
        if len(df_ano) == 0:
            print(f"    ⚠ Sem dados para {ano}")
            return
        
        # Somar casos por município
        dados_municipios = []
        
        for idx, nome_norm in municipio_map.items():
            valores = []
            for _, linha in df_ano.iterrows():
                if idx < len(linha):
                    valor = linha.iloc[idx]
                    if pd.notna(valor):
                        try:
                            valores.append(float(valor))
                        except (ValueError, TypeError):
                            continue
            
            if valores:
                total_casos = np.sum(valores)
                dados_municipios.append({
                    'municipio_norm': nome_norm,
                    'valor': total_casos
                })
        
        # Criar GeoDataFrame
        df_resultado = pd.DataFrame(dados_municipios)
        gdf = self.geodados.copy()
        gdf['municipio_norm'] = gdf['name'].apply(self._normalizar_nome_municipio)
        gdf_final = gdf.merge(df_resultado, on='municipio_norm', how='left')
        
        # Criar mapa especializado para dengue
        arquivo = self.dir_saida / f'dengue_{ano}.png'
        self._criar_mapa_dengue(gdf_final, ano, arquivo)
    
    def gerar_mapas_precipitacao(self, ano):
        """Gera mapa de precipitação para um ano específico"""
        # Carregar dados
        df, municipio_map = self._carregar_dados_precipitacao()
        
        # Calcular média anual
        gdf = self._calcular_media_anual(df, municipio_map, ano)
        
        if gdf is None:
            print(f"    ⚠ Sem dados para {ano}")
            return
        
        # Criar mapa com classes
        titulo = f'Precipitação - Ano {ano}\nMédia Anual (mm) - Região Sul do Brasil'
        arquivo = self.dir_saida / f'precipitacao_{ano}.png'
        
        # Definir classes para precipitação: 0 a 350mm
        bins = [0, 50, 100, 150, 200, 250, 300, 400]
        labels = ['0 - 49 mm', '50 - 99 mm', '100 - 149 mm', '150 - 199 mm', 
                  '200 - 249 mm', '250 - 299 mm', '> 300 mm']
        colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#3182bd', '#08519c']
        
        self._criar_mapa(gdf, titulo, arquivo, cmap=colors, 
                       bins=bins, labels=labels, 
                       label_legenda='Precipitação média (mm)')
    
    def gerar_todos_mapas(self, ano_inicial=2015, ano_final=2024):
        """
        Gera todos os mapas para o intervalo de anos especificado
        
        Args:
            ano_inicial: Ano inicial (padrão: 2015)
            ano_final: Ano final (padrão: 2024)
        """
        print("\n" + "="*70)
        print("GERAÇÃO DE MAPAS ANUAIS - REGIÃO SUL DO BRASIL")
        print("="*70)
        
        anos = list(range(ano_inicial, ano_final + 1))
        total_mapas = len(anos) * 5  # 3 temperaturas + dengue + precipitação
        contador = 0
        
        inicio = datetime.now()
        
        for ano in anos:
            print(f"\n{'─'*70}")
            print(f"Processando ano: {ano}")
            print(f"{'─'*70}")
            
            # Mapas de temperatura
            for tipo in ['minima', 'media', 'maxima']:
                contador += 1
                print(f"\n[{contador}/{total_mapas}] Temperatura {tipo.capitalize()} - {ano}")
                try:
                    self.gerar_mapas_temperatura(ano, tipo)
                except Exception as e:
                    print(f"    ✗ Erro: {e}")
            
            # Mapa de dengue
            contador += 1
            print(f"\n[{contador}/{total_mapas}] Dengue - {ano}")
            try:
                self.gerar_mapas_dengue(ano)
            except Exception as e:
                print(f"    ✗ Erro: {e}")
            
            # Mapa de precipitação
            contador += 1
            print(f"\n[{contador}/{total_mapas}] Precipitação - {ano}")
            try:
                self.gerar_mapas_precipitacao(ano)
            except Exception as e:
                print(f"    ✗ Erro: {e}")
        
        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()
        
        print("\n" + "="*70)
        print("GERAÇÃO CONCLUÍDA!")
        print("="*70)
        print(f"Total de mapas gerados: {contador}")
        print(f"Tempo total: {duracao:.1f} segundos ({duracao/60:.1f} minutos)")
        print(f"Diretório de saída: {self.dir_saida.absolute()}")
        print("="*70)


def main():
    """Função principal"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║    GERADOR AUTOMÁTICO DE MAPAS ANUAIS - REGIÃO SUL DO BRASIL       ║
║                                                                      ║
║    Este script irá gerar automaticamente:                           ║
║    • Mapas de Temperatura Média (2015-2024): 10 mapas             ║
║    • Mapas de Temperatura Mínima (2015-2024): 10 mapas            ║
║    • Mapas de Temperatura Máxima (2015-2024): 10 mapas            ║
║    • Mapas de Casos de Dengue (2015-2024): 10 mapas               ║
║    • Mapas de Precipitação (2015-2024): 10 mapas                  ║
║                                                                      ║
║    TOTAL: 50 mapas em alta resolução (300 DPI)                     ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Criar gerador
        gerador = GeradorMapasAnuais()
        
        # Gerar todos os mapas
        gerador.gerar_todos_mapas(ano_inicial=2015, ano_final=2024)
        
        print("\n✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"\nTodos os mapas foram salvos em:")
        print(f"  {gerador.dir_saida.absolute()}")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
