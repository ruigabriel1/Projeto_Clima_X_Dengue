# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 56 files · ~45,291 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 774 nodes · 1687 edges · 44 communities (39 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 61 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3da1c72c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- analise_experimento.py
- experimento_v6.py
- main.js
- server.py
- ingestor_api_sul.py
- dlnm.py
- config.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- experimento_v5.py
- get_feature_columns
- Plano v5 — Limpeza e Resultado Publicável
- experimento_horizontes.py
- FonteDados
- test_ml_pipeline.py
- TestModelTraining
- main.py
- build_base_panel
- run_interpretability
- build_ml_features
- teste_prospectivo.py
- test_prediction_service.py
- fit_predict_fold
- Preditor
- artefatos.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- test_experimento.py
- mini_panel
- predictor.py
- ingestor_ibge_populacao.py
- pre-commit
- analise_efeito/__init__.py
- treinar_modelos_finais
- hf_space/README.md
- GLMBinomialNegativa
- ml_orchestrator.py
- TestFeatureEngineering
- get_preditor
- TestMultiDoenca
- Protocolo v6 — Pré-registro (rascunho; vale a partir do commit que o registra)

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 43 edges
2. `get_feature_columns()` - 40 edges
3. `Preditor` - 34 edges
4. `build_base_panel()` - 27 edges
5. `fit_predict_fold()` - 27 edges
6. `FonteDados` - 27 edges
7. `configurar_log()` - 23 edges
8. `treinar_modelos_risco()` - 18 edges
9. `limiares_por_cidade()` - 18 edges
10. `_expanding_window_splits()` - 18 edges

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

## Communities (44 total, 3 thin omitted)

### Community 0 - "analise_experimento.py"
Cohesion: 0.10
Nodes (33): bootstrap_delta_mae(), decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê… (+25 more)

### Community 1 - "experimento_v6.py"
Cohesion: 0.15
Nodes (26): base_v51(), decidir(), efeito(), features_variantes(), preparar(), protocolo_registrado(), ProtocoloNaoRegistrado, DataFrame (+18 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.12
Nodes (27): api_cenario(), api_cidades(), api_confiabilidade(), api_doencas(), api_municipios(), api_previsao(), api_resultados(), api_status() (+19 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.29
Nodes (10): fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima(), process_saude() (+2 more)

### Community 5 - "dlnm.py"
Cohesion: 0.16
Nodes (21): ajustar(), _coef_cov(), cross_basis(), plotar(), preparar(), DataFrame, ndarray, Path (+13 more)

### Community 6 - "config.py"
Cohesion: 0.10
Nodes (33): Connection, date, Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():… (+25 more)

### Community 7 - "🦟 Clima × Arboviroses"
Cohesion: 0.08
Nodes (22): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa) (+14 more)

### Community 8 - "Plano de Experimento Final — Clima × Arboviroses"
Cohesion: 0.10
Nodes (19): 1.1 Variáveis do experimento, 1.2 O que muda em cada horizonte, 1.3 Métricas (fixadas agora, antes de rodar), 1.4 Validação, 1.5 Implementação, 4.1 Retreinar no painel completo (2015–2025), 4.2 Empacotar, 4.3 API de previsão (+11 more)

### Community 9 - "app.js"
Cohesion: 0.19
Nodes (27): api(), ativarAba(), atualizarLoader(), carregando, carregarCenario(), carregarConfiabilidade(), carregarPrevisao(), carregarRanking() (+19 more)

### Community 10 - "experimento_v5.py"
Cohesion: 0.12
Nodes (32): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+24 more)

### Community 11 - "get_feature_columns"
Cohesion: 0.11
Nodes (22): _anomalia_expanding(), get_feature_columns(), grupos_de_features(), _incidencia_vizinhos(), is_clima_parcimonioso(), is_imunidade_longa(), is_suscetibilidade(), is_vizinhos() (+14 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "experimento_horizontes.py"
Cohesion: 0.21
Nodes (15): _linha(), metricas_de_oof(), nome_config(), preparar_dados(), DataFrame, Path, Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline. (+7 more)

### Community 16 - "FonteDados"
Cohesion: 0.05
Nodes (23): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md,…, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades… (+15 more)

### Community 17 - "test_ml_pipeline.py"
Cohesion: 0.19
Nodes (11): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No… (+3 more)

### Community 18 - "TestModelTraining"
Cohesion: 0.40
Nodes (3): Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 19 - "main.py"
Cohesion: 0.07
Nodes (49): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+41 more)

### Community 20 - "build_base_panel"
Cohesion: 0.17
Nodes (17): build_base_panel(), Path, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, git_commit(), main(), Fase 4.1 — Modelo final para produção (docs/PLANO_EXPERIMENTO_FINAL.md).…, avaliar_2025(), carregar_config() (+9 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "build_ml_features"
Cohesion: 0.16
Nodes (6): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, parametrize, TestFeaturesV5, TestFeaturesV6, TestSemVazamento

### Community 23 - "teste_prospectivo.py"
Cohesion: 0.24
Nodes (12): avaliar(), HoldoutJaUsado, markdown(), meses_consolidados(), _metricas(), DataFrame, Path, RuntimeError (+4 more)

### Community 24 - "test_prediction_service.py"
Cohesion: 0.18
Nodes (9): field_validator, aplicar_intervalo(), Intervalo de 90% a partir dos quantis de resíduo log1p calibrados no OOF., PredictRequest, parametrize, Testes do serviço de previsão v5 (alerta de risco): schemas, níveis, intervalo,…, TestIntervalo, TestNiveis (+1 more)

### Community 25 - "fit_predict_fold"
Cohesion: 0.16
Nodes (22): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), fit_predict_fold(), limiares_por_cidade(), margem_persistencia(), _persist_col(), DataFrame (+14 more)

