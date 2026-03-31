#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISE ECO-EPIDEMIOLÓGICA: DENGUE E VARIÁVEIS CLIMÁTICAS POR LATITUDE
=======================================================================

Autor: Cientista de Dados Sênior
Objetivo: Análise estatística automatizada com 16 baterias de testes
          (8 latitudes × 2 abordagens) gerando relatório PDF completo

Metodologia:
- Bloco A (Local): Regressão Y = f(Temperatura, Precipitação) com lags
- Bloco B (Fenômenos): Regressão Y = f(ONI - El Niño/La Niña) com lags
- Testes: Shapiro-Wilk, Pearson/Spearman, Levene, OLS
"""

import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from datetime import datetime

# Estatística e Modelagem
from scipy import stats
from scipy.stats import shapiro, pearsonr, spearmanr, levene
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan

# Visualização
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches

warnings.filterwarnings('ignore')

# ==================== CONFIGURAÇÕES ====================
BASE_DIR = Path(__file__).parent.parent.parent  # raiz do projeto
DADOS_DIR = BASE_DIR / "data" / "raw"
MEDIAS_DIR = BASE_DIR / "output" / "medias_latitude"
OUTPUT_DIR = BASE_DIR / "output" / "analise_estatistica"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_OUTPUT = OUTPUT_DIR / "Relatorio_Analise_Dengue_Latitude.pdf"

# Estilo dos gráficos
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("=" * 80)
print("ANÁLISE ECO-EPIDEMIOLÓGICA: DENGUE × CLIMA POR LATITUDE")
print("=" * 80)


# ==================== FUNÇÕES AUXILIARES ====================

def criar_lags(df, colunas, max_lag=3):
    """
    Cria colunas de lag (atraso temporal) para análise de séries temporais.
    
    Args:
        df: DataFrame com dados temporais
        colunas: Lista de colunas para criar lags
        max_lag: Número máximo de meses de atraso
    
    Returns:
        DataFrame com colunas de lag adicionadas
    """
    df = df.copy()
    
    for col in colunas:
        if col in df.columns:
            for lag in range(1, max_lag + 1):
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
    
    return df


def teste_normalidade(data, nome_var="Variável"):
    """
    Realiza teste de Shapiro-Wilk para normalidade.
    
    Args:
        data: Array de dados
        nome_var: Nome da variável para exibição
    
    Returns:
        dict com estatística W, p-valor e resultado
    """
    data_clean = data.dropna()
    
    if len(data_clean) < 3:
        return {
            'W': np.nan,
            'p_value': np.nan,
            'normal': False,
            'msg': 'Dados insuficientes'
        }
    
    try:
        W, p_value = shapiro(data_clean)
        normal = p_value > 0.05
        
        return {
            'W': W,
            'p_value': p_value,
            'normal': normal,
            'msg': 'Normal' if normal else 'Não Normal'
        }
    except Exception as e:
        return {
            'W': np.nan,
            'p_value': np.nan,
            'normal': False,
            'msg': f'Erro: {str(e)}'
        }


def calcular_correlacao(x, y, metodo='auto'):
    """
    Calcula correlação usando Pearson (se normal) ou Spearman (se não normal).
    
    Args:
        x, y: Arrays de dados
        metodo: 'auto', 'pearson' ou 'spearman'
    
    Returns:
        dict com coeficiente, p-valor e método usado
    """
    # Remove NaN
    mask = ~(pd.isna(x) | pd.isna(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        return {
            'coef': np.nan,
            'p_value': np.nan,
            'metodo': 'N/A',
            'significativo': False
        }
    
    # Decide método se auto
    if metodo == 'auto':
        # Testa normalidade de ambas
        _, p_x = shapiro(x_clean) if len(x_clean) <= 5000 else (None, 0.06)
        _, p_y = shapiro(y_clean) if len(y_clean) <= 5000 else (None, 0.06)
        
        metodo = 'pearson' if (p_x > 0.05 and p_y > 0.05) else 'spearman'
    
    try:
        if metodo == 'pearson':
            coef, p_value = pearsonr(x_clean, y_clean)
        else:
            coef, p_value = spearmanr(x_clean, y_clean)
        
        return {
            'coef': coef,
            'p_value': p_value,
            'metodo': metodo.capitalize(),
            'significativo': p_value < 0.05
        }
    except Exception as e:
        return {
            'coef': np.nan,
            'p_value': np.nan,
            'metodo': metodo,
            'significativo': False
        }


def ajustar_modelo_ols(y, X, nomes_vars):
    """
    Ajusta modelo de Regressão Linear Múltipla (OLS).
    
    Args:
        y: Variável dependente
        X: Variáveis independentes (DataFrame ou array)
        nomes_vars: Lista com nomes das variáveis
    
    Returns:
        dict com resultados do modelo
    """
    # Remove NaN
    if isinstance(X, pd.DataFrame):
        dados = pd.concat([y, X], axis=1).dropna()
        y_clean = dados.iloc[:, 0]
        X_clean = dados.iloc[:, 1:]
    else:
        mask = ~(pd.isna(y) | pd.isna(X).any(axis=1))
        y_clean = y[mask]
        X_clean = X[mask]
    
    if len(y_clean) < len(nomes_vars) + 2:
        return {
            'R2': np.nan,
            'R2_ajustado': np.nan,
            'p_valor_modelo': np.nan,
            'coeficientes': {},
            'residuos': np.array([]),
            'valido': False,
            'msg': 'Dados insuficientes'
        }
    
    try:
        # Adiciona constante
        X_const = sm.add_constant(X_clean)
        
        # Ajusta modelo
        modelo = sm.OLS(y_clean, X_const).fit()
        
        # Extrai coeficientes
        coefs = {}
        for i, nome in enumerate(['const'] + nomes_vars):
            coefs[nome] = {
                'valor': modelo.params[i],
                'p_valor': modelo.pvalues[i],
                'significativo': modelo.pvalues[i] < 0.05
            }
        
        # Teste de homocedasticidade (Breusch-Pagan)
        try:
            _, p_homo, _, _ = het_breuschpagan(modelo.resid, X_const)
            homocedastico = p_homo > 0.05
        except:
            p_homo = np.nan
            homocedastico = None
        
        return {
            'R2': modelo.rsquared,
            'R2_ajustado': modelo.rsquared_adj,
            'p_valor_modelo': modelo.f_pvalue,
            'coeficientes': coefs,
            'residuos': modelo.resid,
            'p_homocedasticidade': p_homo,
            'homocedastico': homocedastico,
            'valido': True,
            'msg': 'Modelo ajustado com sucesso',
            'modelo_completo': modelo
        }
    except Exception as e:
        return {
            'R2': np.nan,
            'R2_ajustado': np.nan,
            'p_valor_modelo': np.nan,
            'coeficientes': {},
            'residuos': np.array([]),
            'valido': False,
            'msg': f'Erro no ajuste: {str(e)}'
        }


def encontrar_melhor_lag(df, var_dependente, vars_independentes, max_lag=3):
    """
    Testa diferentes lags e retorna o que tem melhor R².
    
    Args:
        df: DataFrame com dados
        var_dependente: Nome da coluna Y
        vars_independentes: Lista de colunas X (sem lag)
        max_lag: Máximo de lags a testar
    
    Returns:
        dict com melhor lag e resultados
    """
    resultados = []
    
    for lag in range(1, max_lag + 1):
        # Cria nomes das variáveis com lag
        vars_lag = [f"{var}_lag{lag}" for var in vars_independentes]
        
        # Verifica se existem
        vars_disponiveis = [v for v in vars_lag if v in df.columns]
        
        if not vars_disponiveis:
            continue
        
        # Prepara dados
        y = df[var_dependente]
        X = df[vars_disponiveis]
        
        # Ajusta modelo
        resultado = ajustar_modelo_ols(y, X, vars_disponiveis)
        resultado['lag'] = lag
        resultado['vars_usadas'] = vars_disponiveis
        
        resultados.append(resultado)
    
    # Ordena por R² (maior primeiro)
    resultados_validos = [r for r in resultados if r['valido'] and not np.isnan(r['R2'])]
    
    if not resultados_validos:
        return {
            'melhor_lag': None,
            'melhor_R2': np.nan,
            'todos_resultados': resultados
        }
    
    resultados_validos.sort(key=lambda x: x['R2'], reverse=True)
    
    return {
        'melhor_lag': resultados_validos[0]['lag'],
        'melhor_R2': resultados_validos[0]['R2'],
        'melhor_modelo': resultados_validos[0],
        'todos_resultados': resultados
    }


# ==================== CARREGAMENTO DE DADOS ====================

def carregar_dados_completos():
    """
    Carrega e mescla todos os dados necessários: dengue, clima e ONI.
    
    Returns:
        DataFrame consolidado com todas as variáveis
    """
    print("\n[DADOS] Carregando dados...")
    
    # 1. Dengue (log-transformado)
    df_dengue = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais.csv")
    df_dengue = df_dengue[['FAIXA_LATITUDE', 'ANO', 'MES', 'MEDIA_LOG_CASOS_DENGUE']]
    df_dengue.columns = ['LATITUDE', 'ANO', 'MES', 'INCIDENCIA']
    
    # 2. Temperatura (média das 3 temperaturas)
    df_temp_max = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais_temp_maxima.csv")
    df_temp_med = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais_temp_media.csv")
    df_temp_min = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais_temp_minima.csv")
    
    # Calcula temperatura média geral
    df_temp = df_temp_med[['FAIXA_LATITUDE', 'ANO', 'MES']].copy()
    df_temp['TEMPERATURA'] = (
        df_temp_max['MEDIA_TEMP_MAXIMA'] + 
        df_temp_med['MEDIA_TEMP_MEDIA'] + 
        df_temp_min['MEDIA_TEMP_MINIMA']
    ) / 3
    df_temp.columns = ['LATITUDE', 'ANO', 'MES', 'TEMPERATURA']
    
    # 3. Precipitação
    df_precip = pd.read_csv(MEDIAS_DIR / "todas_faixas_medias_mensais_precipitacao.csv")
    df_precip = df_precip[['FAIXA_LATITUDE', 'ANO', 'MES', 'MEDIA_PRECIPITACAO_MENSAL']]
    df_precip.columns = ['LATITUDE', 'ANO', 'MES', 'PRECIPITACAO']
    
    # 4. ONI (El Niño/La Niña)
    df_oni = pd.read_csv(DADOS_DIR / "elnino_lanina_2015-2024.csv", sep=';')
    
    # Transforma ONI de wide para long
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
             'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    
    oni_long = []
    for _, row in df_oni.iterrows():
        ano = row['ANO/MES']
        if pd.notna(ano) and str(ano).isdigit():
            ano = int(ano)
            for i, mes in enumerate(meses, 1):
                if mes in row and pd.notna(row[mes]):
                    valor = str(row[mes]).replace(',', '.')
                    try:
                        oni_long.append({
                            'ANO': ano,
                            'MES': i,
                            'ONI': float(valor)
                        })
                    except:
                        pass
    
    df_oni_long = pd.DataFrame(oni_long)
    
    # 5. Merge de tudo
    print("  [MERGE] Mesclando datasets...")
    df = df_dengue.merge(df_temp, on=['LATITUDE', 'ANO', 'MES'], how='left')
    df = df.merge(df_precip, on=['LATITUDE', 'ANO', 'MES'], how='left')
    
    # Garante que ANO e MES sejam inteiros antes do merge
    df['ANO'] = df['ANO'].astype(int)
    df['MES'] = df['MES'].astype(int)
    if len(df_oni_long) > 0:
        df = df.merge(df_oni_long, on=['ANO', 'MES'], how='left')
    else:
        df['ONI'] = np.nan
    
    # Cria coluna de data
    df['DATA'] = pd.to_datetime(df['ANO'].astype(str) + '-' + df['MES'].astype(str).str.zfill(2))
    
    # Ordena por latitude e data
    df = df.sort_values(['LATITUDE', 'DATA']).reset_index(drop=True)
    
    print(f"  [OK] Dados carregados: {len(df)} registros")
    print(f"  [INFO] Latitudes: {sorted(df['LATITUDE'].unique())}")
    print(f"  [INFO] Período: {df['ANO'].min()}-{df['ANO'].max()}")
    
    return df


def preparar_dados_por_latitude(df):
    """
    Separa dados por latitude e cria lags para cada faixa.
    
    Returns:
        dict com DataFrames por latitude
    """
    print("\n[PREP] Preparando dados por latitude (criando lags)...")
    
    dados_por_lat = {}
    
    for lat in sorted(df['LATITUDE'].unique()):
        df_lat = df[df['LATITUDE'] == lat].copy()
        
        # Cria lags para variáveis climáticas
        vars_para_lag = ['TEMPERATURA', 'PRECIPITACAO', 'ONI']
        df_lat = criar_lags(df_lat, vars_para_lag, max_lag=3)
        
        # Remove linhas com muitos NaN (primeiros 3 meses)
        df_lat = df_lat.dropna(subset=['INCIDENCIA'])
        
        dados_por_lat[int(lat)] = df_lat
        
        print(f"  [LAT{int(lat)}] {len(df_lat)} observações válidas")
    
    return dados_por_lat


# ==================== ANÁLISES ESTATÍSTICAS ====================

def analisar_latitude_bloco_a(df_lat, lat_num):
    """
    BLOCO A: Regressão Local (Temperatura + Precipitação)
    
    Args:
        df_lat: DataFrame da latitude específica
        lat_num: Número da latitude
    
    Returns:
        dict com todos os resultados da análise
    """
    print(f"\n  [BLOCO-A] Local - Latitude {lat_num}")
    
    resultados = {
        'latitude': lat_num,
        'bloco': 'A - Local (Temp + Precip)',
        'n_observacoes': len(df_lat)
    }
    
    # Teste de normalidade da variável dependente
    norm_y = teste_normalidade(df_lat['INCIDENCIA'], 'Incidência')
    resultados['normalidade_y'] = norm_y
    
    # Encontra melhor lag para variáveis locais
    vars_locais = ['TEMPERATURA', 'PRECIPITACAO']
    melhor = encontrar_melhor_lag(df_lat, 'INCIDENCIA', vars_locais, max_lag=3)
    
    resultados['melhor_lag'] = melhor['melhor_lag']
    resultados['melhor_R2'] = melhor['melhor_R2']
    resultados['modelo'] = melhor.get('melhor_modelo', {})
    resultados['todos_lags'] = melhor['todos_resultados']
    
    # Correlações individuais com melhor lag
    if melhor['melhor_lag'] is not None:
        lag = melhor['melhor_lag']
        
        corr_temp = calcular_correlacao(
            df_lat[f'TEMPERATURA_lag{lag}'].values,
            df_lat['INCIDENCIA'].values,
            metodo='auto'
        )
        
        corr_precip = calcular_correlacao(
            df_lat[f'PRECIPITACAO_lag{lag}'].values,
            df_lat['INCIDENCIA'].values,
            metodo='auto'
        )
        
        resultados['correlacao_temp'] = corr_temp
        resultados['correlacao_precip'] = corr_precip
    
    return resultados


def analisar_latitude_bloco_b(df_lat, lat_num):
    """
    BLOCO B: Regressão Fenômenos (ONI - El Niño/La Niña)
    
    Args:
        df_lat: DataFrame da latitude específica
        lat_num: Número da latitude
    
    Returns:
        dict com todos os resultados da análise
    """
    print(f"  [BLOCO-B] Fenômenos - Latitude {lat_num}")
    
    resultados = {
        'latitude': lat_num,
        'bloco': 'B - Fenômenos (ONI)',
        'n_observacoes': len(df_lat)
    }
    
    # Encontra melhor lag para ONI
    melhor = encontrar_melhor_lag(df_lat, 'INCIDENCIA', ['ONI'], max_lag=3)
    
    resultados['melhor_lag'] = melhor['melhor_lag']
    resultados['melhor_R2'] = melhor['melhor_R2']
    resultados['modelo'] = melhor.get('melhor_modelo', {})
    resultados['todos_lags'] = melhor['todos_resultados']
    
    # Correlação ONI com melhor lag
    if melhor['melhor_lag'] is not None:
        lag = melhor['melhor_lag']
        
        corr_oni = calcular_correlacao(
            df_lat[f'ONI_lag{lag}'].values,
            df_lat['INCIDENCIA'].values,
            metodo='auto'
        )
        
        resultados['correlacao_oni'] = corr_oni
    
    return resultados


def executar_analise_completa(dados_por_lat):
    """
    Executa análise completa: 8 latitudes × 2 blocos = 16 testes.
    
    Returns:
        list com 16 dicionários de resultados
    """
    print("\n" + "=" * 80)
    print("EXECUTANDO 16 BATERIAS DE TESTES (8 Latitudes × 2 Blocos)")
    print("=" * 80)
    
    resultados_completos = []
    
    for lat_num in sorted(dados_por_lat.keys()):
        df_lat = dados_por_lat[lat_num]
        
        print(f"\n{'─' * 80}")
        print(f"🌍 LATITUDE {lat_num} ({len(df_lat)} observações)")
        print(f"{'─' * 80}")
        
        # Bloco A: Local (Temp + Precip)
        resultado_a = analisar_latitude_bloco_a(df_lat, lat_num)
        resultados_completos.append(resultado_a)
        
        # Bloco B: Fenômenos (ONI)
        resultado_b = analisar_latitude_bloco_b(df_lat, lat_num)
        resultados_completos.append(resultado_b)
    
    print("\n" + "=" * 80)
    print("[OK] ANÁLISE COMPLETA: 16 testes executados com sucesso!")
    print("=" * 80)
    
    return resultados_completos


# ==================== GERAÇÃO DO PDF ====================

def criar_capa_pdf(pdf, df):
    """Cria página de capa do relatório."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Título principal
    ax.text(0.5, 0.85, 'ANÁLISE ECO-EPIDEMIOLÓGICA', 
            ha='center', fontsize=26, fontweight='bold', color='#1f77b4')
    ax.text(0.5, 0.80, 'Dengue × Variáveis Climáticas por Latitude', 
            ha='center', fontsize=18, color='#333333')
    
    # Linha decorativa
    ax.plot([0.2, 0.8], [0.77, 0.77], 'k-', linewidth=2, alpha=0.3)
    
    # Informações do estudo
    periodo = f"{df['ANO'].min()}-{df['ANO'].max()}"
    n_latitudes = df['LATITUDE'].nunique()
    
    ax.text(0.5, 0.68, f'Período de Análise: {periodo}', 
            ha='center', fontsize=14, style='italic')
    ax.text(0.5, 0.64, f'Faixas de Latitude: {n_latitudes}', 
            ha='center', fontsize=14, style='italic')
    ax.text(0.5, 0.60, f'Total de Observações: {len(df):,}', 
            ha='center', fontsize=14, style='italic')
    
    # Metodologia
    ax.text(0.5, 0.50, 'METODOLOGIA ESTATÍSTICA', 
            ha='center', fontsize=16, fontweight='bold', color='#2ca02c')
    
    metodologia = [
        '• 16 Baterias de Testes (8 Latitudes × 2 Blocos)',
        '• Bloco A: Regressão Local (Temperatura + Precipitação)',
        '• Bloco B: Regressão Fenômenos (ONI - El Niño/La Niña)',
        '• Lags Temporais: 1, 2 e 3 meses',
        '• Testes: Shapiro-Wilk, Pearson/Spearman, OLS'
    ]
    
    y_pos = 0.44
    for item in metodologia:
        ax.text(0.1, y_pos, item, fontsize=11, va='top')
        y_pos -= 0.04
    
    # Nota sobre lags
    nota = ("NOTA: Variáveis climáticas apresentam efeito com atraso temporal\n"
            "sobre a incidência de dengue. Por isso, testamos lags de 1-3 meses.")
    ax.text(0.5, 0.18, nota, ha='center', fontsize=10, 
            style='italic', color='#d62728',
            bbox=dict(boxstyle='round', facecolor='#fff3cd', alpha=0.8))
    
    # Rodapé
    ax.text(0.5, 0.05, f'Relatório gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 
            ha='center', fontsize=9, color='#666666')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def criar_pagina_latitude(pdf, resultado_a, resultado_b, df_lat):
    """
    Cria página completa para uma latitude (2 blocos).
    """
    lat_num = resultado_a['latitude']
    
    fig = plt.figure(figsize=(11, 8.5))
    gs = fig.add_gridspec(4, 2, hspace=0.4, wspace=0.3)
    
    # ===== TÍTULO DA PÁGINA =====
    fig.suptitle(f'LATITUDE {lat_num} - Análise Completa', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # ===== BLOCO A: TABELA RESUMO =====
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    ax1.text(0.5, 0.9, 'BLOCO A: Local (Temp + Precip)', 
             ha='center', fontsize=12, fontweight='bold', transform=ax1.transAxes)
    
    # Dados da tabela Bloco A
    modelo_a = resultado_a.get('modelo', {})
    lag_a = resultado_a.get('melhor_lag', 'N/A')
    r2_a = resultado_a.get('melhor_R2', np.nan)
    
    tabela_a = [
        ['Métrica', 'Valor'],
        ['Melhor Lag', f'{lag_a} meses' if lag_a != 'N/A' else 'N/A'],
        ['R²', f'{r2_a:.4f}' if not np.isnan(r2_a) else 'N/A'],
        ['R² Ajust.', f'{modelo_a.get("R2_ajustado", np.nan):.4f}' if modelo_a.get('valido') else 'N/A'],
        ['p-valor', f'{modelo_a.get("p_valor_modelo", np.nan):.4f}' if modelo_a.get('valido') else 'N/A'],
        ['Normal?', resultado_a.get('normalidade_y', {}).get('msg', 'N/A')]
    ]
    
    table_a = ax1.table(cellText=tabela_a, cellLoc='left', loc='center',
                        bbox=[0.05, 0.0, 0.9, 0.8])
    table_a.auto_set_font_size(False)
    table_a.set_fontsize(9)
    table_a.scale(1, 1.8)
    
    for i in range(len(tabela_a[0])):
        table_a[(0, i)].set_facecolor('#4CAF50')
        table_a[(0, i)].set_text_props(weight='bold', color='white')
    
    # ===== BLOCO B: TABELA RESUMO =====
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    ax2.text(0.5, 0.9, 'BLOCO B: Fenomenos (ONI)', 
             ha='center', fontsize=12, fontweight='bold', transform=ax2.transAxes)
    
    # Dados da tabela Bloco B
    modelo_b = resultado_b.get('modelo', {})
    lag_b = resultado_b.get('melhor_lag', 'N/A')
    r2_b = resultado_b.get('melhor_R2', np.nan)
    
    tabela_b = [
        ['Métrica', 'Valor'],
        ['Melhor Lag', f'{lag_b} meses' if lag_b != 'N/A' else 'N/A'],
        ['R²', f'{r2_b:.4f}' if not np.isnan(r2_b) else 'N/A'],
        ['R² Ajust.', f'{modelo_b.get("R2_ajustado", np.nan):.4f}' if modelo_b.get('valido') else 'N/A'],
        ['p-valor', f'{modelo_b.get("p_valor_modelo", np.nan):.4f}' if modelo_b.get('valido') else 'N/A'],
        ['ONI Corr.', f'{resultado_b.get("correlacao_oni", {}).get("coef", np.nan):.3f}' if resultado_b.get('melhor_lag') else 'N/A']
    ]
    
    table_b = ax2.table(cellText=tabela_b, cellLoc='left', loc='center',
                        bbox=[0.05, 0.0, 0.9, 0.8])
    table_b.auto_set_font_size(False)
    table_b.set_fontsize(9)
    table_b.scale(1, 1.8)
    
    for i in range(len(tabela_b[0])):
        table_b[(0, i)].set_facecolor('#2196F3')
        table_b[(0, i)].set_text_props(weight='bold', color='white')
    
    # ===== SÉRIE TEMPORAL: DENGUE =====
    ax3 = fig.add_subplot(gs[1, :])
    ax3.plot(df_lat['DATA'], df_lat['INCIDENCIA'], 
             marker='o', linewidth=2, markersize=4, color='#d62728', label='Incidência Dengue')
    ax3.set_xlabel('Data', fontsize=10)
    ax3.set_ylabel('Incidência (log)', fontsize=10)
    ax3.set_title('Série Temporal: Incidência de Dengue', fontsize=11, fontweight='bold')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    # ===== SÉRIE TEMPORAL: CLIMA COM MELHOR LAG =====
    ax4 = fig.add_subplot(gs[2, :])
    
    if lag_a != 'N/A' and lag_a is not None:
        ax4_twin = ax4.twinx()
        
        # Temperatura com lag
        ax4.plot(df_lat['DATA'], df_lat[f'TEMPERATURA_lag{lag_a}'], 
                color='#ff7f0e', linewidth=2, label=f'Temperatura (lag {lag_a}m)', alpha=0.8)
        ax4.set_ylabel('Temperatura (°C)', fontsize=10, color='#ff7f0e')
        ax4.tick_params(axis='y', labelcolor='#ff7f0e')
        
        # Precipitação com lag
        ax4_twin.bar(df_lat['DATA'], df_lat[f'PRECIPITACAO_lag{lag_a}'], 
                    width=20, color='#1f77b4', alpha=0.4, label=f'Precipitação (lag {lag_a}m)')
        ax4_twin.set_ylabel('Precipitação (mm)', fontsize=10, color='#1f77b4')
        ax4_twin.tick_params(axis='y', labelcolor='#1f77b4')
        
        ax4.set_xlabel('Data', fontsize=10)
        ax4.set_title(f'Variáveis Climáticas com Lag Ótimo ({lag_a} meses)', 
                     fontsize=11, fontweight='bold')
        
        # Legenda combinada
        lines1, labels1 = ax4.get_legend_handles_labels()
        lines2, labels2 = ax4_twin.get_legend_handles_labels()
        ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)
    else:
        ax4.text(0.5, 0.5, 'Dados insuficientes para plotar clima com lag', 
                ha='center', va='center', transform=ax4.transAxes, fontsize=10)
    
    ax4.grid(True, alpha=0.3)
    
    # ===== MATRIZ DE CORRELAÇÃO (Bloco A) =====
    ax5 = fig.add_subplot(gs[3, 0])
    
    if lag_a != 'N/A' and lag_a is not None:
        # Prepara dados de correlação
        vars_corr = ['INCIDENCIA', f'TEMPERATURA_lag{lag_a}', f'PRECIPITACAO_lag{lag_a}']
        df_corr = df_lat[vars_corr].dropna()
        
        if len(df_corr) > 3:
            corr_matrix = df_corr.corr(method='spearman')
            
            im = ax5.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
            
            # Labels
            labels = ['Dengue', f'Temp\n(lag{lag_a})', f'Precip\n(lag{lag_a})']
            ax5.set_xticks(range(3))
            ax5.set_yticks(range(3))
            ax5.set_xticklabels(labels, fontsize=8)
            ax5.set_yticklabels(labels, fontsize=8)
            
            # Valores
            for i in range(3):
                for j in range(3):
                    ax5.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                            ha="center", va="center", color="black", fontsize=9)
            
            ax5.set_title('Correlação (Spearman)\nBloco A', fontsize=10, fontweight='bold')
        else:
            ax5.text(0.5, 0.5, 'Dados insuficientes', 
                    ha='center', va='center', transform=ax5.transAxes)
    else:
        ax5.text(0.5, 0.5, 'Modelo não ajustado', 
                ha='center', va='center', transform=ax5.transAxes)
    
    # ===== CONCLUSÃO =====
    ax6 = fig.add_subplot(gs[3, 1])
    ax6.axis('off')
    
    # Monta texto de conclusão
    conclusao = f"LATITUDE {lat_num} - CONCLUSÃO\n\n"
    
    if lag_a != 'N/A' and not np.isnan(r2_a):
        conclusao += f"✓ Bloco A: Lag {lag_a}m explica {r2_a*100:.1f}% da variação\n"
        
        if r2_a > 0.5:
            conclusao += "  → Relação FORTE entre clima local e dengue\n"
        elif r2_a > 0.3:
            conclusao += "  → Relação MODERADA\n"
        else:
            conclusao += "  → Relação FRACA\n"
    else:
        conclusao += "✗ Bloco A: Modelo não significativo\n"
    
    conclusao += "\n"
    
    if lag_b != 'N/A' and not np.isnan(r2_b):
        conclusao += f"✓ Bloco B: ONI (lag {lag_b}m) R²={r2_b:.3f}\n"
        
        corr_oni = resultado_b.get('correlacao_oni', {}).get('coef', np.nan)
        if not np.isnan(corr_oni):
            if corr_oni > 0:
                conclusao += f"  → El Niño favorece dengue (ρ={corr_oni:.3f})\n"
            else:
                conclusao += f"  → La Niña reduz dengue (ρ={corr_oni:.3f})\n"
    else:
        conclusao += "✗ Bloco B: ONI não significativo\n"
    
    ax6.text(0.05, 0.95, conclusao, 
            va='top', ha='left', fontsize=9, family='monospace',
            transform=ax6.transAxes,
            bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def gerar_relatorio_pdf(resultados, dados_por_lat, df_original):
    """
    Gera relatório PDF completo com todas as análises.
    """
    print("\n" + "=" * 80)
    print("[PDF] GERANDO RELATORIO PDF")
    print("=" * 80)
    
    with PdfPages(PDF_OUTPUT) as pdf:
        # Página 1: Capa
        print("  → Página 1: Capa")
        criar_capa_pdf(pdf, df_original)
        
        # Páginas 2-9: Uma por latitude
        latitudes = sorted(dados_por_lat.keys())
        
        for i, lat in enumerate(latitudes, 2):
            print(f"  [Pag {i}] Latitude {lat}")
            
            # Pega resultados dos 2 blocos
            idx_base = (lat - 1) * 2
            resultado_a = resultados[idx_base]
            resultado_b = resultados[idx_base + 1]
            
            df_lat = dados_por_lat[lat]
            
            criar_pagina_latitude(pdf, resultado_a, resultado_b, df_lat)
        
        # Página final: Sumário executivo
        print(f"  [Pag {len(latitudes) + 2}] Sumario Executivo")
        criar_pagina_sumario(pdf, resultados)
    
    print(f"\n[OK] PDF gerado com sucesso!")
    print(f"   [FILE] {PDF_OUTPUT}")
    print("=" * 80)


def criar_pagina_sumario(pdf, resultados):
    """Cria página de sumário executivo comparando todas as latitudes."""
    fig = plt.figure(figsize=(11, 8.5))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    fig.suptitle('SUMÁRIO EXECUTIVO - Comparação entre Latitudes', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Extrai dados para comparação
    latitudes = []
    r2_bloco_a = []
    r2_bloco_b = []
    lag_bloco_a = []
    lag_bloco_b = []
    
    for i in range(0, len(resultados), 2):
        res_a = resultados[i]
        res_b = resultados[i + 1]
        
        latitudes.append(res_a['latitude'])
        r2_bloco_a.append(res_a.get('melhor_R2', 0))
        r2_bloco_b.append(res_b.get('melhor_R2', 0))
        lag_bloco_a.append(res_a.get('melhor_lag', 0))
        lag_bloco_b.append(res_b.get('melhor_lag', 0))
    
    # Gráfico 1: Comparação R² Bloco A
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.bar(latitudes, r2_bloco_a, color='#4CAF50', alpha=0.7)
    ax1.set_xlabel('Latitude', fontsize=10)
    ax1.set_ylabel('R²', fontsize=10)
    ax1.set_title('Bloco A: R² por Latitude\n(Temp + Precip)', fontsize=11, fontweight='bold')
    ax1.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='R²=0.5')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Gráfico 2: Comparação R² Bloco B
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.bar(latitudes, r2_bloco_b, color='#2196F3', alpha=0.7)
    ax2.set_xlabel('Latitude', fontsize=10)
    ax2.set_ylabel('R²', fontsize=10)
    ax2.set_title('Bloco B: R² por Latitude\n(ONI)', fontsize=11, fontweight='bold')
    ax2.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='R²=0.5')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Gráfico 3: Lags ótimos Bloco A
    ax3 = fig.add_subplot(gs[1, 0])
    lags_validos_a = [l if l is not None else 0 for l in lag_bloco_a]
    ax3.scatter(latitudes, lags_validos_a, s=100, c='#4CAF50', alpha=0.7)
    ax3.set_xlabel('Latitude', fontsize=10)
    ax3.set_ylabel('Lag Ótimo (meses)', fontsize=10)
    ax3.set_title('Bloco A: Lag Ótimo por Latitude', fontsize=11, fontweight='bold')
    ax3.set_yticks([1, 2, 3])
    ax3.grid(True, alpha=0.3)
    
    # Gráfico 4: Lags ótimos Bloco B
    ax4 = fig.add_subplot(gs[1, 1])
    lags_validos_b = [l if l is not None else 0 for l in lag_bloco_b]
    ax4.scatter(latitudes, lags_validos_b, s=100, c='#2196F3', alpha=0.7)
    ax4.set_xlabel('Latitude', fontsize=10)
    ax4.set_ylabel('Lag Ótimo (meses)', fontsize=10)
    ax4.set_title('Bloco B: Lag Ótimo por Latitude', fontsize=11, fontweight='bold')
    ax4.set_yticks([1, 2, 3])
    ax4.grid(True, alpha=0.3)
    
    # Tabela resumo
    ax5 = fig.add_subplot(gs[2, :])
    ax5.axis('off')
    
    tabela_resumo = [['Lat', 'R² Bloco A', 'Lag A', 'R² Bloco B', 'Lag B', 'Melhor Abordagem']]
    
    for i, lat in enumerate(latitudes):
        r2_a = r2_bloco_a[i]
        r2_b = r2_bloco_b[i]
        lag_a = lag_bloco_a[i] if lag_bloco_a[i] is not None else '-'
        lag_b = lag_bloco_b[i] if lag_bloco_b[i] is not None else '-'
        
        if not np.isnan(r2_a) and not np.isnan(r2_b):
            melhor = 'Local' if r2_a > r2_b else 'ONI'
        elif not np.isnan(r2_a):
            melhor = 'Local'
        elif not np.isnan(r2_b):
            melhor = 'ONI'
        else:
            melhor = 'N/A'
        
        tabela_resumo.append([
            str(lat),
            f'{r2_a:.3f}' if not np.isnan(r2_a) else 'N/A',
            str(lag_a),
            f'{r2_b:.3f}' if not np.isnan(r2_b) else 'N/A',
            str(lag_b),
            melhor
        ])
    
    table = ax5.table(cellText=tabela_resumo, cellLoc='center', loc='center',
                      bbox=[0.1, 0.1, 0.8, 0.8])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Formata header
    for i in range(6):
        table[(0, i)].set_facecolor('#FF9800')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


