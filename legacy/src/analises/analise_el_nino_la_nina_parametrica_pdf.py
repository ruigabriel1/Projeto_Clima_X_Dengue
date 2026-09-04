"""
Script para Análise El Niño vs La Niña por Faixas de Latitude + PDF
TESTES PARAMÉTRICOS: Pearson, Levene e ANOVA
Inclui todas as 8 faixas de latitude
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, levene, f_oneway, ttest_ind
from pathlib import Path
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class AnalisadorENSOLatitudeParametrico:
    """Análise comparativa El Niño vs La Niña por latitude - TESTES PARAMÉTRICOS"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent  # raiz do projeto
        self.output_dir = self.base_path / "output" / "relatorios_latitude"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.df = None
        self.resultados = {}
        
    def carregar_dados(self):
        """Carrega médias mensais por latitude e ONI"""
        print("\n" + "="*80)
        print("ANÁLISE EL NIÑO vs LA NIÑA POR FAIXAS DE LATITUDE - TESTES PARAMÉTRICOS")
        print("="*80)
        
        print("\n[1/8] Carregando médias mensais por latitude...")
        
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
        
        # Identificar coluna de ano
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
        """Analisa cada faixa de latitude separadamente - TESTES PARAMÉTRICOS"""
        print("\n[2/8] Analisando por faixa de latitude (TESTES PARAMÉTRICOS)...")
        
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
            
            # TESTE 1: ANOVA (compara os 3 grupos)
            if len(el_nino) > 2 and len(la_nina) > 2 and len(neutro) > 2:
                try:
                    f_stat, p_value = f_oneway(el_nino, la_nina, neutro)
                    stats_faixa['ANOVA'] = {
                        'F': f_stat,
                        'p-valor': p_value,
                        'Significativo': 'Sim' if p_value < 0.05 else 'Não'
                    }
                    print(f"    ANOVA: F={f_stat:.3f}, p={p_value:.4f} {'*' if p_value < 0.05 else ''}")
                except Exception as e:
                    print(f"    ⚠ Erro ANOVA: {e}")
                    stats_faixa['ANOVA'] = {'Erro': str(e)}
            
            # TESTE 2: Levene (homogeneidade de variâncias)
            if len(el_nino) > 2 and len(la_nina) > 2 and len(neutro) > 2:
                try:
                    w_stat, p_value = levene(el_nino, la_nina, neutro)
                    stats_faixa['Levene'] = {
                        'W': w_stat,
                        'p-valor': p_value,
                        'Homogêneo': 'Sim' if p_value >= 0.05 else 'Não'
                    }
                    print(f"    Levene: W={w_stat:.3f}, p={p_value:.4f} (Homogêneo: {'Sim' if p_value >= 0.05 else 'Não'})")
                except Exception as e:
                    print(f"    ⚠ Erro Levene: {e}")
                    stats_faixa['Levene'] = {'Erro': str(e)}
            
            # TESTE 3: t-test (El Niño vs La Niña)
            if len(el_nino) > 2 and len(la_nina) > 2:
                try:
                    t_stat, p_value = ttest_ind(el_nino, la_nina, equal_var=True)
                    stats_faixa['t-test'] = {
                        't': t_stat,
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
                    
                    print(f"    t-test (El Niño vs La Niña): t={t_stat:.3f}, p={p_value:.4f} {'*' if p_value < 0.05 else ''}")
                    print(f"    → Maior impacto: {maior_impacto} (diferença: {diferenca:.4f}, {stats_faixa['Maior_Impacto']['Percentual']:.1f}%)")
                    
                except Exception as e:
                    print(f"    ⚠ Erro t-test: {e}")
                    stats_faixa['t-test'] = {'Erro': str(e)}
            
            # TESTE 4: Correlação de Pearson (ONI vs Dengue)
            df_faixa_clean = df_faixa[['ONI', 'MEDIA_LOG_CASOS_DENGUE']].dropna()
            if len(df_faixa_clean) > 2:
                try:
                    r, p_value = pearsonr(df_faixa_clean['ONI'], df_faixa_clean['MEDIA_LOG_CASOS_DENGUE'])
                    stats_faixa['Pearson'] = {
                        'r': r,
                        'p-valor': p_value,
                        'Significativo': 'Sim' if p_value < 0.05 else 'Não',
                        'Interpretação': 'Positiva forte' if r > 0.7 else 'Positiva moderada' if r > 0.3 else 'Positiva fraca' if r > 0 else 'Negativa fraca' if r > -0.3 else 'Negativa moderada' if r > -0.7 else 'Negativa forte'
                    }
                    print(f"    Pearson (ONI x Dengue): r={r:.3f}, p={p_value:.4f} ({'Significativo' if p_value < 0.05 else 'Não significativo'})")
                except Exception as e:
                    print(f"    ⚠ Erro Pearson: {e}")
                    stats_faixa['Pearson'] = {'Erro': str(e)}
            
            resultados_faixas[faixa] = stats_faixa
        
        self.resultados['por_faixa'] = resultados_faixas
        print("\n  ✓ Análise paramétrica por faixa concluída (8 faixas)")
    
    def analise_global_enso(self):
        """Análise global (todas as faixas juntas) - TESTES PARAMÉTRICOS"""
        print("\n[3/8] Análise global ENSO (TESTES PARAMÉTRICOS)...")
        
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
        
        # ANOVA
        f_stat, p_value = f_oneway(el_nino, la_nina, neutro)
        global_stats['ANOVA'] = {
            'F': f_stat,
            'p-valor': p_value,
            'Significativo': 'Sim' if p_value < 0.05 else 'Não'
        }
        print(f"  ANOVA Global: F={f_stat:.3f}, p={p_value:.4f}")
        
        # Levene
        w_stat, p_value = levene(el_nino, la_nina, neutro)
        global_stats['Levene'] = {
            'W': w_stat,
            'p-valor': p_value,
            'Homogêneo': 'Sim' if p_value >= 0.05 else 'Não'
        }
        print(f"  Levene Global: W={w_stat:.3f}, p={p_value:.4f}")
        
        # t-test
        t_stat, p_value = ttest_ind(el_nino, la_nina, equal_var=True)
        global_stats['t-test'] = {
            't': t_stat,
            'p-valor': p_value,
            'Significativo': 'Sim' if p_value < 0.05 else 'Não'
        }
        print(f"  t-test Global: t={t_stat:.3f}, p={p_value:.4f}")
        
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
        
        print(f"  → Fase predominante: {maior_impacto} ({global_stats['Conclusão_Global']['Percentual']:.1f}% maior)")
        
        self.resultados['global'] = global_stats
    
    def gerar_visualizacoes(self, pdf):
        """Gera visualizações para o PDF"""
        print("\n[4/8] Gerando visualizações...")
        
        # Página 1: Boxplots por faixa
        fig, axes = plt.subplots(4, 2, figsize=(14, 16))
        axes = axes.flatten()
        
        for i, faixa in enumerate(sorted(self.df['FAIXA_LATITUDE'].unique())):
            df_faixa = self.df[self.df['FAIXA_LATITUDE'] == faixa]
            
            data_to_plot = [
                df_faixa[df_faixa['FASE_ENSO'] == 'El Niño']['MEDIA_LOG_CASOS_DENGUE'].dropna(),
                df_faixa[df_faixa['FASE_ENSO'] == 'La Niña']['MEDIA_LOG_CASOS_DENGUE'].dropna(),
                df_faixa[df_faixa['FASE_ENSO'] == 'Neutro']['MEDIA_LOG_CASOS_DENGUE'].dropna()
            ]
            
            bp = axes[i].boxplot(data_to_plot, labels=['El Niño', 'La Niña', 'Neutro'],
                                patch_artist=True)
            
            # Colorir
            colors = ['#ff9999', '#66b3ff', '#99ff99']
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
            
            axes[i].set_title(f'Faixa {faixa}', fontweight='bold')
            axes[i].set_ylabel('Log(Casos Dengue + 1)')
            axes[i].grid(True, alpha=0.3)
            
            # Adicionar p-valor se disponível
            if faixa in self.resultados['por_faixa']:
                if 'ANOVA' in self.resultados['por_faixa'][faixa]:
                    p_val = self.resultados['por_faixa'][faixa]['ANOVA'].get('p-valor', None)
                    if p_val is not None:
                        axes[i].text(0.5, 0.95, f"p={p_val:.4f}", transform=axes[i].transAxes,
                                   ha='center', va='top', fontsize=9, 
                                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.suptitle('Distribuição de Dengue por Fase ENSO - Todas as Faixas', 
                    fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Página 2: Séries temporais
        fig, axes = plt.subplots(4, 2, figsize=(14, 16))
        axes = axes.flatten()
        
        for i, faixa in enumerate(sorted(self.df['FAIXA_LATITUDE'].unique())):
            df_faixa = self.df[self.df['FAIXA_LATITUDE'] == faixa].sort_values('DATA')
            
            for fase, color in [('El Niño', 'red'), ('La Niña', 'blue'), ('Neutro', 'green')]:
                df_fase = df_faixa[df_faixa['FASE_ENSO'] == fase]
                axes[i].plot(df_fase['DATA'], df_fase['MEDIA_LOG_CASOS_DENGUE'], 
                           'o-', label=fase, color=color, alpha=0.7, markersize=4)
            
            axes[i].set_title(f'Faixa {faixa}', fontweight='bold')
            axes[i].set_ylabel('Log(Casos Dengue + 1)')
            axes[i].legend(loc='best', fontsize=8)
            axes[i].grid(True, alpha=0.3)
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.suptitle('Séries Temporais de Dengue por Fase ENSO - Todas as Faixas', 
                    fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Página 3: Correlações Pearson
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        correlacoes = []
        p_valores = []
        faixas = []
        
        for faixa in sorted(self.df['FAIXA_LATITUDE'].unique()):
            if faixa in self.resultados['por_faixa']:
                if 'Pearson' in self.resultados['por_faixa'][faixa]:
                    r = self.resultados['por_faixa'][faixa]['Pearson'].get('r', None)
                    p = self.resultados['por_faixa'][faixa]['Pearson'].get('p-valor', None)
                    if r is not None and p is not None:
                        correlacoes.append(r)
                        p_valores.append(p)
                        faixas.append(f'Faixa {faixa}')
        
        if correlacoes:
            colors = ['red' if p < 0.05 else 'gray' for p in p_valores]
            bars = ax.barh(faixas, correlacoes, color=colors, alpha=0.7)
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
            ax.set_xlabel('Coeficiente de Correlação de Pearson (r)', fontweight='bold')
            ax.set_title('Correlação ONI x Dengue por Faixa de Latitude\n(Vermelho: p<0.05)', 
                        fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            
            # Adicionar valores
            for i, (bar, r, p) in enumerate(zip(bars, correlacoes, p_valores)):
                ax.text(r + 0.01 if r >= 0 else r - 0.01, i, 
                       f'r={r:.3f}\np={p:.3f}', 
                       va='center', ha='left' if r >= 0 else 'right', fontsize=9)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        print("  ✓ Visualizações geradas")
    
    def gerar_tabelas_resultados(self, pdf):
        """Gera tabelas de resultados"""
        print("\n[5/8] Gerando tabelas de resultados...")
        
        # Página: Tabela de resultados por faixa
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.axis('tight')
        ax.axis('off')
        
        # Dados da tabela
        table_data = [['Faixa', 'El Niño\nMédia±DP', 'La Niña\nMédia±DP', 'Neutro\nMédia±DP', 
                      'ANOVA\np-valor', 'Levene\np-valor', 't-test\np-valor', 'Pearson\nr (p-valor)']]
        
        for faixa in sorted(self.resultados['por_faixa'].keys()):
            stats = self.resultados['por_faixa'][faixa]
            
            el_nino_str = f"{stats['El Niño']['Média']:.3f}±{stats['El Niño']['DP']:.3f}"
            la_nina_str = f"{stats['La Niña']['Média']:.3f}±{stats['La Niña']['DP']:.3f}"
            neutro_str = f"{stats['Neutro']['Média']:.3f}±{stats['Neutro']['DP']:.3f}"
            
            anova_p = stats.get('ANOVA', {}).get('p-valor', 'N/A')
            anova_str = f"{anova_p:.4f}" if isinstance(anova_p, float) else 'N/A'
            
            levene_p = stats.get('Levene', {}).get('p-valor', 'N/A')
            levene_str = f"{levene_p:.4f}" if isinstance(levene_p, float) else 'N/A'
            
            ttest_p = stats.get('t-test', {}).get('p-valor', 'N/A')
            ttest_str = f"{ttest_p:.4f}" if isinstance(ttest_p, float) else 'N/A'
            
            pearson_r = stats.get('Pearson', {}).get('r', None)
            pearson_p = stats.get('Pearson', {}).get('p-valor', None)
            if pearson_r is not None and pearson_p is not None:
                pearson_str = f"{pearson_r:.3f}\n({pearson_p:.4f})"
            else:
                pearson_str = 'N/A'
            
            table_data.append([f'{faixa}', el_nino_str, la_nina_str, neutro_str, 
                             anova_str, levene_str, ttest_str, pearson_str])
        
        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.08, 0.14, 0.14, 0.14, 0.12, 0.12, 0.12, 0.14])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2.5)
        
        # Estilizar cabeçalho
        for i in range(8):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Colorir linhas alternadas
        for i in range(1, len(table_data)):
            for j in range(8):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        plt.title('Resultados dos Testes Paramétricos por Faixa de Latitude\n(Todas as 8 Faixas)', 
                 fontsize=12, fontweight='bold', pad=20)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        print("  ✓ Tabelas geradas")
    
    def salvar_csv(self):
        """Salva resultados em CSV"""
        print("\n[6/8] Salvando resultados em CSV...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV detalhado por faixa
        dados_csv = []
        for faixa, stats in self.resultados['por_faixa'].items():
            row = {
                'FAIXA_LATITUDE': faixa,
                'EL_NINO_N': stats['El Niño']['N'],
                'EL_NINO_MEDIA': stats['El Niño']['Média'],
                'EL_NINO_DP': stats['El Niño']['DP'],
                'LA_NINA_N': stats['La Niña']['N'],
                'LA_NINA_MEDIA': stats['La Niña']['Média'],
                'LA_NINA_DP': stats['La Niña']['DP'],
                'NEUTRO_N': stats['Neutro']['N'],
                'NEUTRO_MEDIA': stats['Neutro']['Média'],
                'NEUTRO_DP': stats['Neutro']['DP'],
                'ANOVA_F': stats.get('ANOVA', {}).get('F', None),
                'ANOVA_P': stats.get('ANOVA', {}).get('p-valor', None),
                'LEVENE_W': stats.get('Levene', {}).get('W', None),
                'LEVENE_P': stats.get('Levene', {}).get('p-valor', None),
                'TTEST_T': stats.get('t-test', {}).get('t', None),
                'TTEST_P': stats.get('t-test', {}).get('p-valor', None),
                'PEARSON_R': stats.get('Pearson', {}).get('r', None),
                'PEARSON_P': stats.get('Pearson', {}).get('p-valor', None),
                'MAIOR_IMPACTO': stats.get('Maior_Impacto', {}).get('Fase', None),
                'DIFERENCA_PERCENTUAL': stats.get('Maior_Impacto', {}).get('Percentual', None)
            }
            dados_csv.append(row)
        
        df_resultados = pd.DataFrame(dados_csv)
        arquivo_csv = self.output_dir / f"analise_el_nino_la_nina_parametrica_{timestamp}.csv"
        df_resultados.to_csv(arquivo_csv, index=False)
        print(f"  ✓ CSV salvo: {arquivo_csv.name}")
        
        return arquivo_csv
    
    def gerar_relatorio_pdf(self):
        """Gera relatório PDF completo"""
        print("\n[7/8] Gerando relatório PDF...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo_pdf = self.output_dir / f"analise_el_nino_la_nina_parametrica_{timestamp}.pdf"
        
        with PdfPages(arquivo_pdf) as pdf:
            # Página de título
            fig = plt.figure(figsize=(11, 8.5))
            fig.text(0.5, 0.7, 'ANÁLISE EL NIÑO vs LA NIÑA', 
                    ha='center', fontsize=24, fontweight='bold')
            fig.text(0.5, 0.6, 'Testes Paramétricos (ANOVA, Levene, Pearson)', 
                    ha='center', fontsize=16)
            fig.text(0.5, 0.5, f'Todas as 8 Faixas de Latitude', 
                    ha='center', fontsize=14)
            fig.text(0.5, 0.4, f'Período: {self.df["ANO"].min()}-{self.df["ANO"].max()}', 
                    ha='center', fontsize=12)
            fig.text(0.5, 0.3, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 
                    ha='center', fontsize=10, style='italic')
            fig.text(0.5, 0.1, 'NEDE/UFSM', ha='center', fontsize=10)
            plt.axis('off')
            pdf.savefig(fig)
            plt.close()
            
            # Gerar visualizações
            self.gerar_visualizacoes(pdf)
            
            # Gerar tabelas
            self.gerar_tabelas_resultados(pdf)
            
            # Página de resumo global
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.axis('off')
            
            global_stats = self.resultados['global']
            
            resumo_text = f"""
RESUMO GLOBAL - ANÁLISE PARAMÉTRICA

Estatísticas Descritivas:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
El Niño:    N={global_stats['El Niño']['N']:>3}  Média={global_stats['El Niño']['Média']:.4f}  DP={global_stats['El Niño']['DP']:.4f}
La Niña:    N={global_stats['La Niña']['N']:>3}  Média={global_stats['La Niña']['Média']:.4f}  DP={global_stats['La Niña']['DP']:.4f}
Neutro:     N={global_stats['Neutro']['N']:>3}  Média={global_stats['Neutro']['Média']:.4f}  DP={global_stats['Neutro']['DP']:.4f}

Testes Estatísticos:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANOVA:      F={global_stats['ANOVA']['F']:.3f}  p={global_stats['ANOVA']['p-valor']:.4f}  ({global_stats['ANOVA']['Significativo']})
Levene:     W={global_stats['Levene']['W']:.3f}  p={global_stats['Levene']['p-valor']:.4f}  (Homogêneo: {global_stats['Levene']['Homogêneo']})
t-test:     t={global_stats['t-test']['t']:.3f}  p={global_stats['t-test']['p-valor']:.4f}  ({global_stats['t-test']['Significativo']})

Conclusão:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fase Predominante: {global_stats['Conclusão_Global']['Fase_Predominante']}
Diferença Percentual: {global_stats['Conclusão_Global']['Percentual']:.1f}%

Interpretação:
{global_stats['Conclusão_Global']['Fase_Predominante']} apresenta incidência de dengue 
{global_stats['Conclusão_Global']['Percentual']:.1f}% maior em comparação com a outra fase.
"""
            
            ax.text(0.1, 0.9, resumo_text, transform=ax.transAxes,
                   fontsize=11, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
            
            plt.title('Resumo Global - Testes Paramétricos', fontsize=14, fontweight='bold', pad=20)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        
        print(f"  ✓ PDF salvo: {arquivo_pdf.name}")
        return arquivo_pdf
    
    def executar(self):
        """Executa análise completa"""
        try:
            self.carregar_dados()
            self.analise_por_latitude()
            self.analise_global_enso()
            arquivo_csv = self.salvar_csv()
            arquivo_pdf = self.gerar_relatorio_pdf()
            
            print("\n[8/8] Gerando resumo textual...")
            
            # Resumo textual
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            arquivo_txt = self.output_dir / f"resumo_el_nino_la_nina_parametrica_{timestamp}.txt"
            
            with open(arquivo_txt, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("ANÁLISE EL NIÑO vs LA NIÑA - TESTES PARAMÉTRICOS\n")
                f.write("="*80 + "\n\n")
                
                f.write(f"Período: {self.df['ANO'].min()}-{self.df['ANO'].max()}\n")
                f.write(f"Total de observações: {len(self.df)}\n")
                f.write(f"Faixas de latitude analisadas: 8\n\n")
                
                f.write("RESULTADOS POR FAIXA DE LATITUDE:\n")
                f.write("-"*80 + "\n\n")
                
                for faixa in sorted(self.resultados['por_faixa'].keys()):
                    stats = self.resultados['por_faixa'][faixa]
                    f.write(f"Faixa {faixa}:\n")
                    f.write(f"  El Niño:  N={stats['El Niño']['N']:>3}  Média={stats['El Niño']['Média']:.4f}  DP={stats['El Niño']['DP']:.4f}\n")
                    f.write(f"  La Niña:  N={stats['La Niña']['N']:>3}  Média={stats['La Niña']['Média']:.4f}  DP={stats['La Niña']['DP']:.4f}\n")
                    f.write(f"  Neutro:   N={stats['Neutro']['N']:>3}  Média={stats['Neutro']['Média']:.4f}  DP={stats['Neutro']['DP']:.4f}\n")
                    
                    if 'ANOVA' in stats:
                        f.write(f"  ANOVA:    F={stats['ANOVA'].get('F', 'N/A'):.3f}  p={stats['ANOVA'].get('p-valor', 'N/A'):.4f}\n")
                    if 'Levene' in stats:
                        f.write(f"  Levene:   W={stats['Levene'].get('W', 'N/A'):.3f}  p={stats['Levene'].get('p-valor', 'N/A'):.4f}\n")
                    if 't-test' in stats:
                        f.write(f"  t-test:   t={stats['t-test'].get('t', 'N/A'):.3f}  p={stats['t-test'].get('p-valor', 'N/A'):.4f}\n")
                    if 'Pearson' in stats:
                        f.write(f"  Pearson:  r={stats['Pearson'].get('r', 'N/A'):.3f}  p={stats['Pearson'].get('p-valor', 'N/A'):.4f}\n")
                    if 'Maior_Impacto' in stats:
                        f.write(f"  Maior impacto: {stats['Maior_Impacto']['Fase']} ({stats['Maior_Impacto']['Percentual']:.1f}% maior)\n")
                    f.write("\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write("ANÁLISE GLOBAL\n")
                f.write("="*80 + "\n\n")
                
                global_stats = self.resultados['global']
                f.write(f"Fase predominante: {global_stats['Conclusão_Global']['Fase_Predominante']}\n")
                f.write(f"Diferença: {global_stats['Conclusão_Global']['Percentual']:.1f}%\n\n")
                f.write(f"ANOVA Global: F={global_stats['ANOVA']['F']:.3f}, p={global_stats['ANOVA']['p-valor']:.4f}\n")
                f.write(f"Levene Global: W={global_stats['Levene']['W']:.3f}, p={global_stats['Levene']['p-valor']:.4f}\n")
                f.write(f"t-test Global: t={global_stats['t-test']['t']:.3f}, p={global_stats['t-test']['p-valor']:.4f}\n")
            
            print(f"  ✓ Resumo salvo: {arquivo_txt.name}")
            
            print("\n" + "="*80)
            print("✅ ANÁLISE PARAMÉTRICA CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print(f"\nArquivos gerados:")
            print(f"  📄 PDF:  {arquivo_pdf}")
            print(f"  📊 CSV:  {arquivo_csv}")
            print(f"  📝 TXT:  {arquivo_txt}")
            print(f"\nTodas as 8 faixas de latitude foram analisadas.")
            print()
            
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analisador = AnalisadorENSOLatitudeParametrico()
    analisador.executar()
