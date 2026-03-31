"""
Script de Validação de Integridade dos Dados
Autor: Especialista em Ciência de Dados e Bioestatística
Objetivo: Verificar a estrutura, consistência e qualidade dos dados antes da análise estatística
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class ValidadorIntegridadeDados:
    """Classe para validação completa da integridade dos dados epidemiológicos"""
    
    def __init__(self, arquivo_path):
        """
        Inicializa o validador com o caminho do arquivo
        
        Args:
            arquivo_path (str): Caminho para o arquivo CSV ou Excel
        """
        self.arquivo_path = arquivo_path
        self.df = None
        self.resultados = {}
        
    def carregar_dados(self):
        """Carrega o arquivo CSV ou Excel"""
        try:
            if self.arquivo_path.endswith('.csv'):
                self.df = pd.read_csv(self.arquivo_path)
                print(f"✓ Arquivo CSV carregado com sucesso")
            elif self.arquivo_path.endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(self.arquivo_path)
                print(f"✓ Arquivo Excel carregado com sucesso")
            else:
                raise ValueError("Formato não suportado. Use CSV ou Excel (.xlsx/.xls)")
            
            self.resultados['arquivo'] = self.arquivo_path
            self.resultados['formato'] = 'CSV' if self.arquivo_path.endswith('.csv') else 'Excel'
            return True
            
        except Exception as e:
            print(f"✗ Erro ao carregar arquivo: {e}")
            return False
    
    def verificar_colunas_obrigatorias(self):
        """Verifica a existência das colunas obrigatórias"""
        print("\n" + "="*80)
        print("VERIFICAÇÃO DE COLUNAS")
        print("="*80)
        
        colunas_obrigatorias = [
            'temperatura media',
            'temperatura minima', 
            'temperatura maxima',
            'casos de dengue',
            'el nino'
        ]
        
        colunas_opcionais = ['precipitacao', 'data']
        
        # Normalizar nomes das colunas (remover espaços extras, lowercase)
        colunas_presentes = [col.strip().lower() for col in self.df.columns]
        
        colunas_faltando = []
        colunas_encontradas = []
        
        print("\nColunas Obrigatórias:")
        for col in colunas_obrigatorias:
            if col.lower() in colunas_presentes:
                print(f"  ✓ '{col}' - ENCONTRADA")
                colunas_encontradas.append(col)
            else:
                print(f"  ✗ '{col}' - AUSENTE")
                colunas_faltando.append(col)
        
        print("\nColunas Opcionais:")
        for col in colunas_opcionais:
            if col.lower() in colunas_presentes:
                print(f"  ✓ '{col}' - ENCONTRADA")
                colunas_encontradas.append(col)
            else:
                print(f"  ○ '{col}' - AUSENTE (opcional)")
        
        self.resultados['colunas_obrigatorias'] = colunas_obrigatorias
        self.resultados['colunas_faltando'] = colunas_faltando
        self.resultados['colunas_encontradas'] = colunas_encontradas
        
        if colunas_faltando:
            print(f"\n⚠ ATENÇÃO: {len(colunas_faltando)} coluna(s) obrigatória(s) ausente(s)!")
            return False
        else:
            print("\n✓ Todas as colunas obrigatórias estão presentes")
            return True
    
    def processar_coluna_data(self):
        """Identifica e processa a coluna de data/tempo"""
        print("\n" + "="*80)
        print("PROCESSAMENTO DA COLUNA DE DATA")
        print("="*80)
        
        # Tentar identificar coluna de data
        colunas_possiveis = ['data', 'date', 'mes', 'month', 'ano_mes', 'periodo']
        coluna_data = None
        
        for col in self.df.columns:
            if col.strip().lower() in colunas_possiveis:
                coluna_data = col
                break
        
        if coluna_data:
            try:
                self.df[coluna_data] = pd.to_datetime(self.df[coluna_data])
                print(f"✓ Coluna '{coluna_data}' convertida para datetime")
                print(f"  Período: {self.df[coluna_data].min()} a {self.df[coluna_data].max()}")
                self.resultados['coluna_data'] = coluna_data
                self.resultados['periodo_inicio'] = str(self.df[coluna_data].min())
                self.resultados['periodo_fim'] = str(self.df[coluna_data].max())
                return True
            except Exception as e:
                print(f"✗ Erro ao converter coluna '{coluna_data}': {e}")
                return False
        else:
            print("⚠ Nenhuma coluna de data identificada")
            self.resultados['coluna_data'] = None
            return False
    
    def verificar_dimensoes(self):
        """Verifica dimensões do dataset"""
        print("\n" + "="*80)
        print("DIMENSÕES DO DATASET")
        print("="*80)
        
        n_linhas, n_colunas = self.df.shape
        print(f"\nTotal de observações: {n_linhas:,}")
        print(f"Total de variáveis: {n_colunas}")
        
        self.resultados['total_observacoes'] = n_linhas
        self.resultados['total_variaveis'] = n_colunas
        
        if n_linhas < 30:
            print("⚠ AVISO: Menos de 30 observações. Testes estatísticos podem ter baixo poder.")
        
        return True
    
    def verificar_valores_nulos(self):
        """Verifica valores nulos/faltantes em todas as colunas"""
        print("\n" + "="*80)
        print("ANÁLISE DE VALORES NULOS")
        print("="*80)
        
        nulos_por_coluna = self.df.isnull().sum()
        percent_nulos = (nulos_por_coluna / len(self.df)) * 100
        
        df_nulos = pd.DataFrame({
            'Coluna': nulos_por_coluna.index,
            'Valores Nulos': nulos_por_coluna.values,
            'Percentual (%)': percent_nulos.values
        })
        
        df_nulos = df_nulos[df_nulos['Valores Nulos'] > 0].sort_values(
            'Valores Nulos', ascending=False
        )
        
        if len(df_nulos) > 0:
            print("\nColunas com valores nulos:")
            print(df_nulos.to_string(index=False))
            print(f"\n⚠ Total: {len(df_nulos)} coluna(s) com valores faltantes")
        else:
            print("\n✓ Nenhum valor nulo encontrado no dataset!")
        
        self.resultados['colunas_com_nulos'] = df_nulos.to_dict('records')
        self.resultados['total_nulos'] = int(nulos_por_coluna.sum())
        
        return True
    
    def verificar_tipos_dados(self):
        """Verifica e valida os tipos de dados das colunas numéricas"""
        print("\n" + "="*80)
        print("VALIDAÇÃO DE TIPOS DE DADOS")
        print("="*80)
        
        colunas_numericas = [
            'temperatura media',
            'temperatura minima',
            'temperatura maxima',
            'casos de dengue'
        ]
        
        # Adicionar precipitacao se existir
        if 'precipitacao' in [col.strip().lower() for col in self.df.columns]:
            colunas_numericas.append('precipitacao')
        
        tipos_corretos = {}
        tipos_incorretos = {}
        
        for col in colunas_numericas:
            # Encontrar coluna no dataframe (case insensitive)
            col_real = None
            for c in self.df.columns:
                if c.strip().lower() == col.lower():
                    col_real = c
                    break
            
            if col_real:
                dtype = self.df[col_real].dtype
                is_numeric = pd.api.types.is_numeric_dtype(self.df[col_real])
                
                if is_numeric:
                    print(f"✓ '{col}' - Tipo: {dtype} (numérico)")
                    tipos_corretos[col] = str(dtype)
                else:
                    print(f"✗ '{col}' - Tipo: {dtype} (NÃO numérico) - ATENÇÃO!")
                    tipos_incorretos[col] = str(dtype)
                    
                    # Tentar converter
                    try:
                        self.df[col_real] = pd.to_numeric(self.df[col_real], errors='coerce')
                        print(f"  → Conversão automática aplicada")
                    except:
                        print(f"  → Falha na conversão automática")
        
        self.resultados['tipos_corretos'] = tipos_corretos
        self.resultados['tipos_incorretos'] = tipos_incorretos
        
        if tipos_incorretos:
            print(f"\n⚠ {len(tipos_incorretos)} coluna(s) com tipo incorreto detectada(s)")
            return False
        else:
            print("\n✓ Todos os tipos de dados estão corretos")
            return True
    
    def detectar_outliers(self):
        """Detecta outliers extremos em casos de dengue usando IQR"""
        print("\n" + "="*80)
        print("DETECÇÃO DE OUTLIERS EXTREMOS")
        print("="*80)
        
        # Encontrar coluna casos de dengue
        col_dengue = None
        for col in self.df.columns:
            if col.strip().lower() == 'casos de dengue':
                col_dengue = col
                break
        
        if not col_dengue:
            print("✗ Coluna 'casos de dengue' não encontrada")
            return False
        
        # Remover valores nulos temporariamente
        dados_dengue = self.df[col_dengue].dropna()
        
        if len(dados_dengue) == 0:
            print("✗ Todos os valores de casos de dengue são nulos")
            return False
        
        # Método IQR (Interquartile Range)
        Q1 = dados_dengue.quantile(0.25)
        Q3 = dados_dengue.quantile(0.75)
        IQR = Q3 - Q1
        
        limite_inferior = Q1 - 3 * IQR  # 3*IQR para outliers extremos
        limite_superior = Q3 + 3 * IQR
        
        outliers = dados_dengue[(dados_dengue < limite_inferior) | 
                                 (dados_dengue > limite_superior)]
        
        print(f"\nMétodo: IQR (Interquartile Range) - Extremos (3×IQR)")
        print(f"  Q1 (25%): {Q1:.2f}")
        print(f"  Q3 (75%): {Q3:.2f}")
        print(f"  IQR: {IQR:.2f}")
        print(f"  Limite Inferior: {limite_inferior:.2f}")
        print(f"  Limite Superior: {limite_superior:.2f}")
        print(f"\n  Outliers extremos detectados: {len(outliers)}")
        
        if len(outliers) > 0:
            print(f"  Percentual de outliers: {(len(outliers)/len(dados_dengue))*100:.2f}%")
            print(f"  Valores: {sorted(outliers.values, reverse=True)[:10]}")  # Top 10
        else:
            print("  ✓ Nenhum outlier extremo detectado")
        
        self.resultados['outliers_dengue'] = {
            'total': len(outliers),
            'percentual': (len(outliers)/len(dados_dengue))*100,
            'metodo': 'IQR (3x)',
            'limite_inferior': float(limite_inferior),
            'limite_superior': float(limite_superior)
        }
        
        return True
    
    def gerar_relatorio_sumario(self):
        """Gera um sumário final da validação"""
        print("\n" + "="*80)
        print("RESUMO DA VALIDAÇÃO")
        print("="*80)
        
        print(f"\nArquivo: {self.resultados.get('arquivo', 'N/A')}")
        print(f"Total de observações: {self.resultados.get('total_observacoes', 0):,}")
        print(f"Total de variáveis: {self.resultados.get('total_variaveis', 0)}")
        print(f"Valores nulos encontrados: {self.resultados.get('total_nulos', 0)}")
        
        if self.resultados.get('coluna_data'):
            print(f"Período: {self.resultados.get('periodo_inicio')} a {self.resultados.get('periodo_fim')}")
        
        outliers_info = self.resultados.get('outliers_dengue', {})
        print(f"Outliers extremos (dengue): {outliers_info.get('total', 0)} ({outliers_info.get('percentual', 0):.2f}%)")
        
        # Status geral
        print("\n" + "-"*80)
        colunas_faltando = self.resultados.get('colunas_faltando', [])
        tipos_incorretos = self.resultados.get('tipos_incorretos', {})
        
        if not colunas_faltando and not tipos_incorretos:
            print("STATUS FINAL: ✓ DADOS VÁLIDOS PARA ANÁLISE ESTATÍSTICA")
        else:
            print("STATUS FINAL: ⚠ AJUSTES NECESSÁRIOS ANTES DA ANÁLISE")
            if colunas_faltando:
                print(f"  - Colunas ausentes: {', '.join(colunas_faltando)}")
            if tipos_incorretos:
                print(f"  - Tipos incorretos: {', '.join(tipos_incorretos.keys())}")
        
        print("="*80 + "\n")
        
        return self.resultados
    
    def executar_validacao_completa(self):
        """Executa todas as etapas de validação"""
        print("\n")
        print("╔" + "="*78 + "╗")
        print("║" + " "*20 + "VALIDAÇÃO DE INTEGRIDADE DOS DADOS" + " "*24 + "║")
        print("╚" + "="*78 + "╝")
        
        if not self.carregar_dados():
            return None
        
        self.verificar_colunas_obrigatorias()
        self.processar_coluna_data()
        self.verificar_dimensoes()
        self.verificar_valores_nulos()
        self.verificar_tipos_dados()
        self.detectar_outliers()
        
        return self.gerar_relatorio_sumario()


def main():
    """Função principal para executar o validador"""
    import sys
    
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
    else:
        # Caminho padrão - ajustar conforme necessário
        arquivo = "../Dados/dados_consolidados.csv"
        print(f"⚠ Nenhum arquivo especificado. Usando padrão: {arquivo}")
    
    validador = ValidadorIntegridadeDados(arquivo)
    resultados = validador.executar_validacao_completa()
    
    if resultados:
        # Salvar resultados em JSON para uso posterior
        import json
        output_file = "validacao_integridade_resultados.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=4, ensure_ascii=False)
        print(f"📄 Resultados salvos em: {output_file}")


if __name__ == "__main__":
    main()
