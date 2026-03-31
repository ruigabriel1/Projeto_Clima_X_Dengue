"""
Script para converter arquivos CSV para XLSX aplicando transformação logarítmica
Aplica log10(x+1) nos casos de dengue para compatibilidade com Excel
"""

import pandas as pd
import numpy as np
from pathlib import Path
from openpyxl.styles import Alignment, Font

def converter_csv_log_para_xlsx():
    """
    Converte todos os arquivos CSV da pasta csvs_latitude para XLSX
    aplicando transformação log10(x+1) nos casos de dengue
    """
    # Diretório de entrada e saída (dinâmico baseado na localização do arquivo)
    pasta_csv = Path(__file__).parent.parent.parent / "output" / "csvs_latitude"
    
    # Lista todos os arquivos CSV
    arquivos_csv = list(pasta_csv.glob("dengue_faixa_latitude_*.csv"))
    
    print(f"Encontrados {len(arquivos_csv)} arquivos CSV para converter")
    print("Aplicando transformação: log10(CASOS_DENGUE + 1)\n")
    
    for arquivo_csv in sorted(arquivos_csv):
        # Nome do arquivo de saída (substitui .csv por .xlsx)
        arquivo_xlsx = arquivo_csv.with_suffix('.xlsx')
        
        print(f"\nProcessando: {arquivo_csv.name}")
        
        try:
            # Lê o CSV
            df = pd.read_csv(arquivo_csv)
            
            print(f"  - Linhas: {len(df)}")
            print(f"  - Colunas: {list(df.columns)}")
            print(f"  - Amostra original CASOS_DENGUE: {df['CASOS_DENGUE'].head(5).tolist()}")
            
            # Aplica transformação logarítmica: log10(x + 1)
            df['CASOS_DENGUE'] = np.log10(df['CASOS_DENGUE'] + 1)
            
            print(f"  - Amostra logaritmada CASOS_DENGUE: {df['CASOS_DENGUE'].head(5).round(4).tolist()}")
            print(f"  - Amostra logaritmada CASOS_DENGUE: {df['CASOS_DENGUE'].head(5).round(4).tolist()}")
            
            # Salva como XLSX com formatação adequada
            with pd.ExcelWriter(arquivo_xlsx, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Dengue')
                
                # Acessa a planilha para formatar
                worksheet = writer.sheets['Dengue']
                
                # Formatar cabeçalho
                for cell in worksheet[1]:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Ajusta largura das colunas
                ajustes_largura = {
                    'A': 18,  # CODIGO_MUNICIPIO
                    'B': 8,   # ANO
                    'C': 8,   # MES
                    'D': 15,  # CASOS_DENGUE (logaritmado)
                    'E': 25,  # NOME_MUNICIPIO
                    'F': 12,  # LATITUDE
                    'G': 12,  # LONGITUDE
                    'H': 15,  # FAIXA_LATITUDE
                    'I': 22   # CLASSIFICACAO_VISUAL
                }
                
                for col_letter, width in ajustes_largura.items():
                    worksheet.column_dimensions[col_letter].width = width
                
                # Formatar números da coluna CASOS_DENGUE (coluna D)
                for row in range(2, len(df) + 2):
                    cell = worksheet[f'D{row}']
                    cell.number_format = '0.0000'  # 4 casas decimais
            
            print(f"  ✓ Salvo como: {arquivo_xlsx.name}")
            
        except Exception as e:
            print(f"  ✗ Erro ao processar {arquivo_csv.name}: {e}")
    
    print("\n" + "="*60)
    print("Conversão concluída!")
    print("="*60)

if __name__ == "__main__":
    converter_csv_log_para_xlsx()
