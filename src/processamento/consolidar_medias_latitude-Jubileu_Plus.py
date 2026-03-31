"""
Script para consolidar médias mensais por faixa de latitude.
Agrupa todos os municípios de cada faixa e calcula a média mensal de casos de dengue LOGARITMIZADOS.
Aplica transformação log10(x+1) aos valores de casos antes de calcular as médias.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

def consolidar_medias_latitude():
    """
    Consolida os dados de dengue por faixa de latitude, calculando médias mensais.
    """
    # Caminhos (dinâmicos baseados na localização do arquivo)
    _base = Path(__file__).parent.parent.parent  # raiz do projeto
    pasta_entrada = _base / "output" / "csvs_latitude"
    pasta_saida = _base / "output" / "medias_latitude"
    
    # Criar pasta de saída se não existir
    pasta_saida.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("CONSOLIDAÇÃO DE MÉDIAS MENSAIS POR FAIXA DE LATITUDE")
    print("=" * 80)
    
    # Processar cada faixa de latitude (1 a 8)
    for faixa in range(1, 9):
        arquivo_entrada = pasta_entrada / f"dengue_faixa_latitude_{faixa}.csv"
        
        if not arquivo_entrada.exists():
            print(f"⚠️  Arquivo não encontrado: {arquivo_entrada.name}")
            continue
        
        print(f"\n📊 Processando Faixa {faixa}...")
        
        # Ler dados
        df = pd.read_csv(arquivo_entrada)
        
        # Informações sobre os dados originais
        num_municipios = df['CODIGO_MUNICIPIO'].nunique()
        num_registros = len(df)
        
        print(f"   • Municípios na faixa: {num_municipios}")
        print(f"   • Registros totais: {num_registros}")
        
        # Aplicar transformação logarítmica log10(x+1) aos casos de dengue
        df['CASOS_DENGUE_LOG'] = np.log10(df['CASOS_DENGUE'] + 1)
        
        # Calcular médias mensais dos valores logaritmizados
        # Agrupar por ANO e MES, calculando a média de casos de dengue logaritmizados
        df_medias = df.groupby(['ANO', 'MES']).agg({
            'CASOS_DENGUE_LOG': 'mean',
            'LATITUDE': 'mean',  # Média das latitudes (para referência)
            'FAIXA_LATITUDE': 'first'  # Manter a identificação da faixa
        }).reset_index()
        
        # Renomear coluna para deixar claro que é média dos valores log
        df_medias.rename(columns={'CASOS_DENGUE_LOG': 'MEDIA_LOG_CASOS_DENGUE'}, inplace=True)
        
        # Arredondar valores
        df_medias['MEDIA_LOG_CASOS_DENGUE'] = df_medias['MEDIA_LOG_CASOS_DENGUE'].round(4)
        df_medias['LATITUDE'] = df_medias['LATITUDE'].round(6)
        
        # Adicionar informação sobre quantos municípios estão na média
        df_medias['NUM_MUNICIPIOS_NA_MEDIA'] = num_municipios
        
        # Reordenar colunas
        df_medias = df_medias[['FAIXA_LATITUDE', 'ANO', 'MES', 'MEDIA_LOG_CASOS_DENGUE', 
                                'NUM_MUNICIPIOS_NA_MEDIA', 'LATITUDE']]
        
        # Salvar em CSV
        arquivo_csv = pasta_saida / f"media_mensal_faixa_latitude_{faixa}.csv"
        df_medias.to_csv(arquivo_csv, index=False)
        print(f"   ✅ CSV salvo: {arquivo_csv.name}")
        
        # Salvar em XLSX
        arquivo_xlsx = pasta_saida / f"media_mensal_faixa_latitude_{faixa}.xlsx"
        df_medias.to_excel(arquivo_xlsx, index=False, sheet_name=f'Faixa {faixa}')
        print(f"   ✅ XLSX salvo: {arquivo_xlsx.name}")
        
        # Estatísticas da média
        print(f"   • Períodos com dados: {len(df_medias)}")
        print(f"   • Média geral LOG: {df_medias['MEDIA_LOG_CASOS_DENGUE'].mean():.4f}")
        print(f"   • Máxima média LOG mensal: {df_medias['MEDIA_LOG_CASOS_DENGUE'].max():.4f}")
    
    print("\n" + "=" * 80)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
    print(f"📁 Arquivos salvos em: {pasta_saida}")
    print("=" * 80)
    
    # Criar um arquivo consolidado com todas as faixas
    print("\n📊 Criando arquivo consolidado com todas as faixas...")
    
    todos_dados = []
    for faixa in range(1, 9):
        arquivo_csv = pasta_saida / f"media_mensal_faixa_latitude_{faixa}.csv"
        if arquivo_csv.exists():
            df_faixa = pd.read_csv(arquivo_csv)
            todos_dados.append(df_faixa)
    
    if todos_dados:
        df_consolidado = pd.concat(todos_dados, ignore_index=True)
        df_consolidado = df_consolidado.sort_values(['ANO', 'MES', 'FAIXA_LATITUDE'])
        
        # Salvar consolidado em CSV
        arquivo_consolidado_csv = pasta_saida / "todas_faixas_medias_mensais.csv"
        df_consolidado.to_csv(arquivo_consolidado_csv, index=False)
        print(f"   ✅ CSV consolidado salvo: {arquivo_consolidado_csv.name}")
        
        # Salvar consolidado em XLSX (com uma aba para cada faixa)
        arquivo_consolidado_xlsx = pasta_saida / "todas_faixas_medias_mensais.xlsx"
        with pd.ExcelWriter(arquivo_consolidado_xlsx, engine='openpyxl') as writer:
            # Aba com todas as faixas
            df_consolidado.to_excel(writer, sheet_name='Todas as Faixas', index=False)
            
            # Aba para cada faixa individual
            for faixa in range(1, 9):
                df_faixa = df_consolidado[df_consolidado['FAIXA_LATITUDE'] == faixa]
                if not df_faixa.empty:
                    df_faixa.to_excel(writer, sheet_name=f'Faixa {faixa}', index=False)
        
        print(f"   ✅ XLSX consolidado salvo: {arquivo_consolidado_xlsx.name}")
        print(f"   • Total de registros: {len(df_consolidado)}")
    
    print("\n🎉 Processo finalizado com sucesso!")

if __name__ == "__main__":
    consolidar_medias_latitude()
