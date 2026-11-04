# CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)

Projeto de ML que prevê casos mensais de **dengue e chikungunya** nos 1.190 municípios da
Região Sul (PR, SC, RS) a partir do histórico de casos + clima, e serve a previsão via API.

**Pergunta de pesquisa (fixa):** "Variáveis climáticas melhoram a previsão de casos de dengue e
chikungunya em horizontes de 1, 2 e 3 meses, além do que o histórico de casos já explica?"

O plano de trabalho vigente está em `docs/PLANO_EXPERIMENTO_FINAL.md` (Fases 0–5).

## Comandos

Sempre use o Python do venv: `.venv/Scripts/python.exe` (Windows, Python 3.12).

```bash
.venv/Scripts/python.exe -m pytest -q                       # testes (devem passar sempre)
.venv/Scripts/python.exe main.py experimento                # Fase 1: 24 rodadas + baselines (dev 2018–2024)
.venv/Scripts/python.exe main.py analise                    # Fase 2: tabela comparativa + SHAP + config sugerida
.venv/Scripts/python.exe main.py teste-final                # Fase 3: teste ÚNICO em 2025 (trava após rodar)
.venv/Scripts/python.exe main.py modelo-final               # Fase 4: retreina 2015–2025 e salva artefatos de produção
.venv/Scripts/python.exe main.py serve                      # dashboard + API em http://localhost:8000
.venv/Scripts/python.exe main.py train --doenca todas       # pipeline v4 do dashboard (Modelo A/B + SSP)
.venv/Scripts/python.exe main.py export-dashboard           # JSONs do dashboard
```

## Arquitetura

```
data/processed/dengue_analytics.db   SQLite (gitignored): ingestao_saude, ingestao_clima,
                                     ingestao_enso, ingestao_populacao (texto em UTF-8; o console
                                     cp1252 do Windows exibe acentos como "�" — não é corrupção)
src/processamento/                   Robôs de ingestão (InfoDengue, Open-Meteo, NOAA, IBGE)
src/ml_pipeline/
  data_ingestion.py      SQLite → painel (code, year, month, casos, clima, pop). Códigos IBGE de 6 dígitos.
  feature_engineering.py build_ml_features(panel, doenca, horizonte) + get_feature_columns(..., usar_clima)
  model_training.py      XGB_PARAMS fixos, folds expanding window, fit_predict_fold, train_model
  metricas.py            As 5 métricas do plano (MAE, R², MAE-surto, Skill Score, AUC risco alto)
  baselines.py           Persistência (lag h), sazonal (lag 12), GLM NB
  experimento_horizontes.py  Fase 1 → output/experimento/resultados.csv
  analise_experimento.py     Fase 2 → output/experimento/analise.md + config_escolhida.json
  teste_final.py             Fase 3 → output/experimento/teste_final_2025.json (+ trava)
  modelo_final.py            Fase 4.1 → output/models/final/<doenca>/ (modelos por horizonte + metadata.json)
  ml_orchestrator.py     Pipeline v4 do dashboard (Modelo A + Modelo B/SSP)
src/prediction_service/  predictor, risk_classifier, data_fetcher, schemas (Pydantic)
app/server.py            FastAPI: dashboard + POST /api/predict
tests/                   pytest, só dados sintéticos (não depende do banco)
```

## Regras metodológicas (não violar)

- **Sem vazamento.** Toda feature da linha t usa só informação até t−h (h = horizonte).
  O baseline de persistência no horizonte h é `casos[t−h]`, nunca `lag1`.
  Limiares (P99 do corte, mediana/P90 das métricas) são calculados **só com anos de treino** do fold.
- **2025 é holdout.** Desenvolvimento usa apenas 2015–2024 (folds de teste 2018–2024).
  `ANO_HOLDOUT` em `src/config.py`. O teste em 2025 roda uma única vez (`teste-final` grava trava).
- **Hiperparâmetros fixos** (`XGB_PARAMS` em `model_training.py`). Não fazer grid search nem
  trocar de algoritmo no experimento — estamos medindo efeito de horizonte e clima.
- **Zika fora** do experimento e da API (dados só até 2024, poucos casos). A API responde com aviso.
- NaN em features = "sem histórico"; o XGBoost trata nativamente. Não preencher com 0.
- Avaliar sempre no valor real (sem corte); o corte P99 só afeta o alvo de treino.
- Reportar onde o modelo perde. Resultado negativo ("clima não agrega") é conclusão válida.

## Convenções

- Código, comentários, logs e docs em **português**. Nomes de doença: `dengue`, `chikungunya`, `zika`;
  colunas-alvo `dengue_cases`, `chik_cases`, `zika_cases`; prefixos de feature `dengue_`, `chik_`, `zika_`.
- Caminhos sempre via `pathlib` a partir da raiz (`src/config.py`), nunca absolutos.
- `output/` e `data/processed/` são gitignored: artefatos são regeneráveis pelos comandos acima.
- Testes novos usam o fixture `mini_panel` (sintético). Rode `pytest` antes de commitar.
- Legado: `src/processamento/motor_lote_modelagem_v2_por_latitude.py`, `docs/legado/`, `scratch/`
  não fazem parte do pipeline atual — não estender.
- `graphify-out/` contém o grafo de conhecimento do código (`GRAPH_REPORT.md`); atualizar com
  `graphify update .` após mudanças grandes.
