# Graph Report - Projeto_Clima_X_Dengue  (2026-11-07)

## Corpus Check
- 66 files · ~60,458 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 940 nodes · 2054 edges · 55 communities (45 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 72 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2e175b8d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_experimento.py
- experimento_horizontes.py
- charts.js
- server.py
- ingestor_api_sul.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- experimento_v5.py
- .prever
- Plano v5 — Limpeza e Resultado Publicável
- ingestor_sinan_sorotipo.py
- TestAplicacaoV51
- ml_orchestrator.py
- .features_previsao
- main.py
- experimento_v7.py
- run_interpretability
- build_ml_features
- Preditor
- predictor.py
- fit_predict_fold
- Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)
- analise_experimento.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- avaliar
- mini_panel
- test_prediction_service.py
- export_dashboard.py
- pre-commit
- analise_efeito/__init__.py
- get_feature_columns
- hf_space/README.md
- test_experimento_v7.py
- TestFeatureEngineering
- grupos_de_features
- Protocolo v7 — Pré-registro
- test_sorotipo.py
- Protocolo v6 — Pré-registro
- artefatos.py
- .test_pipeline_end_to_end
- TestRt
- experimento_v6.py
- main.js
- avaliar
- Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)
- painel_grade

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 47 edges
2. `get_feature_columns()` - 46 edges
3. `Preditor` - 40 edges
4. `build_base_panel()` - 32 edges
5. `FonteDados` - 32 edges
6. `fit_predict_fold()` - 30 edges
7. `configurar_log()` - 26 edges
8. `limiares_por_cidade()` - 20 edges
9. `_expanding_window_splits()` - 20 edges
10. `main()` - 19 edges

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

## Communities (55 total, 5 thin omitted)

### Community 0 - "test_experimento.py"
Cohesion: 0.14
Nodes (18): avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas., avaliar_2025(), HoldoutJaUsado (+10 more)

