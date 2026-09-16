# Graph Report - Projeto_Clima_X_Dengue  (2026-09-12)

## Corpus Check
- 17 files · ~22,365 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 92 nodes · 153 edges · 17 communities (7 shown, 3 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ff40095b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- motor_lote_modelagem_v2_por_latitude.py
- ingestor_api_sul.py
- loaders.py
- DataFrame
- main
- run_full_ml
- Medallion Architecture
- main.py
- Compass Rose
- Dengue Modeling with ID

## God Nodes (most connected - your core abstractions)
1. `main()` - 11 edges
2. `save_pdf_reports()` - 10 edges
3. `save_ml_2025_forecasts()` - 8 edges
4. `load_historical_incidents_from_sqlite()` - 8 edges
5. `run_full_ml()` - 7 edges
6. `read_wide_monthly()` - 6 edges
7. `project_city()` - 6 edges
8. `save_outputs_by_latitude()` - 6 edges
9. `CalibrationBundle` - 5 edges
10. `to_float()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `project_city()` --references--> `CalibrationBundle`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_por_latitude.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py  _Bridges community 5 → community 4_
- `run_full_ml()` --references--> `Path`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_por_latitude.py →   _Bridges community 0 → community 6_
- `save_ml_2025_forecasts()` --references--> `Path`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_por_latitude.py →   _Bridges community 0 → community 4_
- `save_outputs_by_latitude()` --references--> `Path`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_por_latitude.py →   _Bridges community 0 → community 5_
- `_build_ml_features()` --references--> `DataFrame`  [EXTRACTED]
  src/processamento/motor_lote_modelagem_v2_por_latitude.py →   _Bridges community 4 → community 6_

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Medallion Data Layers** — data_readme, docs_arquitetura_de_dados, docs_legado_historico_diario_projeto [EXTRACTED 0.95]

## Communities (17 total, 3 thin omitted)

### Community 0 - "motor_lote_modelagem_v2_por_latitude.py"
Cohesion: 0.22
Nodes (15): Path, build_base_panel(), build_code_lookup_from_latitude_files(), discover_files(), load_historical_incidents_from_sqlite(), normalize_code(), Verifica integridade das fontes de dados antes do processamento., Sombras em cenários de referência, no estilo do exemplo IPCC. (+7 more)

### Community 1 - "ingestor_api_sul.py"
Cohesion: 0.19
Nodes (11): Coleta isolada de São Carlos, SC — Clima + Saúde em 1 execução., fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima() (+3 more)

### Community 3 - "loaders.py"
Cohesion: 0.22
Nodes (10): GeoDataFrame, carregar_dados_brutos(), carregar_dados_processados(), carregar_geodados(), DataFrame, Carrega dados da pasta data/processed, Carrega shapefiles ou geojson da pasta data/geodados, Salva dataframe na pasta data/processed (+2 more)

### Community 4 - "DataFrame"
Cohesion: 0.31
Nodes (10): build_monthly_climatology(), build_yearly_templates(), predict_annual_cases_2025_no_increment(), predict_annual_cases_2025_with_increment(), project_city(), DataFrame, Cria templates mensais por ano historico para manter variacao interanual…, Previsao anual de 2025 com 1 passo de incremento SSP (base 2024). (+2 more)

### Community 5 - "main"
Cohesion: 0.27
Nodes (10): calibrate_region(), CalibrationBundle, CoverageInfo, incidentes_formatter(), main(), Gera dois PDFs: gráficos por latitude + relatório executivo., Salva saídas organizadas por faixa de latitude + consolidado regional., save_outputs_by_latitude() (+2 more)

### Community 6 - "run_full_ml"
Cohesion: 0.29
Nodes (8): ndarray, _build_ml_features(), _evaluate_split(), Faixa simétrica (+/- erro%) por SSP, com erro crescente no horizonte., Treina ML completo com split temporal e projeta 2025-2040. Parameters…, run_full_ml(), _safe_mape(), uncertainty_bounds()

### Community 8 - "main.py"
Cohesion: 0.70
Nodes (4): command_generate_reports(), command_process_data(), command_run_model(), main()

## Knowledge Gaps
- **3 isolated node(s):** `Dengue Modeling with ID`, `XGBoost Global Model`, `Compass Rose`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 31 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_historical_incidents_from_sqlite()` connect `motor_lote_modelagem_v2_por_latitude.py` to `DataFrame`, `main`, `run_full_ml`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `save_pdf_reports()` connect `main` to `motor_lote_modelagem_v2_por_latitude.py`, `DataFrame`, `run_full_ml`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `save_ml_2025_forecasts()` connect `DataFrame` to `motor_lote_modelagem_v2_por_latitude.py`, `main`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `Dengue Modeling with ID`, `XGBoost Global Model`, `Compass Rose` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._