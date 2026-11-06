# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 50 files · ~36,655 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 654 nodes · 1383 edges · 39 communities (35 shown, 2 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 48 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `035dd15a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- experimento_v5.py
- get_feature_columns
- main.js
- server.py
- config.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- Preditor
- test_prediction_service.py
- build_ml_features
- Plano v5 — Limpeza e Resultado Publicável
- predictor.py
- TestAplicacaoV51
- test_ml_pipeline.py
- TestModelTraining
- main.py
- test_experimento.py
- run_interpretability
- analise_experimento.py
- GLMBinomialNegativa
- PredictRequest
- fit_predict_fold
- ModeloIndisponivel
- TestMultiDoenca
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- ml_orchestrator.py
- mini_panel
- _expanding_window_splits
- teste_prospectivo.py
- pre-commit
- analise_efeito/__init__.py
- build_base_panel
- experimento_horizontes.py
- api_predict

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 37 edges
2. `get_feature_columns()` - 34 edges
3. `Preditor` - 29 edges
4. `build_base_panel()` - 24 edges
5. `FonteDados` - 24 edges
6. `fit_predict_fold()` - 21 edges
7. `treinar_modelos_risco()` - 18 edges
8. `configurar_log()` - 18 edges
9. `limiares_por_cidade()` - 16 edges
10. `_expanding_window_splits()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `api_predict()` --uses--> `CidadeNaoEncontrada`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_predict()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_predict()` --uses--> `PredictRequest`  [INFERRED]
  app/server.py → src/prediction_service/schemas.py
