# Graph Report - Projeto_Clima_X_Dengue  (2026-09-04)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 618 nodes · 1091 edges · 29 communities (27 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 17 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5232f807`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- motor_lote_modelagem_v2_por_latitude.py
- gerar_relatorio_abnt_projecoes_ssp.py
- VisualizadorDados
- gerar_relatorio_abnt_sem_incremento.py
- AnalisadorRegressaoMultipla
- analise_dengue_latitude_pdf.py
- GeradorMapasAnuais
- AnalisadorENSOLatitude
- ValidadorIntegridadeDados
- AnalisadorEstatistico
- AnalisadorRegressaoLag3
- processar_clima_por_latitude.py
- gerar_relatorios_latitude_individuais.py
- AnalisadorENSOLatitudeParametrico
- analise_global_dengue_log_pdf.py
- MapaTemperaturas
- validar_todas_tarefas.py
- gerar_relatorio_pdf.py
- gerar_mapas_municipios_latitude.py
- validar_mapas_latitude.py
- gerar_paineis_comparativos.py
- gerar_mapas_faixas_latitude.py
- loaders.py
- criar_mapa_dengue_agregado_total.py
- main.py
- consolidar_medias_latitude.py
- converter_csv_para_xlsx_log.py
- criar_cache_geodados.py

## God Nodes (most connected - your core abstractions)
1. `generate()` - 23 edges
2. `generate()` - 21 edges
3. `AnalisadorRegressaoMultipla` - 19 edges
4. `GeradorMapasAnuais` - 15 edges
5. `AnalisadorENSOLatitude` - 14 edges
6. `ValidadorIntegridadeDados` - 14 edges
7. `AnalisadorEstatistico` - 14 edges
8. `_h1()` - 14 edges
9. `_h1()` - 14 edges
10. `AnalisadorRegressaoLag3` - 13 edges

## Surprising Connections (you probably didn't know these)
- `pipeline_completo()` --uses--> `ValidadorIntegridadeDados`  [INFERRED]
  src/pipeline.py → src/validacao/validar_integridade_dados.py
- `pipeline_completo()` --uses--> `AnalisadorEstatistico`  [INFERRED]
  src/pipeline.py → src/analises/analise_estatistica_nao_parametrica.py
- `pipeline_completo()` --uses--> `VisualizadorDados`  [INFERRED]
  src/pipeline.py → src/validacao/visualizar_dados.py
- `build_dw()` --calls--> `build_base_panel()`  [EXTRACTED]
  src/processamento/build_data_warehouse.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `main()` --calls--> `build_base_panel()`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_sem_incremento.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py

## Import Cycles
- None detected.

## Communities (29 total, 1 thin omitted)

### Community 0 - "motor_lote_modelagem_v2_por_latitude.py"
Cohesion: 0.09
Nodes (56): ndarray, build_dw(), Pipeline ETL para criação do Data Warehouse Analítico (SQLite). Lê arquivos CSV…, build_base_panel(), build_code_lookup_from_latitude_files(), _build_ml_features(), build_monthly_climatology(), build_yearly_templates() (+48 more)

### Community 1 - "gerar_relatorio_abnt_projecoes_ssp.py"
Cohesion: 0.14
Nodes (45): _add_chart(), _add_footer_page_number(), _body(), _body_ni(), _fmt(), generate(), _h1(), _h2() (+37 more)

### Community 2 - "VisualizadorDados"
Cohesion: 0.06
Nodes (26): GeradorRelatorioMarkdown, main(), pipeline_completo(), Script Master - Pipeline Completo de Análise Estatística Autor: Especialista em…, Gera seção de análise para uma variável climática Args: var_nome (str): Nome da…, Classe para gerar relatório completo em Markdown, Gera seção de análise El Niño, Inicializa o gerador de relatório Args: resultados_validacao (dict): Resultados… (+18 more)

### Community 3 - "gerar_relatorio_abnt_sem_incremento.py"
Cohesion: 0.19
Nodes (40): _add_chart(), _add_footer_page_number(), _body(), _body_ni(), _fmt(), generate(), _h1(), _h2() (+32 more)

### Community 4 - "AnalisadorRegressaoMultipla"
Cohesion: 0.08
Nodes (17): AnalisadorRegressaoMultipla, Script para Análise de Regressão Linear Múltipla + PDF Usa TODAS as variáveis…, Estatísticas descritivas das variáveis, Ajusta modelo de regressão linear múltipla, Análise de diagnóstico dos resíduos, Análise de Regressão Linear Múltipla com todas as variáveis climáticas, Análise de importância das variáveis, Cria PDF com todos os resultados (+9 more)

### Community 5 - "analise_dengue_latitude_pdf.py"
Cohesion: 0.10
Nodes (30): ajustar_modelo_ols(), analisar_latitude_bloco_a(), analisar_latitude_bloco_b(), calcular_correlacao(), carregar_dados_completos(), criar_capa_pdf(), criar_lags(), criar_pagina_latitude() (+22 more)

