# Graph Report - Projeto_Clima_X_Dengue  (2026-09-10)

## Corpus Check
- 15 files · ~20,074 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 92 nodes · 161 edges · 14 communities (6 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `05ab162f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- motor_lote_modelagem_v2_por_latitude.py
- ingestor_api_sul.py
- loaders.py
- DataFrame
- save_pdf_reports
- Medallion Architecture
- main.py
- Compass Rose
- Dengue Modeling with ID

## God Nodes (most connected - your core abstractions)
1. `main()` - 11 edges
2. `save_pdf_reports()` - 10 edges
3. `save_ml_2025_forecasts()` - 8 edges
4. `load_historical_incidents_from_csvs_latitude()` - 8 edges
5. `load_ml_panel_from_csvs_latitude()` - 8 edges
6. `run_full_ml_from_csvs_latitude()` - 8 edges
7. `to_float()` - 6 edges
8. `read_enso_series()` - 6 edges
9. `read_wide_monthly()` - 6 edges
10. `project_city()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `save_pdf_reports()` --references--> `CalibrationBundle`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_por_latitude.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py  _Bridges community 4 → community 6_
- `build_base_panel()` --references--> `Path`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_por_latitude.py →   _Bridges community 0 → community 4_
- `save_pdf_reports()` --references--> `Path`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_por_latitude.py →   _Bridges community 0 → community 6_

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Medallion Data Layers** — data_readme, docs_arquitetura_de_dados, docs_legado_historico_diario_projeto [EXTRACTED 0.95]

## Communities (14 total, 3 thin omitted)

### Community 0 - "motor_lote_modelagem_v2_por_latitude.py"
Cohesion: 0.19
Nodes (19): Path, build_code_lookup_from_latitude_files(), _build_ml_features(), discover_files(), load_historical_incidents_from_csvs_latitude(), load_ml_panel_from_csvs_latitude(), normalize_code(), Verifica integridade das fontes de dados antes do processamento. (+11 more)

### Community 1 - "ingestor_api_sul.py"
Cohesion: 0.19
Nodes (11): Coleta isolada de São Carlos, SC — Clima + Saúde em 1 execução., fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima() (+3 more)

### Community 3 - "loaders.py"
Cohesion: 0.22
Nodes (10): GeoDataFrame, carregar_dados_brutos(), carregar_dados_processados(), carregar_geodados(), DataFrame, Carrega dados da pasta data/processed, Carrega shapefiles ou geojson da pasta data/geodados, Salva dataframe na pasta data/processed (+2 more)

### Community 4 - "DataFrame"
Cohesion: 0.21
Nodes (17): build_base_panel(), build_monthly_climatology(), build_yearly_templates(), calibrate_region(), CalibrationBundle, main(), predict_annual_cases_2025_no_increment(), predict_annual_cases_2025_with_increment() (+9 more)

### Community 6 - "save_pdf_reports"
Cohesion: 0.25
Nodes (9): ndarray, CoverageInfo, _evaluate_split(), incidentes_formatter(), Gera dois PDFs: gráficos por latitude + relatório executivo., Faixa simétrica (+/- erro%) por SSP, com erro crescente no horizonte., _safe_mape(), save_pdf_reports() (+1 more)

### Community 8 - "main.py"
Cohesion: 0.70
Nodes (4): command_generate_reports(), command_process_data(), command_run_model(), main()

## Knowledge Gaps
- **3 isolated node(s):** `XGBoost Global Model`, `Compass Rose`, `Dengue Modeling with ID`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 30 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_historical_incidents_from_csvs_latitude()` connect `motor_lote_modelagem_v2_por_latitude.py` to `DataFrame`, `save_pdf_reports`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `save_pdf_reports()` connect `save_pdf_reports` to `motor_lote_modelagem_v2_por_latitude.py`, `DataFrame`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `run_full_ml_from_csvs_latitude()` connect `motor_lote_modelagem_v2_por_latitude.py` to `DataFrame`, `save_pdf_reports`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **What connects `XGBoost Global Model`, `Compass Rose`, `Dengue Modeling with ID` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._