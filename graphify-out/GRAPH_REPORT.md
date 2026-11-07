# Graph Report - Projeto_Clima_X_Dengue  (2026-11-07)

## Corpus Check
- 68 files · ~63,259 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 966 nodes · 2113 edges · 57 communities (48 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `65ed4974`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_experimento
- analise_experimento.py
- charts.js
- server.py
- ingestor_api_sul.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- alerta_risco.py
- CidadeNaoEncontrada
- Plano v5 — Limpeza e Resultado Publicável
- ingestor_sinan_sorotipo.py
- TestAplicacaoV51
- GLMBinomialNegativa
- test_ml_pipeline.py
- main.py
- experimento_v7.py
- run_interpretability
- build_ml_features
- Preditor
- config.py
- fit_predict_fold
- Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)
- experimento_v5.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- get_preditor
- mini_panel
- predictor.py
- ml_orchestrator.py
- pre-commit
- analise_efeito/__init__.py
- get_feature_columns
- hf_space/README.md
- exportar
- TestFeatureEngineering
- DataFrame
- Protocolo v7 — Pré-registro
- test_sorotipo.py
- Protocolo v6 — Pré-registro
- artefatos.py
- .test_pipeline_end_to_end
- export_dashboard.py
- modelo_final.py
- experimento_v6.py
- main.js
- PredictRequest
- TestModelTraining
- Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)
- test_experimento.py

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 47 edges
2. `get_feature_columns()` - 46 edges
3. `Preditor` - 40 edges
4. `build_base_panel()` - 32 edges
5. `FonteDados` - 32 edges
6. `fit_predict_fold()` - 30 edges
7. `configurar_log()` - 26 edges
8. `main()` - 20 edges
9. `limiares_por_cidade()` - 20 edges
10. `_expanding_window_splits()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `api_predict()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_predict()` --uses--> `PredictRequest`  [INFERRED]
  app/server.py → src/prediction_service/schemas.py
- `_erro_http()` --uses--> `CidadeNaoEncontrada`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `_erro_http()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_ranking()` --uses--> `RankingItem`  [INFERRED]
  app/server.py → src/prediction_service/schemas.py

## Import Cycles
- None detected.

## Communities (57 total, 4 thin omitted)

### Community 0 - "run_experimento"
Cohesion: 0.32
Nodes (8): metricas_de_oof(), DataFrame, Path, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline., Executa o experimento completo e grava os resultados. Retorna o DataFrame de…, Roda os 4 modelos + 2 baselines em todos os folds. Retorna (oof_wide,…, rodar_doenca_horizonte(), run_experimento()

### Community 1 - "analise_experimento.py"
Cohesion: 0.19
Nodes (21): bootstrap_delta_mae(), decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê… (+13 more)

### Community 2 - "charts.js"
Cohesion: 0.80
Nodes (4): getPlotlyConfig(), getPlotlyLayout(), renderChartHeatmap(), renderChartSazonal()

### Community 3 - "server.py"
Cohesion: 0.14
Nodes (21): api_cidades(), api_doencas(), api_historico(), api_modelo_info(), api_resultados(), api_status(), index(), lifespan() (+13 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.17
Nodes (17): agregar_infodengue_mensal(), fetch_clima(), fetch_infodengue(), fetch_infodengue_semanal(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude() (+9 more)

### Community 5 - "dlnm.py"
Cohesion: 0.16
Nodes (21): ajustar(), _coef_cov(), cross_basis(), plotar(), preparar(), DataFrame, ndarray, Path (+13 more)

### Community 6 - "atualizacao_incremental.py"
Cohesion: 0.06
Nodes (59): Connection, date, avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():…, Acrescenta as previsões do lote; ignora as que já tinham sido emitidas. Retorna… (+51 more)

### Community 7 - "🦟 Clima × Arboviroses"
Cohesion: 0.12
Nodes (16): A aplicação, Arquitetura, 🦟 Clima × Arboviroses, Como a IA foi usada, e onde ela foi barrada, Depois de 2026: o diagnóstico, a v6 e a v7, El Niño e La Niña: fora da versão atual, exploratório para as próximas, Em 30 segundos, Engenharia de dados (+8 more)

### Community 8 - "Plano de Experimento Final — Clima × Arboviroses"
Cohesion: 0.10
Nodes (19): 1.1 Variáveis do experimento, 1.2 O que muda em cada horizonte, 1.3 Métricas (fixadas agora, antes de rodar), 1.4 Validação, 1.5 Implementação, 4.1 Retreinar no painel completo (2015–2025), 4.2 Empacotar, 4.3 API de previsão (+11 more)

### Community 9 - "app.js"
Cohesion: 0.12
Nodes (42): alerta(), api(), apiEstatica(), ativarAba(), atualizarLoader(), autocompletar(), cacheDados, carregando (+34 more)

### Community 10 - "alerta_risco.py"
Cohesion: 0.22
Nodes (15): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+7 more)

### Community 11 - "CidadeNaoEncontrada"
Cohesion: 0.33
Nodes (6): api_predict(), api_recarregar(), Previsão de casos para um município, doença e horizonte (1–3 meses). Rota…, Relê o banco depois de uma ingestão (protegido pela variável de ambiente…, post, CidadeNaoEncontrada

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "ingestor_sinan_sorotipo.py"
Cohesion: 0.23
Nodes (15): agregar(), baixar(), contar(), dir_cache(), executar(), ler_campos_dbf(), processar_ano(), DataFrame (+7 more)

### Community 16 - "TestAplicacaoV51"
Cohesion: 0.10
Nodes (13): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades…, Faixa (× fator climático) para os `meses` seguintes ao último mês consolidado. (+5 more)

### Community 17 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 18 - "test_ml_pipeline.py"
Cohesion: 0.18
Nodes (13): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No… (+5 more)

### Community 19 - "main.py"
Cohesion: 0.07
Nodes (49): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+41 more)

### Community 20 - "experimento_v7.py"
Cohesion: 0.07
Nodes (53): adota(), base_v6(), carregar_sorotipo(), com_rt(), decidir(), efeito(), _feats(), modelos() (+45 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "build_ml_features"
Cohesion: 0.14
Nodes (8): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, parametrize, TestFeaturesV5, TestFeaturesV6, parametrize, TestRt, Verifica que os lags de chikungunya são criados quando solicitado.

### Community 23 - "Preditor"
Cohesion: 0.05
Nodes (38): nivel_por_probabilidade(), avaliar(), HoldoutJaUsado, markdown(), meses_consolidados(), _metricas(), DataFrame, Path (+30 more)

### Community 24 - "config.py"
Cohesion: 0.16
Nodes (16): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray, Path (+8 more)

### Community 25 - "fit_predict_fold"
Cohesion: 0.12
Nodes (25): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), _expanding_window_splits(), fit_predict_fold(), limiares_por_cidade(), margem_persistencia(), _persist_col() (+17 more)

### Community 26 - "Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)"
Cohesion: 0.33
Nodes (5): Chikungunya, Dengue, Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)

### Community 27 - "experimento_v5.py"
Cohesion: 0.19
Nodes (18): calibrar_temporal(), decidir(), efeitos(), metricas(), nome(), preparar(), DataFrame, Path (+10 more)

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "get_preditor"
Cohesion: 0.17
Nodes (14): api_cenario(), api_confiabilidade(), api_municipios(), api_previsao(), api_ranking(), _erro_http(), Casos de um município em um mês. Até 3 meses após o último mês consolidado:…, Cidades ordenadas pela probabilidade de risco alto (relativo ao histórico de… (+6 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "predictor.py"
Cohesion: 0.27
Nodes (11): BaseModel, Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, CenarioResponse, FaixaMes, PontoCenario, PredictResponse, PrevisaoMesResponse, RankingItem (+3 more)

### Community 33 - "ml_orchestrator.py"
Cohesion: 0.32
Nodes (7): DataFrame, Path, Orquestrador MLOps principal v4 (multi-doença). Acopla ingestão, validação,…, Executa o pipeline completo de ML (hiperparâmetros fixos, sem tunagem). Args:…, Executa o pipeline para uma doença específica., run_pipeline(), _run_single_disease()

### Community 36 - "get_feature_columns"
Cohesion: 0.12
Nodes (19): get_feature_columns(), grupos_de_features(), is_clima_parcimonioso(), is_imunidade_longa(), is_rt(), is_rt_bruto(), is_suscetibilidade(), is_vizinhos() (+11 more)

### Community 38 - "exportar"
Cohesion: 0.24
Nodes (13): _cenario(), _dump(), exportar(), _gravar(), _pagina(), _proximos_meses(), Path, Versão estática da aplicação (GitHub Pages): as mesmas 5 abas, com as respostas… (+5 more)

### Community 39 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 40 - "DataFrame"
Cohesion: 0.29
Nodes (8): _anomalia_expanding(), _incidencia_vizinhos(), DataFrame, Series, Rolling por cidade aplicado sobre a série já deslocada (nunca inclui…, Anomalia = valor - média do MESMO mês nos anos ANTERIORES da mesma cidade.…, Incidência agregada (casos / pop × 100 mil) das k cidades mais próximas…, _roll_shifted()

### Community 41 - "Protocolo v7 — Pré-registro"
Cohesion: 0.20
Nodes (10): Base e candidatas (fixas), Dados, Desvios, Exploratório (não entra na decisão), Hipóteses, O que já se sabia (e motivou a v7), Protocolo v7 — Pré-registro, Regra de decisão (sequencial, fixa, por doença) (+2 more)

### Community 42 - "test_sorotipo.py"
Cohesion: 0.47
Nodes (5): _dbf(), Leitura do SINAN (DBF) e contagem de sorotipos por UF × mês (protocolo v7,…, Escreve um .dbf mínimo (campos texto/data de tamanho fixo)., test_campo_ausente_e_vazio(), test_le_campos_e_conta_por_uf_mes()

### Community 43 - "Protocolo v6 — Pré-registro"
Cohesion: 0.22
Nodes (9): Desvios, Exploratório (não entra na decisão), Hipóteses, Motivação (o que a v5 errou), Mudanças candidatas (fixas), Protocolo v6 — Pré-registro, Regra de decisão (sequencial, fixa), Teste: modo sombra prospectivo (uso único) (+1 more)

### Community 44 - "artefatos.py"
Cohesion: 0.21
Nodes (13): _arquivos(), empacotar(), extrair(), garantir(), Path, Artefatos de execução (o que o git não versiona): modelos de produção, snapshot…, Caminhos (absolutos) que entram no pacote., Cópia consistente do SQLite (API de backup), segura mesmo com uma ingestão… (+5 more)

### Community 45 - ".test_pipeline_end_to_end"
Cohesion: 0.25
Nodes (5): parametrize, Testa o fluxo completo: features → treino → predição, por doença., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., TestIntegration

### Community 47 - "export_dashboard.py"
Cohesion: 0.27
Nodes (10): _clean(), _code6(), exportar_dados_dashboard(), exportar_doenca(), _historico(), _mean(), DataFrame, Series (+2 more)

### Community 48 - "modelo_final.py"
Cohesion: 0.25
Nodes (10): estatisticas_cidades(), main(), DataFrame, Path, Fase 4.1 — Modelo final para produção (docs/PLANO_EXPERIMENTO_FINAL.md).…, Treina e salva os modelos de produção. Retorna {doenca: metadata}., Nome, limiares de risco (histórico completo) e R² OOF por horizonte para cada…, treinar_modelos_finais() (+2 more)

### Community 50 - "experimento_v6.py"
Cohesion: 0.07
Nodes (40): build_base_panel(), DataFrame, Path, Módulo responsável por construir o painel base a partir do banco de dados…, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, validate_panel(), base_v51() (+32 more)

### Community 52 - "PredictRequest"
Cohesion: 0.38
Nodes (4): field_validator, PredictRequest, parametrize, TestSchemas

### Community 53 - "TestModelTraining"
Cohesion: 0.40
Nodes (3): Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 54 - "Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)"
Cohesion: 0.25
Nodes (8): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa)

### Community 56 - "test_experimento.py"
Cohesion: 0.11
Nodes (23): _linha(), Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas. (+15 more)

## Knowledge Gaps
- **88 isolated node(s):** `MESES_LONGO`, `ICONE`, `NIVEIS`, `ORDEM_NIVEL`, `COR` (+83 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 372 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `analise_experimento.py`, `ml_orchestrator.py`, `get_feature_columns`, `TestFeatureEngineering`, `DataFrame`, `alerta_risco.py`, `.test_pipeline_end_to_end`, `experimento_v6.py`, `test_ml_pipeline.py`, `experimento_v7.py`, `Preditor`, `test_experimento.py`, `experimento_v5.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `predictor.py`, `atualizacao_incremental.py`, `TestAplicacaoV51`, `experimento_v7.py`, `test_experimento.py`, `get_preditor`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `experimento_v6.py` to `run_experimento`, `analise_experimento.py`, `ml_orchestrator.py`, `get_feature_columns`, `dlnm.py`, `alerta_risco.py`, `modelo_final.py`, `main.py`, `experimento_v7.py`, `Preditor`, `test_experimento.py`, `experimento_v5.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `FonteDados` (e.g. with `Cenarios` and `Preditor`) actually correct?**
  _`FonteDados` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `ICONE`, `NIVEIS` to the rest of the system?**
  _88 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `server.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13852813852813853 - nodes in this community are weakly interconnected._