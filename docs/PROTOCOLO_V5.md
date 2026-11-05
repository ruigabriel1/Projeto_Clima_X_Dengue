# Protocolo v5 — Pré-registro (fixado antes de ingerir dados de 2026)

Data do registro: 2026-11-04. Estado do banco no registro: `ingestao_saude`, `ingestao_clima` e
`ingestao_populacao` terminam em dez/2025; `ingestao_enso` já contém jan–ago/2026 (índice global da
NOAA, não usado como feature no v5). Nenhum caso nem clima municipal de 2026 foi carregado ou analisado.
O hash do commit que introduz este arquivo é a referência do pré-registro.

## Hipóteses

- **H1 (efeito):** temperatura e precipitação têm efeito defasado (0–3 meses) sobre a incidência de
  dengue e chikungunya, estimado por DLNM com controle de sazonalidade local e choques interanuais comuns.
- **H2 (valor preditivo):** acrescentar clima a um modelo com histórico de casos NÃO reduz o erro de
  previsão de 1–3 meses de forma consistente (resultado do experimento final, a ser reconfirmado
  com o desenho parcimonioso abaixo).
- **H3 (suscetibilidade):** features de incidência acumulada (proxy de imunidade de rebanho)
  reduzem o erro de previsão, sobretudo após anos epidêmicos.

## Análise de efeito (DLNM) — responde H1

- Modelo: Poisson condicional, `log E[casos] = cb(temp) + cb(prec) + β·log1p(casos t−1) + EF(cidade×mês-calendário) + EF(UF×ano) + offset log(pop)`.
- Cross-basis: temperatura média mensal e precipitação mensal; dimensão do valor = spline natural com
  3 graus de liberdade (nós nos percentis 10/50/90 da série completa); dimensão do lag = lags 0–3 meses,
  sem restrição (4 coeficientes por função de base).
- Período: 2015–2025. 2026 não entra.
- Inferência: erro padrão agrupado por município; IC 95%.
- Resultado reportado: RR acumulado (lags 0–3) no P10 e no P90 de cada variável vs. a mediana;
  curva exposição-resposta; curva lag-resposta no P90.
- Sensibilidade: (a) sem EF de UF×ano (mostra o confundimento por choques interanuais);
  (b) sem o termo autorregressivo.

## Experimento preditivo — responde H2 e H3

- Algoritmo e hiperparâmetros: XGBoost Poisson com `XGB_PARAMS` fixos (inalterados). Sem grid search.
- Alvo: casos mensais com offset log(pop/100 mil) (o modelo aprende incidência).
- Grupos de features:
  - `casos` (sempre): lags/médias da doença-alvo e da outra doença, incidência defasada, incidência da
    faixa de latitude, sazonalidade (seno/cosseno do mês), log(pop), |latitude|, longitude.
  - `clima_parcimonioso`: `temp_lag{h..h+2}`, `prec_lag{h..h+2}`. Nada mais (sem ENSO, sem receptividade,
    sem anomalias, sem umidade).
  - `suscetibilidade`: incidência acumulada em 12, 24 e 36 meses terminando em t−h; meses desde o último
    mês com incidência ≥ 100/100 mil até t−h (limite fixo, sem quantis, para não vazar), truncado em 60.
- Fatores: doença {dengue, chikungunya} × h {1, 2, 3} × clima {sem, parcimonioso} × suscetibilidade {sem, com}.
- Validação de desenvolvimento: expanding window, folds 2018–2024. O ano de 2025 é reportado à parte como
  "segunda validação já vista" (foi o holdout v4; não é teste limpo).
- Métricas: MAE (casos); MAE de incidência por cidade com agregação pela **mediana** entre cidades;
  Skill vs. persistência (casos[t−h]); AUC, Brier e calibração do alvo de risco.
- **Alvo de risco:** incidência do mês > P75 da incidência mensal da própria cidade nos anos de treino.
  Escore = incidência prevista / P75 da cidade; probabilidade = calibração isotônica do escore
  ajustada em folds anteriores (cross-fitting temporal).
- Benchmark de alerta: `nivel` do InfoDengue no mês t−h (último alerta oficial conhecido), máximo das
  semanas do mês.

## Regra de decisão (fixa)

