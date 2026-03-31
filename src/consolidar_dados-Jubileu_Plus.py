#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Final de Consolidação - Versão Funcional
Consolida dados meteorológicos e epidemiológicos para análise estat

ística
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path

# Configurações
PASTA_DADOS = Path(__file__).parent.parent / "data" / "raw"
ARQUIVO_SAIDA = Path(__file__).parent.parent / "data" / "processed" / "dados_consolidados.csv"

def carregar_dados_wide_temperatura_dengue(arquivo, tipo_dado):
    """Carrega CSVs de temperatura e dengue (formato wide)"""
    # Lê CSV pulando as 2 primeiras linhas (cabeçalho)
    df = pd.read_csv(arquivo, sep=';', skiprows=2)
    
    # Renomeia primeiras colunas
    df = df.rename(columns={df.columns[0]: 'year', df.columns[1]: 'mes'})
    
    # Cria data
    df['data'] = pd.to_datetime(df['year'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2), format='%Y-%m', errors='coerce')
    
    # Seleciona colunas numéricas (municípios)
    colunas_excluir = ['year', 'mes', 'data', 'municipio', 'CÓDIGO DO MUNICÍPIO', 'Unnamed: 0']
    colunas_municipios = [col for col in df.columns if col not in colunas_excluir]
    
    # Converte para numérico e calcula média
    df_numeric = df[colunas_municipios].apply(pd.to_numeric, errors='coerce')
    df[tipo_dado] = df_numeric.mean(axis=1, skipna=True)
    
    return df[['data', tipo_dado]].dropna(subset=['data'])

def carregar_precipitacao(arquivo):
    """Carrega CSV de precipitação (tem header diferente)"""
    # Lê CSV
    df = pd.read_csv(arquivo, sep=';')
    
    # Remove coluna Unnamed se existir
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    
    # Identifica colunas year e mes (geralmente últimas 2 linhas são cabeçalho)
    if 'year' not in df.columns:
        # As 2 primeiras linhas têm info, vamos pegar da linha 2 em diante
        df = pd.read_csv(arquivo, sep=';', skiprows=2)
        df = df.rename(columns={df.columns[0]: 'year', df.columns[1]: 'mes'})
    
    # Cria data
    df['data'] = pd.to_datetime(df['year'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2), format='%Y-%m', errors='coerce')
    
    # Seleciona colunas numéricas
    colunas_excluir = ['year', 'mes', 'data', 'municipio', 'CÓDIGO DO MUNICÍPIO', 'Unnamed: 0']
    colunas_municipios = [col for col in df.columns if col not in colunas_excluir]
    
    # Média
    df_numeric = df[colunas_municipios].apply(pd.to_numeric, errors='coerce')
    df['precipitacao'] = df_numeric.mean(axis=1, skipna=True)
    
    return df[['data', 'precipitacao']].dropna(subset=['data'])

def carregar_elnino(arquivo):
    """Carrega dados de El Niño/La Niña"""
    # Lê CSV
    df = pd.read_csv(arquivo, sep=';')
    
    # Estrutura: primeira coluna é ANO/MES, demais são meses
    # Transforma de wide para long
    df = df.rename(columns={df.columns[0]: 'ano'})
    
    # Remove colunas vazias
    df = df.dropna(axis=1, how='all')
    
    # Melt para formato long
    meses_map = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    colunas_meses = [col for col in df.columns if col.lower() in meses_map]
    
    df_long = df.melt(id_vars=['ano'], value_vars=colunas_meses, 
                      var_name='mes_nome', value_name='oni_index')
    
    # Mapeia nome do mês para número
    df_long['mes'] = df_long['mes_nome'].str.lower().map(meses_map)
    
    # Cria data
    df_long['data'] = pd.to_datetime(df_long['ano'].astype(str) + '-' + df_long['mes'].astype(str).str.zfill(2), 
                                     format='%Y-%m', errors='coerce')
    
    # Converte ONI para numérico (trata vírgulas)
    df_long['oni_index'] = df_long['oni_index'].astype(str).str.replace(',', '.').astype(float, errors='ignore')
    
    # Classifica fase ENSO
    def classificar_enso(oni):
        if pd.isna(oni):
            return 'Neutro'
        if oni >= 0.5:
            return 'El Niño'
        elif oni <= -0.5:
            return 'La Niña'
        else:
            return 'Neutro'
    
    df_long['fase_enso'] = df_long['oni_index'].apply(classificar_enso)
    
    return df_long[['data', 'oni_index', 'fase_enso']].dropna(subset=['data'])

