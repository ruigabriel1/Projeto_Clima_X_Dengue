# Protocolo v6 — Pré-registro

Data do registro: 2026-11-06, aprovado pelo autor antes de qualquer execução nos dados reais. Nenhum
resultado das mudanças abaixo foi calculado nos dados reais antes deste registro (o código só foi testado
com dados sintéticos; a trava do experimento impede a execução real sem este arquivo commitado). O hash do commit que introduz a versão final deste arquivo é a referência do pré-registro.

## Motivação (o que a v5 errou)

Nos dois testes fora da amostra (2025, protocolo v4; jan–ago/2026, protocolo v5) o modelo falhou do mesmo
jeito: depois de um ano epidêmico, previu outra temporada grande e superestimou o total em 1,5× a 3,5×. Em
2026 perdeu para a persistência (repetir o último mês conhecido) em todos os horizontes, na contagem e na AUC.
A v6 ataca esse ponto com poucas mudanças decididas antes de olhar qualquer resultado.

## Hipóteses

- **H6a (formulação):** partir da persistência e aprender só a mudança reduz o erro de contagem.
- **H6b (vizinhos):** a incidência recente das cidades vizinhas antecipa a chegada de surtos.
- **H6c (imunidade longa):** janelas de 48–60 meses e a imunidade acumulada do estado captam melhor a queda
  depois de anos epidêmicos do que as janelas de 12–36 meses da v5.

## Mudanças candidatas (fixas)

Base (B0): a configuração da v5.1 por doença (dengue `clima_susc`, chikungunya `semclima_susc`), offset
log(pop/100 mil), `XGB_PARAMS` inalterados.

- **A — offset de persistência.** Mesmas features de B0; o offset passa a ser `log(casos[t−h] + 1)` em vez
  de `log(pop/100 mil)`. O XGBoost Poisson aprende então o fator multiplicativo sobre a persistência; com as
  árvores rasas e regularizadas, a previsão encolhe para a persistência quando não há sinal.
  A constante 1 (suavização para cidades com zero casos) é fixada aqui.
- **V — vizinhos.** Para cada cidade, as 8 cidades mais próximas (distância haversine entre as coordenadas
  do município, sem a própria). Features: incidência agregada dos vizinhos (casos/pop × 100 mil) em t−h e
  sua média de 3 meses terminando em t−h.
- **L — imunidade longa.** Incidência acumulada da própria cidade em 48 e 60 meses terminando em t−h e
  incidência acumulada do estado (UF) em 24 meses terminando em t−h.

Nada de ENSO, nada de `NIVEL_*`, nada de zika. Nenhuma outra variante é testada.

## Validação de desenvolvimento

- Dados: todos os meses consolidados (≥ 28 dias após o fim do mês), 2015-01 a 2026-09.
- Expanding window, folds de teste 2018 a 2026 (2026 = jan–set). 2025 e 2026 já foram usados como testes
  únicos (v4 e v5); aqui são dados de desenvolvimento, e por isso a v6 precisa de um teste novo (abaixo).
- Métricas: MAE (casos), skill vs persistência, MAE de incidência (mediana entre cidades), AUC e Brier do
  alvo de risco (P75 da cidade, só com anos de treino), total previsto ÷ real por ano.
- Reportados à parte, sem entrar na decisão: os anos pós-epidêmicos 2025 e 2026.

## Regra de decisão (sequencial, fixa)

Uma mudança é adotada, por doença, se e só se o ΔMAE (com − sem), com IC 95% por bootstrap de municípios,
ficar inteiramente abaixo de zero em pelo menos 2 dos 3 horizontes (mesma regra da v5).

1. A contra B0 → define a formulação F (A ou B0).
2. V contra F e L contra F, cada um isoladamente.
3. Modelo v6 = F + os grupos adotados no passo 2. A combinação final não é testada de novo no desenvolvimento.

Se nada for adotado, a v6 é igual à v5.1 e isso é reportado.

## Teste: modo sombra prospectivo (uso único)

- Depois do registro, o modelo v6 de produção é treinado com os mesmos dados (2015-01 a 2026-09) e passa a
  emitir previsões **ao lado** da v5.1, todo mês, para todas as cidades e horizontes 1–3, registradas em
  `output/monitoramento/previsoes.csv` antes de o mês-alvo consolidar. Só a primeira emissão conta.
- Meses-alvo do teste: **2026-11 a 2027-08**. Avaliação única depois que 2027-08 consolidar.
- Primário, por doença: a v6 substitui a v5.1 na aplicação se o ΔMAE (v6 − v5.1), com IC 95% por bootstrap
  de municípios, ficar abaixo de zero em ≥ 2 dos 3 horizontes. Reportados também: skill vs persistência,
  AUC, total previsto ÷ real e cobertura do intervalo de 90%, para v6, v5.1, persistência e InfoDengue.
- O modelo v6 não é retreinado durante o teste.

## Exploratório (não entra na decisão)

- **Nowcast do último mês:** usar os casos estimados do InfoDengue (`CASOS_EST_*`) do mês ainda não
  consolidado, ganhando um mês de informação. Não pode ser validado no histórico (o banco guarda só o valor
  final de cada mês, não a estimativa da época), então só é avaliável no modo sombra, como variante
  separada, se for implementado antes de 2026-11.

## Desvios

Qualquer desvio é registrado aqui, com data e motivo, antes de rodar a análise afetada.
