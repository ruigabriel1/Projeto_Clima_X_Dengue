from pathlib import Path

# Diretório raiz do projeto (calculado como 2 níveis acima deste arquivo)
# src/config.py -> src -> Projeto_Clima_X_Dengue
BASE_DIR = Path(__file__).resolve().parent.parent

# Diretórios Principais
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DOCS_DIR = BASE_DIR / "docs"

# Subdiretórios de Dados
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_GEODADOS_DIR = DATA_DIR / "geodados"

# Subdiretórios de Output
OUTPUT_CSVS_LATITUDE = OUTPUT_DIR / "csvs_latitude"
OUTPUT_MEDIAS_LATITUDE = OUTPUT_DIR / "medias_latitude"
OUTPUT_MAPAS = OUTPUT_DIR / "mapas"
OUTPUT_MAPAS_LATITUDE = OUTPUT_DIR / "mapas_latitude"
OUTPUT_ANALISE_ESTATISTICA = OUTPUT_DIR / "analise_estatistica"
OUTPUT_PROJECOES_REGIONAIS = OUTPUT_DIR / "projecoes_regionais"
OUTPUT_PROJECOES_SEM_INCREMENTO = OUTPUT_DIR / "projecoes_sem_incremento"

# Configurações de Modelagem e Parâmetros
LAG_MESES = 3
ANO_INICIO_HISTORICO = 2015
ANO_FIM_HISTORICO = 2024
ANO_INICIO_PROJECAO = 2025
ANO_FIM_PROJECAO = 2040

# ---------- Experimento final (docs/PLANO_EXPERIMENTO_FINAL.md) ----------
# 2025 é o holdout: não entra em nenhuma decisão de desenvolvimento.
ANO_HOLDOUT = 2025
ANO_PRIMEIRO_TESTE_DEV = 2018          # folds de desenvolvimento: 2018..2024
HORIZONTES = (1, 2, 3)
DOENCAS_EXPERIMENTO = ("dengue", "chikungunya")   # zika fica fora (dados insuficientes)
OUTPUT_EXPERIMENTO = OUTPUT_DIR / "experimento"
OUTPUT_MODELOS_FINAIS = OUTPUT_DIR / "models" / "final"
DB_PATH = DATA_PROCESSED_DIR / "dengue_analytics.db"

# Garantir que todos os diretórios essenciais existam ao importar as configurações
dirs_to_create = [
    DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_GEODADOS_DIR,
    OUTPUT_CSVS_LATITUDE, OUTPUT_MEDIAS_LATITUDE, OUTPUT_MAPAS,
    OUTPUT_MAPAS_LATITUDE, OUTPUT_ANALISE_ESTATISTICA,
    OUTPUT_PROJECOES_REGIONAIS, OUTPUT_PROJECOES_SEM_INCREMENTO
]

for d in dirs_to_create:
    d.mkdir(parents=True, exist_ok=True)
