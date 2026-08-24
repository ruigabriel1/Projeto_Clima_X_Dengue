"""
Script para processar dados de temperatura e precipitação por faixas de latitude.
Cria arquivos divididos por latitude (sem transformação logarítmica) e arquivos de médias mensais.

DEPENDÊNCIA OBRIGATÓRIA:
  Execute processar_dengue_latitude_mapas.py ANTES deste script.
  Os arquivos output/csvs_latitude/dengue_faixa_latitude_*.csv devem existir
  para que o mapeamento de coordenadas dos municípios seja carregado corretamente.
"""

import logging
import sys
import pandas as pd
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# Configuração de caminhos — usa config centralizado
from src.config import DATA_RAW_DIR, OUTPUT_CSVS_LATITUDE, OUTPUT_MEDIAS_LATITUDE
DADOS_DIR = DATA_RAW_DIR
OUTPUT_DIR = OUTPUT_CSVS_LATITUDE.parent
CSVS_LATITUDE_DIR = OUTPUT_CSVS_LATITUDE
MEDIAS_LATITUDE_DIR = OUTPUT_MEDIAS_LATITUDE

# Dicionário com informações dos arquivos de clima
ARQUIVOS_CLIMA = {
    'temp_maxima': {
        'arquivo_entrada': 'Temp_maxima_MENSAL.csv',
        'coluna_valor': 'TEMP_MAXIMA',
        'prefixo_saida': 'temp_maxima'
    },
    'temp_media': {
        'arquivo_entrada': 'Temp_media_MENSAL.csv',
        'coluna_valor': 'TEMP_MEDIA',
        'prefixo_saida': 'temp_media'
    },
    'temp_minima': {
        'arquivo_entrada': 'Temp_minima_MENSAL.csv',
        'coluna_valor': 'TEMP_MINIMA',
        'prefixo_saida': 'temp_minima'
    },
    'precipitacao': {
        'arquivo_entrada': 'precipitacao_mensal_rev.csv',
        'coluna_valor': 'PRECIPITACAO_MENSAL',
        'prefixo_saida': 'precipitacao'
    }
}


def carregar_mapeamento_latitudes():
    """
    Carrega mapeamento de municípios para faixas de latitude a partir dos arquivos de dengue.
    """
    print("Carregando mapeamento de latitudes dos arquivos de dengue...")

    # Verifica dependência: arquivos de dengue por latitude devem existir
    dengue_file_check = CSVS_LATITUDE_DIR / 'dengue_faixa_latitude_1.csv'
    if not dengue_file_check.exists():
        logger.error(
            "Arquivo de dengue por latitude não encontrado: %s\n"
            "Execute 'processar_dengue_latitude_mapas.py' primeiro.",
            dengue_file_check,
        )
        sys.exit(1)
    
    # Ler todos os arquivos de dengue para ter o mapeamento completo
    mapeamento_frames = []
    for i in range(1, 9):
        dengue_file = CSVS_LATITUDE_DIR / f'dengue_faixa_latitude_{i}.csv'
        if dengue_file.exists():
            df = pd.read_csv(dengue_file)
            # Manter apenas colunas necessárias: código, nome, lat, long, faixa
            df_map = df[['CODIGO_MUNICIPIO', 'NOME_MUNICIPIO', 'LATITUDE', 'LONGITUDE', 'FAIXA_LATITUDE']].drop_duplicates()
            mapeamento_frames.append(df_map)
    
    mapeamento_completo = pd.concat(mapeamento_frames, ignore_index=True).drop_duplicates(subset=['CODIGO_MUNICIPIO'])
    print(f"Mapeamento carregado: {len(mapeamento_completo)} municípios")
    
    return mapeamento_completo


