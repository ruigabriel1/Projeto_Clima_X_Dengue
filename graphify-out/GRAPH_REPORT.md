# Graph Report - Projeto_Clima_X_Dengue  (2026-09-27)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 149 nodes · 246 edges · 20 communities (8 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e8ec8e72`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- motor_lote_modelagem_v2_por_latitude.py
- app_v2.js
- server.py
- ml_runner.py
- app.js
- ingestor_ibge_populacao.py
- loaders.py
- ingestor_api_sul.py
- Medallion Architecture
- main.py
- Compass Rose

## God Nodes (most connected - your core abstractions)
1. `main()` - 11 edges
2. `save_pdf_reports()` - 10 edges
3. `carregarResultados()` - 10 edges
4. `run_full_ml()` - 9 edges
5. `load_historical_incidents_from_sqlite()` - 8 edges
6. `save_ml_2025_forecasts()` - 8 edges
7. `carregarResultados()` - 7 edges
8. `getCSSVar()` - 7 edges
9. `treinar()` - 7 edges
10. `project_city()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `treinar()` --calls--> `build_base_panel()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `treinar()` --calls--> `_build_ml_features()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `treinar()` --calls--> `_evaluate_split()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `treinar()` --calls--> `run_full_ml()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `api_cidades()` --calls--> `get_cidades()`  [EXTRACTED]
  app/server.py → app/ml_runner.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Medallion Data Layers** — data_readme, docs_arquitetura_de_dados, docs_legado_historico_diario_projeto [EXTRACTED 0.95]

## Communities (20 total, 3 thin omitted)

### Community 0 - "motor_lote_modelagem_v2_por_latitude.py"
Cohesion: 0.13
Nodes (34): Path, build_code_lookup_from_latitude_files(), build_monthly_climatology(), build_yearly_templates(), calibrate_region(), CalibrationBundle, CoverageInfo, discover_files() (+26 more)

### Community 1 - "app_v2.js"
Cohesion: 0.21
Nodes (13): carregarResultados(), getCSSVar(), iniciarTreino(), renderChartBarras(), renderChartBarrasProjecao(), renderChartCenarios(), renderChartClima(), renderChartFI() (+5 more)

### Community 2 - "server.py"
Cohesion: 0.21
Nodes (14): get_cidades(), get_db_status(), Retorna estatísticas do banco para o painel de status., Lista cidades disponíveis no SQLite para o filtro avançado., api_cidades(), api_progresso(), api_resultados(), api_status() (+6 more)

### Community 3 - "ml_runner.py"
Cohesion: 0.26
Nodes (12): ml_runner.py — Wrapper leve do motor ML para a interface Prodígia. Encapsula…, Executa treino XGBoost e retorna métricas + dados para gráficos. Parameters…, treinar(), ndarray, build_base_panel(), _build_ml_features(), _evaluate_split(), Faixa simétrica (+/- erro%) por SSP, com erro crescente no horizonte. (+4 more)

### Community 4 - "app.js"
Cohesion: 0.27
Nodes (10): carregarResultados(), iniciarTreino(), renderChartBarras(), renderChartClima(), renderChartFI(), renderChartHeatmap(), renderChartSerieTemporal(), renderMetricas() (+2 more)

### Community 5 - "ingestor_ibge_populacao.py"
Cohesion: 0.20
Nodes (8): Coleta isolada de São Carlos, SC — Clima + Saúde em 1 execução., fetch_populacao_ibge(), get_ibge_7(), main(), DataFrame, ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API…, Busca população estimada do IBGE via API SIDRA (tabela 6579)., Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos.

### Community 6 - "loaders.py"
Cohesion: 0.22
Nodes (10): GeoDataFrame, carregar_dados_brutos(), carregar_dados_processados(), carregar_geodados(), DataFrame, Carrega dados da pasta data/processed, Carrega shapefiles ou geojson da pasta data/geodados, Salva dataframe na pasta data/processed (+2 more)

### Community 7 - "ingestor_api_sul.py"
Cohesion: 0.29
Nodes (10): fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima(), process_saude() (+2 more)

## Knowledge Gaps
- **2 isolated node(s):** `Compass Rose`, `XGBoost Global Model`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 48 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `treinar()` connect `ml_runner.py` to `server.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `run_full_ml()` connect `ml_runner.py` to `motor_lote_modelagem_v2_por_latitude.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `ml_runner.py` to `motor_lote_modelagem_v2_por_latitude.py`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `carregarResultados()` (e.g. with `renderChartBarras()` and `renderChartClima()`) actually correct?**
  _`carregarResultados()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Compass Rose`, `XGBoost Global Model` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `motor_lote_modelagem_v2_por_latitude.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._