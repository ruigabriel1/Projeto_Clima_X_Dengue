# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 61 files · ~52,697 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 822 nodes · 1766 edges · 41 communities (36 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 67 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7c1bdffe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_experimento.py
- experimento_v6.py
- main.js
- get_preditor
- ingestor_api_sul.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- experimento_v5.py
- test_prediction_service.py
- Plano v5 — Limpeza e Resultado Publicável
- alerta_risco.py
- TestAplicacaoV51
- evaluate_baselines
- clip_outliers_per_city
- main.py
- teste_prospectivo.py
- run_interpretability
- build_ml_features
- Preditor
- server.py
- experimento_horizontes.py
- Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)
- artefatos.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- artefatos
- mini_panel
- PredictRequest
- pre-commit
- analise_efeito/__init__.py
- hf_space/README.md
- TestFeatureEngineering
- get_feature_columns
- Protocolo v7 — Pré-registro
- Protocolo v6 — Pré-registro
- .test_pipeline_end_to_end

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 43 edges
2. `get_feature_columns()` - 40 edges
3. `Preditor` - 34 edges
4. `build_base_panel()` - 30 edges
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
- `_erro_http()` --uses--> `CidadeNaoEncontrada`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `_erro_http()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_cenario()` --uses--> `CenarioResponse`  [INFERRED]
  app/server.py → src/prediction_service/schemas.py

## Import Cycles
- None detected.

## Communities (41 total, 3 thin omitted)

### Community 0 - "test_experimento.py"
Cohesion: 0.05
Nodes (62): bootstrap_delta_mae(), decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê… (+54 more)

### Community 1 - "experimento_v6.py"
Cohesion: 0.11
Nodes (28): base_v51(), decidir(), efeito(), features_variantes(), preparar(), protocolo_registrado(), ProtocoloNaoRegistrado, DataFrame (+20 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "get_preditor"
Cohesion: 0.13
Nodes (21): api_cenario(), api_confiabilidade(), api_historico(), api_modelo_info(), api_municipios(), api_previsao(), api_resultados(), _erro_http() (+13 more)

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
Cohesion: 0.08
Nodes (22): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa) (+14 more)

### Community 8 - "Plano de Experimento Final — Clima × Arboviroses"
Cohesion: 0.10
Nodes (19): 1.1 Variáveis do experimento, 1.2 O que muda em cada horizonte, 1.3 Métricas (fixadas agora, antes de rodar), 1.4 Validação, 1.5 Implementação, 4.1 Retreinar no painel completo (2015–2025), 4.2 Empacotar, 4.3 API de previsão (+11 more)

### Community 9 - "app.js"
Cohesion: 0.19
Nodes (27): api(), ativarAba(), atualizarLoader(), carregando, carregarCenario(), carregarConfiabilidade(), carregarPrevisao(), carregarRanking() (+19 more)

### Community 10 - "experimento_v5.py"
Cohesion: 0.11
Nodes (32): aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray, Path, Combinação modelo + persistência (docs/PROTOCOLO_V5.md, desvio de 2026-11-04,… (+24 more)

### Community 11 - "test_prediction_service.py"
Cohesion: 0.14
Nodes (17): nivel_por_probabilidade(), aplicar_intervalo(), CidadeNaoEncontrada, _fmt_mes(), margem_modelo(), ModeloIndisponivel, DataFrame, ndarray (+9 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "alerta_risco.py"
Cohesion: 0.21
Nodes (16): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+8 more)

### Community 16 - "TestAplicacaoV51"
Cohesion: 0.10
Nodes (13): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades…, Faixa (× fator climático) para os `meses` seguintes ao último mês consolidado. (+5 more)

### Community 17 - "evaluate_baselines"
Cohesion: 0.10
Nodes (19): evaluate_baselines(), GLMBinomialNegativa, _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, DataFrame, ndarray, Prediz casos a partir do GLM ajustado. (+11 more)

### Community 18 - "clip_outliers_per_city"
Cohesion: 0.25
Nodes (6): clip_outliers_per_city(), Series, Clipping P<percentile> **por cidade** usando o próprio df como referência.…, Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 19 - "main.py"
Cohesion: 0.07
Nodes (49): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+41 more)

### Community 20 - "teste_prospectivo.py"
Cohesion: 0.24
Nodes (12): avaliar(), HoldoutJaUsado, markdown(), meses_consolidados(), _metricas(), DataFrame, Path, RuntimeError (+4 more)

