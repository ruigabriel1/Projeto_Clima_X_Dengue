import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from app.ml_runner import treinar

print("Reexecutando o pipeline para exportar os gráficos Plotly...")
treinar(modo="rapido")
print("Pronto! Gráficos salvos em graficos_artigo/")
