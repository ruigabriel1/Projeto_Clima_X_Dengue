# 📊 Guia de Interpretação dos Resultados

## Como Ler e Interpretar a Análise Estatística

---

## 1. Teste de Normalidade

### O que é?
Verifica se os dados seguem uma distribuição normal (curva de sino).

### Exemplo de Resultado:

```
Teste: Shapiro-Wilk
Estatística: 0.8523
p-valor: 0.0001
Interpretação: Dados NÃO seguem distribuição normal (p ≤ 0.05)
```

### Como Interpretar:

| p-valor | Interpretação | O que significa? |
|---------|---------------|------------------|
| **p < 0.05** | ❌ **NÃO normal** | Dados não seguem distribuição de sino. Use testes não paramétricos! |
| **p ≥ 0.05** | ✅ **Normal** | Dados seguem distribuição de sino. Pode usar testes paramétricos. |

### Para Dados de Dengue:
✅ **Esperado: p < 0.05** (dados NÃO normais)  
📌 **Por quê?** Surtos epidêmicos causam picos (assimetria)

---

## 2. Correlação de Spearman (ρ)

### O que é?
Mede a **força e direção** da relação entre duas variáveis (sem assumir normalidade).

### Exemplo de Resultado:

```
ρ (rho) = 0.45
p-valor = 0.0001
Força: Moderada
Direção: Positiva
Interpretação: Correlação moderada positiva. Estatisticamente significativa (p < 0.05)
```

### Como Interpretar:

#### Força da Correlação (|ρ|):

| |ρ| | Força | Significado Prático |
|-----|-------|---------------------|
| **< 0.1** | Desprezível | Praticamente sem relação |
| **0.1 - 0.3** | Fraca | Relação existe, mas é fraca |
| **0.3 - 0.5** | Moderada | Relação evidente e relevante |
| **≥ 0.5** | Forte | Relação forte e importante |

#### Direção:

| ρ | Direção | Significado |
|---|---------|-------------|
| **ρ > 0** | ➚ Positiva | Quando uma variável aumenta, a outra também aumenta |
| **ρ < 0** | ➘ Negativa | Quando uma variável aumenta, a outra diminui |

#### Significância Estatística:

| p-valor | Significância | Símbolo | Confiança |
|---------|---------------|---------|-----------|
| **p < 0.001** | Altamente significativo | *** | 99.9% de confiança |
| **p < 0.01** | Muito significativo | ** | 99% de confiança |
| **p < 0.05** | Significativo | * | 95% de confiança |
| **p ≥ 0.05** | Não significativo | ns | Pode ser acaso |

### Exemplos Práticos:

#### Exemplo 1: Temperatura Média
```
ρ = 0.45, p = 0.0001 ***
```
**Interpretação:**  
✅ Correlação **moderada positiva**  
✅ **Altamente significativa** (não é acaso)  
📊 **Conclusão:** Temperaturas mais altas estão associadas a mais casos de dengue

#### Exemplo 2: Temperatura Mínima
```
ρ = 0.12, p = 0.35 ns
```
**Interpretação:**  
⚠️ Correlação **fraca positiva**  
❌ **Não significativa** (pode ser acaso)  
📊 **Conclusão:** Temperatura mínima não mostra relação clara com casos de dengue

#### Exemplo 3: Precipitação
```
ρ = -0.28, p = 0.02 *
```
**Interpretação:**  
⚠️ Correlação **fraca negativa**  
✅ **Significativa** (não é acaso)  
📊 **Conclusão:** Mais chuva está associada a menos casos (pode indicar lavagem de criadouros)

---

## 3. Teste Mann-Whitney U

### O que é?
Compara dois grupos independentes para ver se há diferença estatística (sem assumir normalidade).

### Exemplo de Resultado:

```
Ponto de Corte (Mediana): 28.5°C

Grupo ALTA temperatura:
  N = 45
  Média de casos: 520.3
  Mediana: 480.0

Grupo BAIXA temperatura:
  N = 43
  Média de casos: 310.7
  Mediana: 290.0

Teste Mann-Whitney U:
  Estatística U = 1234.5
  p-valor = 0.0023
  Diferença Significativa: ✅ Sim
```

### Como Interpretar:

1. **Comparar as Médias:**
   - Grupo Alta: 520.3 casos
   - Grupo Baixa: 310.7 casos
   - Diferença: +209.6 casos (+67.5%)

2. **Verificar Significância:**
   - p = 0.0023 < 0.05
   - ✅ **Diferença é estatisticamente significativa**

3. **Conclusão:**
   - Períodos de temperatura alta têm **significativamente mais casos** de dengue
   - Não é coincidência (confiança > 99%)

### Exemplo Não Significativo:

```
Grupo ALTA precipitação: Média = 450 casos
Grupo BAIXA precipitação: Média = 430 casos
p-valor = 0.45 ns
```

**Interpretação:**  
❌ Diferença de 20 casos NÃO é significativa  
📊 Pode ser variação aleatória

---

## 4. Teste Kruskal-Wallis

### O que é?
Compara **três ou mais grupos** (versão não paramétrica do ANOVA).

### Exemplo de Resultado:

```
Eventos analisados: El Niño, La Niña, Neutro

Estatísticas por Evento:
  El Niño:   Média = 580 casos
  La Niña:   Média = 350 casos
  Neutro:    Média = 420 casos

Teste Kruskal-Wallis:
  Estatística H = 15.42
  Graus de liberdade = 2
  p-valor = 0.0004 ***
  Diferença Significativa: ✅ Sim
```

### Como Interpretar:

