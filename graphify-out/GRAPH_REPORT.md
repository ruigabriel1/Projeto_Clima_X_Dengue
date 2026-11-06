# Graph Report - Projeto_Clima_X_Dengue  (2026-11-06)

## Corpus Check
- 54 files · ~41,345 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 712 nodes · 1520 edges · 38 communities (33 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 57 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `671ae899`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- experimento_v5.py
- FonteDados
- main.js
- server.py
- ingestor_api_sul.py
- dlnm.py
- atualizacao_incremental.py
- 🦟 Clima × Arboviroses
- Plano de Experimento Final — Clima × Arboviroses
- app.js
- alerta_risco.py
- build_ml_features
- Plano v5 — Limpeza e Resultado Publicável
- experimento_horizontes.py
- Cenarios
- ml_orchestrator.py
- TestModelTraining
- main.py
- build_base_panel
- run_interpretability
- analise_experimento.py
- teste_prospectivo.py
- test_prediction_service.py
- fit_predict_fold
- Preditor
- artefatos.py
- CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)
- Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão
- calcular_metricas
- mini_panel
- TestAplicacaoV51
- ingestor_ibge_populacao.py
- pre-commit
- analise_efeito/__init__.py
- treinar_modelos_finais
- hf_space/README.md

## God Nodes (most connected - your core abstractions)
1. `build_ml_features()` - 37 edges
2. `get_feature_columns()` - 34 edges
3. `Preditor` - 31 edges
4. `build_base_panel()` - 24 edges
5. `FonteDados` - 24 edges
6. `fit_predict_fold()` - 21 edges
7. `configurar_log()` - 20 edges
8. `treinar_modelos_risco()` - 18 edges
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

## Communities (38 total, 3 thin omitted)

