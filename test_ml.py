"""Teste rápido do novo pipeline ML (RandomForest + LOYO)."""
import sys; sys.path.insert(0, ".")
from src.processamento.motor_lote_modelagem_v2_por_latitude import build_base_panel, run_full_ml
from pathlib import Path

root = Path(".")
panel, lookup = build_base_panel(root, modo="rapido")
print(f"Painel: {len(panel)} registros, {panel['code'].nunique()} cidade(s)")
print(f"Anos: {panel['year'].min()}-{panel['year'].max()}")

result = run_full_ml(root, panel)
print()
print("=== METRICAS LOYO ===")
for m in result["metricas"]:
    print(f"  {m['split']}: R2={m['r2']:.3f}  MAE={m['mae']:.1f}")
print()
print("=== TOP-5 FEATURES ===")
for name, imp in result["feature_importance"][:5]:
    print(f"  {name}: {imp:.3f}")
print()

# Verificar projeções
import pandas as pd
proj = pd.read_csv("output/projecoes_regionais/ml_completo/projecao_ml_completa_municipios_mensal.csv")
proj_245 = proj[(proj["scenario"] == "ssp245") & (proj["year"] >= 2026) & (proj["year"] <= 2030)]
print("=== PROJECAO SSP245 (2026-2030) ===")
for year in sorted(proj_245["year"].unique()):
    total = proj_245[proj_245["year"] == year]["pred_cases_ml"].sum()
    pico = proj_245[proj_245["year"] == year]["pred_cases_ml"].max()
    print(f"  {year}: Total anual={total:.0f}  Pico mensal={pico:.0f}")
