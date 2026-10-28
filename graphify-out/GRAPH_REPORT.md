# Graph Report - Projeto_Clima_X_Dengue  (2026-10-25)

## Corpus Check
- 33 files · ~82,989 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 478 nodes · 693 edges · 26 communities
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5d04e880`
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
- test_ml_pipeline.py
- C.2 Algoritmos Recomendados para Este Problema
- Como obter os dados
- main.py
- ml_orchestrator.py
- run_interpretability
- evaluate_baselines
- GLMBinomialNegativa
- TestMultiDoenca
- mini_panel

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 23 edges
2. `📊 Mapas de Faixas de Latitude - Incidência de Dengue` - 15 edges
3. `train_model()` - 14 edges
4. `get_feature_columns()` - 13 edges
5. `run_interpretability()` - 12 edges
6. `📊 Guia de Interpretação dos Resultados` - 12 edges
7. `🏗️ Mentoria: Projeto Clima × Dengue — Engenharia de Dados Sênior` - 12 edges
8. `main()` - 11 edges
9. `evaluate_baselines()` - 10 edges
10. `_run_single_disease()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `TestMultiDoenca` --uses--> `PersistenciaBaseline`  [INFERRED]
  tests/test_ml_pipeline.py → src/ml_pipeline/baselines.py
- `TestMultiDoenca` --uses--> `NaiveSazonalBaseline`  [INFERRED]
  tests/test_ml_pipeline.py → src/ml_pipeline/baselines.py
- `api_status()` --calls--> `get_db_status()`  [INFERRED]
  app/server.py → src/ml_pipeline/export_dashboard.py
- `api_cidades()` --calls--> `get_cidades()`  [INFERRED]
  app/server.py → src/ml_pipeline/export_dashboard.py
- `command_train()` --calls--> `run_pipeline()`  [EXTRACTED]
  main.py → src/ml_pipeline/ml_orchestrator.py

## Import Cycles
- None detected.

## Communities (26 total, 0 thin omitted)

### Community 0 - "motor_lote_modelagem_v2_por_latitude.py"
Cohesion: 0.10
Nodes (44): ml_runner.py — Wrapper leve do motor ML para a interface Prodígia. Encapsula…, build_base_panel(), build_code_lookup_from_latitude_files(), _build_ml_features(), build_monthly_climatology(), build_yearly_templates(), calibrate_region(), CalibrationBundle (+36 more)

### Community 1 - "build_ml_features"
Cohesion: 0.11
Nodes (20): Experimento: efeito do clipping e das features do mês corrente no R² v3., _anomalia_expanding(), build_ml_features(), get_feature_columns(), _prefixo_doenca(), DataFrame, Series, Módulo de Feature Engineering v4 (multi-doença, multi-horizonte). Princípios: -… (+12 more)

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
Cohesion: 0.05
Nodes (42): 1. Caminhos Absolutos Hardcoded — **Severidade: CRÍTICA**, 1. Tratamento de Anomalias Climáticas (INMET), 2. Duplicação da Lógica Wide→Long — **Severidade: ALTA**, 2. Tratamento Epidemiológico de Lacunas (SINAN), 3. Overhaul do Geoprocessamento Visual (Mapas), 3. Pipeline sem Orquestração de Dependências — **Severidade: ALTA**, 4. Nomenclatura Inconsistente de Colunas — **Severidade: MÉDIA**, 5. Sem Testes Unitários — **Severidade: MÉDIA** (+34 more)

### Community 7 - "Arquitetura de Dados — Pipeline Medallion (Evolução API/SQLite)"
Cohesion: 0.06
Nodes (28): 1. Camada Bronze — Ingestão via API e SQLite, 2. Camada Silver — Merge & Transformação Mensal, 3. Camada Gold — Feature Store e Machine Learning, 4. Evolução Histórica (O Nosso Legado), A Arquitetura Antiga (v1 - Baseada em CSVs), Arquitetura de Dados — Pipeline Medallion (Evolução API/SQLite), Por que Evoluímos para a v2 (APIs + Banco)?, Visão Geral do Pipeline (Atual) (+20 more)

### Community 8 - "📊 Mapas de Faixas de Latitude - Incidência de Dengue"
Cohesion: 0.06
Nodes (30): Ajuste de faixas de latitude:, 📈 Análise dos Resultados (2015-2023), 🎨 Classificação de Cores, 🚀 Como Executar, Cálculo da Média por Faixa, Descrição, Entrada, Erro: "Nenhum arquivo CSV encontrado" (+22 more)