Para cada doença, um grupo de features (clima ou suscetibilidade) entra no modelo de produção se e só se,
em pelo menos 2 dos 3 horizontes, o ΔMAE (com − sem, mantendo o outro grupo como na melhor alternativa)
for negativo com IC 95% por bootstrap de municípios inteiramente abaixo de zero. Em caso contrário, fica de fora.
O produto é o **alerta de risco**; a contagem é informação secundária.

## Holdout prospectivo

- Janela: **jan–ago/2026**, só meses com ≥ 8 semanas entre o fim do mês e a data de ingestão.
- Treino: 2015–2025 completo. Uma única execução, com trava (`--confirmar`); nada é ajustado depois.
- Reportado: MAE, Skill, AUC, Brier, calibração e o benchmark do InfoDengue, por doença e horizonte.

## Desvios

Qualquer desvio deste protocolo é registrado aqui, com data e motivo, antes de rodar a análise afetada.

- **2026-11-04 — DLNM, dimensão do valor.** O texto "spline natural com 3 graus de liberdade (nós nos
  percentis 10/50/90)" é inconsistente: 3 nós internos + fronteiras no mínimo/máximo geram 4 funções de
  base (convenção de `ns()` no R, usada pelo pacote `dlnm`). Adota-se a especificação pelos nós
  (P10/P50/P90 internos, fronteiras no mín./máx.) → 4 g.l. por variável. Registrado antes de rodar o DLNM.
- **2026-11-04 22:46 — 1ª execução do teste de 2026 invalidada por vazamento no código do teste.**
  Em `teste_prospectivo.avaliar`, a coluna auxiliar `_incid` (casos do mês-alvo ÷ população) foi criada
  antes da seleção de features e entrou como variável. Resultado impossível (AUC 0,998–1,000; correlação
  previsto × real 0,997) denunciou o erro. Experimento v5, DLNM e modelos de produção não tinham o bug
  (features conferidas idênticas ao `meta.json`). Correção: seleção de features antes de qualquer coluna
  auxiliar, colunas com prefixo `_` nunca são features, e o teste agora aborta se as features divergirem
  das do desenvolvimento. O que a execução inválida expôs: totais de casos de 2026 e as métricas da
  persistência e do alerta InfoDengue (que não dependem do modelo); nada sobre o modelo. **Nenhuma
  configuração, peso ou regra foi alterada.** O teste é reexecutado uma vez com `--forcar`; os arquivos da
  execução inválida ficam em `output/experimento_v5/teste_2026_invalido/`.
- **2026-11-04 (noite) — Combinação modelo + persistência e contagem como métrica co-primária.**
  Registrado ANTES de qualquer teste em 2026 e antes de calcular qualquer resultado da combinação.
  Motivo: no desenvolvimento, a persistência empatou ou venceu o modelo na dengue a 1–2 meses, e o
  objetivo do projeto é prever casos o mais perto possível da realidade.
  - Combinação: `casos_comb = w · casos_modelo + (1 − w) · casos[t−h]` por doença × horizonte, com
    `w ∈ {0,0; 0,1; …; 1,0}` escolhido por menor MAE. Na validação, `w` do ano Y é escolhido só com
    os anos < Y (cross-fitting temporal; 2018 usa w = 1). Para o teste de 2026, `w` final usa 2018–2025.
  - O escore de risco passa a vir da incidência combinada (mesma calibração isotônica temporal).
  - Regra: a combinação substitui o modelo puro (na contagem e no risco) se reduzir o MAE com IC 95%
    por bootstrap de municípios abaixo de zero em ≥ 2 dos 3 horizontes (OOF 2018–2024), por doença.
  - No teste de 2026 a contagem (MAE, Skill, MAE de incidência por cidade) passa a ser reportada como
    resultado co-primário, ao lado do risco (AUC, Brier). Modelo puro, combinação, persistência e
    alerta do InfoDengue são todos reportados.
- **2026-11-04 — Suscetibilidade, "meses desde o último surto".** Quando a cidade nunca teve mês
  ≥ 100/100 mil até t−h, a feature fica ausente (NaN, tratado nativamente pelo XGBoost), em vez de
  truncada em 60 (o truncamento em 60 vale para quem já teve surto). Implementado assim no código antes da
  execução; registrado aqui durante a execução do experimento v5, antes de qualquer resultado ser visto.
