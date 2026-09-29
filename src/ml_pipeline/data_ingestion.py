"""
Módulo responsável por construir o painel base a partir do banco de dados (SQLite).
Separa a preocupação de IO e queries SQL da lógica do modelo.
"""
from pathlib import Path
import sqlite3
import pandas as pd

def build_base_panel(root_dir: Path, modo: str = "regional") -> tuple[pd.DataFrame, pd.DataFrame]:
    # TODO: Migrar o código original de motor_lote_modelagem_v2_por_latitude.py para cá
    pass
