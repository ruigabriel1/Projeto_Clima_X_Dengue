# Protocolo v7 — Pré-registro

Data do registro: 2026-11-06, aprovado pelo autor antes de qualquer execução nos dados reais. Nenhum resultado das mudanças abaixo
foi calculado nos dados reais. O que foi olhado antes deste registro está listado em "O que já se sabia". A
trava do experimento impede a execução real sem este arquivo commitado. A referência do pré-registro é o hash
do commit que introduz a versão final deste arquivo.

## O que já se sabia (e motivou a v7)

- **Teste de 2026 (protocolo v5).** O modelo superestimou o total em 1,5× a 3,5× e perdeu para a persistência
  em todos os horizontes.
- **Diagnóstico de 2026-11-06, feito antes deste registro sobre previsões já existentes.** Reescalando a
  previsão para que o total regional de cada mês fosse o real (um oráculo), o MAE da dengue em 2026 cairia de
  8,4/23,1/33,0 para 4,5/6,8/8,1. A persistência teve 5,8/8,7/10,8.
- **Validação v5 de 2018–2025.** Nos anos epidêmicos o modelo previu 20% a 50% do total real. O erro dominante
  é o **nível regional** da temporada, não a distribuição entre cidades.
- **v6.** A formulação A (offset de persistência) foi adotada para dengue. Vizinhos e imunidade longa (48/60
  meses) foram rejeitados. A regra só olhava o MAE, e a mudança adotada baixou a AUC.
- **Verificações de disponibilidade de dados, sem olhar desfechos:**
  - o InfoDengue tem dengue semanal de 2010 a 2014 (Maringá, Porto Alegre, Chapecó);
  - a chikungunya só tem vigilância a partir de 2015;
  - a API entrega `Rt` e `p_rt1`;
  - o histórico do InfoDengue é recalculado (`casos_est = casos` nas semanas antigas), então não existem
    estimativas "da época".

## Hipóteses

- **H7a (histórico):** treinar a dengue com 2010–2014 a mais (ciclos de subida e queda) reduz o erro.
- **H7b (Rt):** o número de reprodução estimado pelo InfoDengue antecipa a virada da temporada.
- **H7c (nível regional):** prever o total da UF com um modelo próprio e distribuí-lo entre as cidades pelo
  modelo por cidade reduz o erro de contagem.
- **H7d (sorotipo):** a novidade do sorotipo circulante explica o tamanho da temporada. Só é testada se passar
  no portão de cobertura.

## Dados

- **Saúde (InfoDengue).** Meses consolidados, ≥ 28 dias após o fim do mês, até 2026-09.
  - Dengue a partir de 2010-01; chikungunya a partir de 2015-01. Os zeros da chikungunya antes de 2015 são
    falta de vigilância e ficam ausentes.
  - O backfill 2010–2014 só insere linhas inexistentes. Casos e clima de 2015 em diante não mudam: um checksum
    antes e depois é reportado.
- **Clima (Open-Meteo, ERA5).** 2009-07 a 2014-12 com as mesmas variáveis e a mesma agregação mensal de hoje.
- **População (IBGE, SIDRA 6579).** 2009–2014. 2010 é interpolado linearmente entre 2009 e 2011. Municípios
  instalados depois de 2010 não têm linhas antes da instalação.
- **Rt.** Para cada cidade, doença e mês m, com as semanas cujo início cai em m:
  - `rt_medio` = média do Rt;
  - `rt_ult` = Rt da última semana;
  - `prt1` = média do p_rt1;
  - `rt_uf` = média de `rt_medio` das cidades da UF, ponderada pela população.

  As colunas são acrescentadas aos meses anteriores a 2026, como já acontece com `NIVEL_*`; casos e clima não
  são tocados. **Limitação declarada:** o Rt histórico é o recalculado com dados consolidados, não o que se
  sabia na época.
- **Sorotipo (SINAN, `DENGBR{aa}`, 2010–2025).** Casos com SOROTIPO preenchido, por UF de residência e mês dos
  primeiros sintomas: `n_testados` e `n_denv1..4`.

ENSO cru, `NIVEL_*` e zika continuam fora de qualquer feature.

## Validação de desenvolvimento

- Expanding window com folds de teste de 2018 a 2026 (2026 = jan–set). São os mesmos da v6, para comparar.
- `XGB_PARAMS` inalterados, sem tuning.
- Métricas por doença e horizonte:
  - MAE de casos;
  - skill contra a persistência;
  - AUC e Brier do alvo de risco (P75 da cidade, só com anos de treino);
  - razão total previsto/real por ano.
- Reportados à parte, sem entrar na decisão:
  - os anos pós-epidêmicos 2025–2026;
  - o oráculo do nível regional real;
  - a verificação de que F reproduz a v6 (dengue, MAE dev 16,53/26,23/32,13).

## Base e candidatas (fixas)