### Community 1 - "experimento_horizontes.py"
Cohesion: 0.27
Nodes (10): _linha(), metricas_de_oof(), DataFrame, Path, Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline., Executa o experimento completo e grava os resultados. Retorna o DataFrame de…, Roda os 4 modelos + 2 baselines em todos os folds. Retorna (oof_wide,… (+2 more)

### Community 2 - "charts.js"
Cohesion: 0.80
Nodes (4): getPlotlyConfig(), getPlotlyLayout(), renderChartHeatmap(), renderChartSazonal()

### Community 3 - "server.py"
Cohesion: 0.09
Nodes (39): api_cenario(), api_cidades(), api_confiabilidade(), api_doencas(), api_historico(), api_modelo_info(), api_municipios(), api_predict() (+31 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.17
Nodes (17): agregar_infodengue_mensal(), fetch_clima(), fetch_infodengue(), fetch_infodengue_semanal(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude() (+9 more)

### Community 5 - "dlnm.py"
Cohesion: 0.16
Nodes (21): ajustar(), _coef_cov(), cross_basis(), plotar(), preparar(), DataFrame, ndarray, Path (+13 more)

### Community 6 - "atualizacao_incremental.py"
Cohesion: 0.08
Nodes (47): Connection, date, atualizar(), atualizar_enso(), cidades_do_banco(), coletar_clima(), coletar_clima_historico(), coletar_saude() (+39 more)

### Community 7 - "🦟 Clima × Arboviroses"
Cohesion: 0.13
Nodes (15): A aplicação, Arquitetura, 🦟 Clima × Arboviroses, Como a IA foi usada, e onde ela foi barrada, Depois de 2026: o diagnóstico, a v6 e a v7, Em 30 segundos, Engenharia de dados, Estrutura (+7 more)

### Community 8 - "Plano de Experimento Final — Clima × Arboviroses"
Cohesion: 0.10
Nodes (19): 1.1 Variáveis do experimento, 1.2 O que muda em cada horizonte, 1.3 Métricas (fixadas agora, antes de rodar), 1.4 Validação, 1.5 Implementação, 4.1 Retreinar no painel completo (2015–2025), 4.2 Empacotar, 4.3 API de previsão (+11 more)

### Community 9 - "app.js"
Cohesion: 0.15
Nodes (34): alerta(), api(), ativarAba(), atualizarLoader(), carregando, carregarCenario(), carregarConfiabilidade(), carregarPrevisao() (+26 more)

### Community 10 - "experimento_v5.py"
Cohesion: 0.17
Nodes (18): Combinação modelo + persistência (docs/PROTOCOLO_V5.md, desvio de 2026-11-04,…, calibrar_temporal(), decidir(), efeitos(), nome(), preparar(), DataFrame, Path (+10 more)

### Community 11 - ".prever"
Cohesion: 0.17
Nodes (11): CidadeNaoEncontrada, _fmt_mes(), margem_modelo(), ModeloIndisponivel, DataFrame, ndarray, RuntimeError, "Quantos casos em <mês>?". Até 3 meses após o último mês consolidado: previsão… (+3 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "ingestor_sinan_sorotipo.py"
Cohesion: 0.22
Nodes (16): agregar(), baixar(), contar(), dir_cache(), executar(), ler_campos_dbf(), main(), processar_ano() (+8 more)

### Community 16 - "TestAplicacaoV51"
Cohesion: 0.09
Nodes (14): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md,…, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades… (+6 more)

### Community 17 - "ml_orchestrator.py"
Cohesion: 0.05
Nodes (39): evaluate_baselines(), GLMBinomialNegativa, _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, DataFrame, ndarray, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a… (+31 more)

### Community 18 - ".features_previsao"
Cohesion: 0.33
Nodes (3): DataFrame, Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com…, Painel + h meses futuros por cidade (após o último mês com alvo observado).

### Community 19 - "main.py"
Cohesion: 0.06
Nodes (58): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+50 more)

### Community 20 - "experimento_v7.py"
Cohesion: 0.07
Nodes (63): metricas(), base_v51(), decidir(), efeito(), preparar(), protocolo_registrado(), ProtocoloNaoRegistrado, DataFrame (+55 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "build_ml_features"
Cohesion: 0.23
Nodes (5): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, parametrize, TestFeaturesV5, TestFeaturesV6

### Community 23 - "Preditor"
Cohesion: 0.12
Nodes (9): FonteDados, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Preditor, Path, TestExperimentoV6, TestExperimentoV7, fixture, TestAPI (+1 more)

### Community 24 - "predictor.py"
Cohesion: 0.22
Nodes (12): BaseModel, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, CenarioResponse, FaixaMes, PontoCenario, PredictResponse, PrevisaoMesResponse (+4 more)

### Community 25 - "fit_predict_fold"
Cohesion: 0.12
Nodes (26): rodar(), alvo_treino(), _build_base_margin(), clip_outliers_per_city(), _expanding_window_splits(), fit_predict_fold(), limiares_por_cidade(), margem_persistencia() (+18 more)

### Community 26 - "Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)"
Cohesion: 0.33
Nodes (5): Chikungunya, Dengue, Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)

### Community 27 - "analise_experimento.py"
Cohesion: 0.19
Nodes (21): bootstrap_delta_mae(), decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê… (+13 more)

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "avaliar"
Cohesion: 0.10
Nodes (25): aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray, Path, w · modelo + (1 − w) · persistência; persistência ausente conta como zero… (+17 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "test_prediction_service.py"
Cohesion: 0.13
Nodes (15): field_validator, nivel_por_probabilidade(), Remove meses ingeridos menos de `dias` após o fim do mês: o InfoDengue ainda…, remover_meses_nao_consolidados(), aplicar_intervalo(), Intervalo de 90% a partir dos quantis de resíduo log1p calibrados no OOF., PredictRequest, artefatos() (+7 more)

### Community 33 - "export_dashboard.py"
Cohesion: 0.27
Nodes (10): _clean(), _code6(), exportar_dados_dashboard(), exportar_doenca(), _historico(), _mean(), DataFrame, Series (+2 more)

### Community 36 - "get_feature_columns"
Cohesion: 0.12
Nodes (19): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, get_feature_columns(), is_clima_parcimonioso(), is_imunidade_longa(), is_rt(), is_rt_bruto(), is_suscetibilidade() (+11 more)

### Community 38 - "test_experimento_v7.py"
Cohesion: 0.20
Nodes (6): painel_v7(), fixture, Protocolo v7: features de Rt, nível regional (GLM + reconciliação), sorotipo,…, 9 cidades (3 por UF) × 2010–2020, sazonal, com Rt; chikungunya só a partir de…, sorotipo_sint(), TestNivelRegional

### Community 39 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 40 - "grupos_de_features"
Cohesion: 0.22
Nodes (10): _anomalia_expanding(), grupos_de_features(), _incidencia_vizinhos(), DataFrame, Series, Grupos do protocolo v5: casos (sempre), clima_parcimonioso e suscetibilidade., Rolling por cidade aplicado sobre a série já deslocada (nunca inclui…, Anomalia = valor - média do MESMO mês nos anos ANTERIORES da mesma cidade.… (+2 more)

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

### Community 48 - "experimento_v6.py"
Cohesion: 0.13
Nodes (21): build_base_panel(), Path, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, git_commit(), features_variantes(), Experimento v6 (docs/PROTOCOLO_V6.md) — responde H6a (formulação), H6b…, Modelo v6 do modo sombra: configuração decidida em decisao.json, treinada com…, treinar_producao() (+13 more)

### Community 53 - "avaliar"
Cohesion: 0.25
Nodes (12): avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():…, Acrescenta as previsões do lote; ignora as que já tinham sido emitidas. Retorna…, Desempenho por doença × horizonte das previsões cujo mês-alvo já foi observado…, registrar() (+4 more)

### Community 54 - "Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)"
Cohesion: 0.25
Nodes (8): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa)

### Community 56 - "painel_grade"
Cohesion: 0.67
Nodes (3): painel_grade(), fixture, 12 cidades numa grade de coordenadas × 4 anos (para os vizinhos do protocolo…

## Knowledge Gaps
- **87 isolated node(s):** `MESES_LONGO`, `ICONE`, `NIVEIS`, `ORDEM_NIVEL`, `COR` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 366 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `test_experimento.py`, `experimento_horizontes.py`, `get_feature_columns`, `test_experimento_v7.py`, `TestFeatureEngineering`, `grupos_de_features`, `experimento_v5.py`, `.test_pipeline_end_to_end`, `TestRt`, `experimento_v6.py`, `ml_orchestrator.py`, `.features_previsao`, `main.py`, `experimento_v7.py`, `fit_predict_fold`, `analise_experimento.py`, `avaliar`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `test_experimento.py`, `test_prediction_service.py`, `server.py`, `test_experimento_v7.py`, `.prever`, `TestAplicacaoV51`, `avaliar`, `predictor.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `experimento_v6.py` to `test_experimento.py`, `experimento_horizontes.py`, `get_feature_columns`, `dlnm.py`, `experimento_v5.py`, `ml_orchestrator.py`, `.features_previsao`, `main.py`, `experimento_v7.py`, `analise_experimento.py`, `avaliar`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `FonteDados` (e.g. with `Cenarios` and `Preditor`) actually correct?**
  _`FonteDados` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `ICONE`, `NIVEIS` to the rest of the system?**
  _87 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_experimento.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13538461538461538 - nodes in this community are weakly interconnected._