# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 60 files · ~51,236 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 804 nodes · 1725 edges · 48 communities (43 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 63 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9b9191de`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- analise_experimento.py
- experimento_v6.py
- main.js
- server.py
- ingestor_api_sul.py
- dlnm.py
- avaliar
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- experimento_v5.py
- .prever
- Plano v5 — Limpeza e Resultado Publicável
- run_experimento
- TestAplicacaoV51
- _expanding_window_splits
- TestModelTraining
- main.py
- teste_final.py
- run_interpretability
- build_ml_features
- Preditor
- predictor.py
- test_experimento.py
- Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)
- artefatos.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- experimento_horizontes.py
- mini_panel
- test_prediction_service.py
- ingestor_ibge_populacao.py
- pre-commit
- analise_efeito/__init__.py
- api_predict
- hf_space/README.md
- GLMBinomialNegativa
- TestFeatureEngineering
- get_feature_columns
- Protocolo v7 — Pré-registro
- modelo_final.py
- Protocolo v6 — Pré-registro
- build_base_panel
- .test_pipeline_end_to_end
- _run_single_disease
- painel_grade

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

## Communities (48 total, 3 thin omitted)

### Community 0 - "analise_experimento.py"
Cohesion: 0.22
Nodes (18): decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê…, Treina o modelo COM clima em 2015–2024 e devolve o ranking SHAP (média |SHAP|). (+10 more)

