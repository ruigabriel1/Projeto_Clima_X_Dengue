# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 66 files · ~57,771 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 917 nodes · 1984 edges · 46 communities (41 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 69 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `79ad5418`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- build_base_panel
- alerta_risco.py
- main.js
- server.py
- ingestor_api_sul.py
- dlnm.py
- config.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- experimento_v5.py
- .prever
- Plano v5 — Limpeza e Resultado Publicável
- ingestor_sinan_sorotipo.py
- TestAplicacaoV51
- baselines.py
- _expanding_window_splits
- main.py
- experimento_v7.py
- run_interpretability
- build_ml_features
- Preditor
- predictor.py
- model_training.py
- Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)
- nivel_regional.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- Cenarios
- mini_panel
- test_prediction_service.py
- GLMBinomialNegativa
- pre-commit
- analise_efeito/__init__.py
- get_feature_columns
- hf_space/README.md
- .features_previsao
- TestFeatureEngineering
- ml_orchestrator.py
- Protocolo v7 — Pré-registro
- test_sorotipo.py
- Protocolo v6 — Pré-registro
- TestMultiDoenca
- test_experimento.py

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 47 edges
2. `get_feature_columns()` - 46 edges
3. `Preditor` - 34 edges
4. `build_base_panel()` - 32 edges
5. `fit_predict_fold()` - 29 edges
6. `FonteDados` - 27 edges
7. `configurar_log()` - 25 edges
8. `limiares_por_cidade()` - 20 edges
9. `_expanding_window_splits()` - 20 edges
10. `treinar_modelos_risco()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `api_predict()` --uses--> `CidadeNaoEncontrada`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_predict()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `_erro_http()` --uses--> `CidadeNaoEncontrada`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `_erro_http()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `TestMultiDoenca` --uses--> `PersistenciaBaseline`  [INFERRED]
  tests/test_ml_pipeline.py → src/ml_pipeline/baselines.py

## Import Cycles
- None detected.

## Communities (46 total, 3 thin omitted)

### Community 0 - "build_base_panel"
Cohesion: 0.06
Nodes (55): decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê…, Treina o modelo COM clima em 2015–2024 e devolve o ranking SHAP (média |SHAP|). (+47 more)

