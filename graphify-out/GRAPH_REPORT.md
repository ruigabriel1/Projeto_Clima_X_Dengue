# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 66 files · ~59,644 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 933 nodes · 2051 edges · 56 communities (49 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 73 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `39a8d3e7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- teste_final.py
- config.py
- main.js
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
- test_ml_pipeline.py
- clip_outliers_per_city
- main.py
- experimento_v7.py
- run_interpretability
- build_ml_features
- Preditor
- predictor.py
- test_experimento.py
- Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)
- analise_experimento.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- combinacao.py
- mini_panel
- PredictRequest
- GLMBinomialNegativa
- pre-commit
- analise_efeito/__init__.py
- get_feature_columns
- hf_space/README.md
- export_dashboard.py
- TestFeatureEngineering
- ml_orchestrator.py
- Protocolo v7 — Pré-registro
- test_sorotipo.py
- Protocolo v6 — Pré-registro
- artefatos.py
- .test_pipeline_end_to_end
- painel_grade
- experimento_horizontes.py
- build_base_panel
- grupos_de_features
- experimento_v6.py
- TestRt
- test_experimento_v7.py
- avaliar
- Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)

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

## Communities (56 total, 4 thin omitted)

### Community 0 - "teste_final.py"
Cohesion: 0.13
Nodes (17): avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas., avaliar_2025(), HoldoutJaUsado (+9 more)

### Community 1 - "config.py"
Cohesion: 0.21
Nodes (11): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, estatisticas_cidades(), main(), DataFrame, Path, Fase 4.1 — Modelo final para produção (docs/PLANO_EXPERIMENTO_FINAL.md).…, Treina e salva os modelos de produção. Retorna {doenca: metadata}., Nome, limiares de risco (histórico completo) e R² OOF por horizonte para cada… (+3 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.11
Nodes (31): api_cenario(), api_cidades(), api_confiabilidade(), api_historico(), api_modelo_info(), api_municipios(), api_predict(), api_previsao() (+23 more)

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
Cohesion: 0.19
Nodes (27): api(), ativarAba(), atualizarLoader(), carregando, carregarCenario(), carregarConfiabilidade(), carregarPrevisao(), carregarRanking() (+19 more)

### Community 10 - "experimento_v5.py"
Cohesion: 0.07
Nodes (49): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+41 more)

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

### Community 17 - "test_ml_pipeline.py"
Cohesion: 0.18
Nodes (13): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No… (+5 more)

### Community 18 - "clip_outliers_per_city"
Cohesion: 0.29
Nodes (5): clip_outliers_per_city(), Clipping P<percentile> **por cidade** usando o próprio df como referência.…, Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 19 - "main.py"
Cohesion: 0.08
Nodes (46): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+38 more)

