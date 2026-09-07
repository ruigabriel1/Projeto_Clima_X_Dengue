# Arquitetura de Dados — Pipeline Medallion (Evolução API/SQLite)

Este documento descreve a arquitetura de dados atual do projeto, baseada em consumo robusto de APIs, cache geoespacial e orquestração via banco de dados local (SQLite). O modelo segue o padrão **Medallion Architecture** adaptado para execução ágil.

## Visão Geral do Pipeline (Atual)

```mermaid
flowchart TD
    subgraph Fontes["Fontes de Dados (APIs e Arquivos)"]
        A1[API InfoDengue\n(Dengue, Zika, Chik)]
        A2[API Open-Meteo\n(Clima Diário)]
        A3[Geopackage\n(cache_municipios_sul)]
        A4[NOAA\n(ENSO CSV)]
    end

    subgraph Bronze["Camada Bronze (Ingestão & Banco de Dados)"]
        R1[ingestor_api_sul.py]
        DB[(dengue_analytics.db\nSQLite)]
        
        R1 -- Baixa --> A1 & A2 & A3
        R1 -- Salva --> DB
        
        T1[Tabela: ingestao_saude]
        T2[Tabela: ingestao_clima]
        
        DB --- T1 & T2
    end

    subgraph Silver["Camada Silver (Merge & Transformação)"]
        M1[motor_lote_modelagem_v2_por_latitude.py]
        M1 -- Lê --> DB
        M1 -- Lê --> A4
        M1 -- Agrega por Mês/Ano --> P1[Painel Base na Memória]
    end

    subgraph Gold["Camada Gold (Machine Learning)"]
        P1 --> ML1[Local Intercepts\n(Regressão por Município)]
        ML1 --> ML2[XGBoost\n(8 Modelos por Latitude)]
        ML2 --> OUT[Previsões 2025]
    end

    Fontes --> Bronze --> Silver --> Gold
```

---

## 1. Camada Bronze — Ingestão via API e SQLite

**Princípio:** Extrair os dados diretamente das fontes oficiais, lidando com paginação, *rate limits* e conectividade, gravando-os em tabelas segregadas num banco relacional leve.

*   **Motor de Ingestão:** `src/processamento/ingestor_api_sul.py`
    *   **Alvo `infodengue`:** Coleta dados epidemiológicos por semana e agrega por mês. Identifica os códigos IBGE de 7 dígitos.
    *   **Alvo `openmeteo`:** Coleta 11 anos de clima diário via API Archive. Agrupa dados brutos em médias/somas mensais. Possui "Freio de Mão" (20s delay) para burlar bloqueios (Burst Limit).
*   **Armazenamento:** Banco de Dados SQLite (`data/processed/dengue_analytics.db`). 
    *   O banco garante resiliência: se a internet cair ou o rate limit estourar, o robô sabe exatamente de qual cidade retomar na próxima execução, sem perder o progresso.

## 2. Camada Silver — Merge & Transformação Mensal

**Princípio:** Combinar as tabelas separadas do banco de dados e os arquivos externos (El Niño) num painel unificado pronto para a IA.

*   **Transformação:** Feita diretamente pela função `build_base_panel()` dentro do script do motor de ML.
*   **Regras Aplicadas:**
    *   Cruzamento de Municípios (`CODIGO_MUNICIPIO`) e Tempo (`ANO`, `MES`).
    *   Cruzamento das anomalias oceânicas (ENSO - El Niño/La Niña) através do CSV local (`data/raw/elnino_lanina_2015-2024.csv`).
    *   Conversão de dados geográficos e numéricos, mitigação de `NaNs`.

## 3. Camada Gold — Feature Store e Machine Learning

**Princípio:** Treinar o modelo preditivo considerando características imunológicas, temporais e espaciais.

*   **Engenharia de Features:** Variáveis derivadas criadas *on the fly*, como lags temporais (`temp_lag3`, `casos_lag1`, `casos_lag12`) que representam a memória imunológica e velocidade de contágio.
*   **Modelagem Dupla (Híbrida):**
    1.  **Imunidade Local:** O `train_local_intercept` treina Regressões Lineares individuais para cada um dos 1.191 municípios, capturando a vulnerabilidade endêmica de cada cidade.
    2.  **Macromodelo Climático:** O XGBoost é treinado dividindo o mapa da região Sul em 8 faixas de latitude, generalizando o impacto climático na proliferação do vetor.

---

## 4. Evolução Histórica (O Nosso Legado)

Este projeto passou por uma enorme evolução arquitetural para chegar ao estágio atual de autonomia e resiliência. Deixamos este histórico documentado para demonstrar o avanço de maturidade de engenharia de dados.

### A Arquitetura Antiga (v1 - Baseada em CSVs)
No início, a pipeline dependia puramente da ingestão manual e processamento de arquivos CSV gigantescos:
*   Os dados vinham do **SINAN** (`dengue_MENSAL.csv`) num formato "wide" doloroso de manipular (colunas espalhadas por mês).
*   O clima vinha de extrações do **INMET** (`Temp_media_MENSAL.csv`, `precipitacao_mensal_rev.csv`, etc.).
*   A limpeza era feita por scripts intermediários como `consolidar_dados.py` e separada fisicamente em 48 arquivos CSV por latitude (`output/csvs_latitude/`).

### Por que Evoluímos para a v2 (APIs + Banco)?
A arquitetura de CSVs não era sustentável para escalar. As bases do SINAN demoravam para atualizar e as estações do INMET tinham muitas falhas de medição (-9999). 
Nós criamos o **Robô de Ingestão (ingestor_api_sul.py)** que consome diretamente as APIs (InfoDengue da Fiocruz e Open-Meteo). Ao gravar tudo em um **Banco SQLite** com tabelas desacopladas (`ingestao_saude` e `ingestao_clima`), resolvemos o problema de paralelismo, permitindo que a coleta de saúde e clima acontecesse simultaneamente sem corromper arquivos ou dar conflito, e tornando todo o sistema imune a quedas.
