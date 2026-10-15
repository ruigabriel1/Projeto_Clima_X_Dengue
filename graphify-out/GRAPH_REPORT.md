# Graph Report - Projeto_Clima_X_Dengue  (2026-10-14)

## Corpus Check
- 31 files · ~79,384 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 398 nodes · 533 edges · 20 communities
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `be9c7881`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- motor_lote_modelagem_v2_por_latitude.py
- build_ml_features
- main.js
- server.py
- ingestor_api_sul.py
- 📊 Guia de Interpretação dos Resultados
- 🏗️ Mentoria: Projeto Clima × Dengue — Engenharia de Dados Sênior
- Arquitetura de Dados — Pipeline Medallion (Evolução API/SQLite)
- 📊 Mapas de Faixas de Latitude - Incidência de Dengue
- prediction.py
- GUIA DE EXECUÇÃO DAS ANÁLISES URGENTES
- Plano de Correção: ML + Aplicação Prodígia
- 2. Correlação de Spearman (ρ)
- 🚨 O que você deve corrigir urgentemente
- C.2 Algoritmos Recomendados para Este Problema
- Como obter os dados
- exportar_dados_dashboard

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 15 edges
2. `📊 Mapas de Faixas de Latitude - Incidência de Dengue` - 15 edges
3. `train_model()` - 12 edges
4. `📊 Guia de Interpretação dos Resultados` - 12 edges
5. `🏗️ Mentoria: Projeto Clima × Dengue — Engenharia de Dados Sênior` - 12 edges
6. `get_feature_columns()` - 11 edges
7. `main()` - 11 edges
8. `save_pdf_reports()` - 10 edges
9. `GUIA DE EXECUÇÃO DAS ANÁLISES URGENTES` - 10 edges
10. `build_base_panel()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `api_status()` --calls--> `get_db_status()`  [INFERRED]
  app/server.py → src/ml_pipeline/export_dashboard.py
- `api_cidades()` --calls--> `get_cidades()`  [INFERRED]
  app/server.py → src/ml_pipeline/export_dashboard.py
- `main()` --calls--> `exportar_dados_dashboard()`  [EXTRACTED]
  main.py → src/ml_pipeline/export_dashboard.py
- `exportar_dados_dashboard()` --calls--> `build_base_panel()`  [EXTRACTED]
  src/ml_pipeline/export_dashboard.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `loadAndRender()` --calls--> `fetchResultados()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/api.js

## Import Cycles
- None detected.

## Communities (20 total, 0 thin omitted)

### Community 0 - "motor_lote_modelagem_v2_por_latitude.py"
Cohesion: 0.10
Nodes (44): ml_runner.py — Wrapper leve do motor ML para a interface Prodígia. Encapsula…, build_base_panel(), build_code_lookup_from_latitude_files(), _build_ml_features(), build_monthly_climatology(), build_yearly_templates(), calibrate_region(), CalibrationBundle (+36 more)

