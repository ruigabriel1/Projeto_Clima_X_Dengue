# CLAUDE.md — Projeto Clima × Arboviroses (Região Sul)

Projeto de ML/epidemiologia sobre **dengue e chikungunya** nos 1.190 municípios da Região Sul
(PR, SC, RS), com duas frentes separadas:

1. **Efeito do clima (inferência):** DLNM — quanto temperatura e chuva mudam o risco, com defasagem.
2. **Previsão (produto):** alerta de risco de 1–3 meses — P(incidência > P75 da própria cidade).

**Tese:** o clima tem efeito mensurável, mas acrescenta pouco à previsão de curto prazo além do
histórico de casos; a previsão útil é de risco relativo, não de magnitude.

Protocolo vigente (pré-registrado): `docs/PROTOCOLO_V5.md` (produção v5.1). Em modo sombra: `docs/PROTOCOLO_V6.md`
(teste 2026-11 a 2027-08) e `docs/PROTOCOLO_V7.md` (histórico 2010+, Rt, nível regional; teste 2027-01 a 2027-08).
Plano: `docs/PLANO_V5_LIMPEZA_PUBLICAVEL.md`.
Histórico v4 (experimento final + teste 2025): `docs/PLANO_EXPERIMENTO_FINAL.md`, `docs/resultados_experimento/`.

## Comandos

Sempre use o Python do venv: `.venv/Scripts/python.exe` (Windows, Python 3.12).

```bash
.venv/Scripts/python.exe -m pytest -q                    # testes (dados sintéticos; devem passar sempre)
.venv/Scripts/python.exe main.py atualizar-dados         # ingestão incremental idempotente (InfoDengue, Open-Meteo, NOAA)
.venv/Scripts/python.exe main.py dlnm                    # H1: efeito do clima (output/dlnm/)
.venv/Scripts/python.exe main.py experimento-v5          # H2/H3: clima parcimonioso × suscetibilidade (output/experimento_v5/)
.venv/Scripts/python.exe main.py modelo-risco            # benchmark InfoDengue + modelos de alerta (output/models/final_v5/)
.venv/Scripts/python.exe main.py modelo-risco --sem-benchmark --producao   # PRODUÇÃO v5.1: todos os meses consolidados
.venv/Scripts/python.exe main.py atualizar-dados --alvo backfill   # v7: dengue 2010–2014, clima 2009-07+, população (só insere)
.venv/Scripts/python.exe main.py sorotipo               # v7: sorotipo por UF×mês do SINAN (cache fora do OneDrive)
.venv/Scripts/python.exe main.py experimento-v6 / modelo-v6     # v6 (trava de pré-registro) e modelo do modo sombra
.venv/Scripts/python.exe main.py experimento-v7 / modelo-v7     # v7 (trava de pré-registro) e modelo do modo sombra
.venv/Scripts/python.exe main.py atualizar-mensal        # ingestão + monitoramento ao vivo + previsões do mês (v5.1 e sombra v6/v7)
.venv/Scripts/python.exe main.py empacotar               # dist/artefatos_v5.1.zip (modelos + banco, SHA-256) para a Release
docker build -t prodigia . && docker run -p 8000:8000 prodigia   # serviço empacotado (requirements-api.txt, versões fixas)
.venv/Scripts/python.exe main.py teste-prospectivo --confirmar   # teste ÚNICO jan–ago/2026 (trava)
.venv/Scripts/python.exe main.py serve                   # dashboard + API em http://localhost:8000 (/docs)
.venv/Scripts/python.exe main.py train / export-dashboard        # modelo e JSON do dashboard
.venv/Scripts/python.exe main.py experimento / analise / teste-final   # v4 (reprodutibilidade; 2025 já usado)
```

## Arquitetura