### Community 6 - "GeradorMapasAnuais"
Cohesion: 0.10
Nodes (16): GeradorMapasAnuais, main(), Gerador de Mapas Anuais - Região Sul do Brasil…, Carrega dados de dengue, Carrega dados de precipitação, Calcula a média anual para cada município Args: df: DataFrame com os dados…, Cria um mapa com os dados fornecidos (padrão igual aos mapas de dengue) Agora…, Inicializa o gerador de mapas anuais Args: dir_dados: Diretório com os arquivos… (+8 more)

### Community 7 - "AnalisadorENSOLatitude"
Cohesion: 0.10
Nodes (14): AnalisadorENSOLatitude, Script para Análise El Niño vs La Niña por Faixas de Latitude + PDF Determina…, Análise global (todas as faixas juntas), Análise comparativa El Niño vs La Niña por latitude, Cria PDF com todos os gráficos e resultados, Série temporal por fase ENSO, Boxplots por faixa de latitude, Carrega médias mensais por latitude e ONI (+6 more)

### Community 8 - "ValidadorIntegridadeDados"
Cohesion: 0.10
Nodes (15): main(), Script de Validação de Integridade dos Dados Autor: Especialista em Ciência de…, Identifica e processa a coluna de data/tempo, Verifica dimensões do dataset, Classe para validação completa da integridade dos dados epidemiológicos, Verifica valores nulos/faltantes em todas as colunas, Inicializa o validador com o caminho do arquivo Args: arquivo_path (str):…, Verifica e valida os tipos de dados das colunas numéricas (+7 more)