def transformar_formato_wide_para_long(arquivo_entrada, coluna_valor):
    """
    Transforma dados de formato wide (municípios como colunas) para long (municípios como linhas).
    """
    print(f"Lendo arquivo: {arquivo_entrada}")
    
    # Estrutura do arquivo:
    # Linha 0: ;;CÓDIGO DO MUNICÍPIO;410010;410020;...
    # Linha 1: municipio;;;abatia;adrianopolis;...
    # Linha 2: year;mes;;;;;;;...
    # Linha 3+: dados numéricos (2015;1;;35.2;...)
    
    # Ler os códigos de município da primeira linha
    df_codigos = pd.read_csv(DADOS_DIR / arquivo_entrada, sep=';', nrows=1, header=None)
    codigos_municipios = []
    for i in range(3, len(df_codigos.columns)):  # Começar da coluna 3 (após ;;CÓDIGO DO MUNICÍPIO)
        cod = df_codigos.iloc[0, i]
        if pd.notna(cod) and str(cod).strip() != '':
            try:
                codigos_municipios.append(int(cod))
            except:
                pass
    
    print(f"Total de municípios identificados: {len(codigos_municipios)}")
    
    # Ler os dados numéricos (a partir da linha 3, pulando as 3 primeiras linhas)
    df = pd.read_csv(DADOS_DIR / arquivo_entrada, sep=';', skiprows=3, header=None)
    
    # As colunas são: [ano, mês, coluna_vazia, valores_municipios...]
    # Remover a terceira coluna que é vazia
    df = df.drop(columns=[2])
    
    # Renomear colunas: ano, mês, e códigos de municípios
    n_colunas_dados = df.shape[1] - 2  # Excluindo ano e mês
    
    # Ajustar lista de códigos se necessário
    if n_colunas_dados < len(codigos_municipios):
        codigos_municipios = codigos_municipios[:n_colunas_dados]
    elif n_colunas_dados > len(codigos_municipios):
        # Se houver mais colunas do que códigos, truncar o dataframe
        df = df.iloc[:, :len(codigos_municipios)+2]
    
    colunas = ['ANO', 'MES'] + codigos_municipios
    df.columns = colunas
    
    print(f"Dimensões dos dados: {df.shape}")
    
    # Transformar de wide para long
    df_long = df.melt(
        id_vars=['ANO', 'MES'],
        value_vars=codigos_municipios,
        var_name='CODIGO_MUNICIPIO',
        value_name=coluna_valor
    )
    
    # Converter código de município para inteiro
    df_long['CODIGO_MUNICIPIO'] = pd.to_numeric(df_long['CODIGO_MUNICIPIO'], errors='coerce').astype('Int64')
    
    # Remover linhas com valores nulos no código do município
    df_long = df_long.dropna(subset=['CODIGO_MUNICIPIO'])
    
    # Converter valor para float
    df_long[coluna_valor] = pd.to_numeric(df_long[coluna_valor], errors='coerce')
    
    # Converter ano e mês para inteiro
    df_long['ANO'] = pd.to_numeric(df_long['ANO'], errors='coerce').astype('Int64')
    df_long['MES'] = pd.to_numeric(df_long['MES'], errors='coerce').astype('Int64')
    
    # Remover linhas com ano ou mês inválido
    df_long = df_long.dropna(subset=['ANO', 'MES'])
    
    print(f"Dimensões após transformação: {df_long.shape}")
    print(f"Período: {df_long['ANO'].min()}-{df_long['ANO'].max()}")
    
    return df_long


