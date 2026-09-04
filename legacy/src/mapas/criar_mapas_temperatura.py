"""
Script para criar mapas de temperatura da região Sul do Brasil
Gera visualizações geográficas coloridas com dados de temperatura por município
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from pathlib import Path

# Configurações
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

class MapaTemperaturas:
    def __init__(self, dados_dir, output_dir):
        """
        Inicializa o gerador de mapas
        
        Args:
            dados_dir: Diretório com os arquivos CSV de temperatura
            output_dir: Diretório onde os mapas serão salvos
        """
        self.dados_dir = Path(dados_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Carregar dados geográficos do Brasil
        print("Carregando dados geográficos...")
        self.gdf_municipios = self._carregar_geodados()
        
    def _carregar_geodados(self):
        """Carrega dados geográficos dos municípios do Brasil"""
        # URL dos dados do IBGE (municipios do Brasil)
        url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"
        
        try:
            gdf = gpd.read_file(url)
            # Filtrar apenas estados do Sul
            gdf = gdf[gdf['id'].str[:2].isin(['41', '42', '43'])]  # PR, SC, RS
            return gdf
        except Exception as e:
            print(f"Erro ao carregar geodados: {e}")
            print("Usando dados simplificados...")
            return None
    
    def _normalizar_nome_municipio(self, nome):
        """Normaliza nomes de municípios para correspondência"""
        import unicodedata
        # Remove acentos
        nome = ''.join(c for c in unicodedata.normalize('NFD', str(nome))
                      if unicodedata.category(c) != 'Mn')
        # Converte para minúsculas e remove espaços extras
        return nome.lower().strip().replace("'", "").replace("-", " ")
    
    def carregar_dados_temperatura(self, tipo='media'):
        """
        Carrega dados de temperatura
        
        Args:
            tipo: 'minima', 'media' ou 'maxima'
        
        Returns:
            DataFrame com dados de temperatura
        """
        arquivo_map = {
            'minima': 'Temp_minima_MENSAL.csv',
            'media': 'Temp_media_MENSAL.csv',
            'maxima': 'Temp_maxima_MENSAL.csv'
        }
        
        arquivo = self.dados_dir / arquivo_map.get(tipo, arquivo_map['media'])
        
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
        
        print(f"Carregando {arquivo}...")
        
        # Ler as primeiras 3 linhas: códigos, nomes dos municípios e cabeçalho
        # Primeira linha: códigos dos municípios
        codigos = pd.read_csv(arquivo, sep=';', encoding='utf-8', nrows=1, header=None)
        # Segunda linha: nomes dos municípios
        nomes = pd.read_csv(arquivo, sep=';', encoding='utf-8', skiprows=1, nrows=1, header=None)
        
        # Dados principais (pular as 2 primeiras linhas)
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8', skiprows=2)
        
        # Renomear colunas vazias no início
        if df.columns[0] == 'year':
            pass
        else:
            # Se a primeira coluna não for 'year', ajustar
            df = df.rename(columns={df.columns[0]: 'year', df.columns[1]: 'mes'})
        
        # Criar mapeamento de colunas para nomes de municípios
        # Ignorar as primeiras 3 colunas vazias ou de controle
        municipios_dict = {}
        for i in range(3, len(nomes.columns)):
            if i < len(nomes.columns):
                nome_mun = nomes.iloc[0, i]
                if pd.notna(nome_mun) and str(nome_mun).strip():
                    municipios_dict[df.columns[i-1]] = str(nome_mun).strip()
        
        # Renomear colunas com nomes de municípios
        df = df.rename(columns=municipios_dict)
        
        return df
    
    def preparar_dados_mapa(self, df, ano, mes):
        """
        Prepara dados para um mês/ano específico
        
        Args:
            df: DataFrame com dados de temperatura
            ano: Ano desejado
            mes: Mês desejado (1-12)
        
        Returns:
            GeoDataFrame pronto para plotar
        """
        # Filtrar dados do período
        df_periodo = df[(df['year'] == ano) & (df['mes'] == mes)].copy()
        
        if df_periodo.empty:
            raise ValueError(f"Sem dados para {mes:02d}/{ano}")
        
        # Pegar linha de dados
        linha = df_periodo.iloc[0]
        
        # Criar DataFrame com municípios e temperaturas
        dados_mapa = []
        for i, col in enumerate(df.columns):
            if col in ['year', 'mes']:
                continue
            
            try:
                valor = linha.iloc[i] if hasattr(linha, 'iloc') else linha[i]
                if pd.notna(valor):
                    temp_valor = float(valor)
                    dados_mapa.append({
                        'municipio': col,
                        'temperatura': temp_valor
                    })
            except (ValueError, TypeError, IndexError):
                # Ignorar valores que não podem ser convertidos para float
                continue
        
        df_temp = pd.DataFrame(dados_mapa)
        
        # Normalizar nomes
        df_temp['municipio_norm'] = df_temp['municipio'].apply(self._normalizar_nome_municipio)
        
        if self.gdf_municipios is not None:
            self.gdf_municipios['nome_norm'] = self.gdf_municipios['name'].apply(self._normalizar_nome_municipio)
            
            # Fazer merge com geodados
            gdf_merged = self.gdf_municipios.merge(
                df_temp,
                left_on='nome_norm',
                right_on='municipio_norm',
                how='left'
            )
            
            return gdf_merged
        else:
            return df_temp
    
    def criar_mapa(self, gdf, titulo, arquivo_saida, tipo_temp='media'):
        """
        Cria um mapa de temperatura
        
        Args:
            gdf: GeoDataFrame com dados
            titulo: Título do mapa
            arquivo_saida: Nome do arquivo de saída
            tipo_temp: Tipo de temperatura para definir escala de cores
        """
        fig, ax = plt.subplots(1, 1, figsize=(12, 14))
        
        # Definir escala de cores baseada no tipo
        if tipo_temp == 'minima':
            cmap = 'cool'  # Azul para frio
            vmin, vmax = 0, 25
        elif tipo_temp == 'maxima':
            cmap = 'hot'  # Vermelho para quente
            vmin, vmax = 15, 35
        else:  # media
            cmap = 'YlOrRd'  # Amarelo-Laranja-Vermelho
            vmin, vmax = 10, 30
        
        # Plotar municípios com dados
        gdf_com_dados = gdf[gdf['temperatura'].notna()]
        gdf_sem_dados = gdf[gdf['temperatura'].isna()]
        
        # Plotar municípios sem dados (cinza)
        if len(gdf_sem_dados) > 0:
            gdf_sem_dados.plot(ax=ax, color='lightgray', edgecolor='white', linewidth=0.3)
        
        # Plotar municípios com dados
        if len(gdf_com_dados) > 0:
            gdf_com_dados.plot(
                column='temperatura',
                ax=ax,
                legend=True,
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                edgecolor='white',
                linewidth=0.3,
                legend_kwds={
                    'label': 'Temperatura (°C)',
                    'orientation': 'vertical',
                    'shrink': 0.7,
                    'pad': 0.05
                }
            )
        
        # Configurar mapa
        ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20)
        ax.axis('off')
        
        # Adicionar informações
        texto_info = f"Região Sul do Brasil\n{len(gdf_com_dados)} municípios com dados"
        ax.text(0.02, 0.02, texto_info, transform=ax.transAxes,
                fontsize=9, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Salvar
        caminho_saida = self.output_dir / arquivo_saida
        plt.tight_layout()
        plt.savefig(caminho_saida, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"Mapa salvo: {caminho_saida}")
        
        return str(caminho_saida)
    
    def gerar_serie_mapas(self, tipo='media', ano=2015):
        """
        Gera uma série de mapas para todos os meses de um ano
        
        Args:
            tipo: Tipo de temperatura ('minima', 'media', 'maxima')
            ano: Ano desejado
        """
        # Carregar dados
        df = self.carregar_dados_temperatura(tipo)
        
        # Nome do tipo em português
        tipo_nome = {
            'minima': 'Mínima',
            'media': 'Média',
            'maxima': 'Máxima'
        }[tipo]
        
        meses_nome = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        
        mapas_criados = []
        
        print(f"\nGerando mapas de Temperatura {tipo_nome} para {ano}...")
        print("=" * 60)
        
        for mes in range(1, 13):
            try:
                # Preparar dados
                gdf = self.preparar_dados_mapa(df, ano, mes)
                
                # Criar título
                titulo = f"Temperatura {tipo_nome} - {meses_nome[mes-1]}/{ano}"
                
                # Nome do arquivo
                arquivo = f"mapa_temp_{tipo}_{ano}_{mes:02d}.png"
                
                # Criar mapa
                caminho = self.criar_mapa(gdf, titulo, arquivo, tipo)
                mapas_criados.append(caminho)
                
            except Exception as e:
                print(f"Erro ao criar mapa para {mes:02d}/{ano}: {e}")
        
        print("=" * 60)
        print(f"\nTotal de mapas criados: {len(mapas_criados)}")
        
        return mapas_criados
    
    def criar_mapa_comparativo(self, ano, mes):
        """
        Cria um mapa comparativo com as três temperaturas (min, média, max)
        
        Args:
            ano: Ano desejado
            mes: Mês desejado
        """
        fig, axes = plt.subplots(1, 3, figsize=(20, 8))
        
        tipos = ['minima', 'media', 'maxima']
        titulos = ['Temperatura Mínima', 'Temperatura Média', 'Temperatura Máxima']
        cmaps = ['cool', 'YlOrRd', 'hot']
        
        meses_nome = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        
        for i, (tipo, titulo_sub, cmap_name) in enumerate(zip(tipos, titulos, cmaps)):
            try:
                df = self.carregar_dados_temperatura(tipo)
                gdf = self.preparar_dados_mapa(df, ano, mes)
                
                ax = axes[i]
                
                # Plotar
                gdf_com_dados = gdf[gdf['temperatura'].notna()]
                gdf_sem_dados = gdf[gdf['temperatura'].isna()]
                
                if len(gdf_sem_dados) > 0:
                    gdf_sem_dados.plot(ax=ax, color='lightgray', edgecolor='white', linewidth=0.2)
                
                if len(gdf_com_dados) > 0:
                    gdf_com_dados.plot(
                        column='temperatura',
                        ax=ax,
                        legend=True,
                        cmap=cmap_name,
                        edgecolor='white',
                        linewidth=0.2,
                        legend_kwds={'label': '°C', 'shrink': 0.7}
                    )
                
                ax.set_title(titulo_sub, fontsize=12, fontweight='bold')
                ax.axis('off')
                
            except Exception as e:
                print(f"Erro ao processar {tipo}: {e}")
                ax.text(0.5, 0.5, 'Dados não disponíveis', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.axis('off')
        
        # Título geral
        fig.suptitle(f"Comparativo de Temperaturas - {meses_nome[mes-1]}/{ano}",
                     fontsize=16, fontweight='bold', y=0.98)
        
        # Salvar
        arquivo = f"mapa_comparativo_{ano}_{mes:02d}.png"
        caminho_saida = self.output_dir / arquivo
        plt.tight_layout()
        plt.savefig(caminho_saida, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"Mapa comparativo salvo: {caminho_saida}")
        
        return str(caminho_saida)


def main():
    """Função principal"""
    # Definir diretórios
    projeto_dir = Path(__file__).parent.parent
    dados_dir = projeto_dir / 'Dados'
    output_dir = projeto_dir / 'output' / 'mapas'
    
    # Criar diretório de saída
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Inicializar gerador de mapas
    print("=" * 60)
    print("GERADOR DE MAPAS DE TEMPERATURA - REGIÃO SUL DO BRASIL")
    print("=" * 60)
    
    gerador = MapaTemperaturas(dados_dir, output_dir)
    
    # Exemplos de uso:
    
    # 1. Gerar série de mapas de temperatura média para 2015
    print("\n1. Gerando série de mapas mensais de temperatura média (2015)...")
    gerador.gerar_serie_mapas(tipo='media', ano=2015)
    
    # 2. Criar mapa comparativo para Janeiro/2015
    print("\n2. Criando mapa comparativo (Janeiro/2015)...")
    gerador.criar_mapa_comparativo(ano=2015, mes=1)
    
    # 3. Você pode gerar para outros tipos e períodos:
    # gerador.gerar_serie_mapas(tipo='minima', ano=2015)
    # gerador.gerar_serie_mapas(tipo='maxima', ano=2015)
    # gerador.criar_mapa_comparativo(ano=2015, mes=7)  # Julho
    
    print("\n" + "=" * 60)
    print("PROCESSAMENTO CONCLUÍDO!")
    print(f"Mapas salvos em: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