### Community 0 - "experimento_v5.py"
Cohesion: 0.10
Nodes (35): bootstrap_delta_mae(), ΔMAE = MAE(a) − MAE(b) com IC 95% por bootstrap de CIDADES (preserva a…, aplicar(), combinar(), escolher_peso(), pesos_cross_fit(), DataFrame, ndarray (+27 more)

### Community 1 - "FonteDados"
Cohesion: 0.15
Nodes (7): FonteDados, DataFrame, Linhas de features do mês-alvo (último observado + h) de todas as cidades. Com…, Nível de alerta oficial do InfoDengue (1–4) no mês informado, se disponível., Painel + h meses futuros por cidade (após o último mês com alvo observado)., Path, TestAPI

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartBacktest(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.06
Nodes (59): api_cenario(), api_cidades(), api_confiabilidade(), api_doencas(), api_historico(), api_modelo_info(), api_municipios(), api_predict() (+51 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.29
Nodes (10): fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima(), process_saude() (+2 more)

### Community 5 - "dlnm.py"
Cohesion: 0.16
Nodes (21): ajustar(), _coef_cov(), cross_basis(), plotar(), preparar(), DataFrame, ndarray, Path (+13 more)

### Community 6 - "atualizacao_incremental.py"
Cohesion: 0.10
Nodes (31): Connection, date, avaliar(), DataFrame, Path, Monitoramento ao vivo (docs/PROTOCOLO_V5.md, "Produção v5.1"). 1. registrar():…, Acrescenta as previsões do lote; ignora as que já tinham sido emitidas. Retorna…, Desempenho por doença × horizonte das previsões cujo mês-alvo já foi observado… (+23 more)

### Community 7 - "🦟 Clima × Arboviroses"
Cohesion: 0.08
Nodes (22): Análise de efeito (DLNM) — responde H1, Desvios, Experimento preditivo — responde H2 e H3, Hipóteses, Holdout prospectivo, Produção v5.1 (registrado em 2026-11-06, depois do teste de 2026 e antes do retreino), Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026), Regra de decisão (fixa) (+14 more)

### Community 8 - "Plano de Experimento Final — Clima × Arboviroses"
Cohesion: 0.10
Nodes (19): 1.1 Variáveis do experimento, 1.2 O que muda em cada horizonte, 1.3 Métricas (fixadas agora, antes de rodar), 1.4 Validação, 1.5 Implementação, 4.1 Retreinar no painel completo (2015–2025), 4.2 Empacotar, 4.3 API de previsão (+11 more)

### Community 9 - "app.js"
Cohesion: 0.19
Nodes (27): api(), ativarAba(), atualizarLoader(), carregando, carregarCenario(), carregarConfiabilidade(), carregarPrevisao(), carregarRanking() (+19 more)

### Community 10 - "alerta_risco.py"
Cohesion: 0.19
Nodes (18): benchmark_infodengue(), desempenho(), niveis_infodengue(), previsoes_teste_2026(), DataFrame, Path, Produto v5: alerta de risco (docs/PROTOCOLO_V5.md). 1. benchmark_infodengue():…, Curva de confiabilidade (10 faixas) da probabilidade do modelo escolhido, OOF… (+10 more)

### Community 11 - "build_ml_features"
Cohesion: 0.06
Nodes (37): _anomalia_expanding(), build_ml_features(), get_feature_columns(), grupos_de_features(), is_clima_parcimonioso(), is_suscetibilidade(), _prefixo_doenca(), DataFrame (+29 more)

### Community 12 - "Plano v5 — Limpeza e Resultado Publicável"
Cohesion: 0.15
Nodes (12): Plano v5 — Limpeza e Resultado Publicável, Step 0 — Pré-registro do protocolo v5, Step 10 — Revisão final, Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas, Step 2 — Remover o código legado e consolidar a estrutura, Step 3 — Ingestão idempotente de 2026, Step 4 — Ajustes de modelagem v5 (features e alvo), Step 5 — Experimento v5 (desenvolvimento 2018–2024) (+4 more)

### Community 14 - "experimento_horizontes.py"
Cohesion: 0.20
Nodes (14): _linha(), metricas_de_oof(), nome_config(), preparar_dados(), DataFrame, Path, Fase 1 — Experimento controlado (docs/PLANO_EXPERIMENTO_FINAL.md). Fatores:…, Métricas agregadas (todas as linhas do OOF) para cada modelo e baseline. (+6 more)

### Community 16 - "Cenarios"
Cohesion: 0.16
Nodes (10): Cenarios, CurvaClima, DataFrame, ndarray, Path, Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades…, Faixa (× fator climático) para os `meses` seguintes ao último mês consolidado., Curva exposição-resposta do DLNM reduzida à parte quente e monotônica. (+2 more)

### Community 17 - "ml_orchestrator.py"
Cohesion: 0.07
Nodes (31): evaluate_baselines(), GLMBinomialNegativa, _lag_col_name(), NaiveSazonalBaseline, PersistenciaBaseline, DataFrame, ndarray, Modelos de baseline para comparação com o XGBoost (multi-doença). Todos usam a… (+23 more)

### Community 18 - "TestModelTraining"
Cohesion: 0.40
Nodes (3): Garante que clipping é por cidade e não global., Verifica que EW gera splits corretos., TestModelTraining

### Community 19 - "main.py"
Cohesion: 0.10
Nodes (34): command_analise(), command_atualizar_dados(), command_atualizar_mensal(), command_dlnm(), command_empacotar(), command_experimento(), command_experimento_v5(), command_export_dashboard() (+26 more)

### Community 20 - "build_base_panel"
Cohesion: 0.15
Nodes (18): Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os…, build_base_panel(), Path, Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado, pronto…, git_commit(), main(), Fase 4.1 — Modelo final para produção (docs/PLANO_EXPERIMENTO_FINAL.md).…, avaliar_2025() (+10 more)

### Community 21 - "run_interpretability"
Cohesion: 0.25
Nodes (17): compute_shap_values(), plot_partial_dependence(), plot_shap_importance(), plot_top_pdps(), DataFrame, ndarray, Path, Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença). Fornece: -… (+9 more)

### Community 22 - "analise_experimento.py"
Cohesion: 0.24
Nodes (16): decidir_config(), diagnostico_grupos_clima(), _fmt(), plot_skill(), DataFrame, Path, Fase 2 — Análise e decisão (docs/PLANO_EXPERIMENTO_FINAL.md). Lê…, Treina o modelo COM clima em 2015–2024 e devolve o ranking SHAP (média |SHAP|). (+8 more)

### Community 23 - "teste_prospectivo.py"
Cohesion: 0.24
Nodes (12): avaliar(), HoldoutJaUsado, markdown(), meses_consolidados(), _metricas(), DataFrame, Path, RuntimeError (+4 more)

### Community 24 - "test_prediction_service.py"
Cohesion: 0.13
Nodes (13): field_validator, nivel_por_probabilidade(), Remove meses ingeridos menos de `dias` após o fim do mês: o InfoDengue ainda…, remover_meses_nao_consolidados(), PredictRequest, artefatos(), parametrize, Testes do serviço de previsão v5 (alerta de risco): schemas, níveis, intervalo,… (+5 more)

### Community 25 - "fit_predict_fold"
Cohesion: 0.16
Nodes (22): alvo_treino(), _build_base_margin(), clip_outliers_per_city(), _expanding_window_splits(), fit_predict_fold(), limiares_por_cidade(), _persist_col(), DataFrame (+14 more)

### Community 26 - "Preditor"
Cohesion: 0.16
Nodes (11): LookupError, CidadeNaoEncontrada, _fmt_mes(), ModeloIndisponivel, Preditor, DataFrame, RuntimeError, "Quantos casos em <mês>?". Até 3 meses após o último mês consolidado: previsão… (+3 more)

### Community 27 - "artefatos.py"
Cohesion: 0.23
Nodes (11): _arquivos(), empacotar(), extrair(), garantir(), Path, Artefatos de execução (o que o git não versiona): modelos de produção, snapshot…, Caminhos (absolutos) que entram no pacote., Extrai o zip conferindo cada arquivo contra o manifesto. Recusa caminhos fora… (+3 more)

### Community 28 - "CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)"
Cohesion: 0.29
Nodes (6): Arquitetura, CLAUDE.md — Projeto Clima × Arboviroses (Região Sul), Comandos, Convenções, Grafo do código (graphify): consulte antes de abrir arquivos, Regras metodológicas (não violar)

### Community 29 - "Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão"
Cohesion: 0.33
Nodes (5): 1. Bronze — ingestão, 2. Silver — painel, 3. Gold — duas análises separadas, 4. Evolução histórica, Arquitetura de Dados — APIs públicas → SQLite → Painel → Efeito e Previsão

### Community 30 - "calcular_metricas"
Cohesion: 0.24
Nodes (7): avaliar_criterios(), calcular_metricas(), ndarray, As 5 métricas do experimento final (fixadas ANTES de rodar — ver…, Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha =…, Aplica os critérios de aceitação do plano a um dicionário de métricas., TestMetricas

### Community 31 - "mini_panel"
Cohesion: 0.40
Nodes (4): mini_panel(), fixture, Fixtures compartilhados: painel sintético (não depende do banco)., Cria um painel sintético com 2 cidades × 72 meses (6 anos) e 3 doenças.

### Community 32 - "TestAplicacaoV51"
Cohesion: 0.22
Nodes (3): fixture, Produção v5.1: previsão por mês, ranking, cenário, monitoramento e endpoints., TestAplicacaoV51

### Community 33 - "ingestor_ibge_populacao.py"
Cohesion: 0.32
Nodes (7): fetch_populacao_ibge(), get_ibge_7(), main(), DataFrame, ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API…, Busca população estimada do IBGE via API SIDRA (tabela 6579)., Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos.

### Community 36 - "treinar_modelos_finais"
Cohesion: 0.40
Nodes (6): estatisticas_cidades(), DataFrame, Path, Treina e salva os modelos de produção. Retorna {doenca: metadata}., Nome, limiares de risco (histórico completo) e R² OOF por horizonte para cada…, treinar_modelos_finais()

## Knowledge Gaps
- **65 isolated node(s):** `MESES_LONGO`, `NIVEIS`, `COR`, `layoutBase`, `cfgPlot` (+60 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 277 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_ml_features()` connect `build_ml_features` to `experimento_v5.py`, `FonteDados`, `alerta_risco.py`, `experimento_horizontes.py`, `ml_orchestrator.py`, `teste_prospectivo.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `build_base_panel` to `experimento_v5.py`, `FonteDados`, `dlnm.py`, `build_ml_features`, `experimento_horizontes.py`, `ml_orchestrator.py`, `main.py`, `analise_experimento.py`, `teste_prospectivo.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `Preditor` connect `Preditor` to `TestAplicacaoV51`, `FonteDados`, `server.py`, `atualizacao_incremental.py`, `build_ml_features`, `Cenarios`, `test_prediction_service.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Preditor` (e.g. with `Cenarios` and `FonteDados`) actually correct?**
  _`Preditor` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `FonteDados` (e.g. with `Cenarios` and `Preditor`) actually correct?**
  _`FonteDados` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MESES_LONGO`, `NIVEIS`, `COR` to the rest of the system?**
  _65 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `experimento_v5.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09634146341463415 - nodes in this community are weakly interconnected._