def processar_variavel_clima(info_arquivo, mapeamento):
    """
    Processa uma variável climática: transforma, mapeia latitudes e divide por faixas.
    """
    nome_var = info_arquivo['prefixo_saida']
    print(f"\n{'='*60}")
    print(f"Processando: {nome_var.upper()}")
    print(f"{'='*60}")
    
    # 1. Transformar de wide para long
    df_long = transformar_formato_wide_para_long(
        info_arquivo['arquivo_entrada'],
        info_arquivo['coluna_valor']
    )
    
    # 2. Adicionar informações geográficas através do mapeamento
    print("Adicionando informações geográficas...")
    df_completo = df_long.merge(
        mapeamento,
        on='CODIGO_MUNICIPIO',
        how='left'
    )
    
    # Verificar municípios sem mapeamento
    municipios_sem_map = df_completo[df_completo['FAIXA_LATITUDE'].isna()]['CODIGO_MUNICIPIO'].unique()
    if len(municipios_sem_map) > 0:
        print(f"⚠️  {len(municipios_sem_map)} municípios sem mapeamento de latitude")
    
    # Remover municípios sem mapeamento
    df_completo = df_completo.dropna(subset=['FAIXA_LATITUDE'])
    
    # 3. Dividir por faixas de latitude e salvar
    print("Salvando arquivos por faixa de latitude...")
    for faixa in range(1, 9):
        df_faixa = df_completo[df_completo['FAIXA_LATITUDE'] == faixa].copy()
        
        if len(df_faixa) > 0:
            # Ordenar por ano, mês e município
            df_faixa = df_faixa.sort_values(['ANO', 'MES', 'CODIGO_MUNICIPIO'])
            
            # Salvar arquivo individual por faixa
            arquivo_saida = CSVS_LATITUDE_DIR / f'{nome_var}_faixa_latitude_{faixa}.csv'
            df_faixa.to_csv(arquivo_saida, index=False)
            print(f"  Faixa {faixa}: {len(df_faixa)} registros → {arquivo_saida.name}")
    
    # 4. Calcular médias mensais por faixa (sem transformação logarítmica)
    print("Calculando médias mensais por faixa...")
    medias_faixas = []
    
    for faixa in range(1, 9):
        df_faixa = df_completo[df_completo['FAIXA_LATITUDE'] == faixa].copy()
        
        if len(df_faixa) > 0:
            # Calcular média mensal (valores originais, sem log)
            media_mensal = df_faixa.groupby(['FAIXA_LATITUDE', 'ANO', 'MES']).agg({
                info_arquivo['coluna_valor']: 'mean',
                'CODIGO_MUNICIPIO': 'count',
                'LATITUDE': 'mean'
            }).reset_index()
            
            # Renomear colunas
            media_mensal = media_mensal.rename(columns={
                info_arquivo['coluna_valor']: f'MEDIA_{info_arquivo["coluna_valor"]}',
                'CODIGO_MUNICIPIO': 'NUM_MUNICIPIOS_NA_MEDIA'
            })
            
            # Arredondar médias para 2 casas decimais
            media_mensal[f'MEDIA_{info_arquivo["coluna_valor"]}'] = media_mensal[f'MEDIA_{info_arquivo["coluna_valor"]}'].round(2)
            media_mensal['LATITUDE'] = media_mensal['LATITUDE'].round(6)
            
            medias_faixas.append(media_mensal)
            
            # Salvar arquivo individual de média por faixa
            arquivo_media = MEDIAS_LATITUDE_DIR / f'media_mensal_{nome_var}_faixa_latitude_{faixa}.csv'
            media_mensal.to_csv(arquivo_media, index=False)
            print(f"  Média Faixa {faixa}: {len(media_mensal)} registros → {arquivo_media.name}")
    
    # 5. Consolidar todas as médias em um único arquivo
    if medias_faixas:
        todas_medias = pd.concat(medias_faixas, ignore_index=True)
        todas_medias = todas_medias.sort_values(['FAIXA_LATITUDE', 'ANO', 'MES'])
        
        arquivo_consolidado = MEDIAS_LATITUDE_DIR / f'todas_faixas_medias_mensais_{nome_var}.csv'
        todas_medias.to_csv(arquivo_consolidado, index=False)
        print(f"  Consolidado: {len(todas_medias)} registros → {arquivo_consolidado.name}")
    
    return df_completo


def main():
    """
    Função principal que processa todos os arquivos de clima.
    """
    print("="*60)
    print("PROCESSAMENTO DE DADOS CLIMÁTICOS POR LATITUDE")
    print("="*60)
    
    # 1. Carregar mapeamento de latitudes
    try:
        mapeamento = carregar_mapeamento_latitudes()
    except FileNotFoundError as e:
        print(f"❌ ERRO: {e}")
        print("Execute primeiro o script de processamento de dengue.")
        return
    
    # 2. Processar cada variável climática
    resultados = {}
    for nome_var, info in ARQUIVOS_CLIMA.items():
        try:
            df_resultado = processar_variavel_clima(info, mapeamento)
            resultados[nome_var] = df_resultado
            print(f"✅ {nome_var.upper()} processado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao processar {nome_var}: {e}")
            import traceback
            traceback.print_exc()
    
    # 3. Resumo final
    print("\n" + "="*60)
    print("RESUMO DO PROCESSAMENTO")
    print("="*60)
    
    for nome_var, df in resultados.items():
        print(f"\n{nome_var.upper()}:")
        print(f"  Total de registros: {len(df):,}")
        print(f"  Municípios únicos: {df['CODIGO_MUNICIPIO'].nunique()}")
        print(f"  Período: {df['ANO'].min()}-{df['ANO'].max()}")
        print(f"  Arquivos gerados:")
        print(f"    - 8 arquivos por faixa de latitude em: {CSVS_LATITUDE_DIR}")
        print(f"    - 8 arquivos de médias + 1 consolidado em: {MEDIAS_LATITUDE_DIR}")
    
    print("\n✅ Processamento concluído!")


if __name__ == '__main__':
    main()
