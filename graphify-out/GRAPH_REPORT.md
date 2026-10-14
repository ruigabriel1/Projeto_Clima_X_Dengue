# Graph Report - Projeto_Clima_X_Dengue  (2026-10-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 139 nodes · 253 edges · 16 communities (10 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b6a4117c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Path
- ml_orchestrator.py
- main.js
- server.py
- ingestor_api_sul.py
- motor_lote_modelagem_v2_por_latitude.py
- DataFrame
- main
- ingestor_ibge_populacao.py
- prediction.py
- validate_data_sources
- uncertainty_bounds
- should_shade_scenario

## God Nodes (most connected - your core abstractions)
1. `main()` - 11 edges
2. `save_pdf_reports()` - 10 edges
3. `run_full_ml()` - 9 edges
4. `build_base_panel()` - 8 edges
5. `load_historical_incidents_from_sqlite()` - 8 edges
6. `save_ml_2025_forecasts()` - 8 edges
7. `renderAll()` - 7 edges
8. `_build_ml_features()` - 6 edges
9. `_evaluate_split()` - 6 edges
10. `train_model()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `treinar()` --calls--> `build_base_panel()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `treinar()` --calls--> `_build_ml_features()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `treinar()` --calls--> `run_full_ml()`  [EXTRACTED]
  app/ml_runner.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py
- `main()` --calls--> `exportar_dados_dashboard()`  [EXTRACTED]
  main.py → src/ml_pipeline/export_dashboard.py
- `exportar_dados_dashboard()` --calls--> `build_base_panel()`  [EXTRACTED]
  src/ml_pipeline/export_dashboard.py → src/processamento/motor_lote_modelagem_v2_por_latitude.py

## Import Cycles
- None detected.

## Communities (16 total, 3 thin omitted)

### Community 0 - "Path"
Cohesion: 0.13
Nodes (21): ml_runner.py — Wrapper leve do motor ML para a interface Prodígia. Encapsula…, Executa treino XGBoost e retorna métricas + dados para gráficos. Parameters…, treinar(), command_run_model(), main(), exportar_dados_dashboard(), get_cidades(), get_db_status() (+13 more)

### Community 1 - "ml_orchestrator.py"
Cohesion: 0.13
Nodes (18): build_base_panel(), DataFrame, Path, Módulo responsável por construir o painel base a partir do banco de dados…, build_ml_features(), DataFrame, Módulo de Feature Engineering. Responsável por criar as features (lags, médias…, Constrói as features para o modelo preditivo. Adiciona lags de 1 a 3 meses,… (+10 more)

### Community 2 - "main.js"
Cohesion: 0.31
Nodes (12): fetchResultados(), fetchStatus(), getPlotlyConfig(), getPlotlyLayout(), renderChartCenarios(), renderChartHeatmap(), renderChartSazonal(), loadAndRender() (+4 more)

### Community 3 - "server.py"
Cohesion: 0.24
Nodes (11): get_cidades(), get_db_status(), Retorna estatísticas do banco para o painel de status., Lista cidades disponíveis no SQLite para o filtro avançado., api_cidades(), api_resultados(), api_status(), index() (+3 more)

### Community 4 - "ingestor_api_sul.py"
Cohesion: 0.29
Nodes (10): fetch_clima(), fetch_infodengue(), get_ibge_7(), ingest_noaa_enso(), main(), obter_faixa_latitude(), process_clima(), process_saude() (+2 more)

### Community 5 - "motor_lote_modelagem_v2_por_latitude.py"
Cohesion: 0.38
Nodes (8): build_code_lookup_from_latitude_files(), load_historical_incidents_from_sqlite(), normalize_code(), Carrega histórico diretamente do SQLite para preservar integridade dos…, read_enso_series(), read_wide_monthly(), to_float(), to_int()

### Community 6 - "DataFrame"
Cohesion: 0.31
Nodes (10): build_monthly_climatology(), build_yearly_templates(), predict_annual_cases_2025_no_increment(), predict_annual_cases_2025_with_increment(), project_city(), DataFrame, Cria templates mensais por ano historico para manter variacao interanual…, Previsao anual de 2025 com 1 passo de incremento SSP (base 2024). (+2 more)

### Community 7 - "main"
Cohesion: 0.27
Nodes (10): calibrate_region(), CalibrationBundle, CoverageInfo, incidentes_formatter(), main(), Gera dois PDFs: gráficos por latitude + relatório executivo., Salva saídas organizadas por faixa de latitude + consolidado regional., save_outputs_by_latitude() (+2 more)

### Community 8 - "ingestor_ibge_populacao.py"
Cohesion: 0.28
Nodes (7): fetch_populacao_ibge(), get_ibge_7(), main(), DataFrame, ingestor_ibge_populacao.py — Busca estimativas populacionais do IBGE (API…, Busca população estimada do IBGE via API SIDRA (tabela 6579)., Calcula o dígito verificador IBGE para transformar código de 6 em 7 dígitos.

### Community 9 - "prediction.py"
Cohesion: 0.33
Nodes (5): predict_future_scenarios(), DataFrame, Módulo de predição do motor de ML. Responsável por pegar o modelo treinado…, Dada a tabela climática projetada (ou climatologia estendida com deltas do…, # TODO: Implementar a lógica de geração dos DataFrames futuros com os

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_base_panel()` connect `Path` to `motor_lote_modelagem_v2_por_latitude.py`, `DataFrame`, `main`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `get_cidades()` connect `server.py` to `Path`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `get_db_status()` connect `server.py` to `Path`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `Path` be split into smaller, more focused modules?**
  _Cohesion score 0.13405797101449277 - nodes in this community are weakly interconnected._
- **Should `ml_orchestrator.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12987012987012986 - nodes in this community are weakly interconnected._