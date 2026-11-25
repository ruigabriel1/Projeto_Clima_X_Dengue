# Graph Report - Projeto_Clima_X_Dengue  (2026-11-25)

## Corpus Check
- 70 files · ~65,711 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 994 nodes · 2193 edges · 56 communities (48 shown, 4 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c8d2df2e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_preditor
- analise_experimento.py
- charts.js
- get_feature_columns
- ingestor_api_sul.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- Preditor
- .prever
- Plano v5 — Limpeza e Resultado Publicável
- ingestor_sinan_sorotipo.py
- TestAplicacaoV51
- build_base_panel
- ml_orchestrator.py
- main.py
- experimento_v7.py
- combinacao.py
- build_ml_features
- export_dashboard.py
- avaliar
- model_training.py
- README.md
- exportar
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- Cenarios
- mini_panel
- server.py
- preparar_dados
- pre-commit
- analise_efeito/__init__.py
- avaliar
- hf_space/README.md
- TestFeatureEngineering
- TestMultiDoenca
- treinar_modelos_finais
- Protocolo v7 — Pré-registro
- test_sorotipo.py
- Protocolo v6 — Pré-registro
- artefatos.py
- .features_previsao
- experimento_v5.py
- experimento_horizontes.py
- PredictRequest
- main.js
- test_prediction_service.py
- Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)
- GLMBinomialNegativa
- test_experimento.py

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

### Community 0 - "get_preditor"
Cohesion: 0.11
Nodes (27): api_cenario(), api_confiabilidade(), api_historico(), api_modelo_info(), api_municipios(), api_predict(), api_previsao(), api_ranking() (+19 more)

### Community 1 - "analise_experimento.py"
Cohesion: 0.12
Nodes (35): bootstrap_delta_mae(), decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê… (+27 more)

### Community 2 - "charts.js"
Cohesion: 0.80
Nodes (4): getPlotlyConfig(), getPlotlyLayout(), renderChartHeatmap(), renderChartSazonal()

