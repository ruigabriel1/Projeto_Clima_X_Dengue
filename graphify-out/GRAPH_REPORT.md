# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 49 files · ~33,233 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 586 nodes · 1219 edges · 33 communities (28 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `82590daa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- experimento_v5.py
- build_ml_features
- main.js
- server.py
- ingestor_api_sul.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- Preditor
- alerta_risco.py
- analise_experimento.py
- Plano v5 — Limpeza e Resultado Publicável
- predictor.py
- test_prediction_service.py
- main.py
- experimento_horizontes.py
- run_interpretability
- data_fetcher.py
- GLMBinomialNegativa
- PredictRequest
- teste_prospectivo.py
- .prever
- ingestor_ibge_populacao.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- export_dashboard.py
- mini_panel
- risk_classifier.py
- pre-commit
- analise_efeito/__init__.py

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 37 edges
2. `get_feature_columns()` - 34 edges
3. `build_base_panel()` - 24 edges
4. `fit_predict_fold()` - 21 edges
5. `Preditor` - 20 edges
6. `FonteDados` - 19 edges
7. `configurar_log()` - 18 edges
8. `limiares_por_cidade()` - 16 edges
9. `_expanding_window_splits()` - 16 edges
10. `run_teste_final()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `api_predict()` --uses--> `ModeloIndisponivel`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py
- `api_predict()` --uses--> `PredictRequest`  [INFERRED]
  app/server.py → src/prediction_service/schemas.py
- `TestPreditor` --uses--> `ModeloIndisponivel`  [INFERRED]
  tests/test_prediction_service.py → src/prediction_service/predictor.py
- `TestPreditor` --uses--> `CidadeNaoEncontrada`  [INFERRED]
  tests/test_prediction_service.py → src/prediction_service/predictor.py
- `api_predict()` --uses--> `CidadeNaoEncontrada`  [INFERRED]
  app/server.py → src/prediction_service/predictor.py

## Import Cycles
- None detected.

## Communities (33 total, 3 thin omitted)

### Community 0 - "experimento_v5.py"
Cohesion: 0.10
Nodes (33): aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray, Path, Combinação modelo + persistência (docs/PROTOCOLO_V5.md, desvio de 2026-11-04,… (+25 more)

### Community 1 - "build_ml_features"
Cohesion: 0.05
Nodes (49): evaluate_baselines(), _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a…, Avalia persistência, naive sazonal e GLM NB com Expanding Window. Retorna lista…, Constrói o nome da coluna de lag para a doença-alvo., Prever = último valor conhecido no momento da previsão (<doença>_lag<h>). No… (+41 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.17
Nodes (17): api_cidades(), api_doencas(), api_resultados(), api_status(), index(), lifespan(), server.py — FastAPI backend para a interface Prodígia. Rotas: status do banco,…, Aquece o preditor (painel + features de previsão) em segundo plano, sem… (+9 more)

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

### Community 9 - "Preditor"
Cohesion: 0.21
Nodes (6): FonteDados, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Preditor, Path, TestAPI, TestPreditor

### Community 10 - "alerta_risco.py"
Cohesion: 0.12
Nodes (24): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, benchmark_infodengue(), niveis_infodengue(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF…, salvar_calibracao() (+16 more)

### Community 11 - "analise_experimento.py"
Cohesion: 0.21
Nodes (19): bootstrap_delta_mae(), decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê… (+11 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "predictor.py"
Cohesion: 0.20
Nodes (10): api_modelo_info(), api_predict(), Previsão de casos para um município, doença e horizonte (1–3 meses). Rota…, Resumo dos modelos de produção carregados (config, métricas, data de retreino)., LookupError, post, Serviço de previsão de arboviroses (Fase 4 do plano do experimento final)., CidadeNaoEncontrada (+2 more)

### Community 16 - "test_prediction_service.py"
Cohesion: 0.28
Nodes (6): nivel_por_probabilidade(), aplicar_intervalo(), Intervalo de 90% a partir dos quantis de resíduo log1p calibrados no OOF., Testes do serviço de previsão v5 (alerta de risco): schemas, níveis, intervalo,…, TestIntervalo, TestNiveis

### Community 19 - "main.py"
Cohesion: 0.08
Nodes (40): command_analise(), command_atualizar_dados(), command_dlnm(), command_experimento(), command_experimento_v5(), command_export_dashboard(), command_modelo_risco(), command_serve() (+32 more)

### Community 20 - "experimento_horizontes.py"
Cohesion: 0.05
Nodes (58): _linha(), metricas_de_oof(), preparar_dados(), DataFrame, Path, Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline., Executa o experimento completo e grava os resultados. Retorna o DataFrame de… (+50 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "data_fetcher.py"
Cohesion: 0.20
Nodes (7): DataFrame, Fonte de dados do serviço de previsão. A fonte de verdade é o SQLite…, Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com…, Remove meses ingeridos menos de `dias` após o fim do mês: o InfoDengue ainda…, Painel + h meses futuros por cidade (após o último mês com alvo observado)., remover_meses_nao_consolidados(), test_remove_meses_nao_consolidados()

### Community 23 - "GLMBinomialNegativa"
Cohesion: 0.22
Nodes (7): GLMBinomialNegativa, DataFrame, ndarray, Prediz casos a partir do GLM ajustado., GLM Binomial Negativa com offset log(população). Usa variáveis climáticas +…, Seleciona features do Modelo B (sem lags de dengue)., Ajusta o GLM NB com offset log(pop).

### Community 24 - "PredictRequest"
Cohesion: 0.24
Nodes (7): BaseModel, field_validator, PredictRequest, PredictResponse, Schemas Pydantic de entrada e saída da API de previsão (v5: alerta de risco)., parametrize, TestSchemas

### Community 25 - "teste_prospectivo.py"
Cohesion: 0.25
Nodes (12): avaliar(), HoldoutJaUsado, markdown(), meses_consolidados(), _metricas(), DataFrame, Path, RuntimeError (+4 more)

### Community 26 - ".prever"
Cohesion: 0.29
Nodes (3): _fmt_mes(), ModeloIndisponivel, RuntimeError

### Community 27 - "ingestor_ibge_populacao.py"
Cohesion: 0.32
Nodes (7): fetch_populacao_ibge(), get_ibge_7(), main(), DataFrame, ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API…, Busca população estimada do IBGE via API SIDRA (tabela 6579)., Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos.

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "export_dashboard.py"
Cohesion: 0.27
Nodes (10): _clean(), _code6(), exportar_dados_dashboard(), exportar_doenca(), _historico(), _mean(), DataFrame, Series (+2 more)

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

## Knowledge Gaps
- **54 isolated node(s):** `Comandos`, `Arquitetura`, `Grafo do código (graphify): consulte antes de abrir arquivos`, `Regras metodológicas (não violar)`, `Convenções` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 231 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `experimento_v5.py`, `alerta_risco.py`, `experimento_horizontes.py`, `data_fetcher.py`, `teste_prospectivo.py`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `main.py` to `experimento_v5.py`, `build_ml_features`, `dlnm.py`, `alerta_risco.py`, `analise_experimento.py`, `experimento_horizontes.py`, `data_fetcher.py`, `teste_prospectivo.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `get_feature_columns()` connect `build_ml_features` to `experimento_v5.py`, `alerta_risco.py`, `analise_experimento.py`, `experimento_horizontes.py`, `teste_prospectivo.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Preditor` (e.g. with `FonteDados` and `PredictResponse`) actually correct?**
  _`Preditor` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Comandos`, `Arquitetura`, `Grafo do código (graphify): consulte antes de abrir arquivos` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `experimento_v5.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09986504723346828 - nodes in this community are weakly interconnected._
- **Should `build_ml_features` be split into smaller, more focused modules?**
  _Cohesion score 0.050078247261345854 - nodes in this community are weakly interconnected._