### Community 9 - "prediction.py"
Cohesion: 0.21
Nodes (13): get_climate_feature_columns(), Features do Modelo B (clima → risco). Requer build_ml_features(...,…, _apply_ssp_deltas(), bootstrap_uncertainty(), _compute_city_climatology(), predict_scenarios(), DataFrame, Path (+5 more)

### Community 10 - "GUIA DE EXECUÇÃO DAS ANÁLISES URGENTES"
Cohesion: 0.07
Nodes (28): 📦 ARQUIVOS DE SAÍDA ESPERADOS, Dados de entrada:, 📊 DADOS NECESSÁRIOS, Dados Processados:, ✨ DESTAQUES DOS RESULTADOS, 📧 ENTREGA, Erro: "Arquivo não encontrado", Erro: "ModuleNotFoundError" (+20 more)

### Community 11 - "Plano de Correção: ML + Aplicação Prodígia"
Cohesion: 0.08
Nodes (25): Automated Tests, Diagnóstico Resumido, Eliminar o Botão "Treinar Modelo", Estratégia: Treinar com TODOS os dados + Projeção por Climatologia, Fase 1 — Corrigir o Machine Learning (Prioridade MÁXIMA), Fase 2 — Gráficos Profissionais com Plotly, Fase 3 — Redesign do Fluxo da Aplicação, 🔴 Feedback Brutal (como pedido) (+17 more)

### Community 12 - "2. Correlação de Spearman (ρ)"
Cohesion: 0.18
Nodes (11): 2. Correlação de Spearman (ρ), Como Interpretar:, Direção:, Exemplo 1: Temperatura Média, Exemplo 2: Temperatura Mínima, Exemplo 3: Precipitação, Exemplo de Resultado:, Exemplos Práticos: (+3 more)

### Community 16 - "test_ml_pipeline.py"
Cohesion: 0.14
Nodes (20): _build_base_margin(), clip_outliers_per_city(), _detect_persist_col(), _expanding_window_splits(), DataFrame, ndarray, Path, Series (+12 more)

### Community 17 - "C.2 Algoritmos Recomendados para Este Problema"
Cohesion: 0.22
Nodes (9): C.1 Análise do Seu Modelo Atual, C.2 Algoritmos Recomendados para Este Problema, C.3 Fontes de Dados ENSO para Ingestão Contínua, C.4 Integração do ML na Camada Gold, C. Estratégia de Machine Learning e Projeção, Tier 1 — Modelo Principal: **Prophet + Regressores Exógenos**, Tier 2 — Modelo Complementar: **LightGBM com TimeSeriesSplit**, Tier 3 — Validação e Ensemble (+1 more)

### Community 18 - "Como obter os dados"
Cohesion: 0.29
Nodes (6): 1. Dados Meteorológicos (INMET), 2. Dados Epidemiológicos (DataSUS/SINAN), 3. Dados ENSO (NOAA), 4. Recurso Gráfico, Como obter os dados, Estrutura esperada

### Community 19 - "main.py"
Cohesion: 0.29
Nodes (9): command_export_dashboard(), command_run_model(), command_train(), main(), Executa o pipeline ML v4 (multi-doença)., Executa o motor legado de projeções SSP (mantido para retrocompatibilidade)., Exporta dados e gráficos para o Dashboard., exportar_dados_dashboard() (+1 more)

### Community 20 - "ml_orchestrator.py"
Cohesion: 0.16
Nodes (15): Compara o modelo v3 contra baseline de persistência (y_hat = lag1) e lista FI., build_base_panel(), DataFrame, Path, Módulo responsável por construir o painel base a partir do banco de dados…, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, validate_panel() (+7 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "evaluate_baselines"
Cohesion: 0.21
Nodes (10): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = valor do mês anterior (<doença>_lag1). (+2 more)

### Community 23 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 24 - "TestMultiDoenca"
Cohesion: 0.18
Nodes (8): parametrize, Testa que o pipeline funciona para cada doença suportada., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., Verifica que os lags de chikungunya são criados quando solicitado., Testa o fluxo completo: features → treino → predição, por doença., TestIntegration, TestMultiDoenca

### Community 25 - "mini_panel"
Cohesion: 0.67
Nodes (3): fixture, mini_panel(), Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

## Knowledge Gaps
- **165 isolated node(s):** `Resultado Principal`, `Estrutura do Repositório`, `Como Rodar`, `Documentação`, `Fontes de Dados` (+160 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 262 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_pipeline()` connect `ml_orchestrator.py` to `main.py`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `exportar_dados_dashboard()` connect `main.py` to `motor_lote_modelagem_v2_por_latitude.py`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `motor_lote_modelagem_v2_por_latitude.py` to `main.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **What connects `Resultado Principal`, `Estrutura do Repositório`, `Como Rodar` to the rest of the system?**
  _165 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `motor_lote_modelagem_v2_por_latitude.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1036077705827937 - nodes in this community are weakly interconnected._
- **Should `build_ml_features` be split into smaller, more focused modules?**
  _Cohesion score 0.11375661375661375 - nodes in this community are weakly interconnected._
- **Should `ingestor_api_sul.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14210526315789473 - nodes in this community are weakly interconnected._