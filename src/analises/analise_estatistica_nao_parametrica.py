"""
Script de Análise Estatística Não Paramétrica
Autor: Especialista em Ciência de Dados e Bioestatística
Objetivo: Aplicar metodologia estatística rigorosa para dados epidemiológicos (distribuição não-normal)
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import shapiro, kstest, spearmanr, mannwhitneyu, kruskal, levene
import warnings
warnings.filterwarnings('ignore')


class AnalisadorEstatistico:
    """Classe para análise estatística não paramétrica de dados epidemiológicos"""
    
    def __init__(self, df):
        """
        Inicializa o analisador com o dataframe
        
        Args:
            df (pd.DataFrame): DataFrame com os dados validados
        """
        self.df = df
        self.resultados = {
            'descritivas': {},
            'normalidade': {},
            'correlacao_spearman': {},
            'mann_whitney': {},
            'kruskal_wallis': {},
            'el_nino_analise': {}
        }
        
        # Normalizar nomes das colunas
        self.df.columns = [col.strip().lower() for col in self.df.columns]
        
        # Mapeamento de compatibilidade: nomes novos → nomes antigos
        ALIAS_COLUNAS = {
            'temp_media': 'temperatura media',
            'temp_minima': 'temperatura minima',
            'temp_maxima': 'temperatura maxima',
            'incidencia_dengue': 'casos de dengue',
            'oni_index': 'el nino',
            'fase_enso': 'el nino'
        }
        for col_nova, col_antiga in ALIAS_COLUNAS.items():
            if col_nova in self.df.columns and col_antiga not in self.df.columns:
                self.df[col_antiga] = self.df[col_nova]
        
    def estatisticas_descritivas(self, coluna):
        """
        Calcula estatísticas descritivas para uma variável
        
        Args:
            coluna (str): Nome da coluna a analisar
            
        Returns:
            dict: Dicionário com estatísticas descritivas
        """
        dados = self.df[coluna].dropna()
        
        stats_desc = {
            'n_observacoes': len(dados),
            'media': float(dados.mean()),
            'desvio_padrao': float(dados.std()),
            'mediana': float(dados.median()),
            'q1': float(dados.quantile(0.25)),
            'q3': float(dados.quantile(0.75)),
            'minimo': float(dados.min()),
            'maximo': float(dados.max()),
            'iqr': float(dados.quantile(0.75) - dados.quantile(0.25))
        }
        
        return stats_desc
    
    def teste_normalidade(self, coluna, metodo='shapiro'):
        """
        Aplica teste de normalidade (Shapiro-Wilk ou Kolmogorov-Smirnov)
        
        Args:
            coluna (str): Nome da coluna
            metodo (str): 'shapiro' ou 'ks' (Kolmogorov-Smirnov)
            
        Returns:
            dict: Resultados do teste (estatística, p-valor, interpretação)
        """
        dados = self.df[coluna].dropna()
        
        if len(dados) < 3:
            return {
                'erro': 'Dados insuficientes para teste de normalidade',
                'n': len(dados)
            }
        
        if metodo == 'shapiro':
            if len(dados) > 5000:
                # Shapiro-Wilk não é recomendado para n > 5000
                metodo = 'ks'
                print(f"⚠ N > 5000. Usando Kolmogorov-Smirnov ao invés de Shapiro-Wilk")
            else:
                stat, p_value = shapiro(dados)
                teste_nome = "Shapiro-Wilk"
        
        if metodo == 'ks':
            # Normalizar dados para teste KS
            dados_norm = (dados - dados.mean()) / dados.std()
            stat, p_value = kstest(dados_norm, 'norm')
            teste_nome = "Kolmogorov-Smirnov"
        
        # Interpretação
        alpha = 0.05
        if p_value > alpha:
            interpretacao = "Dados seguem distribuição NORMAL (p > 0.05)"
            distribuicao_normal = True
        else:
            interpretacao = "Dados NÃO seguem distribuição normal (p ≤ 0.05)"
            distribuicao_normal = False
        
        return {
            'teste': teste_nome,
            'estatistica': float(stat),
            'p_valor': float(p_value),
            'alpha': alpha,
            'distribuicao_normal': distribuicao_normal,
            'interpretacao': interpretacao,
            'n_amostras': len(dados)
        }
    
    def correlacao_spearman(self, var1, var2):
        """
        Calcula correlação de Spearman entre duas variáveis
        
        Args:
            var1 (str): Nome da primeira variável
            var2 (str): Nome da segunda variável
            
        Returns:
            dict: Coeficiente de correlação, p-valor e interpretação
        """
        # Remover NaNs em ambas as variáveis
        dados_completos = self.df[[var1, var2]].dropna()
        
        if len(dados_completos) < 3:
            return {
                'erro': 'Dados insuficientes para correlação',
                'n': len(dados_completos)
            }
        
        rho, p_value = spearmanr(dados_completos[var1], dados_completos[var2])
        
        # Interpretação da força da correlação (Cohen, 1988)
        rho_abs = abs(rho)
        if rho_abs < 0.1:
            forca = "Desprezível"
        elif rho_abs < 0.3:
            forca = "Fraca"
        elif rho_abs < 0.5:
            forca = "Moderada"
        else:
            forca = "Forte"
        
        # Direção
        direcao = "positiva" if rho > 0 else "negativa"
        
        # Significância
        alpha = 0.05
        if p_value < alpha:
            significancia = f"Estatisticamente significativa (p < {alpha})"
        else:
            significancia = f"Não significativa (p ≥ {alpha})"
        
        interpretacao = f"Correlação {forca.lower()} {direcao}. {significancia}"
        
        return {
            'variavel_1': var1,
            'variavel_2': var2,
            'rho': float(rho),
            'p_valor': float(p_value),
            'n_observacoes': len(dados_completos),
            'forca_correlacao': forca,
            'direcao': direcao,
            'significativa': p_value < alpha,
            'interpretacao': interpretacao
        }
    
    def criar_grupos_temperatura(self, coluna_temp):
        """
        Cria grupos 'Alta' e 'Baixa' usando a mediana como ponto de corte
        
        Args:
            coluna_temp (str): Nome da coluna de temperatura
            
        Returns:
            pd.Series: Série com classificação 'Alta' ou 'Baixa'
        """
        mediana = self.df[coluna_temp].median()
        grupos = self.df[coluna_temp].apply(
            lambda x: 'Alta' if x >= mediana else 'Baixa' if pd.notna(x) else np.nan
        )
        return grupos, mediana
    
    def teste_mann_whitney(self, coluna_temp, coluna_resposta='casos de dengue'):
        """
        Aplica teste Mann-Whitney U para comparar dois grupos (Alta vs Baixa temperatura)
        
        Args:
            coluna_temp (str): Coluna de temperatura para criar grupos
            coluna_resposta (str): Variável resposta (casos de dengue)
            
        Returns:
            dict: Resultados do teste Mann-Whitney U
        """
        # Criar grupos
        grupos, mediana = self.criar_grupos_temperatura(coluna_temp)
        df_temp = self.df.copy()
        df_temp['grupo_temp'] = grupos
        
        # Separar dados por grupo
        grupo_alta = df_temp[df_temp['grupo_temp'] == 'Alta'][coluna_resposta].dropna()
        grupo_baixa = df_temp[df_temp['grupo_temp'] == 'Baixa'][coluna_resposta].dropna()
        
        if len(grupo_alta) < 2 or len(grupo_baixa) < 2:
            return {
                'erro': 'Grupos insuficientes para teste Mann-Whitney',
                'n_alta': len(grupo_alta),
                'n_baixa': len(grupo_baixa)
            }
        
        # Estatísticas descritivas por grupo
        media_alta = float(grupo_alta.mean())
        media_baixa = float(grupo_baixa.mean())
        mediana_alta = float(grupo_alta.median())
        mediana_baixa = float(grupo_baixa.median())
        
        # Teste Mann-Whitney U
        statistic, p_value = mannwhitneyu(grupo_alta, grupo_baixa, alternative='two-sided')
        
        # Teste de Levene (homogeneidade de variâncias)
        levene_stat, levene_p = levene(grupo_alta, grupo_baixa)
        
        # Interpretação
        alpha = 0.05
        if p_value < alpha:
            interpretacao = f"Há diferença SIGNIFICATIVA entre grupos (p < {alpha})"
            diferenca_significativa = True
        else:
            interpretacao = f"NÃO há diferença significativa entre grupos (p ≥ {alpha})"
            diferenca_significativa = False
        
        return {
            'variavel_temperatura': coluna_temp,
            'mediana_corte': float(mediana),
            'grupo_alta': {
                'n': len(grupo_alta),
                'media': media_alta,
                'mediana': mediana_alta,
                'desvio_padrao': float(grupo_alta.std())
            },
            'grupo_baixa': {
                'n': len(grupo_baixa),
                'media': media_baixa,
                'mediana': mediana_baixa,
                'desvio_padrao': float(grupo_baixa.std())
            },
            'mann_whitney': {
                'estatistica_u': float(statistic),
                'p_valor': float(p_value),
                'diferenca_significativa': diferenca_significativa,
                'interpretacao': interpretacao
            },
            'teste_levene': {
                'estatistica': float(levene_stat),
                'p_valor': float(levene_p),
                'variancias_homogeneas': levene_p > alpha
            }
        }
    
    def analise_el_nino(self, coluna_resposta='casos de dengue'):
        """
        Análise de casos de dengue por eventos El Niño/La Niña
        
        Args:
            coluna_resposta (str): Variável resposta (casos de dengue)
            
        Returns:
            dict: Estatísticas por evento e resultado do teste Kruskal-Wallis
        """
        if 'el nino' not in self.df.columns:
            return {'erro': 'Coluna "el nino" não encontrada'}
        
        # Agrupar por evento El Niño
        grupos = self.df.groupby('el nino')[coluna_resposta].apply(list).to_dict()
        
        # Remover NaNs de cada grupo
        grupos_limpos = {}
        for evento, valores in grupos.items():
            valores_limpos = [v for v in valores if pd.notna(v)]
            if len(valores_limpos) > 0:
                grupos_limpos[evento] = valores_limpos
        
        if len(grupos_limpos) < 2:
            return {
                'erro': 'Menos de 2 grupos de eventos El Niño',
                'grupos_encontrados': list(grupos_limpos.keys())
            }
        
        # Estatísticas descritivas por evento
        stats_por_evento = {}
        for evento, valores in grupos_limpos.items():
            dados_evento = pd.Series(valores)
            stats_por_evento[str(evento)] = {
                'n': len(dados_evento),
                'media': float(dados_evento.mean()),
                'mediana': float(dados_evento.median()),
                'desvio_padrao': float(dados_evento.std()),
                'minimo': float(dados_evento.min()),
                'maximo': float(dados_evento.max())
            }
        
        # Teste Kruskal-Wallis (versão não-paramétrica do ANOVA)
        valores_grupos = list(grupos_limpos.values())
        h_stat, p_value = kruskal(*valores_grupos)
        
        # Interpretação
        alpha = 0.05
        if p_value < alpha:
            interpretacao = f"Há diferença SIGNIFICATIVA entre eventos El Niño (p < {alpha})"
            diferenca_significativa = True
        else:
            interpretacao = f"NÃO há diferença significativa entre eventos (p ≥ {alpha})"
            diferenca_significativa = False
        
        return {
            'eventos_analisados': list(grupos_limpos.keys()),
            'n_eventos': len(grupos_limpos),
            'estatisticas_por_evento': stats_por_evento,
            'kruskal_wallis': {
                'estatistica_h': float(h_stat),
                'p_valor': float(p_value),
                'graus_liberdade': len(grupos_limpos) - 1,
                'diferenca_significativa': diferenca_significativa,
                'interpretacao': interpretacao
            }
        }
    
    def analise_completa_variavel_clima(self, var_clima):
        """
        Executa análise completa para uma variável climática vs casos de dengue
        
        Args:
            var_clima (str): Nome da variável climática
            
        Returns:
            dict: Resultados completos da análise
        """
        print(f"\n{'='*80}")
        print(f"ANÁLISE: {var_clima.upper()} vs CASOS DE DENGUE")
        print(f"{'='*80}")
        
        resultados = {}
        
        # 1. Estatísticas Descritivas
        print("\n1. ESTATÍSTICAS DESCRITIVAS")
        print("-" * 80)
        
        stats_clima = self.estatisticas_descritivas(var_clima)
        stats_dengue = self.estatisticas_descritivas('casos de dengue')
        
        print(f"\n{var_clima}:")
        print(f"  Média: {stats_clima['media']:.2f}")
        print(f"  Desvio Padrão: {stats_clima['desvio_padrao']:.2f}")
        print(f"  Mediana: {stats_clima['mediana']:.2f}")
        print(f"  Mínimo: {stats_clima['minimo']:.2f} | Máximo: {stats_clima['maximo']:.2f}")
        
        print(f"\nCasos de Dengue:")
        print(f"  Média: {stats_dengue['media']:.2f}")
        print(f"  Desvio Padrão: {stats_dengue['desvio_padrao']:.2f}")
        print(f"  Mediana: {stats_dengue['mediana']:.2f}")
        print(f"  Mínimo: {stats_dengue['minimo']:.2f} | Máximo: {stats_dengue['maximo']:.2f}")
        
        resultados['descritivas'] = {
            var_clima: stats_clima,
            'casos_dengue': stats_dengue
        }
        
        # 2. Teste de Normalidade
        print("\n2. TESTE DE NORMALIDADE")
        print("-" * 80)
        
        norm_clima = self.teste_normalidade(var_clima, metodo='shapiro')
        norm_dengue = self.teste_normalidade('casos de dengue', metodo='shapiro')
        
        print(f"\n{var_clima}: {norm_clima['teste']}")
        print(f"  Estatística: {norm_clima['estatistica']:.4f}")
        print(f"  p-valor: {norm_clima['p_valor']:.4e}")
        print(f"  {norm_clima['interpretacao']}")
        
        print(f"\nCasos de Dengue: {norm_dengue['teste']}")
        print(f"  Estatística: {norm_dengue['estatistica']:.4f}")
        print(f"  p-valor: {norm_dengue['p_valor']:.4e}")
        print(f"  {norm_dengue['interpretacao']}")
        
        resultados['normalidade'] = {
            var_clima: norm_clima,
            'casos_dengue': norm_dengue
        }
        
        # 3. Correlação de Spearman
        print("\n3. CORRELAÇÃO DE SPEARMAN")
        print("-" * 80)
        
        corr_spearman = self.correlacao_spearman(var_clima, 'casos de dengue')
        
        print(f"\nρ (rho) = {corr_spearman['rho']:.4f}")
        print(f"p-valor = {corr_spearman['p_valor']:.4e}")
        print(f"Força: {corr_spearman['forca_correlacao']}")
        print(f"Direção: {corr_spearman['direcao']}")
        print(f"\n{corr_spearman['interpretacao']}")
        
        resultados['correlacao_spearman'] = corr_spearman
        
        # 4. Teste Mann-Whitney U
        print("\n4. COMPARAÇÃO DE GRUPOS (Mann-Whitney U)")
        print("-" * 80)
        
        mann_whitney = self.teste_mann_whitney(var_clima)
        
        print(f"\nPonto de corte (mediana): {mann_whitney['mediana_corte']:.2f}")
        print(f"\nGrupo ALTA {var_clima}:")
        print(f"  N = {mann_whitney['grupo_alta']['n']}")
        print(f"  Média de casos: {mann_whitney['grupo_alta']['media']:.2f}")
        print(f"  Mediana de casos: {mann_whitney['grupo_alta']['mediana']:.2f}")
        
        print(f"\nGrupo BAIXA {var_clima}:")
        print(f"  N = {mann_whitney['grupo_baixa']['n']}")
        print(f"  Média de casos: {mann_whitney['grupo_baixa']['media']:.2f}")
        print(f"  Mediana de casos: {mann_whitney['grupo_baixa']['mediana']:.2f}")
        
        print(f"\nTeste Mann-Whitney U:")
        print(f"  Estatística U = {mann_whitney['mann_whitney']['estatistica_u']:.2f}")
        print(f"  p-valor = {mann_whitney['mann_whitney']['p_valor']:.4e}")
        print(f"  {mann_whitney['mann_whitney']['interpretacao']}")
        
        print(f"\nTeste de Levene (Homogeneidade de Variâncias):")
        print(f"  Estatística = {mann_whitney['teste_levene']['estatistica']:.4f}")
        print(f"  p-valor = {mann_whitney['teste_levene']['p_valor']:.4f}")
        variancias = "HOMOGÊNEAS" if mann_whitney['teste_levene']['variancias_homogeneas'] else "HETEROGÊNEAS"
        print(f"  Variâncias: {variancias}")
        
        resultados['mann_whitney'] = mann_whitney
        
        return resultados
    
    def analise_el_nino_completa(self):
        """Executa análise completa dos eventos El Niño"""
        print(f"\n{'='*80}")
        print("ANÁLISE: EVENTOS EL NIÑO vs CASOS DE DENGUE")
        print(f"{'='*80}")
        
        analise = self.analise_el_nino()
        
        if 'erro' in analise:
            print(f"\n✗ Erro: {analise['erro']}")
            return analise
        
        print(f"\nEventos analisados: {', '.join(map(str, analise['eventos_analisados']))}")
        print(f"Total de eventos: {analise['n_eventos']}")
        
        print("\nEstatísticas por Evento:")
        print("-" * 80)
        for evento, stats in analise['estatisticas_por_evento'].items():
            print(f"\n{evento}:")
            print(f"  N observações: {stats['n']}")
            print(f"  Média de casos: {stats['media']:.2f}")
            print(f"  Mediana: {stats['mediana']:.2f}")
            print(f"  Desvio Padrão: {stats['desvio_padrao']:.2f}")
            print(f"  Intervalo: [{stats['minimo']:.0f}, {stats['maximo']:.0f}]")
        
        print("\nTeste Kruskal-Wallis:")
        print("-" * 80)
        kw = analise['kruskal_wallis']
        print(f"  Estatística H = {kw['estatistica_h']:.4f}")
        print(f"  Graus de liberdade = {kw['graus_liberdade']}")
        print(f"  p-valor = {kw['p_valor']:.4e}")
        print(f"\n  {kw['interpretacao']}")
        
        return analise
    
    def executar_analise_completa(self):
        """Executa todas as análises estatísticas"""
        print("\n")
        print("╔" + "="*78 + "╗")
        print("║" + " "*18 + "ANÁLISE ESTATÍSTICA NÃO PARAMÉTRICA" + " "*25 + "║")
        print("╚" + "="*78 + "╝")
        
        # Variáveis climáticas
        vars_clima = ['temperatura media', 'temperatura minima', 'temperatura maxima']
        
        # Adicionar precipitacao se existir
        if 'precipitacao' in self.df.columns:
            vars_clima.append('precipitacao')
        
        # Análise para cada variável climática
        for var in vars_clima:
            if var in self.df.columns:
                resultado = self.analise_completa_variavel_clima(var)
                self.resultados[f'analise_{var.replace(" ", "_")}'] = resultado
        
        # Análise El Niño
        resultado_el_nino = self.analise_el_nino_completa()
        self.resultados['el_nino_analise'] = resultado_el_nino
        
        return self.resultados


def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
    else:
        arquivo = "../Dados/dados_consolidados.csv"
        print(f"⚠ Usando arquivo padrão: {arquivo}")
    
    # Carregar dados
    print(f"\nCarregando dados de: {arquivo}")
    df = pd.read_csv(arquivo)
    
    # Normalizar nomes das colunas
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Executar análise
    analisador = AnalisadorEstatistico(df)
    resultados = analisador.executar_analise_completa()
    
    # Salvar resultados
    import json
    output_file = "analise_estatistica_resultados.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)
    print(f"\n📄 Resultados salvos em: {output_file}")


if __name__ == "__main__":
    main()