### Community 21 - "run_interpretability"
Cohesion: 0.14
Nodes (26): DataFrame, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, validate_panel(), compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame (+18 more)

### Community 22 - "build_ml_features"
Cohesion: 0.11
Nodes (16): _anomalia_expanding(), build_ml_features(), grupos_de_features(), _incidencia_vizinhos(), DataFrame, Series, Constrói as features a partir do painel base. Args: panel: saída de…, Grupos do protocolo v5: casos (sempre), clima_parcimonioso e suscetibilidade. (+8 more)

### Community 23 - "Preditor"
Cohesion: 0.14
Nodes (7): FonteDados, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Preditor, Path, TestExperimentoV6, TestAPI, TestPreditor

### Community 24 - "server.py"
Cohesion: 0.13
Nodes (24): api_cidades(), api_doencas(), api_ranking(), api_status(), lifespan(), server.py — FastAPI backend para a interface Prodígia. Rotas: status do banco,…, Cidades ordenadas pela probabilidade de risco alto (relativo ao histórico de…, Aquece o preditor (painel + features de previsão) em segundo plano, sem… (+16 more)

### Community 25 - "experimento_horizontes.py"
Cohesion: 0.10
Nodes (29): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, git_commit(), preparar_dados(), Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Features para (doença, h) usando só anos ≤ ano_max; remove linhas sem alvo., alvo_treino(), _build_base_margin(), fit_predict_fold() (+21 more)

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

### Community 30 - "artefatos"
Cohesion: 0.67
Nodes (3): artefatos(), fixture, Experimento v5 + modelos de risco no painel sintético (com clima e…

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "PredictRequest"
Cohesion: 0.20
Nodes (9): api_predict(), api_recarregar(), Previsão de casos para um município, doença e horizonte (1–3 meses). Rota…, Relê o banco depois de uma ingestão (protegido pela variável de ambiente…, field_validator, post, PredictRequest, parametrize (+1 more)

### Community 39 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 40 - "get_feature_columns"
Cohesion: 0.12
Nodes (17): Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Módulo responsável por construir o painel base a partir do banco de dados…, get_feature_columns(), is_clima_parcimonioso(), is_imunidade_longa(), is_suscetibilidade(), is_vizinhos(), _prefixo_doenca() (+9 more)

### Community 41 - "Protocolo v7 — Pré-registro"
Cohesion: 0.18
Nodes (10): Base e candidatas (fixas), Dados, Desvios, Exploratório (não entra na decisão), Hipóteses, O que já se sabia (e motivou a v7), Protocolo v7 — Pré-registro, Regra de decisão (sequencial, fixa, por doença) (+2 more)

### Community 43 - "Protocolo v6 — Pré-registro"
Cohesion: 0.20
Nodes (9): Desvios, Exploratório (não entra na decisão), Hipóteses, Motivação (o que a v5 errou), Mudanças candidatas (fixas), Protocolo v6 — Pré-registro, Regra de decisão (sequencial, fixa), Teste: modo sombra prospectivo (uso único) (+1 more)

### Community 45 - ".test_pipeline_end_to_end"
Cohesion: 0.25
Nodes (5): parametrize, Testa o fluxo completo: features → treino → predição, por doença., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., TestIntegration

## Knowledge Gaps
- **84 isolated node(s):** `MESES_LONGO`, `NIVEIS`, `COR`, `layoutBase`, `cfgPlot` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 324 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `test_experimento.py`, `experimento_v6.py`, `TestFeatureEngineering`, `get_feature_columns`, `experimento_v5.py`, `.test_pipeline_end_to_end`, `alerta_risco.py`, `evaluate_baselines`, `teste_prospectivo.py`, `run_interpretability`, `experimento_horizontes.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `test_experimento.py`, `get_preditor`, `atualizacao_incremental.py`, `test_prediction_service.py`, `TestAplicacaoV51`, `server.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `test_experimento.py` to `experimento_v6.py`, `dlnm.py`, `get_feature_columns`, `experimento_v5.py`, `main.py`, `teste_prospectivo.py`, `run_interpretability`, `experimento_horizontes.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `NIVEIS`, `COR` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_experimento.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05109218807848945 - nodes in this community are weakly interconnected._
- **Should `experimento_v6.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11363636363636363 - nodes in this community are weakly interconnected._