### Community 1 - "alerta_risco.py"
Cohesion: 0.12
Nodes (26): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+18 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.05
Nodes (62): api_cenario(), api_cidades(), api_confiabilidade(), api_doencas(), api_historico(), api_modelo_info(), api_municipios(), api_predict() (+54 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.17
Nodes (17): agregar_infodengue_mensal(), fetch_clima(), fetch_infodengue(), fetch_infodengue_semanal(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude() (+9 more)

### Community 5 - "dlnm.py"
Cohesion: 0.16
Nodes (21): ajustar(), _coef_cov(), cross_basis(), plotar(), preparar(), DataFrame, ndarray, Path (+13 more)

### Community 6 - "config.py"
Cohesion: 0.06
Nodes (60): Connection, date, Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():… (+52 more)

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
Nodes (49): bootstrap_delta_mae(), ΔMAE = MAE(a) − MAE(b) com IC 95% por bootstrap de CIDADES (preserva a…, aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray (+41 more)

### Community 11 - ".prever"
Cohesion: 0.19
Nodes (11): LookupError, CidadeNaoEncontrada, _fmt_mes(), margem_modelo(), ModeloIndisponivel, DataFrame, ndarray, RuntimeError (+3 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "ingestor_sinan_sorotipo.py"
Cohesion: 0.23
Nodes (15): agregar(), baixar(), contar(), dir_cache(), executar(), ler_campos_dbf(), processar_ano(), DataFrame (+7 more)

### Community 16 - "TestAplicacaoV51"
Cohesion: 0.15
Nodes (6): CurvaClima, ndarray, Curva exposição-resposta do DLNM reduzida à parte quente e monotônica., (fator, lo, hi) do risco para t_normal + delta em relação a t_normal., Produção v5.1: previsão por mês, ranking, cenário, monitoramento e endpoints., TestAplicacaoV51

### Community 17 - "baselines.py"
Cohesion: 0.21
Nodes (10): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No… (+2 more)

### Community 18 - "_expanding_window_splits"
Cohesion: 0.15
Nodes (10): clip_outliers_per_city(), _expanding_window_splits(), Series, Clipping P<percentile> **por cidade** usando o próprio df como referência.…, Gera splits Expanding Window (Walk Forward): Treina em anos < t, testa no ano…, TestSemVazamento, Testes unitários para o pipeline ML v4 (multi-doença). Testa a feature…, Garante que clipping é por cidade e não global. (+2 more)

### Community 19 - "main.py"
Cohesion: 0.06
Nodes (53): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+45 more)

### Community 20 - "experimento_v7.py"
Cohesion: 0.06
Nodes (58): git_commit(), base_v51(), decidir(), efeito(), features_variantes(), preparar(), protocolo_registrado(), ProtocoloNaoRegistrado (+50 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "build_ml_features"
Cohesion: 0.17
Nodes (7): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, parametrize, TestFeaturesV5, TestFeaturesV6, parametrize, TestRt

### Community 23 - "Preditor"
Cohesion: 0.17
Nodes (6): FonteDados, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Preditor, Path, TestAPI, TestPreditor

### Community 24 - "predictor.py"
Cohesion: 0.25
Nodes (5): Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md,…, Fonte de dados do serviço de previsão. A fonte de verdade é o SQLite…, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, FaixaMes

### Community 25 - "model_training.py"
Cohesion: 0.21
Nodes (13): alvo_treino(), _build_base_margin(), _persist_col(), DataFrame, ndarray, Path, Módulo de treinamento do motor de ML v4 (multi-doença, multi-horizonte). Isola…, Offset = log(pop / 100.000) para modelar incidência, não contagem bruta. (+5 more)

### Community 26 - "Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)"
Cohesion: 0.33
Nodes (5): Chikungunya, Dengue, Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)

### Community 27 - "nivel_regional.py"
Cohesion: 0.21
Nodes (19): ajustar(), _completas(), desenho(), _matriz(), nomes_coef(), novidade_sorotipo(), prever(), DataFrame (+11 more)

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "Cenarios"
Cohesion: 0.28
Nodes (6): Cenarios, DataFrame, Path, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades…, Faixa (× fator climático) para os `meses` seguintes ao último mês consolidado., P10/P50/P90 dos casos por mês-calendário (índice 1–12). code='sul' soma a…

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "test_prediction_service.py"
Cohesion: 0.18
Nodes (9): nivel_por_probabilidade(), aplicar_intervalo(), Intervalo de 90% a partir dos quantis de resíduo log1p calibrados no OOF., artefatos(), fixture, Testes do serviço de previsão v5 (alerta de risco): schemas, níveis, intervalo,…, Experimento v5 + modelos de risco no painel sintético (com clima e…, TestIntervalo (+1 more)

### Community 33 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 36 - "get_feature_columns"
Cohesion: 0.11
Nodes (25): _anomalia_expanding(), get_feature_columns(), grupos_de_features(), _incidencia_vizinhos(), is_clima_parcimonioso(), is_imunidade_longa(), is_rt(), is_rt_bruto() (+17 more)

### Community 38 - ".features_previsao"
Cohesion: 0.33
Nodes (3): DataFrame, Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com…, Painel + h meses futuros por cidade (após o último mês com alvo observado).

### Community 39 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 40 - "ml_orchestrator.py"
Cohesion: 0.32
Nodes (7): DataFrame, Path, Orquestrador MLOps principal v4 (multi-doença). Acopla ingestão, validação,…, Executa o pipeline completo de ML (hiperparâmetros fixos, sem tunagem). Args:…, Executa o pipeline para uma doença específica., run_pipeline(), _run_single_disease()

### Community 41 - "Protocolo v7 — Pré-registro"
Cohesion: 0.18
Nodes (10): Base e candidatas (fixas), Dados, Desvios, Exploratório (não entra na decisão), Hipóteses, O que já se sabia (e motivou a v7), Protocolo v7 — Pré-registro, Regra de decisão (sequencial, fixa, por doença) (+2 more)

### Community 42 - "test_sorotipo.py"
Cohesion: 0.47
Nodes (5): _dbf(), Leitura do SINAN (DBF) e contagem de sorotipos por UF × mês (protocolo v7,…, Escreve um .dbf mínimo (campos texto/data de tamanho fixo)., test_campo_ausente_e_vazio(), test_le_campos_e_conta_por_uf_mes()

### Community 43 - "Protocolo v6 — Pré-registro"
Cohesion: 0.20
Nodes (9): Desvios, Exploratório (não entra na decisão), Hipóteses, Motivação (o que a v5 errou), Mudanças candidatas (fixas), Protocolo v6 — Pré-registro, Regra de decisão (sequencial, fixa), Teste: modo sombra prospectivo (uso único) (+1 more)

### Community 45 - "TestMultiDoenca"
Cohesion: 0.18
Nodes (8): parametrize, Verifica que os lags de chikungunya são criados quando solicitado., Testa o fluxo completo: features → treino → predição, por doença., Testa que o pipeline funciona para cada doença suportada., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., TestIntegration, TestMultiDoenca

### Community 46 - "test_experimento.py"
Cohesion: 0.17
Nodes (9): is_climate_feature(), True se a feature é derivada de variáveis climáticas/ENSO., margem_persistencia(), Offset da formulação A (v6): log(casos[t−h] + 1). Persistência ausente conta…, painel_grade(), fixture, Testes do experimento final (Fases 1–3): métricas, ausência de vazamento e…, 12 cidades numa grade de coordenadas × 4 anos (para os vizinhos do protocolo… (+1 more)

## Knowledge Gaps
- **84 isolated node(s):** `MESES_LONGO`, `NIVEIS`, `COR`, `layoutBase`, `cfgPlot` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 355 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `build_base_panel`, `alerta_risco.py`, `get_feature_columns`, `.features_previsao`, `TestFeatureEngineering`, `ml_orchestrator.py`, `experimento_v5.py`, `TestMultiDoenca`, `test_experimento.py`, `baselines.py`, `_expanding_window_splits`, `experimento_v7.py`, `predictor.py`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `build_base_panel` to `alerta_risco.py`, `dlnm.py`, `.features_previsao`, `ml_orchestrator.py`, `experimento_v5.py`, `main.py`, `experimento_v7.py`, `predictor.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `test_prediction_service.py`, `server.py`, `config.py`, `.prever`, `test_experimento.py`, `TestAplicacaoV51`, `predictor.py`, `Cenarios`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `NIVEIS`, `COR` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `build_base_panel` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `alerta_risco.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12169312169312169 - nodes in this community are weakly interconnected._