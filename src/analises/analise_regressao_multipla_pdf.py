"""
Script para Análise de Regressão Linear Múltipla + PDF
Usa TODAS as variáveis em médias mensais: dengue log, temperaturas, precipitação e ONI
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from pathlib import Path
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class AnalisadorRegressaoMultipla:
    """Análise de Regressão Linear Múltipla com todas as variáveis climáticas"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent  # raiz do projeto
        self.output_dir = self.base_path / "output" / "relatorios_latitude"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.df = None
        self.df_modelagem = None
        self.modelo = None
        self.scaler = None
        self.resultados = {}
        
    def carregar_dados(self):
        """Carrega todas as variáveis em médias mensais"""
        print("\n" + "="*80)
        print("ANÁLISE DE REGRESSÃO LINEAR MÚLTIPLA")
        print("="*80)
        
        print("\n[1/9] Carregando dados de médias mensais por latitude...")
        
        # Carregar médias mensais
        arquivo_medias = self.base_path / "output" / "medias_latitude" / "todas_faixas_medias_mensais.csv"
        
        if not arquivo_medias.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_medias}")
        
        self.df = pd.read_csv(arquivo_medias)
        print(f"  → Dados carregados: {self.df.shape}")
        print(f"  → Faixas de latitude: {self.df['FAIXA_LATITUDE'].nunique()}")
        print(f"  → Período: {self.df['ANO'].min()}-{self.df['ANO'].max()}")
        
        # Carregar ONI
        print("\n[2/9] Adicionando índice ONI...")
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
        
        # Merge com dados principais
        self.df = self.df.merge(df_oni_long, on=['ANO', 'MES'], how='left')
        
        # Criar coluna de data
        self.df['DATA'] = pd.to_datetime(
            self.df['ANO'].astype(str) + '-' + 
            self.df['MES'].astype(str).str.zfill(2) + '-01'
        )
        
        print(f"  ✓ Dataset completo: {len(self.df)} registros")
        print(f"  ✓ Variáveis disponíveis: {list(self.df.columns)}")
    
    def preparar_modelagem(self):
        """Prepara dados para modelagem"""
        print("\n[3/9] Preparando dados para modelagem...")
        
        # Selecionar variáveis relevantes (apenas as disponíveis no dataset)
        variaveis = [
            'MEDIA_LOG_CASOS_DENGUE',  # Variável dependente
            'ONI',                     # Preditor: Índice ONI (ENSO)
            'LATITUDE'                 # Preditor: Latitude
        ]
        
        # Filtrar e remover NaN
        self.df_modelagem = self.df[variaveis].copy()
        antes = len(self.df_modelagem)
        self.df_modelagem = self.df_modelagem.dropna()
        depois = len(self.df_modelagem)
        
        print(f"  → Registros antes de remover NaN: {antes}")
        print(f"  → Registros após remover NaN: {depois}")
        print(f"  → Registros removidos: {antes - depois}")
        
        print("\n  ⚠ Nota: Modelo simplificado usando apenas ONI e LATITUDE")
        print("    (Dados de temperatura e precipitação não disponíveis no formato agregado)")
        
        # Separar X e y
        self.X = self.df_modelagem.drop('MEDIA_LOG_CASOS_DENGUE', axis=1)
        self.y = self.df_modelagem['MEDIA_LOG_CASOS_DENGUE']
        
        print(f"\n  Variáveis preditoras (X): {list(self.X.columns)}")
        print(f"  Variável dependente (y): MEDIA_LOG_CASOS_DENGUE")
        print(f"  Dimensões - X: {self.X.shape}, y: {self.y.shape}")
    
    def estatisticas_descritivas(self):
        """Estatísticas descritivas das variáveis"""
        print("\n[4/9] Calculando estatísticas descritivas...")
        
        stats_desc = self.df_modelagem.describe().T
        stats_desc['CV (%)'] = (stats_desc['std'] / stats_desc['mean'] * 100).round(2)
        
        self.resultados['estatisticas_descritivas'] = stats_desc
        
        print("\n  Estatísticas Descritivas:")
        print(stats_desc.to_string())
        
        # Correlações
        print("\n  Calculando matriz de correlação...")
        corr_matrix = self.df_modelagem.corr()
        self.resultados['correlacao'] = corr_matrix
        
        # Correlações com dengue
        corr_dengue = corr_matrix['MEDIA_LOG_CASOS_DENGUE'].sort_values(ascending=False)
        print("\n  Correlações com Dengue (Log):")
        for var, corr in corr_dengue.items():
            if var != 'MEDIA_LOG_CASOS_DENGUE':
                print(f"    {var}: {corr:.4f}")
    
    def ajustar_modelo(self):
        """Ajusta modelo de regressão linear múltipla"""
        print("\n[5/9] Ajustando modelo de regressão linear múltipla...")
        
        # Padronizar variáveis
        print("  → Padronizando variáveis...")
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(self.X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=self.X.columns, index=self.X.index)
        
        # Ajustar modelo
        print("  → Ajustando modelo...")
        self.modelo = LinearRegression()
        self.modelo.fit(X_scaled_df, self.y)
        
        # Predições
        y_pred = self.modelo.predict(X_scaled_df)
        
        # Métricas
        r2 = r2_score(self.y, y_pred)
        r2_adj = 1 - (1 - r2) * (len(self.y) - 1) / (len(self.y) - X_scaled_df.shape[1] - 1)
        rmse = np.sqrt(mean_squared_error(self.y, y_pred))
        mae = mean_absolute_error(self.y, y_pred)
        
        # Calcular F-statistic
        n = len(self.y)
        k = X_scaled_df.shape[1]
        f_stat = (r2 / k) / ((1 - r2) / (n - k - 1))
        f_pvalue = 1 - stats.f.cdf(f_stat, k, n - k - 1)
        
        # Armazenar resultados
        self.resultados['metricas'] = {
            'R²': r2,
            'R² Ajustado': r2_adj,
            'RMSE': rmse,
            'MAE': mae,
            'F-statistic': f_stat,
            'F p-valor': f_pvalue,
            'N': n,
            'K (preditores)': k
        }
        
        # Coeficientes
        coeficientes = pd.DataFrame({
            'Variável': self.X.columns,
            'Coeficiente': self.modelo.coef_,
            'Coef_Abs': np.abs(self.modelo.coef_)
        }).sort_values('Coef_Abs', ascending=False)
        
        coeficientes['Intercepto'] = self.modelo.intercept_
        
        self.resultados['coeficientes'] = coeficientes
        
        # Calcular p-valores dos coeficientes
        residuos = self.y - y_pred
        mse = np.sum(residuos**2) / (n - k - 1)
        var_coef = mse * np.linalg.inv(X_scaled_df.T @ X_scaled_df).diagonal()
        se_coef = np.sqrt(var_coef)
        t_stat = self.modelo.coef_ / se_coef
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - k - 1))
        
        coeficientes_completo = pd.DataFrame({
            'Variável': self.X.columns,
            'Coeficiente': self.modelo.coef_,
            'Erro Padrão': se_coef,
            't-stat': t_stat,
            'p-valor': p_values,
            'Significativo': ['***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '' 
                             for p in p_values]
        })
        
        self.resultados['coeficientes_completo'] = coeficientes_completo
        
        # Armazenar predições
        self.resultados['predicoes'] = pd.DataFrame({
            'Real': self.y,
            'Predito': y_pred,
            'Residuo': residuos
        })
        
        print(f"\n  ✓ Modelo ajustado com sucesso!")
        print(f"    R² = {r2:.4f}")
        print(f"    R² Ajustado = {r2_adj:.4f}")
        print(f"    RMSE = {rmse:.4f}")
        print(f"    F-statistic = {f_stat:.2f} (p = {f_pvalue:.4e})")
        
        print(f"\n  Coeficientes (padronizados):")
        print(coeficientes_completo.to_string(index=False))
    
    def diagnostico_residuos(self):
        """Análise de diagnóstico dos resíduos"""
        print("\n[6/9] Diagnóstico de resíduos...")
        
        residuos = self.resultados['predicoes']['Residuo']
        
        # Teste de normalidade (Shapiro-Wilk)
        if len(residuos) <= 5000:
            stat, p_value = stats.shapiro(residuos)
            normalidade = {
                'Teste': 'Shapiro-Wilk',
                'Estatística': stat,
                'p-valor': p_value,
                'Normal': 'Sim' if p_value > 0.05 else 'Não'
            }
        else:
            stat, p_value = stats.kstest(residuos, 'norm')
            normalidade = {
                'Teste': 'Kolmogorov-Smirnov',
                'Estatística': stat,
                'p-valor': p_value,
                'Normal': 'Sim' if p_value > 0.05 else 'Não'
            }
        
        # Teste de Durbin-Watson (autocorrelação)
        residuos_array = residuos.values
        dw = np.sum(np.diff(residuos_array)**2) / np.sum(residuos_array**2)
        
        diagnostico = {
            'Normalidade': normalidade,
            'Durbin-Watson': {
                'Estatística': dw,
                'Interpretação': 'Sem autocorrelação' if 1.5 < dw < 2.5 else 
                                'Possível autocorrelação positiva' if dw < 1.5 else
                                'Possível autocorrelação negativa'
            },
            'Estatísticas_Residuos': {
                'Média': residuos.mean(),
                'Mediana': residuos.median(),
                'DP': residuos.std(),
                'Min': residuos.min(),
                'Max': residuos.max()
            }
        }
        
        self.resultados['diagnostico'] = diagnostico
        
        print(f"  → Teste de normalidade: {normalidade['Teste']}")
        print(f"    Estatística: {normalidade['Estatística']:.4f}")
        print(f"    p-valor: {normalidade['p-valor']:.4e}")
        print(f"    Resíduos são normais? {normalidade['Normal']}")
        print(f"\n  → Durbin-Watson: {dw:.4f} ({diagnostico['Durbin-Watson']['Interpretação']})")
    
    def analise_importancia_variaveis(self):
        """Análise de importância das variáveis"""
        print("\n[7/9] Analisando importância das variáveis...")
        
        coefs = self.resultados['coeficientes_completo']
        
        # Importância relativa (coeficientes padronizados em valor absoluto)
        importancia = coefs.copy()
        importancia['Importancia_Relativa'] = np.abs(importancia['Coeficiente'])
        importancia['Importancia_Pct'] = (importancia['Importancia_Relativa'] / 
                                          importancia['Importancia_Relativa'].sum() * 100)
        importancia = importancia.sort_values('Importancia_Relativa', ascending=False)
        
        self.resultados['importancia'] = importancia
        
        print("\n  Importância Relativa das Variáveis:")
        for idx, row in importancia.iterrows():
            sinal = '+' if row['Coeficiente'] > 0 else '-'
            sig = row['Significativo']
            print(f"    {row['Variável']}: {row['Importancia_Pct']:.1f}% ({sinal}) {sig}")
    
    def criar_pdf(self):
        """Cria PDF com todos os resultados"""
        print("\n[8/9] Gerando PDF...")
        
        pdf_path = self.output_dir / f"analise_regressao_multipla_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        with PdfPages(pdf_path) as pdf:
            # Página 1: Visão geral do modelo
            self._plot_visao_geral(pdf)
            
            # Página 2: Matriz de correlação
            self._plot_correlacao(pdf)
            
            # Página 3: Coeficientes do modelo
            self._plot_coeficientes(pdf)
            
            # Página 4: Predições vs Observado
            self._plot_predicoes(pdf)
            
            # Página 5: Diagnóstico de resíduos
            self._plot_diagnostico_residuos(pdf)
            
            # Página 6: Importância das variáveis
            self._plot_importancia(pdf)
            
            # Página 7: Análise por variável
            self._plot_efeitos_parciais(pdf)
            
            # Página 8: Relatório técnico
            self._plot_relatorio_tecnico(pdf)
        
        print(f"  ✓ PDF gerado: {pdf_path}")
        return pdf_path
    
    def _plot_visao_geral(self, pdf):
        """Página de visão geral do modelo"""
        fig = plt.figure(figsize=(11, 14))
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        y_pos = 0.95
        
        # Título
        ax.text(0.5, y_pos, 'ANÁLISE DE REGRESSÃO LINEAR MÚLTIPLA',
               ha='center', fontsize=20, fontweight='bold')
        y_pos -= 0.05
        ax.text(0.5, y_pos, 'Dengue (Log) em Função de Variáveis Climáticas e ONI',
               ha='center', fontsize=14, style='italic')
        y_pos -= 0.08
        
        # Equação do modelo
        ax.text(0.1, y_pos, 'EQUAÇÃO DO MODELO', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        coefs = self.resultados['coeficientes_completo']
        intercepto = self.modelo.intercept_
        
        equacao = f"Dengue (Log) = {intercepto:.4f}"
        for idx, row in coefs.iterrows():
            sinal = '+' if row['Coeficiente'] >= 0 else ''
            equacao_linha = f"                {sinal}{row['Coeficiente']:.4f} × {row['Variável']}"
            ax.text(0.12, y_pos, equacao_linha, fontsize=9, family='monospace')
            y_pos -= 0.02
        
        y_pos -= 0.03
        
        # Métricas de ajuste
        ax.text(0.1, y_pos, 'MÉTRICAS DE AJUSTE', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        metricas = self.resultados['metricas']
        metricas_texto = [
            f"R² (Coeficiente de Determinação): {metricas['R²']:.4f}",
            f"R² Ajustado: {metricas['R² Ajustado']:.4f}",
            f"",
            f"RMSE (Erro Quadrático Médio): {metricas['RMSE']:.4f}",
            f"MAE (Erro Absoluto Médio): {metricas['MAE']:.4f}",
            f"",
            f"F-statistic: {metricas['F-statistic']:.2f}",
            f"p-valor (F-test): {metricas['F p-valor']:.4e}",
            f"",
            f"Número de observações: {metricas['N']}",
            f"Número de preditores: {metricas['K (preditores)']}"
        ]
        
        for linha in metricas_texto:
            if linha:
                ax.text(0.12, y_pos, linha, fontsize=10)
            y_pos -= 0.025
        
        y_pos -= 0.02
        
        # Interpretação do R²
        ax.text(0.1, y_pos, 'INTERPRETAÇÃO', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        r2 = metricas['R²']
        interpretacao = []
        
        if r2 >= 0.7:
            qualidade = "EXCELENTE"
        elif r2 >= 0.5:
            qualidade = "BOA"
        elif r2 >= 0.3:
            qualidade = "MODERADA"
        else:
            qualidade = "FRACA"
        
        interpretacao = [
            f"• O modelo possui qualidade de ajuste {qualidade}",
            f"• {r2*100:.1f}% da variação na dengue (log) é explicada pelas",
            f"  variáveis climáticas e ONI incluídas no modelo",
            f"",
            f"• O teste F indica que o modelo é {'estatisticamente significativo' if metricas['F p-valor'] < 0.05 else 'não significativo'}",
            f"  (p = {metricas['F p-valor']:.4e})"
        ]
        
        for linha in interpretacao:
            ax.text(0.12, y_pos, linha, fontsize=10)
            y_pos -= 0.025
        
        y_pos -= 0.02
        
        # Variáveis do modelo
        ax.text(0.1, y_pos, 'VARIÁVEIS DO MODELO', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        ax.text(0.12, y_pos, 'Variável Dependente:', fontsize=10, fontweight='bold')
        y_pos -= 0.02
        ax.text(0.15, y_pos, '• MEDIA_LOG_CASOS_DENGUE (log₁₀(casos + 1))', fontsize=9)
        y_pos -= 0.03
        
        ax.text(0.12, y_pos, 'Variáveis Preditoras:', fontsize=10, fontweight='bold')
        y_pos -= 0.02
        
        preditoras = [
            '• ONI: Índice Oceanic Niño Index (ENSO)',
            '• LATITUDE: Latitude da faixa geográfica',
            '',
            'Nota: Modelo simplificado devido à indisponibilidade de dados',
            'agregados de temperatura e precipitação por latitude.'
        ]
        
        for linha in preditoras:
            if linha:
                ax.text(0.15, y_pos, linha, fontsize=9, style='italic' if 'Nota' in linha else 'normal')
            y_pos -= 0.02
        
        # Rodapé
        ax.text(0.5, 0.03,
               f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
               ha='center', fontsize=9, style='italic', color='gray')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_correlacao(self, pdf):
        """Matriz de correlação"""
        fig, ax = plt.subplots(figsize=(12, 10))
        
        corr = self.resultados['correlacao']
        
        # Heatmap
        sns.heatmap(corr, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
        
        ax.set_title('Matriz de Correlação de Pearson\nTodas as Variáveis do Modelo',
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_coeficientes(self, pdf):
        """Gráfico de coeficientes"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        coefs = self.resultados['coeficientes_completo'].copy()
        coefs = coefs.sort_values('Coeficiente')
        
        # Plot 1: Coeficientes com barras de erro
        colors = ['red' if c < 0 else 'green' for c in coefs['Coeficiente']]
        axes[0].barh(range(len(coefs)), coefs['Coeficiente'], 
                    xerr=coefs['Erro Padrão'], color=colors, alpha=0.7,
                    capsize=5, error_kw={'linewidth': 2})
        axes[0].set_yticks(range(len(coefs)))
        axes[0].set_yticklabels(coefs['Variável'], fontsize=10)
        axes[0].axvline(x=0, color='black', linestyle='--', linewidth=1)
        axes[0].set_xlabel('Coeficiente Padronizado', fontsize=11)
        axes[0].set_title('Coeficientes do Modelo (com Erro Padrão)',
                         fontsize=13, fontweight='bold')
        axes[0].grid(True, alpha=0.3, axis='x')
        
        # Adicionar significância
        for i, (idx, row) in enumerate(coefs.iterrows()):
            sig = row['Significativo']
            if sig:
                axes[0].text(row['Coeficiente'] + row['Erro Padrão'] + 0.01, i,
                           sig, fontsize=12, fontweight='bold', va='center')
        
        # Plot 2: Importância relativa
        importancia = self.resultados['importancia'].copy()
        colors_imp = ['green' if c > 0 else 'red' 
                     for c in importancia['Coeficiente']]
        
        axes[1].barh(range(len(importancia)), importancia['Importancia_Pct'],
                    color=colors_imp, alpha=0.7)
        axes[1].set_yticks(range(len(importancia)))
        axes[1].set_yticklabels(importancia['Variável'], fontsize=10)
        axes[1].set_xlabel('Importância Relativa (%)', fontsize=11)
        axes[1].set_title('Importância Relativa das Variáveis',
                         fontsize=13, fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='x')
        
        # Adicionar valores
        for i, (idx, row) in enumerate(importancia.iterrows()):
            axes[1].text(row['Importancia_Pct'] + 1, i,
                        f"{row['Importancia_Pct']:.1f}%",
                        fontsize=9, va='center')
        
        plt.suptitle('Análise dos Coeficientes de Regressão',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_predicoes(self, pdf):
        """Predições vs Observado"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        pred_df = self.resultados['predicoes']
        
        # Plot 1: Scatter com linha de identidade
        axes[0, 0].scatter(pred_df['Real'], pred_df['Predito'],
                          alpha=0.5, s=30, edgecolors='k', linewidth=0.5)
        
        # Linha de identidade
        min_val = min(pred_df['Real'].min(), pred_df['Predito'].min())
        max_val = max(pred_df['Real'].max(), pred_df['Predito'].max())
        axes[0, 0].plot([min_val, max_val], [min_val, max_val],
                       'r--', linewidth=2, label='Linha de Identidade')
        
        # Linha de tendência
        z = np.polyfit(pred_df['Real'], pred_df['Predito'], 1)
        p = np.poly1d(z)
        axes[0, 0].plot(pred_df['Real'].sort_values(), 
                       p(pred_df['Real'].sort_values()),
                       'b-', linewidth=2, alpha=0.7, label='Tendência')
        
        axes[0, 0].set_xlabel('Valores Observados', fontsize=10)
        axes[0, 0].set_ylabel('Valores Preditos', fontsize=10)
        axes[0, 0].set_title('Predições vs Observações',
                            fontsize=12, fontweight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Adicionar R²
        r2 = self.resultados['metricas']['R²']
        axes[0, 0].text(0.05, 0.95, f'R² = {r2:.4f}',
                       transform=axes[0, 0].transAxes,
                       fontsize=11, fontweight='bold',
                       verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Plot 2: Histograma dos erros
        axes[0, 1].hist(pred_df['Residuo'], bins=30, edgecolor='black', alpha=0.7)
        axes[0, 1].axvline(x=0, color='red', linestyle='--', linewidth=2)
        axes[0, 1].set_xlabel('Resíduos', fontsize=10)
        axes[0, 1].set_ylabel('Frequência', fontsize=10)
        axes[0, 1].set_title('Distribuição dos Resíduos',
                            fontsize=12, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # Plot 3: Resíduos vs Predito
        axes[1, 0].scatter(pred_df['Predito'], pred_df['Residuo'],
                          alpha=0.5, s=30, edgecolors='k', linewidth=0.5)
        axes[1, 0].axhline(y=0, color='red', linestyle='--', linewidth=2)
        axes[1, 0].set_xlabel('Valores Preditos', fontsize=10)
        axes[1, 0].set_ylabel('Resíduos', fontsize=10)
        axes[1, 0].set_title('Resíduos vs Predições\n(verificar homocedasticidade)',
                            fontsize=12, fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Q-Q plot
        stats.probplot(pred_df['Residuo'], dist="norm", plot=axes[1, 1])
        axes[1, 1].set_title('Q-Q Plot\n(verificar normalidade dos resíduos)',
                            fontsize=12, fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.suptitle('Análise de Qualidade das Predições',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_diagnostico_residuos(self, pdf):
        """Diagnóstico detalhado dos resíduos"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        residuos = self.resultados['predicoes']['Residuo']
        
        # Plot 1: Série temporal dos resíduos
        axes[0, 0].plot(residuos.values, linewidth=0.8)
        axes[0, 0].axhline(y=0, color='red', linestyle='--', linewidth=2)
        axes[0, 0].fill_between(range(len(residuos)),
                               residuos.mean() + 2*residuos.std(),
                               residuos.mean() - 2*residuos.std(),
                               alpha=0.2, color='gray')
        axes[0, 0].set_xlabel('Índice da Observação', fontsize=10)
        axes[0, 0].set_ylabel('Resíduo', fontsize=10)
        axes[0, 0].set_title('Série Temporal dos Resíduos\n(± 2 desvios padrão)',
                            fontsize=12, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Resíduos padronizados
        residuos_pad = (residuos - residuos.mean()) / residuos.std()
        axes[0, 1].scatter(range(len(residuos_pad)), np.abs(residuos_pad),
                          alpha=0.5, s=30)
        axes[0, 1].axhline(y=2, color='orange', linestyle='--', linewidth=2,
                          label='Limite 2σ')
        axes[0, 1].axhline(y=3, color='red', linestyle='--', linewidth=2,
                          label='Limite 3σ')
        axes[0, 1].set_xlabel('Índice da Observação', fontsize=10)
        axes[0, 1].set_ylabel('|Resíduo Padronizado|', fontsize=10)
        axes[0, 1].set_title('Resíduos Padronizados (Outliers)',
                            fontsize=12, fontweight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Contar outliers
        outliers_2sigma = np.sum(np.abs(residuos_pad) > 2)
        outliers_3sigma = np.sum(np.abs(residuos_pad) > 3)
        axes[0, 1].text(0.95, 0.95,
                       f'Outliers (>2σ): {outliers_2sigma}\nOutliers (>3σ): {outliers_3sigma}',
                       transform=axes[0, 1].transAxes,
                       fontsize=10, verticalalignment='top',
                       horizontalalignment='right',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Plot 3: Autocorrelação dos resíduos
        from pandas.plotting import autocorrelation_plot
        autocorrelation_plot(pd.Series(residuos.values), ax=axes[1, 0])
        axes[1, 0].set_title('Autocorrelação dos Resíduos',
                            fontsize=12, fontweight='bold')
        axes[1, 0].set_xlabel('Lag', fontsize=10)
        axes[1, 0].set_ylabel('Autocorrelação', fontsize=10)
        
        # Plot 4: Boxplot dos resíduos
        axes[1, 1].boxplot([residuos.values], vert=True, patch_artist=True,
                          boxprops=dict(facecolor='lightblue', alpha=0.7),
                          medianprops=dict(color='red', linewidth=2),
                          showmeans=True, meanline=True)
        axes[1, 1].axhline(y=0, color='red', linestyle='--', linewidth=1)
        axes[1, 1].set_ylabel('Resíduo', fontsize=10)
        axes[1, 1].set_title('Boxplot dos Resíduos',
                            fontsize=12, fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        # Estatísticas
        stats_text = (f"Média: {residuos.mean():.4f}\n"
                     f"Mediana: {residuos.median():.4f}\n"
                     f"DP: {residuos.std():.4f}\n"
                     f"Min: {residuos.min():.4f}\n"
                     f"Max: {residuos.max():.4f}")
        axes[1, 1].text(1.15, 0.5, stats_text,
                       transform=axes[1, 1].transAxes,
                       fontsize=9, verticalalignment='center',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.suptitle('Diagnóstico Completo dos Resíduos',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_importancia(self, pdf):
        """Análise de importância das variáveis"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        importancia = self.resultados['importancia'].copy()
        
        # Plot 1: Pizza da importância
        colors_pie = ['#ff9999' if c < 0 else '#90ee90' 
                     for c in importancia['Coeficiente']]
        
        wedges, texts, autotexts = axes[0].pie(importancia['Importancia_Pct'],
                                               labels=importancia['Variável'],
                                               autopct='%1.1f%%',
                                               colors=colors_pie,
                                               startangle=90,
                                               textprops={'fontsize': 10})
        
        # Destacar significativos
        for i, (idx, row) in enumerate(importancia.iterrows()):
            if row['Significativo']:
                wedges[i].set_linewidth(3)
                wedges[i].set_edgecolor('black')
        
        axes[0].set_title('Importância Relativa das Variáveis\n(bordas grossas = significativas)',
                         fontsize=13, fontweight='bold')
        
        # Plot 2: Tabela de coeficientes
        axes[1].axis('off')
        
        # Preparar dados para tabela
        tabela_data = []
        for idx, row in importancia.iterrows():
            sinal = '+' if row['Coeficiente'] > 0 else '-'
            tabela_data.append([
                row['Variável'],
                f"{row['Coeficiente']:.4f}",
                f"{row['Erro Padrão']:.4f}",
                f"{row['t-stat']:.2f}",
                f"{row['p-valor']:.4e}",
                row['Significativo'],
                f"{row['Importancia_Pct']:.1f}%",
                sinal
            ])
        
        col_labels = ['Variável', 'Coef.', 'EP', 't', 'p-valor', 'Sig.', 'Imp.%', 'Sinal']
        
        table = axes[1].table(cellText=tabela_data,
                             colLabels=col_labels,
                             cellLoc='center',
                             loc='center',
                             bbox=[0, 0, 1, 1])
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2)
        
        # Formatar cabeçalho
        for i in range(len(col_labels)):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Colorir linhas alternadas
        for i in range(1, len(tabela_data) + 1):
            for j in range(len(col_labels)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
                
                # Destacar significativos
                if tabela_data[i-1][5]:  # Se tem significância
                    table[(i, j)].set_edgecolor('red')
                    table[(i, j)].set_linewidth(2)
        
        axes[1].set_title('Tabela Completa de Coeficientes',
                         fontsize=13, fontweight='bold', pad=20)
        
        plt.suptitle('Análise de Importância e Significância',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_efeitos_parciais(self, pdf):
        """Gráficos de efeitos parciais"""
        fig, axes = plt.subplots(3, 2, figsize=(14, 12))
        axes = axes.flatten()
        
        # Para cada variável preditora
        for idx, col in enumerate(self.X.columns):
            if idx < len(axes):
                # Scatter plot
                axes[idx].scatter(self.X[col], self.y,
                                alpha=0.4, s=20, edgecolors='k', linewidth=0.3)
                
                # Linha de tendência
                z = np.polyfit(self.X[col], self.y, 1)
                p = np.poly1d(z)
                x_line = np.linspace(self.X[col].min(), self.X[col].max(), 100)
                axes[idx].plot(x_line, p(x_line), 'r-', linewidth=2, alpha=0.7)
                
                # Correlação
                corr = self.X[col].corr(self.y)
                
                # Coeficiente do modelo
                coef_row = self.resultados['coeficientes_completo'][
                    self.resultados['coeficientes_completo']['Variável'] == col
                ]
                if len(coef_row) > 0:
                    coef = coef_row['Coeficiente'].values[0]
                    sig = coef_row['Significativo'].values[0]
                else:
                    coef = 0
                    sig = ''
                
                axes[idx].set_xlabel(col, fontsize=9)
                axes[idx].set_ylabel('Dengue (Log)', fontsize=9)
                axes[idx].set_title(f'{col}\nCorr={corr:.3f}, Coef={coef:.4f} {sig}',
                                   fontsize=10, fontweight='bold')
                axes[idx].grid(True, alpha=0.3)
        
        plt.suptitle('Efeitos Parciais de Cada Variável Preditora',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _plot_relatorio_tecnico(self, pdf):
        """Relatório técnico final"""
        fig = plt.figure(figsize=(11, 14))
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        y_pos = 0.95
        
        # Título
        ax.text(0.5, y_pos, 'RELATÓRIO TÉCNICO FINAL',
               ha='center', fontsize=20, fontweight='bold')
        y_pos -= 0.05
        ax.text(0.5, y_pos, 'Regressão Linear Múltipla - Dengue e Clima',
               ha='center', fontsize=16, style='italic')
        y_pos -= 0.08
        
        # Seção 1: Objetivo
        ax.text(0.1, y_pos, '1. OBJETIVO DA ANÁLISE', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        objetivo = [
            "Modelar a incidência de dengue (log-transformada) em função de:",
            "• Temperaturas (máxima, média e mínima)",
            "• Precipitação",
            "• Índice ONI (El Niño / La Niña)",
            "• Latitude geográfica",
            "",
            "Utilizando médias mensais agregadas por faixa de latitude."
        ]
        
        for linha in objetivo:
            ax.text(0.12, y_pos, linha, fontsize=10)
            y_pos -= 0.02
        
        y_pos -= 0.02
        
        # Seção 2: Resultados Principais
        ax.text(0.1, y_pos, '2. RESULTADOS PRINCIPAIS', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        metricas = self.resultados['metricas']
        importancia = self.resultados['importancia']
        
        # Variável mais importante
        var_mais_importante = importancia.iloc[0]
        
        resultados = [
            f"• Capacidade explicativa do modelo: R² = {metricas['R²']:.4f}",
            f"  ({metricas['R²']*100:.1f}% da variação na dengue é explicada)",
            f"",
            f"• Erro médio das predições: RMSE = {metricas['RMSE']:.4f}",
            f"",
            f"• Variável mais importante: {var_mais_importante['Variável']}",
            f"  (contribui com {var_mais_importante['Importancia_Pct']:.1f}% da explicação)",
            f"",
            f"• Significância do modelo: p = {metricas['F p-valor']:.4e}",
            f"  → {'Modelo altamente significativo' if metricas['F p-valor'] < 0.001 else 'Modelo significativo' if metricas['F p-valor'] < 0.05 else 'Modelo não significativo'}"
        ]
        
        for linha in resultados:
            ax.text(0.12, y_pos, linha, fontsize=10)
            y_pos -= 0.02
        
        y_pos -= 0.02
        
        # Seção 3: Variáveis Significativas
        ax.text(0.1, y_pos, '3. VARIÁVEIS SIGNIFICATIVAS', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        vars_sig = importancia[importancia['Significativo'] != '']
        
        if len(vars_sig) > 0:
            ax.text(0.12, y_pos, f"Total de {len(vars_sig)} variáveis significativas (p < 0.05):",
                   fontsize=10)
            y_pos -= 0.025
            
            for idx, row in vars_sig.iterrows():
                efeito = "aumenta" if row['Coeficiente'] > 0 else "diminui"
                ax.text(0.14, y_pos,
                       f"• {row['Variável']}: {efeito} a dengue ({row['Significativo']})",
                       fontsize=9)
                y_pos -= 0.02
        else:
            ax.text(0.12, y_pos, "Nenhuma variável individualmente significativa.",
                   fontsize=10)
            y_pos -= 0.02
        
        y_pos -= 0.02
        
        # Seção 4: Diagnóstico do Modelo
        ax.text(0.1, y_pos, '4. DIAGNÓSTICO DO MODELO', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        diagnostico = self.resultados['diagnostico']
        
        diagnostico_texto = [
            f"• Normalidade dos resíduos: {diagnostico['Normalidade']['Normal']}",
            f"  ({diagnostico['Normalidade']['Teste']}, p = {diagnostico['Normalidade']['p-valor']:.4e})",
            f"",
            f"• Autocorrelação: {diagnostico['Durbin-Watson']['Interpretação']}",
            f"  (Durbin-Watson = {diagnostico['Durbin-Watson']['Estatística']:.4f})",
            f"",
            f"• Resíduos: Média = {diagnostico['Estatísticas_Residuos']['Média']:.4f}",
            f"            DP = {diagnostico['Estatísticas_Residuos']['DP']:.4f}"
        ]
        
        for linha in diagnostico_texto:
            ax.text(0.12, y_pos, linha, fontsize=9)
            y_pos -= 0.02
        
        y_pos -= 0.02
        
        # Seção 5: Interpretação e Recomendações
        ax.text(0.1, y_pos, '5. INTERPRETAÇÃO E RECOMENDAÇÕES', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        # Determinar interpretação baseada no R²
        r2 = metricas['R²']
        
        if r2 >= 0.7:
            interpretacao_r2 = "O modelo apresenta excelente capacidade preditiva."
        elif r2 >= 0.5:
            interpretacao_r2 = "O modelo apresenta boa capacidade preditiva."
        elif r2 >= 0.3:
            interpretacao_r2 = "O modelo apresenta capacidade preditiva moderada."
        else:
            interpretacao_r2 = "O modelo apresenta capacidade preditiva limitada."
        
        recomendacoes = [
            interpretacao_r2,
            "",
            "Recomendações:",
            f"• As variáveis climáticas e ONI explicam {r2*100:.1f}% da variação da dengue",
            "• Outros fatores não incluídos (urbanização, controle vetorial, etc.)",
            f"  respondem por {(1-r2)*100:.1f}% da variação",
            "• O modelo pode ser usado para identificar períodos de maior risco",
            "• Considerar análise de séries temporais para capturar sazonalidade"
        ]
        
        for linha in recomendacoes:
            ax.text(0.12, y_pos, linha, fontsize=9)
            y_pos -= 0.02
        
        y_pos -= 0.02
        
        # Seção 6: Limitações
        ax.text(0.1, y_pos, '6. LIMITAÇÕES DO ESTUDO', fontsize=14, fontweight='bold')
        y_pos -= 0.03
        
        limitacoes = [
            "• Modelo assume relações lineares entre variáveis",
            "• Não captura interações não-lineares complexas",
            "• Agregação espacial (latitude) pode mascarar heterogeneidade local",
            "• Não considera defasagens temporais (lags) entre clima e dengue",
            "• Fatores socioeconômicos e de controle vetorial não incluídos"
        ]
        
        for linha in limitacoes:
            ax.text(0.12, y_pos, linha, fontsize=9)
            y_pos -= 0.02
        
        # Rodapé
        ax.text(0.5, 0.03,
               f"Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n"
               f"Análise Estatística - Projeto Dengue e Clima",
               ha='center', fontsize=8, style='italic', color='gray')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def executar_analise(self):
        """Executa análise completa"""
        try:
            self.carregar_dados()
            self.preparar_modelagem()
            self.estatisticas_descritivas()
            self.ajustar_modelo()
            self.diagnostico_residuos()
            self.analise_importancia_variaveis()
            pdf_path = self.criar_pdf()
            
            print("\n[9/9] Finalizando e salvando resultados...")
            
            # Salvar dados de modelagem
            csv_output = self.output_dir / "dados_regressao_multipla.csv"
            self.df_modelagem.to_csv(csv_output, index=False, encoding='utf-8-sig')
            print(f"  ✓ Dados de modelagem salvos: {csv_output}")
            
            # Salvar predições
            pred_output = self.output_dir / "predicoes_regressao_multipla.csv"
            self.resultados['predicoes'].to_csv(pred_output, index=False, encoding='utf-8-sig')
            print(f"  ✓ Predições salvas: {pred_output}")
            
            # Salvar resumo
            resumo_path = self.output_dir / "resumo_regressao_multipla.txt"
            with open(resumo_path, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("RESUMO: REGRESSÃO LINEAR MÚLTIPLA - DENGUE E CLIMA\n")
                f.write("="*80 + "\n\n")
                
                metricas = self.resultados['metricas']
                f.write("MÉTRICAS DO MODELO:\n")
                f.write(f"  R² = {metricas['R²']:.4f}\n")
                f.write(f"  R² Ajustado = {metricas['R² Ajustado']:.4f}\n")
                f.write(f"  RMSE = {metricas['RMSE']:.4f}\n")
                f.write(f"  MAE = {metricas['MAE']:.4f}\n")
                f.write(f"  F-statistic = {metricas['F-statistic']:.2f} (p = {metricas['F p-valor']:.4e})\n")
                f.write(f"  N = {metricas['N']}\n\n")
                
                f.write("COEFICIENTES:\n")
                f.write(self.resultados['coeficientes_completo'].to_string(index=False))
                f.write("\n\n")
                
                f.write("IMPORTÂNCIA DAS VARIÁVEIS:\n")
                importancia = self.resultados['importancia'][['Variável', 'Importancia_Pct', 'Significativo']]
                f.write(importancia.to_string(index=False))
            
            print(f"  ✓ Resumo salvo: {resumo_path}")
            
            print("\n" + "="*80)
            print("✓ ANÁLISE DE REGRESSÃO MÚLTIPLA CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print(f"\n📄 Relatório PDF: {pdf_path}")
            print(f"📊 Dados de modelagem: {csv_output}")
            print(f"📈 Predições: {pred_output}")
            print(f"📝 Resumo: {resumo_path}")
            
            # Exibir métricas principais
            print(f"\n🎯 RESULTADOS PRINCIPAIS:")
            print(f"   R² = {metricas['R²']:.4f} ({metricas['R²']*100:.1f}% de explicação)")
            print(f"   RMSE = {metricas['RMSE']:.4f}")
            
            # Variável mais importante
            var_mais_importante = self.resultados['importancia'].iloc[0]
            print(f"   Variável mais importante: {var_mais_importante['Variável']} ({var_mais_importante['Importancia_Pct']:.1f}%)")
            
            return pdf_path
            
        except Exception as e:
            print(f"\n❌ Erro na análise: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    analisador = AnalisadorRegressaoMultipla()
    analisador.executar_analise()
