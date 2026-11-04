# Plano v5 — Limpeza e Resultado Publicável

> **Contexto (fatos do experimento final, ver docs/resultados_experimento/):**
> - Dengue: o clima não melhora a previsão (ganho de R² +0,0009 sobre lag + mês). O modelo sem clima
>   perdeu para a persistência no teste de 2025 (superestimou o ano pós-epidêmico).
> - Chikungunya: o clima ajudou, quase todo via ENSO, um índice único por mês que funciona como
>   "identificador de ano" (memorização de surtos, ~10 anos de informação interanual).
> - A AUC de "risco alto" se manteve entre 0,86 e 0,91 em 2025: o modelo ordena bem o risco e erra a magnitude.
> - A queda de 2025 foi comum à região inteira (−82% a −85% em todos os quartis), não imunidade local.
>
> **Tese do artigo:** "O clima tem efeito mensurável sobre as arboviroses no Sul do Brasil, mas não
> melhora a previsão de curto prazo além do histórico de casos; a previsão útil é de risco relativo,
> não de magnitude."
>
> **Holdout novo:** 2025 já foi usado. O novo teste prospectivo único é **jan–ago/2026**
> (meses com ≥ 8 semanas de consolidação na data de ingestão). Definido ANTES de ingerir 2026.

---

## Step 0 — Pré-registro do protocolo v5

Criar `docs/PROTOCOLO_V5.md` e commitá-lo ANTES de qualquer ingestão de 2026. Deve fixar:
- hipóteses H1 (efeito DLNM do clima ≠ 0) e H2 (clima não melhora a previsão);
- conjunto climático a priori (só temperatura média e precipitação, lags de 1 a 3 meses; sem ENSO cru);
- definição do alvo de risco (incidência > P75 da própria cidade nos anos de treino);
- métricas (AUC, Brier, calibração, MAE de incidência por cidade com agregação pela mediana);
- regra de decisão;
- holdout jan–ago/2026.
Acceptance: arquivo commitado com hash registrado; nenhum dado de 2026 no banco no momento do commit.
Out of scope: rodar modelos.

## Step 1 — Podar o Modelo B, as projeções SSP e o que o dashboard mostra delas

Remover `src/ml_pipeline/prediction.py`, o Modelo B do `ml_orchestrator`, as features `_FEATURES_MODELO_B`
/ `get_climate_feature_columns`, a exportação de cenários SSP em `export_dashboard.py` e os gráficos
de cenários e o card "+32,9% em 2035–2040" do dashboard (`index.html`, `charts.js`, `ui.js`). Motivo:
projetar casos por cenário climático contradiz o achado de que o clima não melhora a previsão.
Acceptance: `pytest` passa; o dashboard abre sem erro de console e sem nenhuma menção a SSP/2040;
`grep -ri ssp src app` vazio.
Out of scope: redesenhar o dashboard.

## Step 2 — Remover o código legado e consolidar a estrutura

Cleanup: apagar `src/processamento/motor_lote_modelagem_v2_por_latitude.py`, `docs/legado/`, `scratch/`,
`scripts/debug/`, `plano_correcao_ml_e_app.md` e o `.docx` solto na raiz (fica fora do git, só é
movido para `docs/artigo/`); corrigir `iniciar.bat` (porta 8001 → `python main.py serve`); deduplicar
`_PREFIXOS` repetido em `model_training.py` e `baselines.py` (importar de `feature_engineering`).
O comportamento deve ficar idêntico.
Acceptance: `pytest` passa; nenhum import quebrado (`python -c "import src.ml_pipeline.ml_orchestrator"`);
`main.py --help` lista os mesmos comandos.

## Step 3 — Ingestão idempotente de 2026

Implementar a atualização incremental dos robôs (InfoDengue, Open-Meteo, NOAA) até o mês corrente,
com upsert por (CODIGO_MUNICIPIO, ANO, MES) em vez de `append`, `end_year` parametrizável e uma
coluna `INGERIDO_EM`. Guardar também o `nivel` de alerta do InfoDengue (benchmark do Step 7).
Respeitar o rate limit (o ingestor já tem espera por hora).
Acceptance: rodar duas vezes não duplica linhas (teste); 2026 presente para os 1.190 municípios;
`validate_panel` sem duplicatas.
Out of scope: novas fontes de dados.

