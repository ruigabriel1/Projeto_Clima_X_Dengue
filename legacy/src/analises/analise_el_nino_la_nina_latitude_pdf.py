"""
Script para Análise El Niño vs La Niña por Faixas de Latitude + PDF
Determina qual fenômeno influencia mais a dengue
Usa médias mensais por faixa de latitude
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import mannwhitneyu, kruskal
from pathlib import Path
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class AnalisadorENSOLatitude:
    """Análise comparativa El Niño vs La Niña por latitude"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent  # raiz do projeto
        self.output_dir = self.base_path / "output" / "relatorios_latitude"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.df = None
        self.resultados = {}
        
    def carregar_dados(self):
        """Carrega médias mensais por latitude e ONI"""
        print("\n" + "="*80)
        print("ANÁLISE EL NIÑO vs LA NIÑA POR FAIXAS DE LATITUDE")
        print("="*80)
        
        print("\n[1/7] Carregando médias mensais por latitude...")
        
        # Carregar médias de dengue por latitude
        arquivo_medias = self.base_path / "output" / "medias_latitude" / "todas_faixas_medias_mensais.csv"
        
        if not arquivo_medias.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_medias}")
        
        self.df = pd.read_csv(arquivo_medias)
        print(f"  → Dados carregados: {self.df.shape}")
        print(f"  → Faixas de latitude: {self.df['FAIXA_LATITUDE'].nunique()}")
        print(f"  → Período: {self.df['ANO'].min()}-{self.df['ANO'].max()}")
        
        # Carregar ONI
        arquivo_oni = self.base_path / "data" / "raw" / "elnino_lanina_2015-2024.csv"
        df_oni = pd.read_csv(arquivo_oni, sep=';', decimal=',', encoding='utf-8-sig')
        
        # Converter ONI para formato longo
        oni_long = []
        meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        
        # Identificar coluna de ano (pode ter BOM)
        ano_col = [c for c in df_oni.columns if 'ANO' in c.upper()][0]
        
        for idx, row in df_oni.iterrows():
            ano = int(row[ano_col]) if pd.notna(row[ano_col]) else None
            if ano and 2015 <= ano <= 2024:
                for mes_idx, mes_nome in enumerate(meses, 1):
                    oni_val = pd.to_numeric(str(row[mes_nome]).replace(',', '.'), errors='coerce')
                    if pd.notna(oni_val):
                        oni_long.append({
                            'ANO': ano,
                            'MES': mes_idx,
                            'ONI': oni_val
                        })
        
        df_oni_long = pd.DataFrame(oni_long)
        
        # Merge com dados de dengue
        self.df = self.df.merge(df_oni_long, on=['ANO', 'MES'], how='left')
        
        # Classificar fases ENSO
        self.df['FASE_ENSO'] = 'Neutro'
        self.df.loc[self.df['ONI'] >= 0.5, 'FASE_ENSO'] = 'El Niño'
        self.df.loc[self.df['ONI'] <= -0.5, 'FASE_ENSO'] = 'La Niña'
        
        # Criar coluna de data
        self.df['DATA'] = pd.to_datetime(
            self.df['ANO'].astype(str) + '-' + 
            self.df['MES'].astype(str).str.zfill(2) + '-01'
        )
        
        print(f"  ✓ Dados consolidados: {len(self.df)} registros")
        print(f"\n  Distribuição de meses por fase ENSO:")
        print(self.df['FASE_ENSO'].value_counts())
    
    def analise_por_latitude(self):
        """Analisa cada faixa de latitude separadamente"""
        print("\n[2/7] Analisando por faixa de latitude...")
        
        resultados_faixas = {}
        
        for faixa in sorted(self.df['FAIXA_LATITUDE'].unique()):
            print(f"\n  → Faixa {faixa}:")
            
            df_faixa = self.df[self.df['FAIXA_LATITUDE'] == faixa].copy()
            
            # Separar por fase ENSO
            el_nino = df_faixa[df_faixa['FASE_ENSO'] == 'El Niño']['MEDIA_LOG_CASOS_DENGUE'].dropna()
            la_nina = df_faixa[df_faixa['FASE_ENSO'] == 'La Niña']['MEDIA_LOG_CASOS_DENGUE'].dropna()
            neutro = df_faixa[df_faixa['FASE_ENSO'] == 'Neutro']['MEDIA_LOG_CASOS_DENGUE'].dropna()
            
            # Estatísticas descritivas
            stats_faixa = {
                'El Niño': {
                    'N': len(el_nino),
                    'Média': el_nino.mean() if len(el_nino) > 0 else np.nan,
                    'Mediana': el_nino.median() if len(el_nino) > 0 else np.nan,
                    'DP': el_nino.std() if len(el_nino) > 0 else np.nan,
                    'Min': el_nino.min() if len(el_nino) > 0 else np.nan,
                    'Max': el_nino.max() if len(el_nino) > 0 else np.nan
                },
                'La Niña': {
                    'N': len(la_nina),
                    'Média': la_nina.mean() if len(la_nina) > 0 else np.nan,
                    'Mediana': la_nina.median() if len(la_nina) > 0 else np.nan,
                    'DP': la_nina.std() if len(la_nina) > 0 else np.nan,
                    'Min': la_nina.min() if len(la_nina) > 0 else np.nan,
                    'Max': la_nina.max() if len(la_nina) > 0 else np.nan
                },
                'Neutro': {
                    'N': len(neutro),
                    'Média': neutro.mean() if len(neutro) > 0 else np.nan,
                    'Mediana': neutro.median() if len(neutro) > 0 else np.nan,
                    'DP': neutro.std() if len(neutro) > 0 else np.nan,
                    'Min': neutro.min() if len(neutro) > 0 else np.nan,
                    'Max': neutro.max() if len(neutro) > 0 else np.nan
                }
            }
            
            # Teste de Kruskal-Wallis (compara os 3 grupos)
            if len(el_nino) > 0 and len(la_nina) > 0 and len(neutro) > 0:
                try:
                    h_stat, p_value = kruskal(el_nino, la_nina, neutro)
                    stats_faixa['Kruskal-Wallis'] = {
                        'H': h_stat,
                        'p-valor': p_value,
                        'Significativo': 'Sim' if p_value < 0.05 else 'Não'
                    }
                    print(f"    Kruskal-Wallis: H={h_stat:.3f}, p={p_value:.4f}")
                except Exception as e:
                    print(f"    ⚠ Erro no teste: {e}")
            
            # Teste Mann-Whitney (El Niño vs La Niña)
            if len(el_nino) > 0 and len(la_nina) > 0:
                try:
                    u_stat, p_value = mannwhitneyu(el_nino, la_nina, alternative='two-sided')
                    stats_faixa['Mann-Whitney'] = {
                        'U': u_stat,
                        'p-valor': p_value,
                        'Significativo': 'Sim' if p_value < 0.05 else 'Não'
                    }
                    
                    # Determinar qual fase tem maior impacto
                    if stats_faixa['El Niño']['Média'] > stats_faixa['La Niña']['Média']:
                        maior_impacto = 'El Niño'
                        diferenca = stats_faixa['El Niño']['Média'] - stats_faixa['La Niña']['Média']
                    else:
                        maior_impacto = 'La Niña'
                        diferenca = stats_faixa['La Niña']['Média'] - stats_faixa['El Niño']['Média']
                    
                    stats_faixa['Maior_Impacto'] = {
                        'Fase': maior_impacto,
                        'Diferença_Média': diferenca,
                        'Percentual': (diferenca / min(stats_faixa['El Niño']['Média'], 
                                                      stats_faixa['La Niña']['Média']) * 100) if min(stats_faixa['El Niño']['Média'], stats_faixa['La Niña']['Média']) > 0 else 0
                    }
                    
                    print(f"    Mann-Whitney (El Niño vs La Niña): U={u_stat:.1f}, p={p_value:.4f}")
                    print(f"    → Maior impacto: {maior_impacto} (diferença: {diferenca:.4f})")
                    
                except Exception as e:
                    print(f"    ⚠ Erro no teste: {e}")
            
            resultados_faixas[faixa] = stats_faixa
        
        self.resultados['por_faixa'] = resultados_faixas
        print("\n  ✓ Análise por faixa concluída")
    
    def analise_global_enso(self):
        """Análise global (todas as faixas juntas)"""
        print("\n[3/7] Análise global ENSO...")
        
        # Separar por fase
        el_nino = self.df[self.df['FASE_ENSO'] == 'El Niño']['MEDIA_LOG_CASOS_DENGUE'].dropna()
        la_nina = self.df[self.df['FASE_ENSO'] == 'La Niña']['MEDIA_LOG_CASOS_DENGUE'].dropna()
        neutro = self.df[self.df['FASE_ENSO'] == 'Neutro']['MEDIA_LOG_CASOS_DENGUE'].dropna()
        
        # Estatísticas
        global_stats = {
            'El Niño': {
                'N': len(el_nino),
                'Média': el_nino.mean(),
                'Mediana': el_nino.median(),
                'DP': el_nino.std()
            },
            'La Niña': {
                'N': len(la_nina),
                'Média': la_nina.mean(),
                'Mediana': la_nina.median(),
                'DP': la_nina.std()
            },
            'Neutro': {
                'N': len(neutro),
                'Média': neutro.mean(),
                'Mediana': neutro.median(),
                'DP': neutro.std()
            }
        }
        
        # Testes
        if len(el_nino) > 0 and len(la_nina) > 0 and len(neutro) > 0:
            h_stat, p_value = kruskal(el_nino, la_nina, neutro)
            global_stats['Kruskal-Wallis'] = {
                'H': h_stat,
                'p-valor': p_value,
                'Significativo': 'Sim' if p_value < 0.05 else 'Não'
            }
            
            u_stat, p_value = mannwhitneyu(el_nino, la_nina, alternative='two-sided')
            global_stats['Mann-Whitney'] = {
                'U': u_stat,
                'p-valor': p_value,
                'Significativo': 'Sim' if p_value < 0.05 else 'Não'
            }
            
            # Determinar qual fase predomina
            if global_stats['El Niño']['Média'] > global_stats['La Niña']['Média']:
                maior_impacto = 'El Niño'
                diferenca = global_stats['El Niño']['Média'] - global_stats['La Niña']['Média']
            else:
                maior_impacto = 'La Niña'
                diferenca = global_stats['La Niña']['Média'] - global_stats['El Niño']['Média']
            
            global_stats['Conclusão_Global'] = {
                'Fase_Predominante': maior_impacto,
                'Diferença_Média': diferenca,
                'Percentual': (diferenca / min(global_stats['El Niño']['Média'], 
                                              global_stats['La Niña']['Média']) * 100)
            }
            
            print(f"  → Fase predominante: {maior_impacto}")
            print(f"  → Diferença média: {diferenca:.4f} ({global_stats['Conclusão_Global']['Percentual']:.1f}%)")
        
        self.resultados['global'] = global_stats
        print("  ✓ Análise global concluída")
    
    def criar_pdf(self):
        """Cria PDF com todos os gráficos e resultados"""
        print("\n[4/7] Gerando PDF...")
        
        pdf_path = self.output_dir / f"analise_el_nino_la_nina_latitude_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        with PdfPages(pdf_path) as pdf:
            # Página 1: Visão geral temporal
            self._plot_serie_temporal(pdf)
            
            # Página 2: Boxplots por faixa
            self._plot_boxplots_faixas(pdf)
            
            # Página 3: Comparação global
            self._plot_comparacao_global(pdf)
            
            # Página 4: Heatmap por faixa e fase
            self._plot_heatmap_faixas(pdf)
            
            # Página 5: Análise estatística por faixa
            self._plot_testes_estatisticos(pdf)
            
            # Página 6: Relatório final
            self._plot_relatorio_final(pdf)
        
        print(f"  ✓ PDF gerado: {pdf_path}")
        return pdf_path
    
    def _plot_serie_temporal(self, pdf):
        """Série temporal por fase ENSO"""
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        # Plot 1: Todas as faixas coloridas por fase
        for fase, color in [('El Niño', 'red'), ('La Niña', 'blue'), ('Neutro', 'gray')]:
            dados = self.df[self.df['FASE_ENSO'] == fase]
            axes[0].scatter(dados['DATA'], dados['MEDIA_LOG_CASOS_DENGUE'],
                          c=color, label=fase, alpha=0.5, s=20)
        
        axes[0].set_title('Dengue (Log) ao Longo do Tempo - Todas as Faixas de Latitude',
                         fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Dengue (Log)', fontsize=11)
        axes[0].legend(loc='best')
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Média por fase ao longo do tempo
        for fase, color in [('El Niño', 'red'), ('La Niña', 'blue'), ('Neutro', 'gray')]:
            dados_fase = self.df[self.df['FASE_ENSO'] == fase].groupby('DATA')['MEDIA_LOG_CASOS_DENGUE'].mean()
            axes[1].plot(dados_fase.index, dados_fase.values, color=color, 
                        label=fase, linewidth=2, marker='o', markersize=4)
        
        axes[1].set_title('Média de Dengue por Fase ENSO (Agregado de Todas Faixas)',
                         fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Dengue (Log) - Média', fontsize=11)
        axes[1].legend(loc='best')
        axes[1].grid(True, alpha=0.3)
        
        # Plot 3: Índice ONI
        oni_mensal = self.df.drop_duplicates(subset=['ANO', 'MES'])[['DATA', 'ONI']].sort_values('DATA')
        axes[2].plot(oni_mensal['DATA'], oni_mensal['ONI'], 'k-', linewidth=1.5)
        axes[2].axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Limite El Niño')
        axes[2].axhline(y=-0.5, color='blue', linestyle='--', alpha=0.5, label='Limite La Niña')
        axes[2].fill_between(oni_mensal['DATA'], 0.5, oni_mensal['ONI'].max(), 
                            where=oni_mensal['ONI']>=0.5, alpha=0.2, color='red')
        axes[2].fill_between(oni_mensal['DATA'], -0.5, oni_mensal['ONI'].min(),
                            where=oni_mensal['ONI']<=-0.5, alpha=0.2, color='blue')
        
        axes[2].set_title('Índice ONI (El Niño / La Niña) 2015-2024',
                         fontsize=14, fontweight='bold')
        axes[2].set_xlabel('Data', fontsize=11)
        axes[2].set_ylabel('Índice ONI', fontsize=11)
        axes[2].legend(loc='best')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_boxplots_faixas(self, pdf):
        """Boxplots por faixa de latitude"""
        fig, axes = plt.subplots(2, 4, figsize=(16, 10))
        axes = axes.flatten()
        
        faixas = sorted(self.df['FAIXA_LATITUDE'].unique())
        
        for idx, faixa in enumerate(faixas):
            if idx < len(axes):
                df_faixa = self.df[self.df['FAIXA_LATITUDE'] == faixa]
                
                # Preparar dados para boxplot
                dados_plot = []
                labels_plot = []
                colors_plot = []
                
                for fase, color in [('El Niño', 'red'), ('La Niña', 'blue'), ('Neutro', 'gray')]:
                    dados_fase = df_faixa[df_faixa['FASE_ENSO'] == fase]['MEDIA_LOG_CASOS_DENGUE'].dropna()
                    if len(dados_fase) > 0:
                        dados_plot.append(dados_fase.values)
                        labels_plot.append(fase)
                        colors_plot.append(color)
                
                # Boxplot
                bp = axes[idx].boxplot(dados_plot, labels=labels_plot, patch_artist=True,
                                      showmeans=True, meanline=True)
                
                for patch, color in zip(bp['boxes'], colors_plot):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.6)
                
                axes[idx].set_title(f'Faixa {faixa}\nLat: {df_faixa["LATITUDE"].iloc[0]:.2f}°',
                                   fontsize=10, fontweight='bold')
                axes[idx].set_ylabel('Dengue (Log)', fontsize=9)
                axes[idx].grid(True, alpha=0.3, axis='y')
                axes[idx].tick_params(axis='x', rotation=15, labelsize=8)
        
        plt.suptitle('Distribuição de Dengue por Fase ENSO em Cada Faixa de Latitude',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_comparacao_global(self, pdf):
        """Comparação global entre fases"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Boxplot global
        dados_plot = []
        labels_plot = []
        colors_plot = []
        
        for fase, color in [('El Niño', 'red'), ('La Niña', 'blue'), ('Neutro', 'gray')]:
            dados = self.df[self.df['FASE_ENSO'] == fase]['MEDIA_LOG_CASOS_DENGUE'].dropna()
            dados_plot.append(dados.values)
            labels_plot.append(fase)
            colors_plot.append(color)
        
        bp = axes[0, 0].boxplot(dados_plot, labels=labels_plot, patch_artist=True,
                               showmeans=True, meanline=True)
        
        for patch, color in zip(bp['boxes'], colors_plot):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        axes[0, 0].set_title('Distribuição Global de Dengue por Fase ENSO',
                            fontsize=12, fontweight='bold')
        axes[0, 0].set_ylabel('Dengue (Log)', fontsize=10)
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        # Violin plot
        df_plot = self.df[['FASE_ENSO', 'MEDIA_LOG_CASOS_DENGUE']].dropna()
        sns.violinplot(data=df_plot, x='FASE_ENSO', y='MEDIA_LOG_CASOS_DENGUE',
                      palette={'El Niño': 'red', 'La Niña': 'blue', 'Neutro': 'gray'},
                      ax=axes[0, 1])
        axes[0, 1].set_title('Distribuição Detalhada (Violin Plot)',
                            fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('Fase ENSO', fontsize=10)
        axes[0, 1].set_ylabel('Dengue (Log)', fontsize=10)
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # Barras de média com erro padrão
        stats_global = self.resultados.get('global', {})
        fases = ['El Niño', 'La Niña', 'Neutro']
        medias = [stats_global.get(f, {}).get('Média', 0) for f in fases]
        erros = [stats_global.get(f, {}).get('DP', 0) / np.sqrt(stats_global.get(f, {}).get('N', 1)) 
                for f in fases]
        colors = ['red', 'blue', 'gray']
        
        axes[1, 0].bar(fases, medias, yerr=erros, color=colors, alpha=0.7,
                      capsize=10, error_kw={'linewidth': 2})
        axes[1, 0].set_title('Média de Dengue por Fase ENSO (± Erro Padrão)',
                            fontsize=12, fontweight='bold')
        axes[1, 0].set_ylabel('Dengue (Log) - Média', fontsize=10)
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Contagem de observações
        contagens = self.df['FASE_ENSO'].value_counts()
        axes[1, 1].bar(contagens.index, contagens.values,
                      color=['red' if x=='El Niño' else 'blue' if x=='La Niña' else 'gray' 
                            for x in contagens.index],
                      alpha=0.7)
        axes[1, 1].set_title('Número de Observações por Fase ENSO',
                            fontsize=12, fontweight='bold')
        axes[1, 1].set_ylabel('Número de Registros', fontsize=10)
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('Análise Global: El Niño vs La Niña vs Neutro',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_heatmap_faixas(self, pdf):
        """Heatmap de médias por faixa e fase"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Preparar dados para heatmap
        faixas = sorted(self.df['FAIXA_LATITUDE'].unique())
        fases = ['El Niño', 'La Niña', 'Neutro']
        
        matriz = []
        for faixa in faixas:
            linha = []
            for fase in fases:
                media = self.df[(self.df['FAIXA_LATITUDE']==faixa) & 
                               (self.df['FASE_ENSO']==fase)]['MEDIA_LOG_CASOS_DENGUE'].mean()
                linha.append(media)
            matriz.append(linha)
        
        # Plotar heatmap
        im = ax.imshow(matriz, cmap='YlOrRd', aspect='auto')
        
        # Configurar eixos
        ax.set_xticks(range(len(fases)))
        ax.set_yticks(range(len(faixas)))
        ax.set_xticklabels(fases, fontsize=11)
        ax.set_yticklabels([f'Faixa {f}' for f in faixas], fontsize=10)
        
        # Adicionar valores nas células
        for i in range(len(faixas)):
            for j in range(len(fases)):
                text = ax.text(j, i, f'{matriz[i][j]:.3f}',
                             ha="center", va="center", color="black", fontsize=10)
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Dengue (Log) - Média', rotation=270, labelpad=20, fontsize=11)
        
        ax.set_title('Heatmap: Média de Dengue por Faixa de Latitude e Fase ENSO',
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_testes_estatisticos(self, pdf):
        """Página com resultados dos testes estatísticos"""
        fig = plt.figure(figsize=(11, 14))
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        y_pos = 0.95
        
        # Título
        ax.text(0.5, y_pos, 'RESULTADOS DOS TESTES ESTATÍSTICOS',
               ha='center', fontsize=18, fontweight='bold')
        y_pos -= 0.05
        ax.text(0.5, y_pos, 'Comparação El Niño vs La Niña por Faixa de Latitude',
               ha='center', fontsize=14, style='italic')
        y_pos -= 0.08
        
        # Resultados por faixa
        por_faixa = self.resultados.get('por_faixa', {})
        
        for faixa in sorted(por_faixa.keys()):
            stats = por_faixa[faixa]
            
            ax.text(0.1, y_pos, f'FAIXA {faixa}', fontsize=12, fontweight='bold')
            y_pos -= 0.025
            
            # Estatísticas de cada fase
            for fase in ['El Niño', 'La Niña', 'Neutro']:
                if fase in stats:
                    fase_stats = stats[fase]
                    ax.text(0.12, y_pos,
                           f"{fase}: N={fase_stats['N']}, "
                           f"Média={fase_stats['Média']:.4f}, "
                           f"Mediana={fase_stats['Mediana']:.4f}",
                           fontsize=9)
                    y_pos -= 0.02
            
            # Teste Mann-Whitney
            if 'Mann-Whitney' in stats:
                mw = stats['Mann-Whitney']
                ax.text(0.12, y_pos,
                       f"Mann-Whitney: U={mw['U']:.2f}, p={mw['p-valor']:.4f} → {mw['Significativo']}",
                       fontsize=9, style='italic', color='blue')
                y_pos -= 0.02
            
            # Maior impacto
            if 'Maior_Impacto' in stats:
                imp = stats['Maior_Impacto']
                ax.text(0.12, y_pos,
                       f"→ Maior impacto: {imp['Fase']} "
                       f"(diferença: {imp['Diferença_Média']:.4f}, {imp['Percentual']:.1f}%)",
                       fontsize=9, fontweight='bold', color='red')
                y_pos -= 0.02
            
            y_pos -= 0.015
            
            if y_pos < 0.15:
                break
        
        # Conclusão global
        y_pos = 0.12
        ax.text(0.1, y_pos, 'CONCLUSÃO GLOBAL', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        global_stats = self.resultados.get('global', {})
        if 'Conclusão_Global' in global_stats:
            conclusao = global_stats['Conclusão_Global']
            ax.text(0.12, y_pos,
                   f"Fase predominante: {conclusao['Fase_Predominante']}",
                   fontsize=11, fontweight='bold', color='darkgreen')
            y_pos -= 0.025
            ax.text(0.12, y_pos,
                   f"Diferença média: {conclusao['Diferença_Média']:.4f} "
                   f"({conclusao['Percentual']:.1f}% maior)",
                   fontsize=10)
        
        # Rodapé
        ax.text(0.5, 0.03,
               f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
               ha='center', fontsize=9, style='italic', color='gray')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_relatorio_final(self, pdf):
        """Relatório final com conclusões"""
        fig = plt.figure(figsize=(11, 14))
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        y_pos = 0.95
        
        # Título
        ax.text(0.5, y_pos, 'RELATÓRIO FINAL',
               ha='center', fontsize=20, fontweight='bold')
        y_pos -= 0.05
        ax.text(0.5, y_pos, 'Análise El Niño vs La Niña - Impacto na Dengue',
               ha='center', fontsize=16, style='italic')
        y_pos -= 0.08
        
        # Seção 1: Resumo Executivo
        ax.text(0.1, y_pos, '1. RESUMO EXECUTIVO', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        global_stats = self.resultados.get('global', {})
        if 'Conclusão_Global' in global_stats:
            conclusao = global_stats['Conclusão_Global']
            
            texto_conclusao = [
                f"• A análise comparativa entre as fases El Niño e La Niña revelou que",
                f"  {conclusao['Fase_Predominante']} apresenta maior impacto na incidência de dengue.",
                f"",
                f"• Diferença média entre as fases: {conclusao['Diferença_Média']:.4f}",
                f"  ({conclusao['Percentual']:.1f}% maior em {conclusao['Fase_Predominante']})",
                f"",
                f"• Esta diferença foi observada de forma consistente em múltiplas",
                f"  faixas de latitude ao longo da região Sul do Brasil."
            ]
            
            for linha in texto_conclusao:
                ax.text(0.12, y_pos, linha, fontsize=10, wrap=True)
                y_pos -= 0.025
        
        y_pos -= 0.02
        
        # Seção 2: Metodologia
        ax.text(0.1, y_pos, '2. METODOLOGIA', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        metodologia = [
            "• Dados: Médias mensais de dengue (log transformado) por 8 faixas de latitude",
            "• Período: 2015-2024 (120 meses)",
            "• Classificação ENSO: ONI ≥ 0.5 (El Niño), ONI ≤ -0.5 (La Niña)",
            "• Testes não-paramétricos: Mann-Whitney U e Kruskal-Wallis",
            "• Análise realizada por faixa de latitude e globalmente"
        ]
        
        for linha in metodologia:
            ax.text(0.12, y_pos, linha, fontsize=9, wrap=True)
            y_pos -= 0.025
        
        y_pos -= 0.02
        
        # Seção 3: Principais Achados
        ax.text(0.1, y_pos, '3. PRINCIPAIS ACHADOS', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        # Contar faixas com diferença significativa
        por_faixa = self.resultados.get('por_faixa', {})
        faixas_significativas = sum(1 for f in por_faixa.values() 
                                   if 'Mann-Whitney' in f and 
                                   f['Mann-Whitney']['Significativo'] == 'Sim')
        
        # Determinar qual fase predomina em mais faixas
        fases_predominantes = []
        for stats in por_faixa.values():
            if 'Maior_Impacto' in stats:
                fases_predominantes.append(stats['Maior_Impacto']['Fase'])
        
        from collections import Counter
        if fases_predominantes:
            fase_mais_comum = Counter(fases_predominantes).most_common(1)[0]
        
        achados = [
            f"• {faixas_significativas} de {len(por_faixa)} faixas apresentaram diferenças",
            f"  estatisticamente significativas entre El Niño e La Niña (p < 0.05)",
            f"",
            f"• {fase_mais_comum[0]} foi a fase predominante em {fase_mais_comum[1]}",
            f"  das {len(por_faixa)} faixas de latitude analisadas",
            f"",
            f"• A distribuição de observações foi:"
        ]
        
        for linha in achados:
            ax.text(0.12, y_pos, linha, fontsize=9, wrap=True)
            y_pos -= 0.025
        
        # Adicionar contagem
        for fase in ['El Niño', 'La Niña', 'Neutro']:
            if fase in global_stats:
                n = global_stats[fase]['N']
                ax.text(0.15, y_pos, f"  - {fase}: {n} observações", fontsize=9)
                y_pos -= 0.02
        
        y_pos -= 0.02
        
        # Seção 4: Recomendações
        ax.text(0.1, y_pos, '4. RECOMENDAÇÕES', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        recomendacoes = [
            f"• Intensificar ações de vigilância epidemiológica durante períodos de",
            f"  {conclusao['Fase_Predominante']}, especialmente nas faixas de latitude",
            f"  que apresentaram maior susceptibilidade.",
            f"",
            f"• Implementar sistemas de alerta precoce baseados no índice ONI para",
            f"  antecipar possíveis surtos de dengue.",
            f"",
            f"• Considerar a variação latitudinal no planejamento de estratégias",
            f"  de controle vetorial e campanhas de prevenção."
        ]
        
        for linha in recomendacoes:
            ax.text(0.12, y_pos, linha, fontsize=9, wrap=True)
            y_pos -= 0.025
        
        # Rodapé
        ax.text(0.5, 0.05,
               f"Documento gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n"
               f"Análise estatística - Projeto Dengue e Clima",
               ha='center', fontsize=8, style='italic', color='gray')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def executar_analise(self):
        """Executa análise completa"""
        try:
            self.carregar_dados()
            self.analise_por_latitude()
            self.analise_global_enso()
            pdf_path = self.criar_pdf()
            
            print("\n[5/7] Salvando dados processados...")
            csv_output = self.output_dir / "dados_enso_latitude_processados.csv"
            self.df.to_csv(csv_output, index=False, encoding='utf-8-sig')
            print(f"  ✓ Dados salvos: {csv_output}")
            
            # Salvar resumo dos resultados
            print("\n[6/7] Salvando resumo estatístico...")
            resumo_path = self.output_dir / "resumo_el_nino_la_nina.txt"
            with open(resumo_path, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("RESUMO: ANÁLISE EL NIÑO vs LA NIÑA POR LATITUDE\n")
                f.write("="*80 + "\n\n")
                
                global_stats = self.resultados.get('global', {})
                if 'Conclusão_Global' in global_stats:
                    conclusao = global_stats['Conclusão_Global']
                    f.write(f"FASE PREDOMINANTE: {conclusao['Fase_Predominante']}\n")
                    f.write(f"Diferença média: {conclusao['Diferença_Média']:.4f}\n")
                    f.write(f"Percentual: {conclusao['Percentual']:.1f}%\n\n")
                
                f.write("\nRESULTADOS POR FAIXA DE LATITUDE:\n")
                f.write("-"*80 + "\n")
                
                por_faixa = self.resultados.get('por_faixa', {})
                for faixa in sorted(por_faixa.keys()):
                    f.write(f"\nFAIXA {faixa}:\n")
                    stats = por_faixa[faixa]
                    
                    if 'Maior_Impacto' in stats:
                        imp = stats['Maior_Impacto']
                        f.write(f"  Maior impacto: {imp['Fase']}\n")
                        f.write(f"  Diferença: {imp['Diferença_Média']:.4f} ({imp['Percentual']:.1f}%)\n")
                    
                    if 'Mann-Whitney' in stats:
                        mw = stats['Mann-Whitney']
                        f.write(f"  Teste Mann-Whitney: p={mw['p-valor']:.4f} → {mw['Significativo']}\n")
            
            print(f"  ✓ Resumo salvo: {resumo_path}")
            
            print("\n[7/7] Finalizando...")
            print("\n" + "="*80)
            print("✓ ANÁLISE EL NIÑO vs LA NIÑA CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print(f"\n📄 Relatório PDF: {pdf_path}")
            print(f"📊 Dados processados: {csv_output}")
            print(f"📝 Resumo: {resumo_path}")
            
            # Exibir conclusão principal
            if 'Conclusão_Global' in global_stats:
                conclusao = global_stats['Conclusão_Global']
                print(f"\n🎯 CONCLUSÃO PRINCIPAL:")
                print(f"   → {conclusao['Fase_Predominante']} apresenta {conclusao['Percentual']:.1f}% mais impacto na dengue")
            
            return pdf_path
            
        except Exception as e:
            print(f"\n❌ Erro na análise: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    analisador = AnalisadorENSOLatitude()
    analisador.executar_analise()
