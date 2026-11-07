# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 59 files · ~49,862 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 793 nodes · 1715 edges · 40 communities (34 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 63 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c9cc0d77`
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
- Preditor
- Plano v5 — Limpeza e Resultado Publicável
- experimento_horizontes.py
- FonteDados
- ml_orchestrator.py
- TestModelTraining
- main.py
- teste_final.py
- run_interpretability
- TestSemVazamento
- test_prediction_service.py
- predictor.py
- fit_predict_fold
- Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)
- artefatos.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- test_experimento.py
- mini_panel
- PredictRequest
- ingestor_ibge_populacao.py
- pre-commit
- analise_efeito/__init__.py
- api_predict
- hf_space/README.md
- build_ml_features
- Protocolo v6 — Pré-registro

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

## Communities (40 total, 4 thin omitted)

### Community 0 - "analise_experimento.py"
Cohesion: 0.22
Nodes (18): decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê…, Treina o modelo COM clima em 2015–2024 e devolve o ranking SHAP (média |SHAP|). (+10 more)

### Community 1 - "experimento_v6.py"
Cohesion: 0.09
Nodes (39): build_base_panel(), Path, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, git_commit(), base_v51(), decidir(), efeito(), features_variantes() (+31 more)

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

### Community 6 - "config.py"
Cohesion: 0.09
Nodes (40): Connection, date, Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():… (+32 more)

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
Cohesion: 0.10
Nodes (35): bootstrap_delta_mae(), ΔMAE = MAE(a) − MAE(b) com IC 95% por bootstrap de CIDADES (preserva a…, aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray (+27 more)

### Community 11 - "Preditor"
Cohesion: 0.15
Nodes (13): nivel_por_probabilidade(), CidadeNaoEncontrada, _fmt_mes(), margem_modelo(), ModeloIndisponivel, Preditor, DataFrame, ndarray (+5 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "experimento_horizontes.py"
Cohesion: 0.27
Nodes (11): _linha(), metricas_de_oof(), nome_config(), DataFrame, Path, Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline., Executa o experimento completo e grava os resultados. Retorna o DataFrame de… (+3 more)

### Community 16 - "FonteDados"
Cohesion: 0.05
Nodes (22): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md,…, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades… (+14 more)

### Community 17 - "ml_orchestrator.py"
Cohesion: 0.07
Nodes (31): evaluate_baselines(), GLMBinomialNegativa, _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, DataFrame, ndarray, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a… (+23 more)

### Community 18 - "TestModelTraining"
Cohesion: 0.40
Nodes (3): Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 19 - "main.py"
Cohesion: 0.07
Nodes (49): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+41 more)

### Community 20 - "teste_final.py"
Cohesion: 0.20
Nodes (12): avaliar_2025(), carregar_config(), HoldoutJaUsado, _markdown(), DataFrame, Path, RuntimeError, Fase 3 — Teste final no ano de 2025 (docs/PLANO_EXPERIMENTO_FINAL.md). - Usa a… (+4 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 23 - "test_prediction_service.py"
Cohesion: 0.10
Nodes (32): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+24 more)

### Community 24 - "predictor.py"
Cohesion: 0.22
Nodes (12): BaseModel, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, CenarioResponse, FaixaMes, PontoCenario, PredictResponse, PrevisaoMesResponse (+4 more)

### Community 25 - "fit_predict_fold"
Cohesion: 0.14
Nodes (25): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), _expanding_window_splits(), fit_predict_fold(), limiares_por_cidade(), margem_persistencia(), _persist_col() (+17 more)

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

### Community 30 - "test_experimento.py"
Cohesion: 0.17
Nodes (11): avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas., painel_grade(), fixture (+3 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "PredictRequest"
Cohesion: 0.28
Nodes (5): field_validator, PredictRequest, parametrize, TestNiveis, TestSchemas

### Community 33 - "ingestor_ibge_populacao.py"
Cohesion: 0.32
Nodes (7): fetch_populacao_ibge(), get_ibge_7(), main(), DataFrame, ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API…, Busca população estimada do IBGE via API SIDRA (tabela 6579)., Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos.

### Community 36 - "api_predict"
Cohesion: 0.40
Nodes (5): api_predict(), api_recarregar(), Previsão de casos para um município, doença e horizonte (1–3 meses). Rota…, Relê o banco depois de uma ingestão (protegido pela variável de ambiente…, post

### Community 40 - "build_ml_features"
Cohesion: 0.06
Nodes (38): _anomalia_expanding(), build_ml_features(), get_feature_columns(), grupos_de_features(), _incidencia_vizinhos(), is_clima_parcimonioso(), is_imunidade_longa(), is_suscetibilidade() (+30 more)

### Community 43 - "Protocolo v6 — Pré-registro"
Cohesion: 0.20
Nodes (9): Desvios, Exploratório (não entra na decisão), Hipóteses, Motivação (o que a v5 errou), Mudanças candidatas (fixas), Protocolo v6 — Pré-registro, Regra de decisão (sequencial, fixa), Teste: modo sombra prospectivo (uso único) (+1 more)

## Knowledge Gaps
- **75 isolated node(s):** `MESES_LONGO`, `NIVEIS`, `COR`, `layoutBase`, `cfgPlot` (+70 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 309 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `analise_experimento.py`, `experimento_v6.py`, `experimento_v5.py`, `experimento_horizontes.py`, `FonteDados`, `ml_orchestrator.py`, `TestSemVazamento`, `test_prediction_service.py`, `fit_predict_fold`, `test_experimento.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `server.py`, `config.py`, `FonteDados`, `test_prediction_service.py`, `predictor.py`, `test_experimento.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `experimento_v6.py` to `analise_experimento.py`, `dlnm.py`, `experimento_v5.py`, `experimento_horizontes.py`, `ml_orchestrator.py`, `main.py`, `teste_final.py`, `test_prediction_service.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `NIVEIS`, `COR` to the rest of the system?**
  _75 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `experimento_v6.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09191583610188261 - nodes in this community are weakly interconnected._
- **Should `server.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10420168067226891 - nodes in this community are weakly interconnected._