def main():
    """Função principal"""
    print("=" * 80)
    print("CONSOLIDAÇÃO FINAL DE DADOS PARA ANÁLISE ESTATÍSTICA")
    print("=" * 80)
    
    try:
        # 1. Temperatura
        print("\n📊 Carregando temperaturas...")
        df_temp_media = carregar_dados_wide_temperatura_dengue(
            PASTA_DADOS / 'Temp_media_MENSAL.csv', 'temp_media')
        df_temp_minima = carregar_dados_wide_temperatura_dengue(
            PASTA_DADOS / 'Temp_minima_MENSAL.csv', 'temp_minima')
        df_temp_maxima = carregar_dados_wide_temperatura_dengue(
            PASTA_DADOS / 'Temp_maxima_MENSAL.csv', 'temp_maxima')
        print(f"  ✓ Temperaturas carregadas")
        
        # 2. Dengue
        print("\n🦟 Carregando dados de dengue...")
        df_dengue = carregar_dados_wide_temperatura_dengue(
            PASTA_DADOS / 'dengue_MENSAL.csv', 'incidencia_dengue')
        print(f"  ✓ Dengue carregada: {len(df_dengue)} registros")
        
        # 3. Precipitação
        print("\n🌧 Carregando precipitação...")
        df_precip = carregar_precipitacao(PASTA_DADOS / 'precipitacao_mensal_rev.csv')
        print(f"  ✓ Precipitação carregada: {len(df_precip)} registros")
        
        # 4. El Niño/La Niña
        print("\n🌊 Carregando El Niño/La Niña...")
        df_elnino = carregar_elnino(PASTA_DADOS / 'elnino_lanina_2015-2024.csv')
        print(f"  ✓ ENSO carregado: {len(df_elnino)} registros")
        
        # 5. Consolida tudo
        print("\n🔗 Consolidando dados...")
        df_final = df_temp_media
        for df in [df_temp_minima, df_temp_maxima, df_dengue, df_precip, df_elnino]:
            df_final = df_final.merge(df, on='data', how='outer')
        
        # Ordena por data
        df_final = df_final.sort_values('data').reset_index(drop=True)
        
        # Adiciona colunas derivadas
        df_final['ano'] = df_final['data'].dt.year
        df_final['mes'] = df_final['data'].dt.month
        df_final['trimestre'] = df_final['data'].dt.quarter
        df_final['estacao'] = df_final['mes'].apply(lambda x: 
            'Verão' if x in [12, 1, 2] else
            'Outono' if x in [3, 4, 5] else
            'Inverno' if x in [6, 7, 8] else 'Primavera')
        
        # Remove linhas sem dados essenciais
        df_final = df_final.dropna(subset=['temp_media', 'incidencia_dengue'], how='all')
        
        # Criar variáveis com LAG temporal (importante para dengue!)
        print(f"\n📊 Criando variáveis com LAG temporal (2 e 3 meses)...")
        df_final = df_final.sort_values('data').reset_index(drop=True)
        
        # LAG de 2 meses (correlação significativa)
        df_final['temp_media_lag2'] = df_final['temp_media'].shift(2)
        df_final['temp_minima_lag2'] = df_final['temp_minima'].shift(2)
        df_final['temp_maxima_lag2'] = df_final['temp_maxima'].shift(2)
        df_final['precipitacao_lag2'] = df_final['precipitacao'].shift(2)
        
        # LAG de 3 meses (correlação forte)
        df_final['temp_media_lag3'] = df_final['temp_media'].shift(3)
        df_final['temp_minima_lag3'] = df_final['temp_minima'].shift(3)
        df_final['temp_maxima_lag3'] = df_final['temp_maxima'].shift(3)
        df_final['precipitacao_lag3'] = df_final['precipitacao'].shift(3)
        
        print(f"  ✓ Variáveis LAG criadas (primeiros 2-3 meses terão NaN)")
        
        # Salva
        print(f"\n💾 Salvando dados consolidados...")
        df_final.to_csv(ARQUIVO_SAIDA, index=False)
        
        print(f"\n✅ SUCESSO!")
        print(f"  📁 Arquivo: {ARQUIVO_SAIDA}")
        print(f"  📊 Registros: {len(df_final)}")
        print(f"  📅 Período: {df_final['data'].min().strftime('%Y-%m')} até {df_final['data'].max().strftime('%Y-%m')}")
        print(f"  🏷 Colunas: {list(df_final.columns)}")
        
        # Estatísticas
        print("\n📈 Resumo Estatístico:")
        print(df_final[['temp_media', 'temp_minima', 'temp_maxima', 'incidencia_dengue', 'precipitacao', 'oni_index']].describe())
        
        print("\n" + "=" * 80)
        return df_final
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    df = main()