**Base F:** a decisão da v6 por doença.
- Dengue: features `clima_susc` e offset `log(casos[t−h] + 1)`.
- Chikungunya: `semclima_susc` e offset `log(pop/100 mil)`.

- **H — histórico 2010+ (só dengue).** As linhas de treino começam em 2010-01, com as mesmas features e os
  mesmos folds de teste. As janelas de suscetibilidade ficam incompletas em 2010–2012 (valores ausentes, que o
  XGBoost trata).
- **R — Rt.** Acrescenta às features da cidade `{p}_rt_medio`, `{p}_rt_ult`, `{p}_prt1` e `{p}_rt_uf`, todas
  em t−h.
- **N — nível regional (top-down).** Para cada doença e horizonte, um GLM quasi-Poisson (escala de Pearson)
  ajustado nos meses de treino do fold, empilhando as 3 UFs:

  `log E[T_uf,t] = log(pop_uf,t / 100 mil) + α_uf + Σ_{k=1,2} [a_k·sen(2πk·m_t/12) + b_k·cos(2πk·m_t/12)]
  + β1·log(T_uf,t−h + 1) + β2·rt_uf,t−h + β3·incid_acum24_uf,t−h`

  - T_uf,t é o total de casos da UF no mês t.
  - `incid_acum24` = casos da UF nos 24 meses terminando em t−h, por 100 mil habitantes.
  - Para a dengue, a série da UF usa 2010+ em N mesmo que H seja rejeitado, porque ela é o insumo do modelo
    regional.
  - Se o treino de um fold tiver menos de 24 meses completos por UF, aquele fold não é reconciliado (fator 1).
  - **Reconciliação:** previsão final da cidade i na UF u = previsão do modelo por cidade × T̂_u ÷ soma das
    previsões das cidades de u no mesmo mês. A ordem das cidades dentro da UF não muda.
- **S — sorotipo (só dengue, só se passar no portão).** Acrescenta a N o termo β4·`novidade_uf,t−h`, com
  `novidade = 1 − Σ_s p_s(3 meses até t−h) · p_s(36 meses anteriores a essa janela)`, onde p_s é a fração do
  sorotipo s entre os casos sorotipados.

**Portão do sorotipo**, avaliado só com contagens de cobertura, sem nenhum desfecho:
- S é testado se, em ≥ 70% das janelas UF × 3 meses de 2015–2025, houver ≥ 10 casos com sorotipo.
- O resultado é gravado em `docs/resultados_v7/portao_sorotipo.json` antes de rodar S.

## Regra de decisão (sequencial, fixa, por doença)

Uma candidata é adotada se e só se cumprir as duas condições:
1. ΔMAE (com − sem), com IC 95% por bootstrap de municípios, inteiramente abaixo de zero em ≥ 2 dos 3
   horizontes;
2. **e**, em cada um desses horizontes, ΔAUC (com − sem, estimativa pontual) ≥ −0,01.

**Ordem:**
1. H contra F → F′ (para a chikungunya, F′ = F).
2. R contra F′ → F″.
3. N contra F″ → F‴.
4. S contra N, se o portão passou e N foi adotado.

**Modelo v7** = o resultado da sequência. A combinação final não é retestada no desenvolvimento. Se nada for
adotado, a v7 é igual à v6 e isso é reportado.

## Teste: modo sombra prospectivo (uso único)

- O modelo v7 de produção é treinado com todos os meses consolidados e emite previsões todo mês, ao lado da
  v5.1 e da v6, para todas as cidades e horizontes 1–3.
- As previsões vão para `output/monitoramento/previsoes.csv` com `modelo="v7"`. Só a primeira emissão conta, e
  o modelo não é retreinado durante o teste.
- Meses-alvo: **2027-01 a 2027-08**, com avaliação única depois que 2027-08 consolidar.
  - Um mês-alvo entra em um horizonte só se a emissão daquele horizonte foi registrada antes de o mês
    consolidar.
  - A meta é estar emitindo até 2026-12-20.
- **Primário, por doença:** a v7 substitui a v5.1 na aplicação se passar na mesma regra dupla contra a v5.1.
  - Se a v6 também passar no próprio teste, fica a v7 só se o ΔMAE (v7 − v6) for < 0 em ≥ 2 dos 3 horizontes;
    senão fica a v6.
- **Reportados também:**
  - skill contra a persistência;
  - AUC;
  - total previsto ÷ real;
  - cobertura do intervalo de 90%, para v7, v6, v5.1, persistência e InfoDengue.

## Exploratório (não entra na decisão)

- **Nowcast:** usar as cópias semanais de `ingestao_infodengue_snapshot` (desde 2026-11-06) para ganhar as
  semanas do mês ainda não consolidado. Só é avaliável com as cópias acumuladas.

## Desvios

Qualquer desvio é registrado aqui, com data e motivo, antes de rodar a análise afetada.