### Community 1 - "build_ml_features"
Cohesion: 0.06
Nodes (47): fixture, Compara o modelo v3 contra baseline de persistência (y_hat = lag1) e lista FI., Experimento: efeito do clipping e das features do mês corrente no R² v3., Series, build_base_panel(), DataFrame, Path, Módulo responsável por construir o painel base a partir do banco de dados… (+39 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartCenarios(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.21
Nodes (11): api_cidades(), api_resultados(), api_status(), index(), server.py — FastAPI backend para a interface Prodígia. Rotas: status do banco,…, get, Request, get_cidades() (+3 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.14
Nodes (17): fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima(), process_saude() (+9 more)

### Community 5 - "📊 Guia de Interpretação dos Resultados"
Cohesion: 0.05
Nodes (38): 1. Correlação ≠ Causalidade, 1. Teste de Normalidade, 2. Significância ≠ Importância Prática, 3. Considere o Contexto, 3. Teste Mann-Whitney U, 4. Outliers, 4. Teste Kruskal-Wallis, 5. Teste de Levene (+30 more)

### Community 6 - "🏗️ Mentoria: Projeto Clima × Dengue — Engenharia de Dados Sênior"
Cohesion: 0.06
Nodes (32): 1. Tratamento de Anomalias Climáticas (INMET), 2. Tratamento Epidemiológico de Lacunas (SINAN), 3. Overhaul do Geoprocessamento Visual (Mapas), A Engenharia de Features e Validação Global (Notebooks 03 e 04), 🔬 Ambiente de Exploração (Jupyter Notebooks - `.ipynb`), 🏭 Ambiente de Produção (Scripts Python - `.py`), Arquivos para Validação, B. Arquitetura de Dados — Medallion Architecture (+24 more)

### Community 7 - "Arquitetura de Dados — Pipeline Medallion (Evolução API/SQLite)"
Cohesion: 0.06
Nodes (28): 1. Camada Bronze — Ingestão via API e SQLite, 2. Camada Silver — Merge & Transformação Mensal, 3. Camada Gold — Feature Store e Machine Learning, 4. Evolução Histórica (O Nosso Legado), A Arquitetura Antiga (v1 - Baseada em CSVs), Arquitetura de Dados — Pipeline Medallion (Evolução API/SQLite), Por que Evoluímos para a v2 (APIs + Banco)?, Visão Geral do Pipeline (Atual) (+20 more)

### Community 8 - "📊 Mapas de Faixas de Latitude - Incidência de Dengue"
Cohesion: 0.06
Nodes (30): Ajuste de faixas de latitude:, 📈 Análise dos Resultados (2015-2023), 🎨 Classificação de Cores, 🚀 Como Executar, Cálculo da Média por Faixa, Descrição, Entrada, Erro: "Nenhum arquivo CSV encontrado" (+22 more)

### Community 9 - "prediction.py"
Cohesion: 0.33
Nodes (5): predict_future_scenarios(), DataFrame, Módulo de predição do motor de ML. Responsável por pegar o modelo treinado…, Dada a tabela climática projetada (ou climatologia estendida com deltas do…, # TODO: Implementar a lógica de geração dos DataFrames futuros com os

### Community 10 - "GUIA DE EXECUÇÃO DAS ANÁLISES URGENTES"
Cohesion: 0.07
Nodes (28): 📦 ARQUIVOS DE SAÍDA ESPERADOS, Dados de entrada:, 📊 DADOS NECESSÁRIOS, Dados Processados:, ✨ DESTAQUES DOS RESULTADOS, 📧 ENTREGA, Erro: "Arquivo não encontrado", Erro: "ModuleNotFoundError" (+20 more)

### Community 11 - "Plano de Correção: ML + Aplicação Prodígia"
Cohesion: 0.08
Nodes (25): Automated Tests, Diagnóstico Resumido, Eliminar o Botão "Treinar Modelo", Estratégia: Treinar com TODOS os dados + Projeção por Climatologia, Fase 1 — Corrigir o Machine Learning (Prioridade MÁXIMA), Fase 2 — Gráficos Profissionais com Plotly, Fase 3 — Redesign do Fluxo da Aplicação, 🔴 Feedback Brutal (como pedido) (+17 more)

### Community 12 - "2. Correlação de Spearman (ρ)"
Cohesion: 0.18
Nodes (11): 2. Correlação de Spearman (ρ), Como Interpretar:, Direção:, Exemplo 1: Temperatura Média, Exemplo 2: Temperatura Mínima, Exemplo 3: Precipitação, Exemplo de Resultado:, Exemplos Práticos: (+3 more)

### Community 16 - "🚨 O que você deve corrigir urgentemente"
Cohesion: 0.20
Nodes (10): 1. Caminhos Absolutos Hardcoded — **Severidade: CRÍTICA**, 2. Duplicação da Lógica Wide→Long — **Severidade: ALTA**, 3. Pipeline sem Orquestração de Dependências — **Severidade: ALTA**, 4. Nomenclatura Inconsistente de Colunas — **Severidade: MÉDIA**, 5. Sem Testes Unitários — **Severidade: MÉDIA**, 6. Arquivo Temporário na Raiz — **Severidade: BAIXA**, 7. README Desatualizado — **Severidade: BAIXA**, A. Análise Crítica do Processo Atual (+2 more)

### Community 17 - "C.2 Algoritmos Recomendados para Este Problema"
Cohesion: 0.22
Nodes (9): C.1 Análise do Seu Modelo Atual, C.2 Algoritmos Recomendados para Este Problema, C.3 Fontes de Dados ENSO para Ingestão Contínua, C.4 Integração do ML na Camada Gold, C. Estratégia de Machine Learning e Projeção, Tier 1 — Modelo Principal: **Prophet + Regressores Exógenos**, Tier 2 — Modelo Complementar: **LightGBM com TimeSeriesSplit**, Tier 3 — Validação e Ensemble (+1 more)

### Community 18 - "Como obter os dados"
Cohesion: 0.29
Nodes (6): 1. Dados Meteorológicos (INMET), 2. Dados Epidemiológicos (DataSUS/SINAN), 3. Dados ENSO (NOAA), 4. Recurso Gráfico, Como obter os dados, Estrutura esperada

### Community 19 - "exportar_dados_dashboard"
Cohesion: 0.60
Nodes (4): command_run_model(), main(), exportar_dados_dashboard(), Consolida os dados do banco e resultados ML (ml_run_log) no JSON do dashboard.

## Knowledge Gaps
- **165 isolated node(s):** `Resultado Principal`, `Estrutura do Repositório`, `Como Rodar`, `Documentação`, `Fontes de Dados` (+160 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 229 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `🏗️ Mentoria: Projeto Clima × Dengue — Engenharia de Dados Sênior` connect `🏗️ Mentoria: Projeto Clima × Dengue — Engenharia de Dados Sênior` to `🚨 O que você deve corrigir urgentemente`, `C.2 Algoritmos Recomendados para Este Problema`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `📊 Guia de Interpretação dos Resultados` connect `📊 Guia de Interpretação dos Resultados` to `2. Correlação de Spearman (ρ)`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `motor_lote_modelagem_v2_por_latitude.py` to `exportar_dados_dashboard`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **What connects `Resultado Principal`, `Estrutura do Repositório`, `Como Rodar` to the rest of the system?**
  _165 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `motor_lote_modelagem_v2_por_latitude.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1036077705827937 - nodes in this community are weakly interconnected._
- **Should `build_ml_features` be split into smaller, more focused modules?**
  _Cohesion score 0.055299539170506916 - nodes in this community are weakly interconnected._
- **Should `ingestor_api_sul.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14210526315789473 - nodes in this community are weakly interconnected._