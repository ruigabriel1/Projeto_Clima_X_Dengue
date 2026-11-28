# Graph Report - Projeto_Clima_X_Dengue  (2026-11-28)

## Corpus Check
- 70 files · ~66,322 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 997 nodes · 2196 edges · 60 communities (49 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `eb9351a0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- server.py
- run_interpretability
- charts.js
- get_feature_columns
- ingestor_api_sul.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Prodigia
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- Preditor
- .prever
- Plano v5 — Limpeza e Resultado Publicável
- ingestor_sinan_sorotipo.py
- TestAplicacaoV51
- comparacao_algoritmos.py
- baselines.py
- main.py
- experimento_v7.py
- combinacao.py
- build_ml_features
- experimento_v6.py
- nivel_regional.py
- test_experimento.py
- README.md
- test_site_estatico.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- analise_experimento.py
- mini_panel
- predictor.py
- experimento_horizontes.py
- pre-commit
- analise_efeito/__init__.py
- build_base_panel
- hf_space/README.md
- TestFeatureEngineering
- TestMultiDoenca
- modelo_final.py
- Protocolo v7 — Pré-registro
- test_sorotipo.py
- Protocolo v6 — Pré-registro
- artefatos.py
- grupos_de_features
- experimento_v5.py
- test_prediction_service.py
- PredictRequest
- main.js
- test_experimento_v7.py
- TestSemVazamento
- Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)
- TestRt
- teste_final.py
- TestNivelRegional
- lifespan
- painel_grade

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 49 edges
2. `get_feature_columns()` - 48 edges
3. `Preditor` - 40 edges
4. `build_base_panel()` - 34 edges
5. `fit_predict_fold()` - 32 edges
6. `FonteDados` - 32 edges
7. `configurar_log()` - 28 edges
8. `limiares_por_cidade()` - 22 edges
9. `_expanding_window_splits()` - 22 edges
10. `main()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `api_predict()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_predict()` --uses--> `PredictRequest`  [INFERRED]
  app/server.py → src/prediction_service/schemas.py
- `_erro_http()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_ranking()` --uses--> `RankingItem`  [INFERRED]
  app/server.py → src/prediction_service/schemas.py
- `api_ranking()` --uses--> `RankingResponse`  [INFERRED]
  app/server.py → src/prediction_service/schemas.py

## Import Cycles
- None detected.

## Communities (60 total, 7 thin omitted)

### Community 0 - "server.py"
Cohesion: 0.09
Nodes (45): api_cenario(), api_cidades(), api_confiabilidade(), api_doencas(), api_historico(), api_modelo_info(), api_municipios(), api_predict() (+37 more)

### Community 1 - "run_interpretability"
Cohesion: 0.16
Nodes (23): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+15 more)

### Community 2 - "charts.js"
Cohesion: 0.80
Nodes (4): getPlotlyConfig(), getPlotlyLayout(), renderChartHeatmap(), renderChartSazonal()

