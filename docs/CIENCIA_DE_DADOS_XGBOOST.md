# Ciência de Dados — Do Prophet ao XGBoost Global

Este documento detalha as decisões técnicas de modelagem, a engenharia de features e os resultados de validação do modelo preditivo de dengue.

## 1. Evolução dos Modelos

### 1.1 Prophet (Facebook/Meta) — Modelo Descartado
O primeiro modelo testado foi o **Prophet**, um algoritmo de séries temporais univariadas.

**Por que falhou:**
- **Zero-Inflated Data:** Mais de 60% dos meses nas cidades do Sul registram zero casos de dengue (invernos rigorosos). O Prophet não foi projetado para lidar com séries dominadas por zeros.
- **Escopo Local:** O Prophet treina um modelo por cidade. Para 1.190 municípios, isso significaria 1.190 modelos independentes, sem transferência de conhecimento entre cidades vizinhas.
- **Resultados:** R² de 0.454 em Joaçaba (a melhor cidade) e R² negativo em Lobato e Formosa do Oeste.

### 1.2 XGBoost Regressor — Modelo Adotado
A solução foi migrar para um **modelo global** baseado em Gradient Boosted Trees (XGBoost), onde todas as 1.190 cidades são treinadas simultaneamente.

**Por que funciona:**
- Árvores de decisão lidam naturalmente com zeros (criam ramificações do tipo "SE casos = 0 E temperatura < 15°C → prever 0")
- O modelo global aprende padrões transversais: o comportamento da dengue em Londrina (PR) ajuda a prever Joinville (SC)
- Features categóricas e numéricas são tratadas de forma nativa

---

## 2. Engenharia de Features

A chave do sucesso do modelo foi a criação de **7 features** que capturam conhecimento climático, geográfico e epidemiológico sem necessidade de dados externos:

### Features Climáticas (com defasagem de 3 meses)
O mosquito Aedes aegypti tem um ciclo biológico: a chuva de Janeiro cria criadouros, as larvas amadurecem em Fevereiro, e os adultos picam em Março/Abril. Por isso, usamos um **lag de 3 meses** nas variáveis climáticas:
- **`temp_lag3`**: Temperatura média do município 3 meses antes
- **`prec_lag3`**: Precipitação (chuva em mm) 3 meses antes
- **`enso_lag3`**: Índice ONI (El Niño/La Niña) 3 meses antes

### Feature Geográfica
- **`latitude`**: Coordenada geográfica. O XGBoost aprende que municípios com latitude mais negativa (mais ao sul) tendem a ter menos dengue por conta do frio. Também detecta a barreira natural das Serras Gaúcha e Catarinense.

### Feature de Proxy Populacional
- **`max_historico`**: O maior pico de casos que a cidade já registrou em um único mês. Funciona como proxy de urbanização: cidades grandes (Londrina, Maringá) têm picos de milhares, enquanto vilas rurais têm picos de 0 a 5. Validamos que adicionar Temperatura Mínima, Máxima, Longitude e Amplitude Térmica **não melhora** o modelo (R² cai de 0.71 para 0.64 por redundância), confirmando que estas 7 features são o conjunto ótimo.

### Features Epidemiológicas (Autorregressão)
- **`casos_lag1`**: Casos no mês anterior. Captura a velocidade de transmissão: um surto em crescimento alimenta o mês seguinte.
- **`casos_lag12`**: Casos no mesmo mês do ano anterior. Captura a memória imunológica de rebanho: se 2022 teve um surto massivo, a população desenvolveu anticorpos, e 2023 tende a ter menos casos.

---

## 3. Estratégias de Validação

### 3.1 Validação Temporal (Teste Cego 2024)
- **Treino:** 2015 a 2023 (114.240 registros)
- **Teste:** 2024 inteiro (14.280 registros)
- **R² = 0.327** — O modelo foi conservador porque 2024 foi um "Cisne Negro" (escala de surto nunca vista antes no histórico)

### 3.2 Validação Global (Cross-Validation Espacial)
- **Treino:** 80% de todas as cidades, todos os anos
- **Teste:** 20% das cidades restantes
- **R² = 0.744** — O modelo generaliza com alta precisão para cidades nunca vistas, confirmando que as features capturam padrões universais da relação clima-dengue

### 3.3 Variáveis Testadas e Descartadas
Testamos a inclusão de Temperatura Mínima, Temperatura Máxima, Longitude e Amplitude Térmica. O R² caiu de 0.713 para 0.640, confirmando que essas variáveis são redundantes com a Temperatura Média e Latitude. O modelo de 7 features é o conjunto ótimo.

---

## 4. Variáveis Disponíveis vs Utilizadas vs Ausentes

| Variável | Disponível | Utilizada | Motivo |
|----------|-----------|-----------|--------|
| Temperatura Média | Sim | Sim | Correlação direta com ciclo do mosquito |
| Precipitação | Sim | Sim | Criadouros de água parada |
| Índice El Niño (ONI) | Sim | Sim | Anomalias climáticas regionais |
| Latitude | Sim | Sim | Barreira geográfica (frio no sul) |
| Temperatura Mínima | Sim | Não | Redundante com Temp. Média (testado) |
| Temperatura Máxima | Sim | Não | Redundante com Temp. Média (testado) |
| Longitude | Sim | Não | Não melhora o R² (testado) |
| Umidade do Ar | **Não** | — | Impacto alto no mosquito, não disponível nos dados |
| Velocidade do Vento | **Não** | — | Impacto médio, não disponível |
| Altitude | **Não** | — | Impacto alto (proxy parcial via latitude) |
| População / Densidade | **Não** | — | Proxy via `max_historico` |
