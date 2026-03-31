"""
Script de Visualização de Dados
Autor: Especialista em Ciência de Dados e Bioestatística
Objetivo: Gerar visualizações de alta qualidade para análise epidemiológica
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configurações de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class VisualizadorDados:
    """Classe para criação de visualizações científicas"""
    
    def __init__(self, df, resultados_analise=None):
        """
        Inicializa o visualizador
        
        Args:
            df (pd.DataFrame): DataFrame com os dados
            resultados_analise (dict): Resultados da análise estatística (opcional)
        """
        self.df = df
        self.resultados_analise = resultados_analise or {}
        
        # Normalizar nomes das colunas
        self.df.columns = [col.strip().lower() for col in self.df.columns]
        
        # Criar diretório de saída
        import os
        self.output_dir = str(Path(__file__).parent.parent.parent / "output" / "analise_estatistica")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configurar estilo de plots
        self._configurar_estilo()
    
    def _configurar_estilo(self):
        """Configura o estilo padrão dos gráficos"""
        plt.rcParams['figure.figsize'] = (12, 7)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 13
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['figure.titlesize'] = 14
    
    def scatter_regressao_spearman(self, var_clima, var_resposta='casos de dengue', 
                                    resultados_spearman=None):
        """
        Cria scatter plot com linha de tendência e correlação de Spearman
        
        Args:
            var_clima (str): Variável climática (eixo X)
            var_resposta (str): Variável resposta (eixo Y)
            resultados_spearman (dict): Resultados da correlação de Spearman
        """
        # Preparar dados
        dados_completos = self.df[[var_clima, var_resposta]].dropna()
        
        if len(dados_completos) == 0:
            print(f"✗ Sem dados para plotar: {var_clima} vs {var_resposta}")
            return
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Scatter plot
        ax.scatter(dados_completos[var_clima], dados_completos[var_resposta], 
                   alpha=0.6, s=50, color='steelblue', edgecolors='black', linewidth=0.5)
        
        # Linha de tendência (regressão linear para visualização)
        z = np.polyfit(dados_completos[var_clima], dados_completos[var_resposta], 1)
        p = np.poly1d(z)
        x_line = np.linspace(dados_completos[var_clima].min(), 
                             dados_completos[var_clima].max(), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label='Linha de tendência')
        
        # Título com correlação de Spearman
        if resultados_spearman:
            rho = resultados_spearman.get('rho', 0)
            p_valor = resultados_spearman.get('p_valor', 1)
            sig = "***" if p_valor < 0.001 else "**" if p_valor < 0.01 else "*" if p_valor < 0.05 else "ns"
            titulo = f'{var_resposta.title()} vs {var_clima.title()}\n'
            titulo += f'ρ (Spearman) = {rho:.4f} {sig} (p = {p_valor:.4e})'
        else:
            titulo = f'{var_resposta.title()} vs {var_clima.title()}'
        
        ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel(var_clima.title(), fontsize=12, fontweight='bold')
        ax.set_ylabel(var_resposta.title(), fontsize=12, fontweight='bold')
        
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Salvar
        filename = f"{self.output_dir}/scatter_{var_clima.replace(' ', '_')}_vs_dengue.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Scatter plot salvo: {filename}")
        plt.close()
    
    def boxplot_grupos_temperatura(self, var_clima, var_resposta='casos de dengue',
                                    resultados_mann_whitney=None):
        """
        Cria boxplot comparando grupos Alta vs Baixa temperatura
        
        Args:
            var_clima (str): Variável climática
            var_resposta (str): Variável resposta
            resultados_mann_whitney (dict): Resultados do teste Mann-Whitney
        """
        # Criar grupos usando mediana
        mediana = self.df[var_clima].median()
        df_temp = self.df.copy()
        df_temp['grupo'] = df_temp[var_clima].apply(
            lambda x: 'Alta' if x >= mediana else 'Baixa' if pd.notna(x) else np.nan
        )
        
        # Remover NaNs
        df_plot = df_temp[['grupo', var_resposta]].dropna()
        
        if len(df_plot) == 0:
            print(f"✗ Sem dados para boxplot: {var_clima}")
            return
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Boxplot
        bp = ax.boxplot([df_plot[df_plot['grupo'] == 'Baixa'][var_resposta],
                         df_plot[df_plot['grupo'] == 'Alta'][var_resposta]],
                        labels=['Baixa', 'Alta'],
                        patch_artist=True,
                        notch=True,
                        showmeans=True,
                        meanprops=dict(marker='D', markerfacecolor='red', markersize=8))
        
        # Colorir boxes
        colors = ['lightblue', 'lightcoral']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Adicionar pontos individuais
        for i, grupo in enumerate(['Baixa', 'Alta'], start=1):
            dados_grupo = df_plot[df_plot['grupo'] == grupo][var_resposta]
            y = dados_grupo.values
            x = np.random.normal(i, 0.04, size=len(y))
            ax.scatter(x, y, alpha=0.3, s=20, color='black')
        
        # Título com resultado Mann-Whitney
        titulo = f'Comparação de {var_resposta.title()} por {var_clima.title()}\n'
        titulo += f'(Ponto de corte: mediana = {mediana:.2f})'
        
        if resultados_mann_whitney:
            mw = resultados_mann_whitney.get('mann_whitney', {})
            p_valor = mw.get('p_valor', 1)
            sig = "***" if p_valor < 0.001 else "**" if p_valor < 0.01 else "*" if p_valor < 0.05 else "ns"
            titulo += f'\nMann-Whitney U: p = {p_valor:.4e} {sig}'
        
        ax.set_title(titulo, fontsize=13, fontweight='bold', pad=20)
        ax.set_xlabel(f'{var_clima.title()} (Grupos)', fontsize=12, fontweight='bold')
        ax.set_ylabel(var_resposta.title(), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Adicionar anotações de média
        for i, grupo in enumerate(['Baixa', 'Alta'], start=1):
            media = df_plot[df_plot['grupo'] == grupo][var_resposta].mean()
            ax.text(i, media, f'μ={media:.1f}', ha='center', va='bottom', 
                   fontweight='bold', fontsize=9, color='red')
        
        plt.tight_layout()
        
        # Salvar
        filename = f"{self.output_dir}/boxplot_{var_clima.replace(' ', '_')}_grupos.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Boxplot salvo: {filename}")
        plt.close()
    
    def serie_temporal_dengue_el_nino(self):
        """
        Cria gráfico de série temporal com casos de dengue e eventos El Niño
        """
        # Verificar se existe coluna de data
        coluna_data = None
        for col in ['data', 'date', 'mes', 'month', 'periodo', 'ano_mes']:
            if col in self.df.columns:
                coluna_data = col
                break
        
        if not coluna_data:
            print("✗ Coluna de data não encontrada. Impossível criar série temporal.")
            return
        
        # Converter data se necessário
        if not pd.api.types.is_datetime64_any_dtype(self.df[coluna_data]):
            self.df[coluna_data] = pd.to_datetime(self.df[coluna_data])
        
        # Ordenar por data
        df_plot = self.df.sort_values(coluna_data).copy()
        
        # Criar figura com dois eixos Y
        fig, ax1 = plt.subplots(figsize=(16, 7))
        
        # Eixo principal: Casos de dengue
        color = 'tab:red'
        ax1.set_xlabel('Data', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Casos de Dengue', fontsize=12, fontweight='bold', color=color)
        ax1.plot(df_plot[coluna_data], df_plot['casos de dengue'], 
                color=color, linewidth=2, marker='o', markersize=4, label='Casos de Dengue')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.grid(True, alpha=0.3)
        
        # Eixo secundário: El Niño (se categórica, mostrar como área colorida)
        if 'el nino' in self.df.columns:
            # Mapear eventos para cores
            eventos_unicos = df_plot['el nino'].unique()
            color_map = {'El Niño': 'red', 'La Niña': 'blue', 'Neutro': 'gray', 
                        'el niño': 'red', 'la niña': 'blue', 'neutro': 'gray'}
            
            # Adicionar faixas coloridas no fundo
            for i in range(len(df_plot) - 1):
                evento = df_plot.iloc[i]['el nino']
                cor = color_map.get(str(evento).strip(), 'lightgray')
                ax1.axvspan(df_plot.iloc[i][coluna_data], 
                           df_plot.iloc[i+1][coluna_data],
                           alpha=0.15, color=cor)
            
            # Legenda de eventos
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=color_map.get(str(e), 'gray'), 
                                    alpha=0.3, label=str(e)) 
                              for e in eventos_unicos if pd.notna(e)]
            ax1.legend(handles=legend_elements, loc='upper left', title='Eventos El Niño/La Niña')
        
        # Título
        titulo = 'Série Temporal: Casos de Dengue e Eventos El Niño/La Niña'
        ax1.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
        
        # Rotacionar labels do eixo X
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Salvar
        filename = f"{self.output_dir}/serie_temporal_dengue_el_nino.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Série temporal salva: {filename}")
        plt.close()
    
    def barras_media_el_nino(self, resultados_el_nino=None):
        """
        Cria gráfico de barras com média de casos por evento El Niño
        
        Args:
            resultados_el_nino (dict): Resultados da análise El Niño
        """
        if 'el nino' not in self.df.columns:
            print("✗ Coluna 'el nino' não encontrada")
            return
        
        # Calcular média por evento
        medias = self.df.groupby('el nino')['casos de dengue'].agg(['mean', 'std', 'count']).reset_index()
        medias.columns = ['evento', 'media', 'desvio', 'n']
        
        # Ordenar por média decrescente
        medias = medias.sort_values('media', ascending=False)
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Gráfico de barras com barras de erro
        bars = ax.bar(range(len(medias)), medias['media'], 
                      yerr=medias['desvio'], capsize=5,
                      color=['red', 'blue', 'gray'][:len(medias)],
                      alpha=0.7, edgecolor='black', linewidth=1.5)
        
        # Configurar eixos
        ax.set_xticks(range(len(medias)))
        ax.set_xticklabels(medias['evento'], fontsize=11, fontweight='bold')
        ax.set_ylabel('Média de Casos de Dengue', fontsize=12, fontweight='bold')
        ax.set_xlabel('Evento El Niño/La Niña', fontsize=12, fontweight='bold')
        
        # Adicionar valores nas barras
        for i, (idx, row) in enumerate(medias.iterrows()):
            ax.text(i, row['media'] + row['desvio'] + 5, 
                   f"{row['media']:.1f}\n(n={int(row['n'])})",
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Título com resultado Kruskal-Wallis
        titulo = 'Média de Casos de Dengue por Evento El Niño/La Niña'
        
        if resultados_el_nino:
            kw = resultados_el_nino.get('kruskal_wallis', {})
            p_valor = kw.get('p_valor', 1)
            sig = "***" if p_valor < 0.001 else "**" if p_valor < 0.01 else "*" if p_valor < 0.05 else "ns"
            titulo += f'\nKruskal-Wallis: H = {kw.get("estatistica_h", 0):.2f}, p = {p_valor:.4e} {sig}'
        
        ax.set_title(titulo, fontsize=13, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Salvar
        filename = f"{self.output_dir}/barras_media_el_nino.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Gráfico de barras salvo: {filename}")
        plt.close()
    
    def matriz_correlacao_spearman(self):
        """
        Cria matriz de correlação de Spearman entre todas as variáveis numéricas
        """
        # Selecionar colunas numéricas relevantes
        colunas_interesse = ['temperatura media', 'temperatura minima', 'temperatura maxima', 
                            'casos de dengue']
        
        if 'precipitacao' in self.df.columns:
            colunas_interesse.append('precipitacao')
        
        # Filtrar colunas existentes
        colunas_existentes = [col for col in colunas_interesse if col in self.df.columns]
        
        if len(colunas_existentes) < 2:
            print("✗ Colunas insuficientes para matriz de correlação")
            return
        
        # Calcular matriz de correlação de Spearman
        df_corr = self.df[colunas_existentes].dropna()
        corr_matrix = df_corr.corr(method='spearman')
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Heatmap
        sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', 
                   center=0, vmin=-1, vmax=1, square=True, linewidths=1,
                   cbar_kws={"shrink": 0.8}, ax=ax, annot_kws={'fontsize': 10})
        
        # Título
        ax.set_title('Matriz de Correlação de Spearman\n(Variáveis Climáticas e Casos de Dengue)',
                    fontsize=13, fontweight='bold', pad=20)
        
        # Ajustar labels
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        
        plt.tight_layout()
        
        # Salvar
        filename = f"{self.output_dir}/matriz_correlacao_spearman.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Matriz de correlação salva: {filename}")
        plt.close()
    
    def gerar_todas_visualizacoes(self):
        """Gera todas as visualizações"""
        print("\n")
        print("╔" + "="*78 + "╗")
        print("║" + " "*25 + "GERAÇÃO DE VISUALIZAÇÕES" + " "*29 + "║")
        print("╚" + "="*78 + "╝")
        print(f"\nDiretório de saída: {self.output_dir}")
        print("="*80)
        
        # Variáveis climáticas
        vars_clima = ['temperatura media', 'temperatura minima', 'temperatura maxima']
        if 'precipitacao' in self.df.columns:
            vars_clima.append('precipitacao')
        
        # 1. Scatter plots com regressão
        print("\n1. Gerando Scatter Plots com Correlação de Spearman...")
        for var in vars_clima:
            if var in self.df.columns:
                # Buscar resultados de Spearman se disponíveis
                resultados_spearman = None
                if self.resultados_analise:
                    key = f"analise_{var.replace(' ', '_')}"
                    if key in self.resultados_analise:
                        resultados_spearman = self.resultados_analise[key].get('correlacao_spearman')
                
                self.scatter_regressao_spearman(var, resultados_spearman=resultados_spearman)
        
        # 2. Boxplots comparativos
        print("\n2. Gerando Boxplots de Grupos...")
        for var in vars_clima:
            if var in self.df.columns:
                # Buscar resultados Mann-Whitney se disponíveis
                resultados_mw = None
                if self.resultados_analise:
                    key = f"analise_{var.replace(' ', '_')}"
                    if key in self.resultados_analise:
                        resultados_mw = self.resultados_analise[key].get('mann_whitney')
                
                self.boxplot_grupos_temperatura(var, resultados_mann_whitney=resultados_mw)
        
        # 3. Série temporal
        print("\n3. Gerando Série Temporal...")
        self.serie_temporal_dengue_el_nino()
        
        # 4. Gráfico de barras El Niño
        print("\n4. Gerando Gráfico de Barras (El Niño)...")
        resultados_el_nino = None
        if self.resultados_analise:
            resultados_el_nino = self.resultados_analise.get('el_nino_analise')
        self.barras_media_el_nino(resultados_el_nino=resultados_el_nino)
        
        # 5. Matriz de correlação
        print("\n5. Gerando Matriz de Correlação...")
        self.matriz_correlacao_spearman()
        
        print("\n" + "="*80)
        print("✓ Todas as visualizações foram geradas com sucesso!")
        print("="*80 + "\n")


def main():
    """Função principal"""
    import sys
    import json
    
    if len(sys.argv) > 1:
        arquivo_dados = sys.argv[1]
    else:
        arquivo_dados = "../Dados/dados_consolidados.csv"
        print(f"⚠ Usando arquivo padrão: {arquivo_dados}")
    
    # Carregar dados
    print(f"\nCarregando dados de: {arquivo_dados}")
    df = pd.read_csv(arquivo_dados)
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Tentar carregar resultados da análise estatística
    resultados_analise = None
    try:
        with open('analise_estatistica_resultados.json', 'r', encoding='utf-8') as f:
            resultados_analise = json.load(f)
        print("✓ Resultados da análise estatística carregados")
    except:
        print("⚠ Resultados da análise não encontrados. Gráficos sem anotações estatísticas.")
    
    # Gerar visualizações
    visualizador = VisualizadorDados(df, resultados_analise)
    visualizador.gerar_todas_visualizacoes()


if __name__ == "__main__":
    main()
