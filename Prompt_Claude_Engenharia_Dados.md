# Prompt para Estruturação de Projeto de Engenharia de Dados

**Copie o texto abaixo e cole no Claude Opus para iniciar a sua mentoria e reestruturação do projeto:**

---

**Atue como um Engenheiro de Dados Sênior, Arquiteto de Soluções e Especialista em Machine Learning.** 

Tenho um projeto de pesquisa focado na correlação entre o aumento de temperaturas e chuvas na região Sul do Brasil e a incidência de casos de dengue ao longo de 5 a 6 anos. O objetivo original incluía uma projeção de cenários baseada nas previsões dos fenômenos El Niño e La Niña. 

Preciso de uma análise profunda para transformar este trabalho em um verdadeiro **projeto de portfólio de Engenharia de Dados de nível sênior**, implementando as melhores práticas e ferramentas de grandes empresas de tecnologia (preferencialmente utilizando a stack do **Google Cloud Platform - GCP**, além de modelagem em **SQL** para tratamento de dados estruturados).

### 1. Contexto e Estado Atual (O que eu já fiz):
* **Origem dos Dados:** Extraídos de estações meteorológicas locais dos municípios da região Sul e dados públicos de saúde.
* **Problema Inicial:** Os dados estavam em formatos mistos (Excel e CSV), jogados em várias pastas distintas, alguns com metadados e outros não, totalmente desestruturados. Havia uma diferença gritante no padrão de coleta de dados entre os estados.
* **Minha Solução (Camada Bronze):** Criei scripts em Python para ler, limpar, padronizar e consolidar esses arquivos manualmente (primeiro a temperatura/chuva, depois os incidentes de dengue) organizando por estados e municípios.
* **Visualização:** Criei gráficos e mapas após a consolidação.
* **Machine Learning:** Tentei aplicar um modelo de ML para previsões juntamente com os dados do El Niño/La Niña, mas tenho muitas dúvidas se a abordagem foi correta, se o algoritmo era o ideal para séries temporais e se o resultado teve validade estatística.

### 2. O que eu preciso de você (Entregáveis):

Por favor, me guie passo a passo dividindo sua resposta nos seguintes tópicos:

**A. Análise Crítica do meu processo atual:**
* O que eu fiz de certo na ingestão e consolidação com Python?
* O que eu devo corrigir urgentemente (gargalos e más práticas do processo manual)?

**B. Arquitetura de Dados (Medallion Architecture):**
* Desenhe como deve ser a arquitetura desse projeto dividida nas camadas **Bronze, Silver e Gold**.
* Sugira as ferramentas específicas (ex: Cloud Storage para Data Lake, BigQuery para Data Warehouse, orquestradores como Airflow/Cloud Composer, e dbt para transformação SQL). 
* Crie um código em **Mermaid.js** gerando um diagrama visual (fluxograma) detalhado dessa arquitetura Medallion para que eu possa renderizar e usar em uma postagem no LinkedIn.

**C. Estratégia de Machine Learning e Projeção:**
* Qual é o método/algoritmo real e mais adequado para este tipo de problema (previsão de séries temporais cruzando clima e epidemiologia)?
* Como devo tratar a atualização dos dados do El Niño e La Niña (fontes confiáveis, ingestão contínua)?
* Como integro esse modelo de ML na camada Gold da minha arquitetura para consumir os dados limpos e gerar as previsões?

**D. Plano de Estudo e Execução:**
* Liste um roadmap prático do que devo estudar e aplicar nas próximas semanas para tirar essa nova arquitetura do papel, focando no ecossistema de dados moderno.

---