### Community 26 - "Preditor"
Cohesion: 0.15
Nodes (13): nivel_por_probabilidade(), CidadeNaoEncontrada, _fmt_mes(), margem_modelo(), ModeloIndisponivel, Preditor, DataFrame, ndarray (+5 more)

### Community 27 - "artefatos.py"
Cohesion: 0.23
Nodes (11): _arquivos(), empacotar(), extrair(), garantir(), Path, Artefatos de execução (o que o git não versiona): modelos de produção, snapshot…, Caminhos (absolutos) que entram no pacote., Extrai o zip conferindo cada arquivo contra o manifesto. Recusa caminhos fora… (+3 more)

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "test_experimento.py"
Cohesion: 0.12
Nodes (14): avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas., painel_grade(), fixture (+6 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "predictor.py"
Cohesion: 0.23
Nodes (13): api_ranking(), Cidades ordenadas pela probabilidade de risco alto (relativo ao histórico de…, BaseModel, Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, CenarioResponse, FaixaMes, PontoCenario, PredictResponse (+5 more)

### Community 33 - "ingestor_ibge_populacao.py"
Cohesion: 0.32
Nodes (7): fetch_populacao_ibge(), get_ibge_7(), main(), DataFrame, ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API…, Busca população estimada do IBGE via API SIDRA (tabela 6579)., Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos.

### Community 36 - "treinar_modelos_finais"
Cohesion: 0.40
Nodes (6): estatisticas_cidades(), DataFrame, Path, Treina e salva os modelos de produção. Retorna {doenca: metadata}., Nome, limiares de risco (histórico completo) e R² OOF por horizonte para cada…, treinar_modelos_finais()

### Community 38 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 39 - "ml_orchestrator.py"
Cohesion: 0.21
Nodes (11): DataFrame, Módulo responsável por construir o painel base a partir do banco de dados…, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, validate_panel(), DataFrame, Path, Orquestrador MLOps principal v4 (multi-doença). Acopla ingestão, validação,…, Executa o pipeline completo de ML (hiperparâmetros fixos, sem tunagem). Args:… (+3 more)

### Community 40 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 41 - "get_preditor"
Cohesion: 0.18
Nodes (11): api_historico(), api_modelo_info(), api_predict(), api_recarregar(), Previsão de casos para um município, doença e horizonte (1–3 meses). Rota…, Resumo dos modelos de produção carregados (config, métricas, data de retreino)., Casos observados (consolidados) dos últimos `meses` de um município ou da…, Relê o banco depois de uma ingestão (protegido pela variável de ambiente… (+3 more)

### Community 42 - "TestMultiDoenca"
Cohesion: 0.18
Nodes (8): parametrize, Verifica que os lags de chikungunya são criados quando solicitado., Testa o fluxo completo: features → treino → predição, por doença., Testa que o pipeline funciona para cada doença suportada., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., TestIntegration, TestMultiDoenca

### Community 43 - "Protocolo v6 — Pré-registro (rascunho; vale a partir do commit que o registra)"
Cohesion: 0.20
Nodes (9): Desvios, Exploratório (não entra na decisão), Hipóteses, Motivação (o que a v5 errou), Mudanças candidatas (fixas), Protocolo v6 — Pré-registro (rascunho; vale a partir do commit que o registra), Regra de decisão (sequencial, fixa), Teste: modo sombra prospectivo (uso único) (+1 more)

## Knowledge Gaps
- **73 isolated node(s):** `MESES_LONGO`, `NIVEIS`, `COR`, `layoutBase`, `cfgPlot` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 301 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `experimento_v6.py`, `ml_orchestrator.py`, `TestFeatureEngineering`, `experimento_v5.py`, `get_feature_columns`, `TestMultiDoenca`, `experimento_horizontes.py`, `FonteDados`, `test_ml_pipeline.py`, `teste_prospectivo.py`, `test_experimento.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `predictor.py`, `config.py`, `get_preditor`, `FonteDados`, `test_prediction_service.py`, `test_experimento.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `build_base_panel` to `analise_experimento.py`, `experimento_v6.py`, `dlnm.py`, `ml_orchestrator.py`, `experimento_v5.py`, `get_feature_columns`, `experimento_horizontes.py`, `FonteDados`, `main.py`, `teste_prospectivo.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `NIVEIS`, `COR` to the rest of the system?**
  _73 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `analise_experimento.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1036036036036036 - nodes in this community are weakly interconnected._
- **Should `experimento_v6.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14814814814814814 - nodes in this community are weakly interconnected._