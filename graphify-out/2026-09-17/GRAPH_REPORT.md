# Graph Report - Projeto_Clima_X_Dengue  (2026-09-16)

## Corpus Check
- 22 files · ~24,479 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 119 nodes · 197 edges · 23 communities (8 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0d1ea99f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Path
- ingestor_api_sul.py
- loaders.py
- DataFrame
- motor_lote_modelagem_v2_por_latitude.py
- ml_runner.py
- Medallion Architecture
- main.py
- Compass Rose
- Dengue Modeling with ID
- server.py
- app.js
- validate_data_sources
- should_shade_scenario

## God Nodes (most connected - your core abstractions)
1. `main()` - 11 edges
2. `save_pdf_reports()` - 10 edges
3. `run_full_ml()` - 9 edges
4. `save_ml_2025_forecasts()` - 8 edges
5. `load_historical_incidents_from_sqlite()` - 8 edges
6. `treinar()` - 7 edges
7. `read_wide_monthly()` - 6 edges
8. `build_base_panel()` - 6 edges
9. `project_city()` - 6 edges
10. `save_outputs_by_latitude()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `treinar()` --calls--> `build_base_panel()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `treinar()` --calls--> `_build_ml_features()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `treinar()` --calls--> `_evaluate_split()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `treinar()` --calls--> `run_full_ml()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `api_status()` --calls--> `get_db_status()`  [EXTRACTED]
  app/server.py → app/ml_runner.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Medallion Data Layers** — data_readme, docs_arquitetura_de_dados, docs_legado_historico_diario_projeto [EXTRACTED 0.95]

## Communities (23 total, 6 thin omitted)

### Community 0 - "Path"
Cohesion: 0.31
Nodes (10): Path, build_code_lookup_from_latitude_files(), discover_files(), load_historical_incidents_from_sqlite(), normalize_code(), Carrega histórico diretamente do SQLite para preservar integridade dos…, read_enso_series(), read_wide_monthly() (+2 more)

### Community 1 - "ingestor_api_sul.py"
Cohesion: 0.19
Nodes (11): Coleta isolada de São Carlos, SC — Clima + Saúde em 1 execução., fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima() (+3 more)

### Community 3 - "loaders.py"
Cohesion: 0.22
Nodes (10): GeoDataFrame, carregar_dados_brutos(), carregar_dados_processados(), carregar_geodados(), DataFrame, Carrega dados da pasta data/processed, Carrega shapefiles ou geojson da pasta data/geodados, Salva dataframe na pasta data/processed (+2 more)

### Community 4 - "DataFrame"
Cohesion: 0.31
Nodes (10): build_monthly_climatology(), build_yearly_templates(), predict_annual_cases_2025_no_increment(), predict_annual_cases_2025_with_increment(), project_city(), DataFrame, Cria templates mensais por ano historico para manter variacao interanual…, Previsao anual de 2025 com 1 passo de incremento SSP (base 2024). (+2 more)

### Community 5 - "motor_lote_modelagem_v2_por_latitude.py"
Cohesion: 0.32
Nodes (10): calibrate_region(), CalibrationBundle, CoverageInfo, incidentes_formatter(), main(), Gera dois PDFs: gráficos por latitude + relatório executivo., Salva saídas organizadas por faixa de latitude + consolidado regional., save_outputs_by_latitude() (+2 more)

### Community 6 - "ml_runner.py"
Cohesion: 0.26
Nodes (12): ml_runner.py — Wrapper leve do motor ML para a interface Prodígia. Encapsula…, Executa treino XGBoost e retorna métricas + dados para gráficos. Parameters…, treinar(), ndarray, build_base_panel(), _build_ml_features(), _evaluate_split(), Faixa simétrica (+/- erro%) por SSP, com erro crescente no horizonte. (+4 more)

### Community 17 - "server.py"
Cohesion: 0.21
Nodes (14): get_cidades(), get_db_status(), Retorna estatísticas do banco para o painel de status., Lista cidades disponíveis no SQLite para o filtro avançado., api_cidades(), api_progresso(), api_resultados(), api_status() (+6 more)

### Community 18 - "app.js"
Cohesion: 0.39
Nodes (5): carregarResultados(), iniciarTreino(), renderChartBarras(), renderChartFI(), renderMetricas()

## Knowledge Gaps
- **3 isolated node(s):** `Dengue Modeling with ID`, `XGBoost Global Model`, `Compass Rose`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 41 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `treinar()` connect `ml_runner.py` to `server.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `run_full_ml()` connect `ml_runner.py` to `Path`, `DataFrame`, `motor_lote_modelagem_v2_por_latitude.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `build_base_panel()` connect `ml_runner.py` to `Path`, `DataFrame`, `motor_lote_modelagem_v2_por_latitude.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **What connects `Dengue Modeling with ID`, `XGBoost Global Model`, `Compass Rose` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._