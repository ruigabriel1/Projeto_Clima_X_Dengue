"""
Script Master - Pipeline Completo de Análise Estatística
Autor: Especialista em Ciência de Dados e Bioestatística
Objetivo: Executar pipeline completo e gerar relatório em Markdown
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import sys

# Importar classes dos outros scripts
# Adiciona src/ e seus subdiretórios ao sys.path para resolver os imports após refatoração
_src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _src_dir)
sys.path.insert(0, os.path.join(_src_dir, 'validacao'))
sys.path.insert(0, os.path.join(_src_dir, 'analises'))

from validar_integridade_dados import ValidadorIntegridadeDados
from analise_estatistica_nao_parametrica import AnalisadorEstatistico
from visualizar_dados import VisualizadorDados


class GeradorRelatorioMarkdown:
    """Classe para gerar relatório completo em Markdown"""
    
    def __init__(self, resultados_validacao, resultados_analise, arquivo_dados):
        """
        Inicializa o gerador de relatório
        
        Args:
            resultados_validacao (dict): Resultados da validação de integridade
            resultados_analise (dict): Resultados da análise estatística
            arquivo_dados (str): Caminho do arquivo de dados
        """
        self.validacao = resultados_validacao
        self.analise = resultados_analise
        self.arquivo_dados = arquivo_dados
        self.output_dir = str(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output', 'analise_estatistica'))
        
        # Criar diretório se não existir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def gerar_cabecalho(self):
        """Gera cabeçalho do relatório"""
        md = "# Relatório de Análise Estatística\n"
        md += "## Análise de Variáveis Climáticas e Casos de Dengue\n\n"
        md += "---\n\n"
        md += f"**Data da Análise:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        md += f"**Arquivo Analisado:** `{os.path.basename(self.arquivo_dados)}`\n\n"
        md += "**Metodologia:** Análise Estatística Não Paramétrica\n\n"
        md += "---\n\n"
        return md
    
    def gerar_sumario_executivo(self):
        """Gera sumário executivo"""
        md = "## Sumário Executivo\n\n"
        md += "### Objetivo\n\n"
        md += "Este relatório apresenta uma análise estatística rigorosa da relação entre "
        md += "variáveis climáticas (temperatura média, mínima, máxima e precipitação) e a "
        md += "incidência de casos de dengue, considerando também o impacto de eventos "
        md += "El Niño e La Niña.\n\n"
        
        md += "### Metodologia Aplicada\n\n"
        md += "Dada a natureza epidemiológica dos dados (que tipicamente não seguem distribuição normal), "
        md += "aplicamos **testes estatísticos não paramétricos**:\n\n"
        md += "- **Teste de Shapiro-Wilk**: Verificação de normalidade\n"
        md += "- **Correlação de Spearman (ρ)**: Medida de associação entre variáveis\n"
        md += "- **Teste Mann-Whitney U**: Comparação entre dois grupos (temperatura Alta vs Baixa)\n"
        md += "- **Teste de Kruskal-Wallis**: Comparação entre múltiplos grupos (eventos El Niño)\n"
        md += "- **Teste de Levene**: Homogeneidade de variâncias\n\n"
        
        return md
    
    def gerar_integridade_dados(self):
        """Gera seção de integridade dos dados"""
        md = "## 1. Integridade dos Dados\n\n"
        
        # Dimensões
        md += "### 1.1 Dimensões do Dataset\n\n"
        md += f"- **Total de observações:** {self.validacao.get('total_observacoes', 0):,}\n"
        md += f"- **Total de variáveis:** {self.validacao.get('total_variaveis', 0)}\n"
        
        if self.validacao.get('coluna_data'):
            md += f"- **Período analisado:** {self.validacao.get('periodo_inicio')} a "
            md += f"{self.validacao.get('periodo_fim')}\n"
        md += "\n"
        
        # Valores nulos
        md += "### 1.2 Valores Nulos\n\n"
        colunas_nulos = self.validacao.get('colunas_com_nulos', [])
        if colunas_nulos:
            md += "| Coluna | Valores Nulos | Percentual (%) |\n"
            md += "|--------|---------------|----------------|\n"
            for item in colunas_nulos:
                md += f"| {item['Coluna']} | {item['Valores Nulos']} | {item['Percentual (%)']:.2f}% |\n"
            md += "\n"
        else:
            md += "✅ **Nenhum valor nulo encontrado no dataset.**\n\n"
        
        # Outliers
        md += "### 1.3 Outliers Extremos (Casos de Dengue)\n\n"
        outliers = self.validacao.get('outliers_dengue', {})
        if outliers:
            md += f"- **Método:** {outliers.get('metodo', 'IQR')}\n"
            md += f"- **Limite Inferior:** {outliers.get('limite_inferior', 0):.2f}\n"
            md += f"- **Limite Superior:** {outliers.get('limite_superior', 0):.2f}\n"
            md += f"- **Total de outliers:** {outliers.get('total', 0)} ({outliers.get('percentual', 0):.2f}%)\n\n"
            
            if outliers.get('total', 0) > 0:
                md += "⚠️ **Nota:** Outliers identificados podem representar surtos epidêmicos ou erros de registro.\n\n"
        
        md += "---\n\n"
        return md
    
    def gerar_analise_variavel(self, var_nome):
        """
        Gera seção de análise para uma variável climática
        
        Args:
            var_nome (str): Nome da variável climática
        """
        key = f"analise_{var_nome.replace(' ', '_')}"
        if key not in self.analise:
            return ""
        
        analise_var = self.analise[key]
        
        md = f"## Análise: {var_nome.title()} vs Casos de Dengue\n\n"
        
        # Estatísticas Descritivas
        md += "### Estatísticas Descritivas\n\n"
        
        desc_var = analise_var['descritivas']
        
        md += f"#### {var_nome.title()}\n\n"
        md += "| Estatística | Valor |\n"
        md += "|-------------|-------|\n"
        if var_nome in desc_var:
            stats = desc_var[var_nome]
            md += f"| N | {stats['n_observacoes']} |\n"
            md += f"| Média | {stats['media']:.2f} |\n"
            md += f"| Desvio Padrão | {stats['desvio_padrao']:.2f} |\n"
            md += f"| Mediana | {stats['mediana']:.2f} |\n"
            md += f"| Q1 | {stats['q1']:.2f} |\n"
            md += f"| Q3 | {stats['q3']:.2f} |\n"
            md += f"| Mínimo | {stats['minimo']:.2f} |\n"
            md += f"| Máximo | {stats['maximo']:.2f} |\n"
        md += "\n"
        
        md += "#### Casos de Dengue\n\n"
        md += "| Estatística | Valor |\n"
        md += "|-------------|-------|\n"
        if 'casos_dengue' in desc_var:
            stats = desc_var['casos_dengue']
            md += f"| N | {stats['n_observacoes']} |\n"
            md += f"| Média | {stats['media']:.2f} |\n"
            md += f"| Desvio Padrão | {stats['desvio_padrao']:.2f} |\n"
            md += f"| Mediana | {stats['mediana']:.2f} |\n"
            md += f"| Q1 | {stats['q1']:.2f} |\n"
            md += f"| Q3 | {stats['q3']:.2f} |\n"
            md += f"| Mínimo | {stats['minimo']:.2f} |\n"
            md += f"| Máximo | {stats['maximo']:.2f} |\n"
        md += "\n"
        
        # Teste de Normalidade
        md += "### Teste de Normalidade\n\n"
        
        normalidade = analise_var.get('normalidade', {})
        
        md += "| Variável | Teste | Estatística | p-valor | Distribuição Normal? |\n"
        md += "|----------|-------|-------------|---------|----------------------|\n"
        
        if var_nome in normalidade:
            norm = normalidade[var_nome]
            dist_norm = "✅ Sim" if norm.get('distribuicao_normal') else "❌ Não"
            md += f"| {var_nome.title()} | {norm.get('teste', 'N/A')} | {norm.get('estatistica', 0):.4f} | "
            md += f"{norm.get('p_valor', 0):.4e} | {dist_norm} |\n"
        
        if 'casos_dengue' in normalidade:
            norm = normalidade['casos_dengue']
            dist_norm = "✅ Sim" if norm.get('distribuicao_normal') else "❌ Não"
            md += f"| Casos de Dengue | {norm.get('teste', 'N/A')} | {norm.get('estatistica', 0):.4f} | "
            md += f"{norm.get('p_valor', 0):.4e} | {dist_norm} |\n"
        
        md += "\n"
        md += "**Interpretação:** Como esperado para dados epidemiológicos, as variáveis "
        md += "**não seguem distribuição normal** (p < 0.05). Portanto, utilizamos testes não paramétricos.\n\n"
        
        # Correlação de Spearman
        md += "### Correlação de Spearman\n\n"
        
        spearman = analise_var.get('correlacao_spearman', {})
        if spearman:
            rho = spearman.get('rho', 0)
            p_val = spearman.get('p_valor', 1)
            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
            
            md += "| Métrica | Valor |\n"
            md += "|---------|-------|\n"
            md += f"| ρ (rho) | {rho:.4f} {sig} |\n"
            md += f"| p-valor | {p_val:.4e} |\n"
            md += f"| N observações | {spearman.get('n_observacoes', 0)} |\n"
            md += f"| Força da Correlação | {spearman.get('forca_correlacao', 'N/A')} |\n"
            md += f"| Direção | {spearman.get('direcao', 'N/A').capitalize()} |\n"
            md += f"| Significância Estatística | {'✅ Sim' if spearman.get('significativa') else '❌ Não'} |\n"
            md += "\n"
            
            md += f"**Interpretação:** {spearman.get('interpretacao', 'N/A')}\n\n"
            
            # Adicionar imagem do scatter plot
            img_scatter = f"scatter_{var_nome.replace(' ', '_')}_vs_dengue.png"
            md += f"![Scatter Plot - {var_nome.title()} vs Casos de Dengue]({img_scatter})\n\n"
        
        # Teste Mann-Whitney U
        md += "### Comparação de Grupos (Mann-Whitney U)\n\n"
        
        mw = analise_var.get('mann_whitney', {})
        if mw:
            md += f"**Ponto de Corte (Mediana):** {mw.get('mediana_corte', 0):.2f}\n\n"
            
            md += "#### Estatísticas por Grupo\n\n"
            md += "| Grupo | N | Média | Mediana | Desvio Padrão |\n"
            md += "|-------|---|-------|---------|---------------|\n"
            
            grupo_alta = mw.get('grupo_alta', {})
            grupo_baixa = mw.get('grupo_baixa', {})
            
            md += f"| {var_nome.title()} ALTA | {grupo_alta.get('n', 0)} | "
            md += f"{grupo_alta.get('media', 0):.2f} | {grupo_alta.get('mediana', 0):.2f} | "
            md += f"{grupo_alta.get('desvio_padrao', 0):.2f} |\n"
            
            md += f"| {var_nome.title()} BAIXA | {grupo_baixa.get('n', 0)} | "
            md += f"{grupo_baixa.get('media', 0):.2f} | {grupo_baixa.get('mediana', 0):.2f} | "
            md += f"{grupo_baixa.get('desvio_padrao', 0):.2f} |\n"
            md += "\n"
            
            md += "#### Resultado do Teste Mann-Whitney U\n\n"
            mw_teste = mw.get('mann_whitney', {})
            md += "| Métrica | Valor |\n"
            md += "|---------|-------|\n"
            md += f"| Estatística U | {mw_teste.get('estatistica_u', 0):.2f} |\n"
            md += f"| p-valor | {mw_teste.get('p_valor', 1):.4e} |\n"
            md += f"| Diferença Significativa | {'✅ Sim' if mw_teste.get('diferenca_significativa') else '❌ Não'} |\n"
            md += "\n"
            
            md += f"**Interpretação:** {mw_teste.get('interpretacao', 'N/A')}\n\n"
            
            # Teste de Levene
            levene = mw.get('teste_levene', {})
            md += "#### Teste de Levene (Homogeneidade de Variâncias)\n\n"
            md += "| Métrica | Valor |\n"
            md += "|---------|-------|\n"
            md += f"| Estatística | {levene.get('estatistica', 0):.4f} |\n"
            md += f"| p-valor | {levene.get('p_valor', 1):.4f} |\n"
            variancias = "✅ Homogêneas" if levene.get('variancias_homogeneas') else "❌ Heterogêneas"
            md += f"| Variâncias | {variancias} |\n"
            md += "\n"
            
            # Adicionar imagem do boxplot
            img_boxplot = f"boxplot_{var_nome.replace(' ', '_')}_grupos.png"
            md += f"![Boxplot - Comparação de Grupos]({img_boxplot})\n\n"
        
        md += "---\n\n"
        return md
    
    def gerar_analise_el_nino(self):
        """Gera seção de análise El Niño"""
        md = "## Análise: Eventos El Niño/La Niña vs Casos de Dengue\n\n"
        
        el_nino = self.analise.get('el_nino_analise', {})
        
        if 'erro' in el_nino:
            md += f"⚠️ **Erro:** {el_nino['erro']}\n\n"
            return md
        
        md += f"**Eventos analisados:** {', '.join(map(str, el_nino.get('eventos_analisados', [])))}\n\n"
        
        # Estatísticas por evento
        md += "### Estatísticas Descritivas por Evento\n\n"
        md += "| Evento | N | Média | Mediana | Desvio Padrão | Mínimo | Máximo |\n"
        md += "|--------|---|-------|---------|---------------|--------|--------|\n"
        
        stats_eventos = el_nino.get('estatisticas_por_evento', {})
        for evento, stats in stats_eventos.items():
            md += f"| {evento} | {stats['n']} | {stats['media']:.2f} | {stats['mediana']:.2f} | "
            md += f"{stats['desvio_padrao']:.2f} | {stats['minimo']:.0f} | {stats['maximo']:.0f} |\n"
        md += "\n"
        
        # Teste Kruskal-Wallis
        md += "### Teste Kruskal-Wallis\n\n"
        kw = el_nino.get('kruskal_wallis', {})
        
        md += "| Métrica | Valor |\n"
        md += "|---------|-------|\n"
        md += f"| Estatística H | {kw.get('estatistica_h', 0):.4f} |\n"
        md += f"| Graus de Liberdade | {kw.get('graus_liberdade', 0)} |\n"
        md += f"| p-valor | {kw.get('p_valor', 1):.4e} |\n"
        md += f"| Diferença Significativa | {'✅ Sim' if kw.get('diferenca_significativa') else '❌ Não'} |\n"
        md += "\n"
        
        md += f"**Interpretação:** {kw.get('interpretacao', 'N/A')}\n\n"
        
        # Adicionar imagens
        md += "### Visualizações\n\n"
        md += "![Gráfico de Barras - Média por Evento](barras_media_el_nino.png)\n\n"
        md += "![Série Temporal - Casos de Dengue e Eventos](serie_temporal_dengue_el_nino.png)\n\n"
        
        md += "---\n\n"
        return md
    
    def gerar_conclusao(self):
        """Gera conclusão do relatório"""
        md = "## Conclusão\n\n"
        
        md += "### Principais Achados\n\n"
        
        # Coletar correlações
        vars_clima = ['temperatura media', 'temperatura minima', 'temperatura maxima']
        if 'precipitacao' in [k.replace('analise_', '').replace('_', ' ') 
                              for k in self.analise.keys() if k.startswith('analise_')]:
            vars_clima.append('precipitacao')
        
        md += "#### 1. Correlações de Spearman\n\n"
        md += "| Variável Climática | ρ (rho) | p-valor | Força | Significância |\n"
        md += "|--------------------|---------|---------|-------|---------------|\n"
        
        for var in vars_clima:
            key = f"analise_{var.replace(' ', '_')}"
            if key in self.analise:
                spearman = self.analise[key].get('correlacao_spearman', {})
                if spearman:
                    rho = spearman.get('rho', 0)
                    p_val = spearman.get('p_valor', 1)
                    forca = spearman.get('forca_correlacao', 'N/A')
                    sig = "✅ Sim" if spearman.get('significativa') else "❌ Não"
                    md += f"| {var.title()} | {rho:.4f} | {p_val:.4e} | {forca} | {sig} |\n"
        md += "\n"
        
        md += "#### 2. Comparações de Grupos (Mann-Whitney U)\n\n"
        md += "| Variável | Grupo Alta (Média) | Grupo Baixa (Média) | p-valor | Significância |\n"
        md += "|----------|-------------------|---------------------|---------|---------------|\n"
        
        for var in vars_clima:
            key = f"analise_{var.replace(' ', '_')}"
            if key in self.analise:
                mw = self.analise[key].get('mann_whitney', {})
                if mw:
                    alta = mw.get('grupo_alta', {}).get('media', 0)
                    baixa = mw.get('grupo_baixa', {}).get('media', 0)
                    p_val = mw.get('mann_whitney', {}).get('p_valor', 1)
                    sig = "✅ Sim" if mw.get('mann_whitney', {}).get('diferenca_significativa') else "❌ Não"
                    md += f"| {var.title()} | {alta:.2f} | {baixa:.2f} | {p_val:.4e} | {sig} |\n"
        md += "\n"
        
        md += "#### 3. Eventos El Niño/La Niña\n\n"
        el_nino = self.analise.get('el_nino_analise', {})
        if 'kruskal_wallis' in el_nino:
            kw = el_nino['kruskal_wallis']
            md += f"- **Teste Kruskal-Wallis:** H = {kw.get('estatistica_h', 0):.4f}, "
            md += f"p = {kw.get('p_valor', 1):.4e}\n"
            md += f"- **Resultado:** {kw.get('interpretacao', 'N/A')}\n\n"
        
        md += "### Considerações Finais\n\n"
        md += "1. **Distribuição Não Normal:** Os dados confirmaram a natureza não paramétrica esperada "
        md += "para dados epidemiológicos, justificando o uso de testes estatísticos não paramétricos.\n\n"
        
        md += "2. **Aplicabilidade:** Os resultados podem ser utilizados para:\n"
        md += "   - Modelagem preditiva de surtos de dengue\n"
        md += "   - Planejamento de ações de saúde pública\n"
        md += "   - Sistemas de alerta precoce baseados em variáveis climáticas\n\n"
        
        md += "3. **Limitações:** É importante considerar:\n"
        md += "   - Possíveis fatores de confusão não incluídos na análise\n"
        md += "   - Variações regionais e sazonais\n"
        md += "   - Qualidade e completude dos dados epidemiológicos\n\n"
        
        md += "---\n\n"
        md += f"**Relatório gerado em:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n\n"
        md += "**Metodologia:** Análise Estatística Não Paramétrica (Spearman, Mann-Whitney U, Kruskal-Wallis)\n\n"
        
        return md
    
    def gerar_relatorio_completo(self):
        """Gera relatório completo em Markdown"""
        print("\n" + "="*80)
        print("GERANDO RELATÓRIO MARKDOWN")
        print("="*80 + "\n")
        
        md = ""
        
        # Cabeçalho
        md += self.gerar_cabecalho()
        
        # Sumário Executivo
        md += self.gerar_sumario_executivo()
        
        # Integridade dos Dados
        md += self.gerar_integridade_dados()
        
        # Análise de cada variável climática
        vars_clima = ['temperatura media', 'temperatura minima', 'temperatura maxima']
        if 'analise_precipitacao' in self.analise:
            vars_clima.append('precipitacao')
        
        for var in vars_clima:
            md += self.gerar_analise_variavel(var)
        
        # Análise El Niño
        md += self.gerar_analise_el_nino()
        
        # Conclusão
        md += self.gerar_conclusao()
        
        # Salvar arquivo
        output_file = os.path.join(self.output_dir, "RELATORIO_ANALISE_ESTATISTICA.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"✓ Relatório salvo em: {output_file}")
        print("="*80 + "\n")
        
        return output_file


def pipeline_completo(arquivo_dados):
    """
    Executa pipeline completo de análise
    
    Args:
        arquivo_dados (str): Caminho do arquivo de dados
    """
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "PIPELINE DE ANÁLISE ESTATÍSTICA COMPLETO" + " "*18 + "║")
    print("╚" + "="*78 + "╝")
    
    # Etapa 1: Validação de Integridade
    print("\n" + "="*80)
    print("ETAPA 1: VALIDAÇÃO DE INTEGRIDADE DOS DADOS")
    print("="*80)
    
    validador = ValidadorIntegridadeDados(arquivo_dados)
    resultados_validacao = validador.executar_validacao_completa()
    
    if not resultados_validacao:
        print("\n✗ Falha na validação. Encerrando análise.")
        return
    
    # Salvar resultados da validação
    with open('validacao_integridade_resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados_validacao, f, indent=4, ensure_ascii=False)
    
    # Etapa 2: Carregar dados para análise
    print("\n" + "="*80)
    print("ETAPA 2: CARREGAMENTO DE DADOS")
    print("="*80)
    
    df = pd.read_csv(arquivo_dados)
    df.columns = [col.strip().lower() for col in df.columns]
    print(f"✓ Dados carregados: {len(df)} observações, {len(df.columns)} variáveis")
    
    # Etapa 3: Análise Estatística
    print("\n" + "="*80)
    print("ETAPA 3: ANÁLISE ESTATÍSTICA NÃO PARAMÉTRICA")
    print("="*80)
    
    analisador = AnalisadorEstatistico(df)
    resultados_analise = analisador.executar_analise_completa()
    
    # Salvar resultados da análise
    with open('analise_estatistica_resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados_analise, f, indent=4, ensure_ascii=False)
    
    # Etapa 4: Visualizações
    print("\n" + "="*80)
    print("ETAPA 4: GERAÇÃO DE VISUALIZAÇÕES")
    print("="*80)
    
    visualizador = VisualizadorDados(df, resultados_analise)
    visualizador.gerar_todas_visualizacoes()
    
    # Etapa 5: Relatório Markdown
    print("\n" + "="*80)
    print("ETAPA 5: GERAÇÃO DO RELATÓRIO MARKDOWN")
    print("="*80)
    
    gerador = GeradorRelatorioMarkdown(resultados_validacao, resultados_analise, arquivo_dados)
    relatorio_path = gerador.gerar_relatorio_completo()
    
    # Finalização
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*28 + "ANÁLISE CONCLUÍDA" + " "*34 + "║")
    print("╚" + "="*78 + "╝\n")
    
    print("📊 Arquivos gerados:")
    print(f"   • Validação: validacao_integridade_resultados.json")
    print(f"   • Análise: analise_estatistica_resultados.json")
    print(f"   • Relatório: {relatorio_path}")
    print(f"   • Visualizações: ../output/analise_estatistica/\n")


def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
    else:
        # Usar arquivo padrão
        arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed', 'dados_consolidados.csv')
        print(f"⚠️  Nenhum arquivo especificado. Tentando usar: {arquivo}")
        
        if not os.path.exists(arquivo):
            print("\n" + "="*80)
            print("ERRO: ARQUIVO NÃO ENCONTRADO")
            print("="*80)
            print("\nUso: python pipeline_analise_completo.py <caminho_do_arquivo>")
            print("\nExemplo:")
            print("  python pipeline_analise_completo.py ../Dados/dados_consolidados.csv")
            print("\n" + "="*80 + "\n")
            sys.exit(1)
    
    pipeline_completo(arquivo)


if __name__ == "__main__":
    main()
