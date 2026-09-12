# Comandos Úteis do Projeto Clima x Dengue

# 1. Configurar o ambiente (Obrigatório antes de rodar os scripts)
# Ativa o ambiente virtual e define o PYTHONPATH para a raiz do projeto
.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."

# 2. Rodar robôs de ingestão no banco de dados SQLite
# Baixa dados de Clima (Open-Meteo) com freio anti-rate limit
python src/processamento/ingestor_api_sul.py --alvo openmeteo

# Baixa dados de Saúde (InfoDengue)
python src/processamento/ingestor_api_sul.py --alvo infodengue

# Baixa dados de anomalias do El Niño/La Niña (NOAA)
python src/processamento/ingestor_api_sul.py --alvo noaa

# 3. Rodar coleta isolada de São Carlos (SC)
# Baixa 132 meses de clima e saúde e joga no SQLite
python src/processamento/coletar_sao_carlos.py

# 4. Checar o banco de dados via terminal (One-liner rápido)
# Consulta quantos registros e cidades existem na tabela de clima
python -c "import sqlite3, pandas as pd; conn = sqlite3.connect('data/processed/dengue_analytics.db'); print(pd.read_sql_query('SELECT COUNT(*) as registros, COUNT(DISTINCT CODIGO_MUNICIPIO) as cidades FROM ingestao_clima', conn));"

# 5. Acompanhar logs em tempo real das tarefas de segundo plano (Antigravity IDE)
# Lê o arquivo de log mais recente gerado pelo agente na sessão atual
cd C:\Users\ruiga\.gemini\antigravity-ide\brain\8e725034-268d-48cb-b72b-91b1ca6b5a53\.system_generated\tasks\
Get-Content (Get-ChildItem -Filter *.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1) -Wait

# 6. Rodar o Motor de Machine Learning (Após ter os dados no banco)
python src/processamento/motor_lote_modelagem_v2_por_latitude.py

# 7. Atualizar a topologia de arquivos (Graphify)
# Mapeia novamente os arquivos do projeto após excluir ou adicionar scripts
.venv\Scripts\graphify.exe update .