### Community 1 - "experimento_v6.py"
Cohesion: 0.10
Nodes (40): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+32 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.10
Nodes (34): api_cenario(), api_cidades(), api_confiabilidade(), api_doencas(), api_historico(), api_modelo_info(), api_municipios(), api_previsao() (+26 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.17
Nodes (17): agregar_infodengue_mensal(), fetch_clima(), fetch_infodengue(), fetch_infodengue_semanal(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude() (+9 more)

### Community 5 - "dlnm.py"
Cohesion: 0.16
Nodes (21): ajustar(), _coef_cov(), cross_basis(), plotar(), preparar(), DataFrame, ndarray, Path (+13 more)

### Community 6 - "avaliar"
Cohesion: 0.09
Nodes (39): Connection, date, avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():…, Acrescenta as previsões do lote; ignora as que já tinham sido emitidas. Retorna… (+31 more)

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
Cohesion: 0.07
Nodes (48): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, bootstrap_delta_mae(), ΔMAE = MAE(a) − MAE(b) com IC 95% por bootstrap de CIDADES (preserva a…, aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame (+40 more)

### Community 11 - ".prever"
Cohesion: 0.19
Nodes (13): nivel_por_probabilidade(), aplicar_intervalo(), CidadeNaoEncontrada, _fmt_mes(), margem_modelo(), ModeloIndisponivel, DataFrame, ndarray (+5 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "run_experimento"
Cohesion: 0.29
Nodes (7): DataFrame, Path, Executa o experimento completo e grava os resultados. Retorna o DataFrame de…, Roda os 4 modelos + 2 baselines em todos os folds. Retorna (oof_wide,…, rodar_doenca_horizonte(), run_experimento(), TestExperimentoPontaAPonta

### Community 16 - "TestAplicacaoV51"
Cohesion: 0.09
Nodes (14): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md,…, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades… (+6 more)

### Community 17 - "_expanding_window_splits"
Cohesion: 0.16
Nodes (15): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No… (+7 more)

### Community 18 - "TestModelTraining"
Cohesion: 0.40
Nodes (3): Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 19 - "main.py"
Cohesion: 0.07
Nodes (49): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+41 more)

### Community 20 - "teste_final.py"
Cohesion: 0.24
Nodes (11): avaliar_2025(), carregar_config(), HoldoutJaUsado, _markdown(), DataFrame, Path, RuntimeError, Fase 3 — Teste final no ano de 2025 (docs/PLANO_EXPERIMENTO_FINAL.md). - Usa a… (+3 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "build_ml_features"
Cohesion: 0.13
Nodes (8): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, Fonte de dados do serviço de previsão. A fonte de verdade é o SQLite…, parametrize, TestFeaturesV5, TestFeaturesV6, TestSemVazamento, Verifica que os lags de chikungunya são criados quando solicitado.

### Community 23 - "Preditor"
Cohesion: 0.10
Nodes (10): FonteDados, DataFrame, Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com…, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Painel + h meses futuros por cidade (após o último mês com alvo observado)., Preditor, Path, TestExperimentoV6 (+2 more)

### Community 24 - "predictor.py"
Cohesion: 0.22
Nodes (12): BaseModel, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, CenarioResponse, FaixaMes, PontoCenario, PredictResponse, PrevisaoMesResponse (+4 more)

### Community 25 - "test_experimento.py"
Cohesion: 0.15
Nodes (23): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), fit_predict_fold(), limiares_por_cidade(), margem_persistencia(), _persist_col(), DataFrame (+15 more)

### Community 26 - "Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)"
Cohesion: 0.33
Nodes (5): Chikungunya, Dengue, Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)

### Community 27 - "artefatos.py"
Cohesion: 0.23
Nodes (11): _arquivos(), empacotar(), extrair(), garantir(), Path, Artefatos de execução (o que o git não versiona): modelos de produção, snapshot…, Caminhos (absolutos) que entram no pacote., Extrai o zip conferindo cada arquivo contra o manifesto. Recusa caminhos fora… (+3 more)

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "experimento_horizontes.py"
Cohesion: 0.19
Nodes (11): _linha(), metricas_de_oof(), Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline., avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver… (+3 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "test_prediction_service.py"
Cohesion: 0.15
Nodes (10): field_validator, PredictRequest, artefatos(), fixture, parametrize, Testes do serviço de previsão v5 (alerta de risco): schemas, níveis, intervalo,…, Experimento v5 + modelos de risco no painel sintético (com clima e…, TestIntervalo (+2 more)

### Community 33 - "ingestor_ibge_populacao.py"
Cohesion: 0.32
Nodes (7): fetch_populacao_ibge(), get_ibge_7(), main(), DataFrame, ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API…, Busca população estimada do IBGE via API SIDRA (tabela 6579)., Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos.

### Community 36 - "api_predict"
Cohesion: 0.40
Nodes (5): api_predict(), api_recarregar(), Previsão de casos para um município, doença e horizonte (1–3 meses). Rota…, Relê o banco depois de uma ingestão (protegido pela variável de ambiente…, post

### Community 38 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 39 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 40 - "get_feature_columns"
Cohesion: 0.12
Nodes (22): _anomalia_expanding(), get_feature_columns(), grupos_de_features(), _incidencia_vizinhos(), is_clima_parcimonioso(), is_imunidade_longa(), is_suscetibilidade(), is_vizinhos() (+14 more)

### Community 41 - "Protocolo v7 — Pré-registro"
Cohesion: 0.18
Nodes (10): Base e candidatas (fixas), Dados, Desvios, Exploratório (não entra na decisão), Hipóteses, O que já se sabia (e motivou a v7), Protocolo v7 — Pré-registro, Regra de decisão (sequencial, fixa, por doença) (+2 more)

### Community 42 - "modelo_final.py"
Cohesion: 0.29
Nodes (9): nome_config(), estatisticas_cidades(), main(), DataFrame, Path, Fase 4.1 — Modelo final para produção (docs/PLANO_EXPERIMENTO_FINAL.md).…, Treina e salva os modelos de produção. Retorna {doenca: metadata}., Nome, limiares de risco (histórico completo) e R² OOF por horizonte para cada… (+1 more)

### Community 43 - "Protocolo v6 — Pré-registro"
Cohesion: 0.20
Nodes (9): Desvios, Exploratório (não entra na decisão), Hipóteses, Motivação (o que a v5 errou), Mudanças candidatas (fixas), Protocolo v6 — Pré-registro, Regra de decisão (sequencial, fixa), Teste: modo sombra prospectivo (uso único) (+1 more)

### Community 44 - "build_base_panel"
Cohesion: 0.29
Nodes (7): build_base_panel(), DataFrame, Path, Módulo responsável por construir o painel base a partir do banco de dados…, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, validate_panel()

### Community 45 - ".test_pipeline_end_to_end"
Cohesion: 0.25
Nodes (5): parametrize, Testa o fluxo completo: features → treino → predição, por doença., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., TestIntegration

### Community 46 - "_run_single_disease"
Cohesion: 0.40
Nodes (6): DataFrame, Path, Executa o pipeline completo de ML (hiperparâmetros fixos, sem tunagem). Args:…, Executa o pipeline para uma doença específica., run_pipeline(), _run_single_disease()

### Community 47 - "painel_grade"
Cohesion: 0.67
Nodes (3): painel_grade(), fixture, 12 cidades numa grade de coordenadas × 4 anos (para os vizinhos do protocolo…

## Knowledge Gaps
- **84 isolated node(s):** `MESES_LONGO`, `NIVEIS`, `COR`, `layoutBase`, `cfgPlot` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 319 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `analise_experimento.py`, `experimento_v6.py`, `TestFeatureEngineering`, `get_feature_columns`, `experimento_v5.py`, `.test_pipeline_end_to_end`, `_run_single_disease`, `_expanding_window_splits`, `Preditor`, `test_experimento.py`, `experimento_horizontes.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `test_prediction_service.py`, `server.py`, `avaliar`, `.prever`, `TestAplicacaoV51`, `predictor.py`, `test_experimento.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `build_base_panel` to `analise_experimento.py`, `experimento_v6.py`, `dlnm.py`, `get_feature_columns`, `experimento_v5.py`, `modelo_final.py`, `run_experimento`, `_run_single_disease`, `main.py`, `teste_final.py`, `build_ml_features`, `Preditor`, `experimento_horizontes.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `NIVEIS`, `COR` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `experimento_v6.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09988385598141696 - nodes in this community are weakly interconnected._
- **Should `server.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10420168067226891 - nodes in this community are weakly interconnected._