### Community 9 - "AnalisadorEstatistico"
Cohesion: 0.11
Nodes (14): AnalisadorEstatistico, main(), Script de Análise Estatística Não Paramétrica Autor: Especialista em Ciência de…, Calcula correlação de Spearman entre duas variáveis Args: var1 (str): Nome da…, Classe para análise estatística não paramétrica de dados epidemiológicos, Cria grupos 'Alta' e 'Baixa' usando a mediana como ponto de corte Args:…, Inicializa o analisador com o dataframe Args: df (pd.DataFrame): DataFrame com…, Aplica teste Mann-Whitney U para comparar dois grupos (Alta vs Baixa… (+6 more)

### Community 10 - "AnalisadorRegressaoLag3"
Cohesion: 0.11
Nodes (13): AnalisadorRegressaoLag3, Análises de Regressão com Lag de 3 Meses na Dengue Teste 1: dengue_lag3 ~…, Prepara dados para Teste 1: dados agregados com todas as variáveis, Prepara dados para Teste 2: dados mensais por município, Executa regressão linear com escalamento, Teste 1: dengue_lag3 ~ todas as variáveis, Análises de regressão com dengue lag 3 meses, Teste 2: dengue_lag3 ~ variáveis climáticas (dados mensais) (+5 more)

### Community 11 - "processar_clima_por_latitude.py"
Cohesion: 0.11
Nodes (19): carregar_dados_wide_temperatura_dengue(), carregar_elnino(), carregar_precipitacao(), main(), Carrega CSVs de temperatura e dengue (formato wide) com filtros de qualidade, Carrega CSV de precipitação (tem header diferente), Carrega dados de El Niño/La Niña, carregar_mapeamento_latitudes() (+11 more)

### Community 12 - "gerar_relatorios_latitude_individuais.py"
Cohesion: 0.13
Nodes (21): carregar_dados_latitude(), carregar_todos_dados(), criar_analise_lag(), criar_boxplots_sazonais(), criar_graficos_scatter(), criar_matriz_correlacao(), criar_pagina_capa(), criar_serie_temporal() (+13 more)

### Community 13 - "AnalisadorENSOLatitudeParametrico"
Cohesion: 0.13
Nodes (11): AnalisadorENSOLatitudeParametrico, Script para Análise El Niño vs La Niña por Faixas de Latitude + PDF TESTES…, Análise global (todas as faixas juntas) - TESTES PARAMÉTRICOS, Análise comparativa El Niño vs La Niña por latitude - TESTES PARAMÉTRICOS, Gera visualizações para o PDF, Carrega médias mensais por latitude e ONI, Gera tabelas de resultados, Salva resultados em CSV (+3 more)

### Community 14 - "analise_global_dengue_log_pdf.py"
Cohesion: 0.15
Nodes (19): calcular_estatisticas_descritivas(), carregar_dados(), criar_pagina_conclusoes(), criar_pagina_correlacoes(), criar_pagina_enso(), criar_pagina_normalidade(), criar_pagina_regressao(), criar_pagina_visao_geral() (+11 more)

### Community 15 - "MapaTemperaturas"
Cohesion: 0.14
Nodes (11): main(), MapaTemperaturas, Script para criar mapas de temperatura da região Sul do Brasil Gera…, Prepara dados para um mês/ano específico Args: df: DataFrame com dados de…, Cria um mapa de temperatura Args: gdf: GeoDataFrame com dados titulo: Título do…, Inicializa o gerador de mapas Args: dados_dir: Diretório com os arquivos CSV de…, Gera uma série de mapas para todos os meses de um ano Args: tipo: Tipo de…, Cria um mapa comparativo com as três temperaturas (min, média, max) Args: ano:… (+3 more)

### Community 16 - "validar_todas_tarefas.py"
Cohesion: 0.18
Nodes (17): Cores, executar_script(), main(), print_aviso(), print_erro(), print_header(), print_sucesso(), Valida se os arquivos de output foram gerados. (+9 more)

### Community 17 - "gerar_relatorio_pdf.py"
Cohesion: 0.18
Nodes (15): carregar_dados(), criar_boxplots_sazonais(), criar_graficos_scatter(), criar_matriz_correlacao(), criar_pagina_capa(), criar_serie_temporal(), criar_tabela_estatisticas(), main() (+7 more)

### Community 18 - "gerar_mapas_municipios_latitude.py"
Cohesion: 0.20
Nodes (14): carregar_dados_ano(), carregar_dados_consolidado(), carregar_geodados(), classificar_incidencia(), gerar_mapa_consolidado(), gerar_mapa_municipios(), main(), Script para gerar mapas de municípios por latitude (2015-2023) Design idêntico… (+6 more)

### Community 19 - "validar_mapas_latitude.py"
Cohesion: 0.20
Nodes (13): gerar_relatorio_json(), main(), Script de validação dos mapas de latitude gerados Verifica se todos os arquivos…, Gera relatório de validação em JSON, Verifica se todos os CSVs de entrada existem, Função principal de validação, Verifica se todos os mapas individuais foram criados, Verifica se os painéis comparativos foram criados (+5 more)

### Community 20 - "gerar_paineis_comparativos.py"
Cohesion: 0.23
Nodes (12): calcular_medias_todos_anos(), carregar_dados_faixas(), classificar_incidencia(), gerar_grafico_evolucao_temporal(), gerar_painel_comparativo(), main(), Script para criar painel comparativo de todos os anos (2015-2023) Gera uma…, Gera painel com comparação de todos os anos (+4 more)

### Community 21 - "gerar_mapas_faixas_latitude.py"
Cohesion: 0.23
Nodes (11): calcular_media_por_faixa(), carregar_dados_faixas(), classificar_incidencia(), gerar_mapa_faixas(), main(), Script para gerar mapas de faixas de latitude com incidência de dengue Cria…, Gera mapa de barras horizontais com as faixas de latitude, Função principal para gerar todos os mapas (+3 more)

### Community 22 - "loaders.py"
Cohesion: 0.22
Nodes (10): GeoDataFrame, carregar_dados_brutos(), carregar_dados_processados(), carregar_geodados(), DataFrame, Carrega dados da pasta data/processed, Carrega shapefiles ou geojson da pasta data/geodados, Salva dataframe na pasta data/processed (+2 more)

### Community 23 - "criar_mapa_dengue_agregado_total.py"
Cohesion: 0.40
Nodes (5): classificar_incidencia(), criar_mapa_dengue_total(), Script para criar mapa de incidência total de dengue (2015-2024) Segue o padrão…, Classifica incidência em categorias visuais (casos totais agregados), Cria mapa de incidência total de dengue 2015-2024

### Community 24 - "main.py"
Cohesion: 0.70
Nodes (4): command_generate_reports(), command_process_data(), command_run_model(), main()

### Community 25 - "consolidar_medias_latitude.py"
Cohesion: 0.50
Nodes (3): consolidar_medias_latitude(), Script para consolidar médias mensais por faixa de latitude. Agrupa todos os…, Consolida os dados de dengue por faixa de latitude, calculando médias mensais.

### Community 26 - "converter_csv_para_xlsx_log.py"
Cohesion: 0.50
Nodes (3): converter_csv_log_para_xlsx(), Script para converter arquivos CSV para XLSX aplicando transformação…, Converte todos os arquivos CSV da pasta csvs_latitude para XLSX aplicando…

## Knowledge Gaps
- **1 isolated node(s):** `Cores`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 254 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `pipeline_completo()` connect `VisualizadorDados` to `ValidadorIntegridadeDados`, `AnalisadorEstatistico`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `ValidadorIntegridadeDados` connect `ValidadorIntegridadeDados` to `VisualizadorDados`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `AnalisadorEstatistico` connect `AnalisadorEstatistico` to `VisualizadorDados`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **What connects `Cores` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `motor_lote_modelagem_v2_por_latitude.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08644067796610169 - nodes in this community are weakly interconnected._
- **Should `gerar_relatorio_abnt_projecoes_ssp.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14299516908212562 - nodes in this community are weakly interconnected._
- **Should `VisualizadorDados` be split into smaller, more focused modules?**
  _Cohesion score 0.06236786469344609 - nodes in this community are weakly interconnected._