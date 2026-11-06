# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 51 files · ~39,557 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 686 nodes · 1464 edges · 37 communities (32 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 54 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fde633ba`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- experimento_v5.py
- get_feature_columns
- main.js
- server.py
- ingestor_api_sul.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- test_prediction_service.py
- build_ml_features
- Plano v5 — Limpeza e Resultado Publicável
- schemas.py
- FonteDados
- _expanding_window_splits
- TestModelTraining
- main.py
- experimento_horizontes.py
- run_interpretability
- analise_experimento.py
- GLMBinomialNegativa
- PredictRequest
- teste_prospectivo.py
- Preditor
- TestMultiDoenca
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- ml_orchestrator.py
- mini_panel
- TestSemVazamento
- ingestor_ibge_populacao.py
- pre-commit
- analise_efeito/__init__.py
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

## Communities (37 total, 3 thin omitted)

### Community 0 - "experimento_v5.py"
Cohesion: 0.10
Nodes (33): aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray, Path, Combinação modelo + persistência (docs/PROTOCOLO_V5.md, desvio de 2026-11-04,… (+25 more)

### Community 1 - "get_feature_columns"
Cohesion: 0.17
Nodes (15): _anomalia_expanding(), get_feature_columns(), grupos_de_features(), is_clima_parcimonioso(), is_suscetibilidade(), _prefixo_doenca(), DataFrame, Series (+7 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.11
Nodes (32): api_cenario(), api_cidades(), api_confiabilidade(), api_doencas(), api_historico(), api_modelo_info(), api_municipios(), api_previsao() (+24 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.29
Nodes (10): fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima(), process_saude() (+2 more)

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

### Community 9 - "app.js"
Cohesion: 0.19
Nodes (27): api(), ativarAba(), atualizarLoader(), carregando, carregarCenario(), carregarConfiabilidade(), carregarPrevisao(), carregarRanking() (+19 more)

### Community 10 - "test_prediction_service.py"
Cohesion: 0.09
Nodes (32): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+24 more)

### Community 11 - "build_ml_features"
Cohesion: 0.14
Nodes (10): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, TestFeaturesV5, Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação. (+2 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "schemas.py"
Cohesion: 0.27
Nodes (10): api_ranking(), Cidades ordenadas pela probabilidade de risco alto (relativo ao histórico de…, BaseModel, CenarioResponse, PontoCenario, PrevisaoMesResponse, RankingItem, RankingResponse (+2 more)

### Community 16 - "FonteDados"
Cohesion: 0.06
Nodes (22): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md,…, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades… (+14 more)

### Community 17 - "_expanding_window_splits"
Cohesion: 0.16
Nodes (13): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No… (+5 more)

### Community 18 - "TestModelTraining"
Cohesion: 0.40
Nodes (3): Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 19 - "main.py"
Cohesion: 0.08
Nodes (40): command_analise(), command_atualizar_dados(), command_dlnm(), command_experimento(), command_experimento_v5(), command_export_dashboard(), command_modelo_risco(), command_serve() (+32 more)

### Community 20 - "experimento_horizontes.py"
Cohesion: 0.06
Nodes (51): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, build_base_panel(), DataFrame, Path, Módulo responsável por construir o painel base a partir do banco de dados…, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, validate_panel() (+43 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "analise_experimento.py"
Cohesion: 0.22
Nodes (18): bootstrap_delta_mae(), decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê… (+10 more)

### Community 23 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 24 - "PredictRequest"
Cohesion: 0.28
Nodes (5): field_validator, PredictRequest, parametrize, TestNiveis, TestSchemas

### Community 25 - "teste_prospectivo.py"
Cohesion: 0.11
Nodes (32): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), fit_predict_fold(), limiares_por_cidade(), _persist_col(), DataFrame, ndarray (+24 more)

### Community 26 - "Preditor"
Cohesion: 0.14
Nodes (14): nivel_por_probabilidade(), Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., CidadeNaoEncontrada, _fmt_mes(), ModeloIndisponivel, Preditor, DataFrame, RuntimeError (+6 more)

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
Cohesion: 0.32
Nodes (7): DataFrame, Path, Orquestrador MLOps principal v4 (multi-doença). Acopla ingestão, validação,…, Executa o pipeline completo de ML (hiperparâmetros fixos, sem tunagem). Args:…, Executa o pipeline para uma doença específica., run_pipeline(), _run_single_disease()

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 33 - "ingestor_ibge_populacao.py"
Cohesion: 0.32
Nodes (7): fetch_populacao_ibge(), get_ibge_7(), main(), DataFrame, ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API…, Busca população estimada do IBGE via API SIDRA (tabela 6579)., Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos.

### Community 38 - "api_predict"
Cohesion: 0.40
Nodes (5): api_predict(), api_recarregar(), Previsão de casos para um município, doença e horizonte (1–3 meses). Rota…, Relê o banco depois de uma ingestão (protegido pela variável de ambiente…, post

## Knowledge Gaps
- **63 isolated node(s):** `MESES_LONGO`, `NIVEIS`, `COR`, `layoutBase`, `cfgPlot` (+58 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 267 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `experimento_v5.py`, `get_feature_columns`, `TestSemVazamento`, `test_prediction_service.py`, `FonteDados`, `_expanding_window_splits`, `experimento_horizontes.py`, `teste_prospectivo.py`, `TestMultiDoenca`, `ml_orchestrator.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `experimento_horizontes.py` to `experimento_v5.py`, `dlnm.py`, `FonteDados`, `main.py`, `analise_experimento.py`, `teste_prospectivo.py`, `ml_orchestrator.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `get_feature_columns()` connect `get_feature_columns` to `experimento_v5.py`, `TestSemVazamento`, `test_prediction_service.py`, `build_ml_features`, `_expanding_window_splits`, `experimento_horizontes.py`, `analise_experimento.py`, `teste_prospectivo.py`, `TestMultiDoenca`, `ml_orchestrator.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `FonteDados` (e.g. with `Cenarios` and `Preditor`) actually correct?**
  _`FonteDados` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `NIVEIS`, `COR` to the rest of the system?**
  _63 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `experimento_v5.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09986504723346828 - nodes in this community are weakly interconnected._