## Step 4 — Ajustes de modelagem v5 (features e alvo)

Change: alvo em incidência com offset log(pop) (contagem prevista = incidência × pop); conjunto
climático parcimonioso a priori (temp média e precipitação, lags h..h+2) em substituição às 26
variáveis; remover ENSO cru e receptividade das features de previsão; adicionar features de
suscetibilidade (incidência acumulada em 12/24/36 meses defasada em h, meses desde o último mês
acima do P90 da cidade); métricas por cidade (mediana entre cidades) além do agregado.
Acceptance: testes de não-vazamento cobrem as novas features (lag ≥ h); `get_feature_columns`
expõe os grupos `casos`, `clima_parcimonioso`, `suscetibilidade`; pytest passa.
Out of scope: trocar o algoritmo; grid search de hiperparâmetros.

## Step 5 — Experimento v5 (desenvolvimento 2018–2024)

Implementar `experimento_v5` com doença {dengue, chikungunya} × horizonte {1,2,3} × clima
{sem, parcimonioso} × suscetibilidade {sem, com}, avaliado nos folds 2018–2024, mais 2025 reportado
como "segunda validação já vista" (rotulado assim). Incluir o efeito do clima com IC bootstrap por cidade
e a regra de decisão do protocolo v5.
Acceptance: `output/experimento_v5/resultados.csv` com todas as células; relatório markdown com
efeito do clima e da suscetibilidade e IC; nenhum dado de 2026 usado (teste que verifica).
Out of scope: holdout 2026.

## Step 6 — Análise DLNM do efeito do clima (resultado central do artigo)

Implementar `src/analise_efeito/dlnm.py`: regressão de Poisson condicional (`pyfixest.fepois`) com
efeitos fixos cidade×mês-calendário (sazonalidade) e estado×ano (choques interanuais comuns, o que
neutraliza o "ENSO como identificador de ano"), cross-basis de temperatura e precipitação (splines
naturais no valor × lags 0–3 meses), offset log(pop), termo autorregressivo log(casos t−1) e erro
padrão agrupado por cidade. Produzir as curvas de RR exposição-resposta e lag-resposta com IC 95%
e a análise de sensibilidade com e sem o efeito fixo de ano.
Acceptance: curvas de RR (PNG + CSV) por doença; tabela de RR em P10/P90 de temperatura vs. mediana;
teste com dados sintéticos de efeito conhecido recupera o RR simulado (±10%).
Out of scope: previsão; cenários futuros.

## Step 7 — Reposicionar o produto para alerta de risco

Change: a API e o modelo de produção passam a prever a probabilidade de "risco alto" (incidência >
P75 da cidade) por horizonte, com calibração (isotônica nos folds OOF); a contagem vira informação
secundária, com intervalo. `/api/predict` devolve `probabilidade_risco_alto`, `nivel_risco` derivado
da probabilidade e a comparação com o `nivel` do InfoDengue. Métricas: AUC, Brier, curva de
calibração, antecedência do alerta; benchmark contra o `nivel` do InfoDengue.
Acceptance: Brier e AUC do modelo vs. o benchmark InfoDengue no OOF; curva de calibração salva;
testes da API atualizados e passando.
Out of scope: interface do dashboard além do card de previsão.

## Step 8 — Teste prospectivo único em jan–ago/2026

Implementar e rodar uma única vez o teste da configuração escolhida no Step 5/7 sobre jan–ago/2026
(treino ≤ 2025), com trava de uso único como em `teste_final.py`, reportando previsão de contagem,
risco (AUC/Brier/calibração) e o benchmark InfoDengue.
Acceptance: `teste_prospectivo_2026.{json,md}` gravados; trava criada; resultados sem ajuste posterior.

## Step 9 — Documentação e esqueleto do artigo

Atualizar README, CLAUDE.md e o grafo (graphify); criar `docs/artigo/ESBOCO.md` com Introdução,
Dados, Métodos (DLNM + experimento preditivo + holdout prospectivo), Resultados (tabelas geradas),
Discussão (efeito vs. valor preditivo, imunidade/choque comum, ENSO), Limitações.

## Step 10 — Revisão final

Review: revisar o diff completo (correção, vazamento temporal, reprodutibilidade) antes do push.
