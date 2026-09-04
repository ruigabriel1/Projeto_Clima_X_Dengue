"""
Análises de Regressão com Lag de 3 Meses na Dengue
Teste 1: dengue_lag3 ~ latitude + ONI + temp_media + temp_min + temp_max + precipitacao
Teste 2: dengue_lag3 ~ temp_media + temp_min + temp_max + precipitacao (+ latitude opcional)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy import stats
from pathlib import Path
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')

class AnalisadorRegressaoLag3:
    """Análises de regressão com dengue lag 3 meses"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent  # raiz do projeto
        self.output_dir = self.base_path / "output" / "relatorios_latitude"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.df = None
        self.resultados = {}
    
    def carregar_dados_mensais(self):
        """Carrega dados mensais completos"""
        print("\n" + "="*80)
        print("ANÁLISES DE REGRESSÃO COM DENGUE LAG 3 MESES")
        print("="*80)
        
        print("\n[1/8] Carregando dados mensais...")
        
        # Para Teste 1: Usar dados consolidados (agregados)
        arquivo_dados = self.base_path / "data" / "processed" / "dados_consolidados.csv"
        
        if not arquivo_dados.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_dados}")
        
        self.df_agregado = pd.read_csv(arquivo_dados)
        print(f"  → Dados agregados carregados: {self.df_agregado.shape}")
        print(f"  → Período: {self.df_agregado['ano'].min()}-{self.df_agregado['ano'].max()}")
        
        # Criar lag de 3 meses na dengue (dados agregados)
        self.df_agregado = self.df_agregado.sort_values(['ano', 'mes']).reset_index(drop=True)
        self.df_agregado['dengue_lag3'] = self.df_agregado['incidencia_dengue'].shift(-3)
        
        # Para Teste 2: Carregar dados mensais por município
        print("\n  Carregando dados mensais por município...")
        
        # Carregar dengue mensal
        arquivo_dengue = self.base_path / "data" / "raw" / "dengue_MENSAL.csv"
        df_dengue = pd.read_csv(arquivo_dengue, sep=';', decimal=',', encoding='latin1')
        
        # Limpar cabeçalhos duplicados
        df_dengue = df_dengue[~df_dengue.iloc[:, 0].isin(['municipio', 'year'])].copy()
        
        # Converter ano
        df_dengue['ANO'] = pd.to_numeric(df_dengue.iloc[:, 0], errors='coerce')
        df_dengue['MES'] = pd.to_numeric(df_dengue.iloc[:, 1], errors='coerce')
        
        # Filtrar 2015-2024
        df_dengue = df_dengue[(df_dengue['ANO'] >= 2015) & (df_dengue['ANO'] <= 2024)].copy()
        
        # Transformar de wide para long
        colunas_municipios = df_dengue.columns[3:]
        
        dados_long = []
        for idx, row in df_dengue.iterrows():
            ano = row['ANO']
            mes = row['MES']
            for col in colunas_municipios:
                try:
                    cod_mun = int(float(col))
                    casos = pd.to_numeric(row[col], errors='coerce')
                    if pd.notna(casos):
                        dados_long.append({
                            'ano': int(ano),
                            'mes': int(mes),
                            'codigo_municipio': cod_mun,
                            'casos_dengue': casos
                        })
                except:
                    pass
        
        df_dengue_long = pd.DataFrame(dados_long)
        print(f"  → Dados de dengue por município: {len(df_dengue_long):,} registros")
        
        # Carregar dados climáticos (usar médias agregadas para cada mês)
        df_clima = self.df_agregado[['ano', 'mes', 'temp_media', 'temp_minima', 
                                     'temp_maxima', 'precipitacao']].copy()
        
        # Merge dengue com clima
        self.df_mensal = df_dengue_long.merge(df_clima, on=['ano', 'mes'], how='left')
        
        # Criar lag de 3 meses por município
        self.df_mensal = self.df_mensal.sort_values(['codigo_municipio', 'ano', 'mes']).reset_index(drop=True)
        self.df_mensal['dengue_lag3'] = self.df_mensal.groupby('codigo_municipio')['casos_dengue'].shift(-3)
        
        # Remover NaN
        self.df_mensal = self.df_mensal.dropna(subset=['dengue_lag3'])
        
        print(f"  ✓ Dados mensais com lag 3: {len(self.df_mensal):,} registros")
        print(f"  ✓ Municípios: {self.df_mensal['codigo_municipio'].nunique()}")
        
    def preparar_dados_teste1(self):
        """Prepara dados para Teste 1: dados agregados com todas as variáveis"""
        print("\n[2/8] Preparando dados para Teste 1 (Dados Agregados)...")
        
        # Usar dados agregados
        self.df_teste1 = self.df_agregado.copy()
        
        # Adicionar latitude média
        self.df_teste1['latitude'] = -25.0  # Valor médio da região Sul
        
        # Selecionar variáveis preditoras
        # Tentar primeiro com ONI
        self.vars_teste1 = ['latitude', 'oni_index', 'temp_media', 'temp_minima', 
                           'temp_maxima', 'precipitacao']
        
        # Remover NaN
        vars_completas = self.vars_teste1 + ['dengue_lag3']
        self.df_teste1 = self.df_teste1[vars_completas].dropna()
        
        print(f"  ✓ Registros válidos: {len(self.df_teste1)}")
        
        if len(self.df_teste1) == 0:
            print("  ⚠ AVISO: ONI está vazio, usando apenas clima + latitude")
            
            # Sem ONI e sem latitude (constante)
            self.vars_teste1 = ['temp_media', 'temp_minima', 'temp_maxima', 'precipitacao']
            self.df_teste1 = self.df_agregado.copy()
            vars_completas = self.vars_teste1 + ['dengue_lag3']
            self.df_teste1 = self.df_teste1[vars_completas].dropna()
            
            print(f"  ✓ Registros válidos (climático): {len(self.df_teste1)}")
        
        print(f"  ✓ Variáveis: {', '.join(self.vars_teste1)}")
        
    def preparar_dados_teste2(self):
        """Prepara dados para Teste 2: dados mensais por município"""
        print("\n[3/8] Preparando dados para Teste 2 (Dados Mensais Completos)...")
        
        # Variáveis climáticas apenas
        self.vars_teste2 = ['temp_media', 'temp_minima', 'temp_maxima', 'precipitacao']
        
        # Usar dados mensais
        vars_completas = self.vars_teste2 + ['dengue_lag3']
        self.df_teste2 = self.df_mensal[vars_completas].dropna()
        
        print(f"  ✓ Registros válidos: {len(self.df_teste2):,}")
        print(f"  ✓ Variáveis: {', '.join(self.vars_teste2)}")
        print(f"  ✓ Período: {len(self.df_teste2):,} observações mês-município")
        
    def executar_regressao(self, X, y, nome_modelo):
        """Executa regressão linear com escalamento"""
        # Escalar features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Ajustar modelo
        modelo = LinearRegression()
        modelo.fit(X_scaled, y)
        
        # Predições
        y_pred = modelo.predict(X_scaled)
        
        # Métricas
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mae = mean_absolute_error(y, y_pred)
        
        # Coeficientes
        coeficientes = pd.DataFrame({
            'Variavel': X.columns,
            'Coeficiente': modelo.coef_,
            'Coef_Padronizado': modelo.coef_
        })
        
        # Ordenar por importância (valor absoluto)
        coeficientes['Importancia_Abs'] = np.abs(coeficientes['Coeficiente'])
        coeficientes = coeficientes.sort_values('Importancia_Abs', ascending=False)
        coeficientes['Importancia_Relativa'] = (coeficientes['Importancia_Abs'] / 
                                                 coeficientes['Importancia_Abs'].sum() * 100)
        
        # Significância dos coeficientes (teste t)
        n = len(y)
        p = X.shape[1]
        residuos = y - y_pred
        mse_residual = np.sum(residuos**2) / (n - p - 1)
        var_beta = mse_residual * np.linalg.inv(X_scaled.T @ X_scaled).diagonal()
        se_beta = np.sqrt(var_beta)
        t_values = modelo.coef_ / se_beta
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_values), n - p - 1))
        
        coeficientes['t_value'] = t_values
        coeficientes['p_valor'] = p_values
        coeficientes['Significativo'] = coeficientes['p_valor'] < 0.05
        
        resultados = {
            'nome': nome_modelo,
            'modelo': modelo,
            'scaler': scaler,
            'X_scaled': X_scaled,
            'y_pred': y_pred,
            'r2': r2,
            'rmse': rmse,
            'mae': mae,
            'coeficientes': coeficientes,
            'n_obs': n,
            'n_vars': p,
            'residuos': residuos
        }
        
        return resultados
    
    def executar_teste1(self):
        """Teste 1: dengue_lag3 ~ todas as variáveis"""
        print("\n[4/8] Executando Teste 1 (Modelo Completo)...")
        
        X = self.df_teste1[self.vars_teste1]
        y = self.df_teste1['dengue_lag3']
        
        self.resultado_teste1 = self.executar_regressao(X, y, "Teste 1: Modelo Completo")
        
        print(f"\n  Resultados do Teste 1:")
        print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  R²: {self.resultado_teste1['r2']:.4f}")
        print(f"  RMSE: {self.resultado_teste1['rmse']:.4f}")
        print(f"  MAE: {self.resultado_teste1['mae']:.4f}")
        print(f"  N observações: {self.resultado_teste1['n_obs']}")
        print(f"\n  Top 3 variáveis mais importantes:")
        for idx, row in self.resultado_teste1['coeficientes'].head(3).iterrows():
            sig = "*" if row['Significativo'] else ""
            print(f"    {row['Variavel']}: {row['Importancia_Relativa']:.1f}% (p={row['p_valor']:.4f}){sig}")
    
    def executar_teste2(self):
        """Teste 2: dengue_lag3 ~ variáveis climáticas (dados mensais)"""
        print("\n[5/8] Executando Teste 2 (Dados Mensais)...")
        
        X = self.df_teste2[self.vars_teste2]
        y = self.df_teste2['dengue_lag3']
        
        self.resultado_teste2 = self.executar_regressao(X, y, "Teste 2: Modelo Climático (Mensal)")
        
        print(f"\n  Resultados do Teste 2:")
        print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  R²: {self.resultado_teste2['r2']:.4f}")
        print(f"  RMSE: {self.resultado_teste2['rmse']:.4f}")
        print(f"  MAE: {self.resultado_teste2['mae']:.4f}")
        print(f"  N observações: {self.resultado_teste2['n_obs']:,}")
        print(f"\n  Top 3 variáveis mais importantes:")
        for idx, row in self.resultado_teste2['coeficientes'].head(3).iterrows():
            sig = "*" if row['Significativo'] else ""
            print(f"    {row['Variavel']}: {row['Importancia_Relativa']:.1f}% (p={row['p_valor']:.4f}){sig}")
    
    def gerar_visualizacoes(self, pdf):
        """Gera visualizações para o PDF"""
        print("\n[6/8] Gerando visualizações...")
        
        # Página 1: Importância das variáveis - Teste 1
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        coef = self.resultado_teste1['coeficientes'].copy()
        colors = ['green' if sig else 'gray' for sig in coef['Significativo']]
        
        ax.barh(coef['Variavel'], coef['Importancia_Relativa'], color=colors, alpha=0.7)
        ax.set_xlabel('Importância Relativa (%)', fontweight='bold')
        ax.set_title('Teste 1: Importância das Variáveis\n(Verde: p<0.05)', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Adicionar valores
        for i, (idx, row) in enumerate(coef.iterrows()):
            ax.text(row['Importancia_Relativa'] + 1, i, 
                   f"{row['Importancia_Relativa']:.1f}%\np={row['p_valor']:.3f}",
                   va='center', fontsize=9)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Página 2: Valores Observados vs Preditos - Teste 1
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        y_true = self.df_teste1['dengue_lag3']
        y_pred = self.resultado_teste1['y_pred']
        
        # Scatter plot
        ax1.scatter(y_true, y_pred, alpha=0.5, s=30)
        ax1.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 
                'r--', lw=2, label='Linha Perfeita')
        ax1.set_xlabel('Dengue Observado (lag 3)', fontweight='bold')
        ax1.set_ylabel('Dengue Predito', fontweight='bold')
        ax1.set_title(f'Teste 1: Observado vs Predito\nR²={self.resultado_teste1["r2"]:.4f}', 
                     fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Resíduos
        residuos = self.resultado_teste1['residuos']
        ax2.scatter(y_pred, residuos, alpha=0.5, s=30)
        ax2.axhline(y=0, color='r', linestyle='--', lw=2)
        ax2.set_xlabel('Dengue Predito', fontweight='bold')
        ax2.set_ylabel('Resíduos', fontweight='bold')
        ax2.set_title('Teste 1: Análise de Resíduos', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Página 3: Importância das variáveis - Teste 2
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        coef2 = self.resultado_teste2['coeficientes'].copy()
        colors2 = ['green' if sig else 'gray' for sig in coef2['Significativo']]
        
        ax.barh(coef2['Variavel'], coef2['Importancia_Relativa'], color=colors2, alpha=0.7)
        ax.set_xlabel('Importância Relativa (%)', fontweight='bold')
        ax.set_title('Teste 2: Importância das Variáveis Climáticas\n(Verde: p<0.05)', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        for i, (idx, row) in enumerate(coef2.iterrows()):
            ax.text(row['Importancia_Relativa'] + 1, i, 
                   f"{row['Importancia_Relativa']:.1f}%\np={row['p_valor']:.3f}",
                   va='center', fontsize=9)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Página 4: Valores Observados vs Preditos - Teste 2
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        y_true2 = self.df_teste2['dengue_lag3']
        y_pred2 = self.resultado_teste2['y_pred']
        
        ax1.scatter(y_true2, y_pred2, alpha=0.5, s=30, color='orange')
        ax1.plot([y_true2.min(), y_true2.max()], [y_true2.min(), y_true2.max()], 
                'r--', lw=2, label='Linha Perfeita')
        ax1.set_xlabel('Dengue Observado (lag 3)', fontweight='bold')
        ax1.set_ylabel('Dengue Predito', fontweight='bold')
        ax1.set_title(f'Teste 2: Observado vs Predito\nR²={self.resultado_teste2["r2"]:.4f}', 
                     fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        residuos2 = self.resultado_teste2['residuos']
        ax2.scatter(y_pred2, residuos2, alpha=0.5, s=30, color='orange')
        ax2.axhline(y=0, color='r', linestyle='--', lw=2)
        ax2.set_xlabel('Dengue Predito', fontweight='bold')
        ax2.set_ylabel('Resíduos', fontweight='bold')
        ax2.set_title('Teste 2: Análise de Resíduos', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Página 5: Comparação dos modelos
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        modelos = ['Teste 1\n(Completo)', 'Teste 2\n(Climático)']
        r2_vals = [self.resultado_teste1['r2'], self.resultado_teste2['r2']]
        rmse_vals = [self.resultado_teste1['rmse'], self.resultado_teste2['rmse']]
        
        x = np.arange(len(modelos))
        width = 0.35
        
        ax.bar(x - width/2, r2_vals, width, label='R²', alpha=0.7, color='steelblue')
        ax2 = ax.twinx()
        ax2.bar(x + width/2, rmse_vals, width, label='RMSE', alpha=0.7, color='coral')
        
        ax.set_xlabel('Modelo', fontweight='bold')
        ax.set_ylabel('R² (Coeficiente de Determinação)', fontweight='bold', color='steelblue')
        ax2.set_ylabel('RMSE (Erro Quadrático Médio)', fontweight='bold', color='coral')
        ax.set_title('Comparação de Performance dos Modelos', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(modelos)
        ax.tick_params(axis='y', labelcolor='steelblue')
        ax2.tick_params(axis='y', labelcolor='coral')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Adicionar valores
        for i, (r2, rmse) in enumerate(zip(r2_vals, rmse_vals)):
            ax.text(i - width/2, r2 + 0.01, f'{r2:.4f}', ha='center', va='bottom', fontweight='bold')
            ax2.text(i + width/2, rmse + 0.05, f'{rmse:.4f}', ha='center', va='bottom', fontweight='bold')
        
        fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9))
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        print("  ✓ Visualizações geradas")
    
    def salvar_resultados(self):
        """Salva resultados em CSV"""
        print("\n[7/8] Salvando resultados em CSV...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV Teste 1
        csv1 = self.output_dir / f"regressao_lag3_teste1_{timestamp}.csv"
        self.resultado_teste1['coeficientes'].to_csv(csv1, index=False)
        print(f"  ✓ Teste 1: {csv1.name}")
        
        # CSV Teste 2
        csv2 = self.output_dir / f"regressao_lag3_teste2_{timestamp}.csv"
        self.resultado_teste2['coeficientes'].to_csv(csv2, index=False)
        print(f"  ✓ Teste 2: {csv2.name}")
        
        return csv1, csv2
    
    def gerar_relatorio_pdf(self):
        """Gera relatório PDF completo"""
        print("\n[8/8] Gerando relatório PDF...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo_pdf = self.output_dir / f"analise_regressao_lag3_{timestamp}.pdf"
        
        with PdfPages(arquivo_pdf) as pdf:
            # Página de título
            fig = plt.figure(figsize=(11, 8.5))
            fig.text(0.5, 0.7, 'ANÁLISES DE REGRESSÃO', 
                    ha='center', fontsize=24, fontweight='bold')
            fig.text(0.5, 0.6, 'Dengue com Lag de 3 Meses', 
                    ha='center', fontsize=18)
            fig.text(0.5, 0.5, f'Período: {self.df_agregado["ano"].min()}-{self.df_agregado["ano"].max()}', 
                    ha='center', fontsize=14)
            fig.text(0.5, 0.4, f'Teste 1: Dados Agregados ({self.resultado_teste1["n_obs"]} obs)', 
                    ha='center', fontsize=12)
            fig.text(0.5, 0.35, f'Teste 2: Dados Mensais ({self.resultado_teste2["n_obs"]:,} obs município-mês)', 
                    ha='center', fontsize=12)
            fig.text(0.5, 0.25, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 
                    ha='center', fontsize=10, style='italic')
            fig.text(0.5, 0.1, 'NEDE/UFSM', ha='center', fontsize=10)
            plt.axis('off')
            pdf.savefig(fig)
            plt.close()
            
            # Gerar visualizações
            self.gerar_visualizacoes(pdf)
            
            # Página de resumo
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.axis('off')
            
            resumo = f"""
RESUMO DOS RESULTADOS

TESTE 1: Modelo com Dados Agregados
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variáveis: {', '.join(self.vars_teste1)}
Observações: {self.resultado_teste1['n_obs']}
R²: {self.resultado_teste1['r2']:.4f}
RMSE: {self.resultado_teste1['rmse']:.4f}
MAE: {self.resultado_teste1['mae']:.4f}

Variável mais importante: {self.resultado_teste1['coeficientes'].iloc[0]['Variavel']}
  → Importância: {self.resultado_teste1['coeficientes'].iloc[0]['Importancia_Relativa']:.1f}%
  → p-valor: {self.resultado_teste1['coeficientes'].iloc[0]['p_valor']:.4f}

TESTE 2: Modelo com Dados Mensais por Município
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variáveis: {', '.join(self.vars_teste2)}
Observações: {self.resultado_teste2['n_obs']:,} (mês-município)
R²: {self.resultado_teste2['r2']:.4f}
RMSE: {self.resultado_teste2['rmse']:.4f}
MAE: {self.resultado_teste2['mae']:.4f}

Variável mais importante: {self.resultado_teste2['coeficientes'].iloc[0]['Variavel']}
  → Importância: {self.resultado_teste2['coeficientes'].iloc[0]['Importancia_Relativa']:.1f}%
  → p-valor: {self.resultado_teste2['coeficientes'].iloc[0]['p_valor']:.4f}

COMPARAÇÃO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Melhor R²: {'Teste 1 (Agregado)' if self.resultado_teste1['r2'] > self.resultado_teste2['r2'] else 'Teste 2 (Mensal)'}
Diferença R²: {abs(self.resultado_teste1['r2'] - self.resultado_teste2['r2']):.4f}

Teste 1: {self.resultado_teste1['n_obs']} observações (dados agregados mensais)
Teste 2: {self.resultado_teste2['n_obs']:,} observações (dados município-mês)

INTERPRETAÇÃO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{'O modelo com dados agregados (Teste 1) apresentou melhor R².' if self.resultado_teste1['r2'] > self.resultado_teste2['r2'] else 'O modelo com dados mensais por município (Teste 2) apresentou melhor R².'}

O Teste 2 usa {self.resultado_teste2['n_obs']:,} observações (cada município em cada mês),
enquanto o Teste 1 usa apenas {self.resultado_teste1['n_obs']} observações agregadas.

A diferença de R² pode indicar que a agregação {'reduz ruído e melhora o ajuste' if self.resultado_teste1['r2'] > self.resultado_teste2['r2'] else 'remove variações importantes capturadas no nível municipal'}.
"""
            
            ax.text(0.1, 0.95, resumo, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
            
            plt.title('Resumo das Análises de Regressão', fontsize=14, fontweight='bold', pad=20)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        
        print(f"  ✓ PDF salvo: {arquivo_pdf.name}")
        return arquivo_pdf
    
    def executar(self):
        """Executa análise completa"""
        try:
            self.carregar_dados_mensais()
            self.preparar_dados_teste1()
            self.preparar_dados_teste2()
            self.executar_teste1()
            self.executar_teste2()
            csv1, csv2 = self.salvar_resultados()
            arquivo_pdf = self.gerar_relatorio_pdf()
            
            print("\n" + "="*80)
            print("✅ ANÁLISES DE REGRESSÃO LAG 3 CONCLUÍDAS COM SUCESSO!")
            print("="*80)
            print(f"\nArquivos gerados:")
            print(f"  📄 PDF:  {arquivo_pdf}")
            print(f"  📊 CSV1: {csv1}")
            print(f"  📊 CSV2: {csv2}")
            print()
            
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analisador = AnalisadorRegressaoLag3()
    analisador.executar()