```
data/processed/dengue_analytics.db   SQLite (gitignored). Tabelas ingestao_{saude,clima,enso,populacao},
                                     índice UNIQUE (CODIGO_MUNICIPIO, ANO, MES), ingestao_progresso.
                                     Texto em UTF-8 (o console cp1252 mostra acentos como "�": não é corrupção).
src/processamento/   ingestor_api_sul (fetchers), atualizacao_incremental (upsert idempotente, backfill só-inserção,
                     cópias semanais em ingestao_infodengue_snapshot), ingestor_ibge_populacao, ingestor_sinan_sorotipo
src/analise_efeito/  dlnm.py — Poisson condicional (pyfixest) com EF cidade×mês e UF×ano, cross-basis 0–3 meses
src/ml_pipeline/
  data_ingestion.py       SQLite → painel (code 6 dígitos, year, month, casos, clima, pop, NIVEL_*);
                          padrão ano_min=2015 e sem Rt = painel exato da v4–v6 (v7: ano_min=2010, incluir_rt=True)
  feature_engineering.py  build_ml_features(panel, doenca, horizonte); get_feature_columns(..., clima, suscetibilidade);
                          grupos_de_features (casos | clima_parcimonioso | suscetibilidade)
  model_training.py       XGB_PARAMS fixos, folds expanding window, fit_predict_fold (offset log pop)
  experimento_v5.py       experimento do protocolo v5 + decisão pré-registrada
  experimento_v6.py / experimento_v7.py   protocolos v6/v7 (trava: protocolo commitado) + treinar_producao (sombra)
  nivel_regional.py       v7 (N): GLM quasi-Poisson do total por UF + reconciliação com as cidades
  alerta_risco.py         benchmark InfoDengue/persistência + modelos de produção de risco
  teste_prospectivo.py    teste único 2026 com trava
  experimento_horizontes / analise_experimento / teste_final / metricas / modelo_final   (v4)
  ml_orchestrator.py, export_dashboard.py, interpretability.py, baselines.py   (dashboard)
src/prediction_service/  predictor (risco; prever_mes: h≤3 modelo, h>3 faixa histórica; prever_lote = ranking),
                         data_fetcher (só meses consolidados ≥28 dias), cenarios (faixa P10–P90 + fator DLNM, só
                         parte quente/monotônica da curva), monitoramento (1ª emissão vale), rotina_mensal, artefatos, schemas
app/server.py            FastAPI: aplicação (5 abas, app/static/js/app.js) + /api/previsao, /api/ranking, /api/cenario,
                         /api/confiabilidade, /api/historico, /api/municipios, POST /api/predict, /api/modelo/info
Dockerfile, deploy/hf_space/   imagem do serviço e Space do Hugging Face (baixam artefatos da Release modelo-v5.1)
tests/                   pytest, só dados sintéticos
```

## Grafo do código (graphify): consulte antes de abrir arquivos

`graphify-out/graph.json` é um grafo de todo o código e dos docs de referência (~560 nós), atualizado
automaticamente a cada commit pelo hook `.githooks/pre-commit` (ativar uma vez por clone:
`git config core.hooksPath .githooks`). Para economizar contexto, **antes de ler arquivos ou fazer
buscas amplas**, pergunte ao grafo:

```bash
G=.venv/Scripts/graphify.exe
$G explain "Preditor"                      # o que é, arquivo:linha e todas as conexões
$G affected "build_ml_features"            # o que pode quebrar ao mexer nisso (use ANTES de editar)
$G query "como a API calcula o risco" --budget 1500   # mapa do caminho, com limite de tokens
$G path "PredictRequest" "fit_predict_fold"           # rota entre dois pontos
$G god-nodes --top 15                      # hubs da arquitetura
```

Visão geral pronta em `graphify-out/GRAPH_REPORT.md` (comunidades, hubs, conexões). Depois do grafo,
abra só os trechos indicados (arquivo e linha). O grafo é de código: para decisões e resultados, a
fonte é `docs/PROTOCOLO_V5.md` e `docs/resultados_*`.

## Regras metodológicas (não violar)

- **Sem vazamento.** Feature da linha t usa só informação até t−h. Persistência no horizonte h = casos[t−h].
  Limiares (P75 de risco, quantis) só com anos de treino. `NIVEL_*` (alerta InfoDengue do próprio mês)
  NUNCA é feature — só benchmark, e sempre defasado em h.
- **Holdouts são de uso único.** 2025 já foi usado (v4). 2026 (jan–ago) é o holdout da v5; nada de 2026 entra
  em desenvolvimento, DLNM ou decisão. `teste-prospectivo` exige `--confirmar` e grava trava.
- **Histórico imutável.** A ingestão incremental não sobrescreve casos/clima < 2026 (só acrescenta NIVEL_* e, pela v7,
  RT_*/P_RT1_*). O backfill 2010–2014 só insere meses inexistentes. O Rt do próprio mês nunca é feature.
- **Produção ≠ teste.** O modelo v5.1 da aplicação usa 2015–2026 (holdout de 2026 já gasto); o desempenho
  reportado continua sendo o do teste de 2026 + monitoramento ao vivo. Além de 3 meses: só cenário, nunca "previsão".
- **Hiperparâmetros fixos** (`XGB_PARAMS`). Sem grid search, sem trocar algoritmo para "melhorar" métrica.
- **Clima sem ENSO cru nas features de previsão**: ENSO é um valor por mês para todas as cidades e vira
  identificador de ano (memorização de surtos). No DLNM, o EF UF×ano absorve choques interanuais.
- **Desvios do protocolo** são registrados em `docs/PROTOCOLO_V5.md` ANTES de rodar a análise afetada.
- Zika fora (dados insuficientes). Reportar onde o modelo perde, inclusive para a persistência.

## Convenções

- Código, comentários, logs e docs em **português**. Doenças: `dengue`, `chikungunya`, `zika`; alvos
  `dengue_cases`, `chik_cases`, `zika_cases`; prefixos `dengue_`, `chik_`, `zika_`.
- Caminhos via `src/config.py`. `output/` e `data/processed/` são gitignored; resultados que vão para o
  artigo são copiados para `docs/resultados_*`.
- Testes novos usam o fixture `mini_panel` (`tests/conftest.py`). Rode `pytest` antes de commitar.
- Documentos Word do usuário ficam em `docs/artigo/` (fora do git).
- `graphify-out/` é o grafo de conhecimento do código; atualize com `graphify update .` após mudanças grandes.