- `_erro_http()` --uses--> `CidadeNaoEncontrada`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `_erro_http()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py

## Import Cycles
- None detected.

## Communities (39 total, 2 thin omitted)

### Community 0 - "experimento_v5.py"
Cohesion: 0.10
Nodes (35): bootstrap_delta_mae(), ΔMAE = MAE(a) − MAE(b) com IC 95% por bootstrap de CIDADES (preserva a…, aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray (+27 more)

### Community 1 - "get_feature_columns"
Cohesion: 0.14
Nodes (16): _anomalia_expanding(), get_feature_columns(), grupos_de_features(), is_clima_parcimonioso(), is_suscetibilidade(), _prefixo_doenca(), DataFrame, Series (+8 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.11
Nodes (30): api_cenario(), api_cidades(), api_confiabilidade(), api_doencas(), api_modelo_info(), api_previsao(), api_ranking(), api_resultados() (+22 more)

### Community 4 - "config.py"
Cohesion: 0.12
Nodes (19): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, Fonte de dados do serviço de previsão. A fonte de verdade é o SQLite…, fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude() (+11 more)

### Community 5 - "dlnm.py"
Cohesion: 0.16
Nodes (21): ajustar(), _coef_cov(), cross_basis(), plotar(), preparar(), DataFrame, ndarray, Path (+13 more)

### Community 6 - "atualizacao_incremental.py"
Cohesion: 0.17
Nodes (21): Connection, date, atualizar(), atualizar_enso(), cidades_do_banco(), coletar_clima(), coletar_saude(), main() (+13 more)

### Community 7 - "🦟 Clima × Arboviroses"
Cohesion: 0.09
Nodes (21): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa) (+13 more)

### Community 8 - "Plano de Experimento Final — Clima × Arboviroses"
Cohesion: 0.10
Nodes (19): 1.1 Variáveis do experimento, 1.2 O que muda em cada horizonte, 1.3 Métricas (fixadas agora, antes de rodar), 1.4 Validação, 1.5 Implementação, 4.1 Retreinar no painel completo (2015–2025), 4.2 Empacotar, 4.3 API de previsão (+11 more)

### Community 9 - "Preditor"
Cohesion: 0.16
Nodes (7): FonteDados, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Preditor, Path, fixture, TestAPI, TestPreditor

### Community 10 - "test_prediction_service.py"
Cohesion: 0.07
Nodes (35): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+27 more)

### Community 11 - "build_ml_features"
Cohesion: 0.14
Nodes (10): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, parametrize, Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação. (+2 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "predictor.py"
Cohesion: 0.22
Nodes (12): BaseModel, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, CenarioResponse, FaixaMes, PontoCenario, PredictResponse, PrevisaoMesResponse (+4 more)

### Community 16 - "TestAplicacaoV51"
Cohesion: 0.10
Nodes (14): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md,…, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades… (+6 more)

### Community 17 - "test_ml_pipeline.py"
Cohesion: 0.20
Nodes (9): _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No…, Prever = mesmo mês do ano anterior (<doença>_lag12)., Testes unitários para o pipeline ML v4 (multi-doença). Testa a feature… (+1 more)

### Community 18 - "TestModelTraining"
Cohesion: 0.40
Nodes (3): Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 19 - "main.py"
Cohesion: 0.08
Nodes (40): command_analise(), command_atualizar_dados(), command_dlnm(), command_experimento(), command_experimento_v5(), command_export_dashboard(), command_modelo_risco(), command_serve() (+32 more)

### Community 20 - "test_experimento.py"
Cohesion: 0.13
Nodes (19): git_commit(), avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas., avaliar_2025() (+11 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "analise_experimento.py"
Cohesion: 0.22
Nodes (18): decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê…, Treina o modelo COM clima em 2015–2024 e devolve o ranking SHAP (média |SHAP|). (+10 more)

### Community 23 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 24 - "PredictRequest"
Cohesion: 0.24
Nodes (6): field_validator, nivel_por_probabilidade(), PredictRequest, parametrize, TestNiveis, TestSchemas

### Community 25 - "fit_predict_fold"
Cohesion: 0.18
Nodes (20): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), fit_predict_fold(), limiares_por_cidade(), _persist_col(), DataFrame, ndarray (+12 more)

### Community 26 - "ModeloIndisponivel"
Cohesion: 0.26
Nodes (7): CidadeNaoEncontrada, _fmt_mes(), ModeloIndisponivel, DataFrame, RuntimeError, "Quantos casos em <mês>?". Até 3 meses após o último mês consolidado: previsão…, Previsão de todas as cidades para o horizonte h (ranking de risco).

### Community 27 - "TestMultiDoenca"
Cohesion: 0.18
Nodes (8): parametrize, Verifica que os lags de chikungunya são criados quando solicitado., Testa o fluxo completo: features → treino → predição, por doença., Testa que o pipeline funciona para cada doença suportada., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., TestIntegration, TestMultiDoenca

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "ml_orchestrator.py"
Cohesion: 0.18
Nodes (13): evaluate_baselines(), Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, DataFrame, Módulo responsável por construir o painel base a partir do banco de dados…, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, validate_panel(), DataFrame, Path (+5 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "_expanding_window_splits"
Cohesion: 0.29
Nodes (3): _expanding_window_splits(), Gera splits Expanding Window (Walk Forward): Treina em anos < t, testa no ano…, TestSemVazamento

### Community 33 - "teste_prospectivo.py"
Cohesion: 0.24
Nodes (12): avaliar(), HoldoutJaUsado, markdown(), meses_consolidados(), _metricas(), DataFrame, Path, RuntimeError (+4 more)

### Community 36 - "build_base_panel"
Cohesion: 0.20
Nodes (13): build_base_panel(), Path, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, estatisticas_cidades(), main(), DataFrame, Path, Fase 4.1 — Modelo final para produção (docs/PLANO_EXPERIMENTO_FINAL.md).… (+5 more)

### Community 37 - "experimento_horizontes.py"
Cohesion: 0.27
Nodes (11): _linha(), metricas_de_oof(), nome_config(), DataFrame, Path, Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline., Executa o experimento completo e grava os resultados. Retorna o DataFrame de… (+3 more)

### Community 38 - "api_predict"
Cohesion: 0.40
Nodes (5): api_predict(), api_recarregar(), Previsão de casos para um município, doença e horizonte (1–3 meses). Rota…, Relê o banco depois de uma ingestão (protegido pela variável de ambiente…, post

## Knowledge Gaps
- **54 isolated node(s):** `Comandos`, `Arquitetura`, `Grafo do código (graphify): consulte antes de abrir arquivos`, `Regras metodológicas (não violar)`, `Convenções` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 256 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `experimento_v5.py`, `get_feature_columns`, `teste_prospectivo.py`, `_expanding_window_splits`, `config.py`, `experimento_horizontes.py`, `test_prediction_service.py`, `test_ml_pipeline.py`, `test_experimento.py`, `analise_experimento.py`, `TestMultiDoenca`, `ml_orchestrator.py`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `build_base_panel` to `experimento_v5.py`, `teste_prospectivo.py`, `config.py`, `experimento_horizontes.py`, `dlnm.py`, `test_prediction_service.py`, `main.py`, `test_experimento.py`, `analise_experimento.py`, `ml_orchestrator.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `get_feature_columns()` connect `get_feature_columns` to `experimento_v5.py`, `teste_prospectivo.py`, `_expanding_window_splits`, `build_base_panel`, `experimento_horizontes.py`, `test_prediction_service.py`, `build_ml_features`, `test_ml_pipeline.py`, `test_experimento.py`, `analise_experimento.py`, `TestMultiDoenca`, `ml_orchestrator.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `FonteDados` (e.g. with `Cenarios` and `Preditor`) actually correct?**
  _`FonteDados` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Comandos`, `Arquitetura`, `Grafo do código (graphify): consulte antes de abrir arquivos` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `experimento_v5.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09634146341463415 - nodes in this community are weakly interconnected._