# ==================== FUNÇÃO PRINCIPAL ====================

def main():
    """Função principal que orquestra toda a análise."""
    
    try:
        # 1. Carrega dados
        df = carregar_dados_completos()
        
        # 2. Prepara dados por latitude (com lags)
        dados_por_lat = preparar_dados_por_latitude(df)
        
        # 3. Executa 16 análises (8 lat × 2 blocos)
        resultados = executar_analise_completa(dados_por_lat)
        
        # 4. Gera PDF
        gerar_relatorio_pdf(resultados, dados_por_lat, df)
        
        # 5. Salva resultados em JSON (backup)
        import json
        
        # Serializa resultados (converte arrays numpy para listas)
        def serializar(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, (bool, np.bool_)):
                return bool(obj)
            elif pd.isna(obj):
                return None
            return obj
        
        resultados_json = []
        for r in resultados:
            r_clean = {}
            for k, v in r.items():
                if k not in ['modelo', 'todos_lags']:  # Pula objetos complexos
                    r_clean[k] = serializar(v) if not isinstance(v, dict) else {
                        k2: serializar(v2) for k2, v2 in v.items()
                    }
            resultados_json.append(r_clean)
        
        json_path = OUTPUT_DIR / "resultados_analise.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(resultados_json, f, indent=2, ensure_ascii=False)
        
        print(f"\n[JSON] Resultados salvos: {json_path}")
        
        print("\n" + "=" * 80)
        print("ANALISE COMPLETA FINALIZADA COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERRO] ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
