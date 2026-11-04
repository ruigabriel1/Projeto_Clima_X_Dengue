"""Caminhos e constantes do projeto. Nenhum efeito colateral além de criar os diretórios base."""
from pathlib import Path

# src/config.py -> src -> raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DOCS_DIR = BASE_DIR / "docs"

DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_GEODADOS_DIR = DATA_DIR / "geodados"
DB_PATH = DATA_PROCESSED_DIR / "dengue_analytics.db"

# ---------- Experimento final (docs/PLANO_EXPERIMENTO_FINAL.md) ----------
# 2025 foi o holdout da v4 (já usado). O holdout da v5 é jan–ago/2026 (docs/PROTOCOLO_V5.md).
ANO_HOLDOUT = 2025
ANO_PRIMEIRO_TESTE_DEV = 2018          # folds de desenvolvimento: 2018..2024
HORIZONTES = (1, 2, 3)
DOENCAS_EXPERIMENTO = ("dengue", "chikungunya")   # zika fica fora (dados insuficientes)
OUTPUT_EXPERIMENTO = OUTPUT_DIR / "experimento"
OUTPUT_MODELOS_FINAIS = OUTPUT_DIR / "models" / "final"

for _d in (DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_GEODADOS_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)