### Community 3 - "get_feature_columns"
Cohesion: 0.11
Nodes (25): _anomalia_expanding(), get_feature_columns(), grupos_de_features(), _incidencia_vizinhos(), is_clima_parcimonioso(), is_imunidade_longa(), is_rt(), is_rt_bruto() (+17 more)

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
Cohesion: 0.12
Nodes (17): A aplicação, [▶ Abrir a aplicação](https://ruigabriel1.github.io/Projeto_Clima_X_Dengue/), Arquitetura, 🦟 Clima × Arboviroses, Como a IA foi usada, e onde ela foi barrada, Depois de 2026: o diagnóstico, a v6 e a v7, El Niño e La Niña: fora da versão atual, exploratório para as próximas, Em 30 segundos (+9 more)

### Community 8 - "Plano de Experimento Final — Clima × Arboviroses"
Cohesion: 0.10
Nodes (19): 1.1 Variáveis do experimento, 1.2 O que muda em cada horizonte, 1.3 Métricas (fixadas agora, antes de rodar), 1.4 Validação, 1.5 Implementação, 4.1 Retreinar no painel completo (2015–2025), 4.2 Empacotar, 4.3 API de previsão (+11 more)

### Community 9 - "app.js"
Cohesion: 0.11
Nodes (46): alerta(), api(), apiEstatica(), aplicarTema(), ativarAba(), atualizarLoader(), autocompletar(), cacheDados (+38 more)

### Community 10 - "Preditor"
Cohesion: 0.13
Nodes (7): FonteDados, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Preditor, Path, TestExperimentoV6, TestAPI, TestPreditor

### Community 11 - ".prever"
Cohesion: 0.20
Nodes (11): CidadeNaoEncontrada, _fmt_mes(), margem_modelo(), ModeloIndisponivel, DataFrame, ndarray, RuntimeError, "Quantos casos em <mês>?". Até 3 meses após o último mês consolidado: previsão… (+3 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "ingestor_sinan_sorotipo.py"
Cohesion: 0.22
Nodes (16): agregar(), baixar(), contar(), dir_cache(), executar(), ler_campos_dbf(), main(), processar_ano() (+8 more)

### Community 16 - "TestAplicacaoV51"
Cohesion: 0.10
Nodes (10): CurvaClima, ndarray, Curva exposição-resposta do DLNM reduzida à parte quente e monotônica., (fator, lo, hi) do risco para t_normal + delta em relação a t_normal., artefatos(), fixture, Produção v5.1: previsão por mês, ranking, cenário, monitoramento e endpoints., Doença fora da lista não monta caminho de arquivo; output/ não é servido; token… (+2 more)

### Community 17 - "build_base_panel"
Cohesion: 0.10
Nodes (29): kmeans_sazonal(), main(), picos_populacao(), _pre(), prever_sklearn(), DataFrame, ndarray, Path (+21 more)

### Community 18 - "ml_orchestrator.py"
Cohesion: 0.15
Nodes (14): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No… (+6 more)

### Community 19 - "main.py"
Cohesion: 0.07
Nodes (48): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_experimento_v6() (+40 more)

### Community 20 - "experimento_v7.py"
Cohesion: 0.05
Nodes (78): metricas(), base_v51(), decidir(), efeito(), features_variantes(), preparar(), protocolo_registrado(), ProtocoloNaoRegistrado (+70 more)

### Community 21 - "combinacao.py"
Cohesion: 0.19
Nodes (15): aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray, Path, Combinação modelo + persistência (docs/PROTOCOLO_V5.md, desvio de 2026-11-04,… (+7 more)

### Community 22 - "build_ml_features"
Cohesion: 0.13
Nodes (8): build_ml_features(), Constrói as features a partir do painel base. Args: panel: saída de…, parametrize, TestFeaturesV5, TestFeaturesV6, TestSemVazamento, parametrize, TestRt

### Community 23 - "export_dashboard.py"
Cohesion: 0.16
Nodes (16): api_doencas(), api_status(), Lista doenças com resultados exportados., _clean(), _code6(), doencas_exportadas(), exportar_dados_dashboard(), exportar_doenca() (+8 more)

### Community 24 - "avaliar"
Cohesion: 0.25
Nodes (12): avaliar(), _ler(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():…, Acrescenta as previsões do lote; ignora as que já tinham sido emitidas. Retorna…, Desempenho por doença × horizonte das previsões cujo mês-alvo já foi observado…, registrar() (+4 more)

### Community 25 - "model_training.py"
Cohesion: 0.11
Nodes (24): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), _expanding_window_splits(), margem_persistencia(), _persist_col(), DataFrame, ndarray (+16 more)

### Community 26 - "README.md"
Cohesion: 0.20
Nodes (5): Chikungunya, Dengue, Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Efeitos (ΔMAE com − sem, IC 95% bootstrap por município), Experimento v6 — formulação, vizinhos e imunidade longa (protocolo v6)

### Community 27 - "exportar"
Cohesion: 0.24
Nodes (13): _cenario(), _dump(), exportar(), _gravar(), _pagina(), _proximos_meses(), Path, Versão estática da aplicação (GitHub Pages): as mesmas 5 abas, com as respostas… (+5 more)

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "Cenarios"
Cohesion: 0.25
Nodes (7): LookupError, Cenarios, DataFrame, Path, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades…, Faixa (× fator climático) para os `meses` seguintes ao último mês consolidado., P10/P50/P90 dos casos por mês-calendário (índice 1–12). code='sul' soma a…

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "server.py"
Cohesion: 0.21
Nodes (15): api_cidades(), lifespan(), server.py — FastAPI backend para a interface Prodígia. Rotas: status do banco,…, Aquece o preditor (painel + features de previsão) em segundo plano, sem…, BaseModel, FastAPI, get_cidades(), CenarioResponse (+7 more)

### Community 33 - "preparar_dados"
Cohesion: 0.19
Nodes (13): _linha(), metricas_de_oof(), nome_config(), preparar_dados(), DataFrame, Path, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline., Executa o experimento completo e grava os resultados. Retorna o DataFrame de… (+5 more)

### Community 36 - "avaliar"
Cohesion: 0.23
Nodes (11): avaliar(), HoldoutJaUsado, markdown(), meses_consolidados(), _metricas(), DataFrame, Path, RuntimeError (+3 more)

### Community 38 - "TestFeatureEngineering"
Cohesion: 0.15
Nodes (7): Garante que colunas proibidas não aparecem nas features., Verifica que dengue_lag1 corresponde ao valor do mês anterior., O rolling de memória epidêmica NÃO deve incluir o mês corrente., Verifica que o output tem features e menos linhas que o input (warm-up)., Verifica que get_feature_columns exclui colunas de identificação., No modo forecast, nenhuma variável do mês-alvo pode ser feature., TestFeatureEngineering

### Community 39 - "TestMultiDoenca"
Cohesion: 0.18
Nodes (8): parametrize, Verifica que os lags de chikungunya são criados quando solicitado., Testa o fluxo completo: features → treino → predição, por doença., Testa que o pipeline funciona para cada doença suportada., build_ml_features roda sem erro para cada doença., Features de uma doença NÃO devem incluir a coluna-alvo de outra., TestIntegration, TestMultiDoenca

### Community 40 - "treinar_modelos_finais"
Cohesion: 0.33
Nodes (7): estatisticas_cidades(), main(), DataFrame, Path, Treina e salva os modelos de produção. Retorna {doenca: metadata}., Nome, limiares de risco (histórico completo) e R² OOF por horizonte para cada…, treinar_modelos_finais()

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

### Community 45 - ".features_previsao"
Cohesion: 0.33
Nodes (3): DataFrame, Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com…, Painel + h meses futuros por cidade (após o último mês com alvo observado).

### Community 47 - "experimento_v5.py"
Cohesion: 0.25
Nodes (16): calibrar_temporal(), decidir(), efeitos(), nome(), preparar(), DataFrame, Path, Series (+8 more)

### Community 48 - "experimento_horizontes.py"
Cohesion: 0.14
Nodes (23): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():… (+15 more)

### Community 50 - "PredictRequest"
Cohesion: 0.47
Nodes (3): field_validator, PredictRequest, TestSchemas

### Community 52 - "test_prediction_service.py"
Cohesion: 0.13
Nodes (12): nivel_por_probabilidade(), Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md,…, Fonte de dados do serviço de previsão. A fonte de verdade é o SQLite…, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., aplicar_intervalo(), Preditor de produção v5 — ALERTA DE RISCO (docs/PROTOCOLO_V5.md). Produto…, Intervalo de 90% a partir dos quantis de resíduo log1p calibrados no OOF., FaixaMes (+4 more)

### Community 54 - "Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)"
Cohesion: 0.25
Nodes (8): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa)

### Community 55 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 56 - "test_experimento.py"
Cohesion: 0.10
Nodes (25): avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas., limiares_por_cidade(), Quantil q (0–1) de `col` por cidade, calculado em df_ref (tipicamente o… (+17 more)

## Knowledge Gaps
- **89 isolated node(s):** `MESES_LONGO`, `ICONE`, `NIVEIS`, `ORDEM_NIVEL`, `COR` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 383 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `preparar_dados`, `get_feature_columns`, `avaliar`, `TestFeatureEngineering`, `TestMultiDoenca`, `.features_previsao`, `experimento_v5.py`, `experimento_horizontes.py`, `build_base_panel`, `ml_orchestrator.py`, `experimento_v7.py`, `test_prediction_service.py`, `test_experimento.py`, `model_training.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `get_preditor`, `server.py`, `.prever`, `TestAplicacaoV51`, `test_prediction_service.py`, `experimento_v7.py`, `avaliar`, `test_experimento.py`, `Cenarios`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `build_base_panel` to `analise_experimento.py`, `preparar_dados`, `avaliar`, `dlnm.py`, `treinar_modelos_finais`, `.features_previsao`, `experimento_v5.py`, `experimento_horizontes.py`, `ml_orchestrator.py`, `main.py`, `experimento_v7.py`, `test_prediction_service.py`, `test_experimento.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `ICONE`, `NIVEIS` to the rest of the system?**
  _89 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `get_preditor` be split into smaller, more focused modules?**
  _Cohesion score 0.10541310541310542 - nodes in this community are weakly interconnected._
- **Should `analise_experimento.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11561561561561562 - nodes in this community are weakly interconnected._