### Community 20 - "experimento_v7.py"
Cohesion: 0.06
Nodes (71): git_commit(), base_v51(), decidir(), efeito(), preparar(), protocolo_registrado(), ProtocoloNaoRegistrado, DataFrame (+63 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "build_ml_features"
Cohesion: 0.20
Nodes (6): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, parametrize, TestFeaturesV5, TestFeaturesV6, Verifica que os lags de chikungunya são criados quando solicitado.

### Community 23 - "Preditor"
Cohesion: 0.10
Nodes (12): FonteDados, DataFrame, Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com…, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Painel + h meses futuros por cidade (após o último mês com alvo observado)., Preditor, Path, TestExperimentoV6 (+4 more)

### Community 24 - "predictor.py"
Cohesion: 0.19
Nodes (14): api_ranking(), Cidades ordenadas pela probabilidade de risco alto (relativo ao histórico de…, BaseModel, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, CenarioResponse, FaixaMes, PontoCenario (+6 more)

### Community 25 - "test_experimento.py"
Cohesion: 0.19
Nodes (18): alvo_treino(), _build_base_margin(), fit_predict_fold(), margem_persistencia(), _persist_col(), DataFrame, ndarray, Path (+10 more)

### Community 26 - "Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)"
Cohesion: 0.33
Nodes (5): Chikungunya, Dengue, Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)

### Community 27 - "analise_experimento.py"
Cohesion: 0.22
Nodes (18): bootstrap_delta_mae(), decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê… (+10 more)

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "combinacao.py"
Cohesion: 0.19
Nodes (15): aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray, Path, Combinação modelo + persistência (docs/PROTOCOLO_V5.md, desvio de 2026-11-04,… (+7 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "PredictRequest"
Cohesion: 0.24
Nodes (6): field_validator, nivel_por_probabilidade(), PredictRequest, parametrize, TestNiveis, TestSchemas

### Community 33 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 36 - "get_feature_columns"
Cohesion: 0.15
Nodes (16): get_feature_columns(), is_clima_parcimonioso(), is_imunidade_longa(), is_rt(), is_rt_bruto(), is_suscetibilidade(), is_vizinhos(), _prefixo_doenca() (+8 more)

### Community 38 - "export_dashboard.py"
Cohesion: 0.16
Nodes (16): api_doencas(), api_status(), Lista doenças com resultados exportados., _clean(), _code6(), doencas_exportadas(), exportar_dados_dashboard(), exportar_doenca() (+8 more)

### Community 39 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 40 - "ml_orchestrator.py"
Cohesion: 0.24
Nodes (10): DataFrame, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, validate_panel(), DataFrame, Path, Orquestrador MLOps principal v4 (multi-doença). Acopla ingestão, validação,…, Executa o pipeline completo de ML (hiperparâmetros fixos, sem tunagem). Args:…, Executa o pipeline para uma doença específica. (+2 more)

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

### Community 46 - "painel_grade"
Cohesion: 0.67
Nodes (3): painel_grade(), fixture, 12 cidades numa grade de coordenadas × 4 anos (para os vizinhos do protocolo…

### Community 47 - "experimento_horizontes.py"
Cohesion: 0.24
Nodes (13): _linha(), metricas_de_oof(), nome_config(), preparar_dados(), DataFrame, Path, Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline. (+5 more)

### Community 48 - "build_base_panel"
Cohesion: 0.31
Nodes (8): build_base_panel(), Path, Módulo responsável por construir o painel base a partir do banco de dados…, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, _raiz(), Painel com histórico estendido e Rt (protocolo v7): o padrão continua sendo o…, test_historico_estendido_com_rt_e_meses_de_aquecimento(), test_padrao_igual_ao_painel_dos_experimentos()

### Community 49 - "grupos_de_features"
Cohesion: 0.20
Nodes (10): _anomalia_expanding(), grupos_de_features(), _incidencia_vizinhos(), DataFrame, Series, Grupos do protocolo v5: casos (sempre), clima_parcimonioso e suscetibilidade., Rolling por cidade aplicado sobre a série já deslocada (nunca inclui…, Anomalia = valor - média do MESMO mês nos anos ANTERIORES da mesma cidade.… (+2 more)

### Community 50 - "experimento_v6.py"
Cohesion: 0.20
Nodes (9): features_variantes(), Experimento v6 (docs/PROTOCOLO_V6.md) — responde H6a (formulação), H6b…, rodar(), _expanding_window_splits(), limiares_por_cidade(), Series, Quantil q (0–1) de `col` por cidade, calculado em df_ref (tipicamente o…, Gera splits Expanding Window (Walk Forward): Treina em anos < t, testa no ano… (+1 more)

### Community 52 - "test_experimento_v7.py"
Cohesion: 0.20
Nodes (6): painel_v7(), fixture, Protocolo v7: features de Rt, nível regional (GLM + reconciliação), sorotipo,…, 9 cidades (3 por UF) × 2010–2020, sazonal, com Rt; chikungunya só a partir de…, sorotipo_sint(), TestNivelRegional

### Community 53 - "avaliar"
Cohesion: 0.25
Nodes (12): avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():…, Acrescenta as previsões do lote; ignora as que já tinham sido emitidas. Retorna…, Desempenho por doença × horizonte das previsões cujo mês-alvo já foi observado…, registrar() (+4 more)

### Community 54 - "Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)"
Cohesion: 0.25
Nodes (8): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa)

## Knowledge Gaps
- **85 isolated node(s):** `MESES_LONGO`, `NIVEIS`, `COR`, `layoutBase`, `cfgPlot` (+80 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 358 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `get_feature_columns`, `TestFeatureEngineering`, `ml_orchestrator.py`, `experimento_v5.py`, `.test_pipeline_end_to_end`, `experimento_horizontes.py`, `grupos_de_features`, `experimento_v6.py`, `TestRt`, `experimento_v7.py`, `test_experimento_v7.py`, `test_ml_pipeline.py`, `Preditor`, `test_experimento.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `server.py`, `experimento_v5.py`, `.prever`, `TestAplicacaoV51`, `test_experimento_v7.py`, `avaliar`, `predictor.py`, `test_experimento.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `build_base_panel` to `teste_final.py`, `config.py`, `get_feature_columns`, `dlnm.py`, `ml_orchestrator.py`, `experimento_v5.py`, `experimento_horizontes.py`, `experimento_v6.py`, `main.py`, `experimento_v7.py`, `Preditor`, `analise_experimento.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `FonteDados` (e.g. with `Cenarios` and `Preditor`) actually correct?**
  _`FonteDados` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `NIVEIS`, `COR` to the rest of the system?**
  _85 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `teste_final.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12681159420289856 - nodes in this community are weakly interconnected._