### Community 3 - "get_feature_columns"
Cohesion: 0.12
Nodes (19): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, get_feature_columns(), is_clima_parcimonioso(), is_imunidade_longa(), is_rt(), is_rt_bruto(), is_suscetibilidade(), is_vizinhos() (+11 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.17
Nodes (17): agregar_infodengue_mensal(), fetch_clima(), fetch_infodengue(), fetch_infodengue_semanal(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude() (+9 more)

### Community 5 - "dlnm.py"
Cohesion: 0.16
Nodes (21): ajustar(), _coef_cov(), cross_basis(), plotar(), preparar(), DataFrame, ndarray, Path (+13 more)

### Community 6 - "atualizacao_incremental.py"
Cohesion: 0.06
Nodes (59): Connection, date, avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():…, Acrescenta as previsões do lote; ignora as que já tinham sido emitidas. Retorna… (+51 more)

### Community 7 - "🦟 Prodigia"
Cohesion: 0.10
Nodes (20): A aplicação: Prodigia, [▶ Abrir o Prodigia](https://ruigabriel1.github.io/Projeto_Clima_X_Dengue/), Alerta de risco de dengue e chikungunya para os 1.190 municípios do Sul do Brasil, Arquitetura, Cinco algoritmos no mesmo problema, Como a IA foi usada, e onde ela foi barrada, Depois de 2026: o diagnóstico, a v6 e a v7, El Niño e La Niña: fora da versão atual, exploratório para as próximas (+12 more)

### Community 8 - "Plano de Experimento Final — Clima × Arboviroses"
Cohesion: 0.10
Nodes (19): 1.1 Variáveis do experimento, 1.2 O que muda em cada horizonte, 1.3 Métricas (fixadas agora, antes de rodar), 1.4 Validação, 1.5 Implementação, 4.1 Retreinar no painel completo (2015–2025), 4.2 Empacotar, 4.3 API de previsão (+11 more)

### Community 9 - "app.js"
Cohesion: 0.11
Nodes (46): alerta(), api(), apiEstatica(), aplicarTema(), ativarAba(), atualizarLoader(), autocompletar(), cacheDados (+38 more)

### Community 10 - "Preditor"
Cohesion: 0.10
Nodes (11): FonteDados, DataFrame, Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com…, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Painel + h meses futuros por cidade (após o último mês com alvo observado)., Preditor, Path, TestExperimentoV6 (+3 more)

### Community 11 - ".prever"
Cohesion: 0.22
Nodes (11): nivel_por_probabilidade(), _fmt_mes(), margem_modelo(), ModeloIndisponivel, DataFrame, ndarray, RuntimeError, "Quantos casos em <mês>?". Até 3 meses após o último mês consolidado: previsão… (+3 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "ingestor_sinan_sorotipo.py"
Cohesion: 0.22
Nodes (16): agregar(), baixar(), contar(), dir_cache(), executar(), ler_campos_dbf(), main(), processar_ano() (+8 more)

### Community 16 - "TestAplicacaoV51"
Cohesion: 0.09
Nodes (14): LookupError, Cenarios, CurvaClima, DataFrame, ndarray, Path, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades…, Faixa (× fator climático) para os `meses` seguintes ao último mês consolidado. (+6 more)

### Community 17 - "comparacao_algoritmos.py"
Cohesion: 0.22
Nodes (15): kmeans_sazonal(), main(), picos_populacao(), _pre(), prever_sklearn(), DataFrame, ndarray, Path (+7 more)

### Community 18 - "baselines.py"
Cohesion: 0.12
Nodes (17): evaluate_baselines(), GLMBinomialNegativa, _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, DataFrame, ndarray, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a… (+9 more)

### Community 19 - "main.py"
Cohesion: 0.06
Nodes (58): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+50 more)

### Community 20 - "experimento_v7.py"
Cohesion: 0.15
Nodes (26): adota(), base_v6(), carregar_sorotipo(), com_rt(), decidir(), efeito(), _feats(), modelos() (+18 more)

### Community 21 - "combinacao.py"
Cohesion: 0.17
Nodes (17): bootstrap_delta_mae(), ΔMAE = MAE(a) − MAE(b) com IC 95% por bootstrap de CIDADES (preserva a…, aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray (+9 more)

### Community 22 - "build_ml_features"
Cohesion: 0.23
Nodes (5): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, parametrize, TestFeaturesV5, TestFeaturesV6

### Community 23 - "experimento_v6.py"
Cohesion: 0.16
Nodes (25): base_v51(), decidir(), efeito(), features_variantes(), preparar(), protocolo_registrado(), ProtocoloNaoRegistrado, DataFrame (+17 more)

### Community 24 - "nivel_regional.py"
Cohesion: 0.19
Nodes (21): ajustar(), _completas(), desenho(), _matriz(), nomes_coef(), novidade_sorotipo(), prever(), DataFrame (+13 more)

### Community 25 - "test_experimento.py"
Cohesion: 0.11
Nodes (29): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), _expanding_window_splits(), fit_predict_fold(), limiares_por_cidade(), margem_persistencia(), _persist_col() (+21 more)

### Community 26 - "README.md"
Cohesion: 0.20
Nodes (5): Chikungunya, Dengue, Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)

### Community 27 - "test_site_estatico.py"
Cohesion: 0.47
Nodes (5): _pagina(), _proximos_meses(), Versão estática (GitHub Pages): a página gerada aponta para os arquivos e liga…, test_pagina_estatica(), test_proximos_meses_vira_o_ano()

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "analise_experimento.py"
Cohesion: 0.24
Nodes (16): decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê…, Treina o modelo COM clima em 2015–2024 e devolve o ranking SHAP (média |SHAP|). (+8 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "predictor.py"
Cohesion: 0.22
Nodes (12): BaseModel, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, CenarioResponse, FaixaMes, PontoCenario, PredictResponse, PrevisaoMesResponse (+4 more)

### Community 33 - "experimento_horizontes.py"
Cohesion: 0.24
Nodes (13): _linha(), metricas_de_oof(), nome_config(), preparar_dados(), DataFrame, Path, Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline. (+5 more)

### Community 36 - "build_base_panel"
Cohesion: 0.23
Nodes (11): build_base_panel(), DataFrame, Path, Módulo responsável por construir o painel base a partir do banco de dados…, Valida o painel base e retorna um dicionário-relatório de qualidade. Levanta…, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, validate_panel(), _raiz() (+3 more)

### Community 38 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 39 - "TestMultiDoenca"
Cohesion: 0.18
Nodes (8): parametrize, Verifica que os lags de chikungunya são criados quando solicitado., Testa o fluxo completo: features → treino → predição, por doença., Testa que o pipeline funciona para cada doença suportada., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., TestIntegration, TestMultiDoenca

### Community 40 - "modelo_final.py"
Cohesion: 0.25
Nodes (10): estatisticas_cidades(), main(), DataFrame, Path, Fase 4.1 — Modelo final para produção (docs/PLANO_EXPERIMENTO_FINAL.md).…, Treina e salva os modelos de produção. Retorna {doenca: metadata}., Nome, limiares de risco (histórico completo) e R² OOF por horizonte para cada…, treinar_modelos_finais() (+2 more)

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
Cohesion: 0.16
Nodes (16): _arquivos(), conferir_zip(), empacotar(), extrair(), garantir(), Path, Artefatos de execução (o que o git não versiona): modelos de produção, snapshot…, Garante modelos e banco locais. Retorna True se precisou baixar. (+8 more)

### Community 45 - "grupos_de_features"
Cohesion: 0.22
Nodes (10): _anomalia_expanding(), grupos_de_features(), _incidencia_vizinhos(), DataFrame, Series, Grupos do protocolo v5: casos (sempre), clima_parcimonioso e suscetibilidade., Rolling por cidade aplicado sobre a série já deslocada (nunca inclui…, Anomalia = valor - média do MESMO mês nos anos ANTERIORES da mesma cidade.… (+2 more)

### Community 47 - "experimento_v5.py"
Cohesion: 0.19
Nodes (18): calibrar_temporal(), decidir(), efeitos(), metricas(), nome(), preparar(), DataFrame, Path (+10 more)

### Community 48 - "test_prediction_service.py"
Cohesion: 0.09
Nodes (33): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+25 more)

### Community 50 - "PredictRequest"
Cohesion: 0.28
Nodes (5): field_validator, PredictRequest, parametrize, TestNiveis, TestSchemas

### Community 52 - "test_experimento_v7.py"
Cohesion: 0.40
Nodes (5): painel_v7(), fixture, Protocolo v7: features de Rt, nível regional (GLM + reconciliação), sorotipo,…, 9 cidades (3 por UF) × 2010–2020, sazonal, com Rt; chikungunya só a partir de…, sorotipo_sint()

### Community 54 - "Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)"
Cohesion: 0.25
Nodes (8): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa)

### Community 56 - "teste_final.py"
Cohesion: 0.12
Nodes (18): git_commit(), avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas., avaliar_2025() (+10 more)

### Community 58 - "lifespan"
Cohesion: 0.67
Nodes (3): lifespan(), Aquece o preditor (painel + features de previsão) em segundo plano, sem…, FastAPI

### Community 59 - "painel_grade"
Cohesion: 0.67
Nodes (3): painel_grade(), fixture, 12 cidades numa grade de coordenadas × 4 anos (para os vizinhos do protocolo…

## Knowledge Gaps
- **92 isolated node(s):** `MESES_LONGO`, `ICONE`, `NIVEIS`, `ORDEM_NIVEL`, `COR` (+87 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 386 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `experimento_horizontes.py`, `run_interpretability`, `get_feature_columns`, `TestFeatureEngineering`, `TestMultiDoenca`, `Preditor`, `grupos_de_features`, `experimento_v5.py`, `test_prediction_service.py`, `comparacao_algoritmos.py`, `baselines.py`, `test_experimento_v7.py`, `TestSemVazamento`, `TestRt`, `experimento_v6.py`, `test_experimento.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `predictor.py`, `server.py`, `atualizacao_incremental.py`, `.prever`, `TestAplicacaoV51`, `test_prediction_service.py`, `test_experimento_v7.py`, `test_experimento.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `build_base_panel` to `experimento_horizontes.py`, `run_interpretability`, `get_feature_columns`, `dlnm.py`, `modelo_final.py`, `Preditor`, `experimento_v5.py`, `test_prediction_service.py`, `comparacao_algoritmos.py`, `main.py`, `experimento_v7.py`, `experimento_v6.py`, `teste_final.py`, `analise_experimento.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `ICONE`, `NIVEIS` to the rest of the system?**
  _92 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `server.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0851063829787234 - nodes in this community are weakly interconnected._
- **Should `get_feature_columns` be split into smaller, more focused modules?**
  _Cohesion score 0.11594202898550725 - nodes in this community are weakly interconnected._