1. **Comparar Médias:**
   - El Niño tem mais casos (580)
   - La Niña tem menos casos (350)
   - Diferença: 65.7% a mais no El Niño

2. **Verificar Significância:**
   - p = 0.0004 < 0.05
   - ✅ **Diferença entre eventos é significativa**

3. **Conclusão:**
   - Eventos El Niño estão associados a **mais casos de dengue**
   - La Niña está associada a **menos casos**
   - Diferenças são estatisticamente robustas

---

## 5. Teste de Levene

### O que é?
Verifica se a **variabilidade** (dispersão) é similar entre grupos.

### Exemplo de Resultado:

```
Estatística = 2.45
p-valor = 0.12
Variâncias: ✅ Homogêneas
```

### Como Interpretar:

| p-valor | Resultado | Significado |
|---------|-----------|-------------|
| **p > 0.05** | ✅ Homogêneas | Variâncias são similares entre grupos (bom!) |
| **p ≤ 0.05** | ❌ Heterogêneas | Variâncias diferem (requer cuidado na interpretação) |

---

## 6. Visualizações

### Scatter Plot (Dispersão)

**O que ver:**
- **Pontos subindo para a direita** → Correlação positiva
- **Pontos descendo para a direita** → Correlação negativa
- **Pontos espalhados aleatoriamente** → Sem correlação
- **Linha vermelha tracejada** → Tendência geral

### Boxplot

**O que ver:**
- **Caixa** → 50% dos dados (Q1 a Q3)
- **Linha no meio** → Mediana
- **Diamante vermelho** → Média
- **"Bigodes"** → Extensão dos dados
- **Pontos isolados** → Outliers

**Comparação:**
- Caixas em **alturas diferentes** → Grupos têm valores diferentes
- Caixas **sobrepostas** → Grupos similares

### Série Temporal

**O que ver:**
- **Linha azul** → Evolução dos casos ao longo do tempo
- **Fundo colorido** → Períodos de El Niño (vermelho), La Niña (azul), Neutro (cinza)
- **Picos na linha** → Surtos epidêmicos
- **Padrões** → Sazonalidade ou tendências

### Gráfico de Barras (El Niño)

**O que ver:**
- **Altura das barras** → Média de casos em cada evento
- **Barras de erro** → Variabilidade (quanto mais longas, mais variação)
- Compare alturas para identificar qual evento tem mais casos

---

## 🎯 Checklist de Interpretação

### Para cada variável climática, pergunte:

- [ ] **Há correlação?** (|ρ| > 0.3)
- [ ] **É significativa?** (p < 0.05)
- [ ] **Qual a direção?** (positiva ou negativa)
- [ ] **Grupos diferem?** (Mann-Whitney p < 0.05)
- [ ] **Diferença é grande?** (compare médias em %)

### Para eventos El Niño:

- [ ] **Qual evento tem mais casos?**
- [ ] **Diferença é significativa?** (Kruskal-Wallis p < 0.05)
- [ ] **Diferença é relevante?** (compare médias)

---

## 💡 Exemplos de Conclusões

### Conclusão FORTE:

```
Temperatura média apresenta correlação FORTE e positiva com casos de dengue 
(ρ = 0.62, p < 0.001). Períodos de alta temperatura têm média de 580 casos, 
enquanto períodos de baixa temperatura têm 310 casos (87% a mais, p = 0.0001). 
A relação é estatisticamente robusta e praticamente relevante.
```

### Conclusão MODERADA:

```
Temperatura mínima mostra correlação MODERADA e positiva (ρ = 0.35, p = 0.02). 
A diferença entre grupos é significativa (p = 0.04), mas a magnitude é menor 
(40% a mais em períodos quentes). Sugere influência, mas não é o principal fator.
```

### Conclusão FRACA/NULA:

```
Precipitação apresenta correlação FRACA (ρ = 0.15, p = 0.25). A diferença 
entre períodos de alta e baixa precipitação não é significativa (p = 0.18). 
Não há evidência clara de relação com casos de dengue neste dataset.
```

---

## ⚠️ Cuidados na Interpretação

### 1. Correlação ≠ Causalidade

❌ **Errado:** "Temperatura alta CAUSA dengue"  
✅ **Correto:** "Temperatura alta está ASSOCIADA a mais casos de dengue"

### 2. Significância ≠ Importância Prática

- p < 0.05 significa que é **estatisticamente significativo**
- Mas diferença de 5 casos pode ser significativa e não ser **clinicamente relevante**

### 3. Considere o Contexto

- Tamanho da amostra
- Período analisado
- Região geográfica
- Fatores não incluídos (urbanização, campanhas, etc.)

### 4. Outliers

- Podem ser **surtos reais** ou **erros de dados**
- Investigar valores extremos antes de descartar

---

## 📚 Glossário Rápido

| Termo | Significado |
|-------|-------------|
| **p-valor** | Probabilidade de resultado ser acaso (p < 0.05 = não é acaso) |
| **ρ (rho)** | Coeficiente de correlação de Spearman (-1 a +1) |
| **Mediana** | Valor do meio (50% acima, 50% abaixo) |
| **IQR** | Intervalo interquartil (Q3 - Q1) |
| **H** | Estatística do teste Kruskal-Wallis |
| **U** | Estatística do teste Mann-Whitney |
| **ns** | Não significativo (p ≥ 0.05) |
| ***** | Significativo (p < 0.05) |
| ****** | Muito significativo (p < 0.01) |
| ******* | Altamente significativo (p < 0.001) |

---

**Dica Final:** Leia sempre o relatório completo (`RELATORIO_ANALISE_ESTATISTICA.md`) para contexto completo!
