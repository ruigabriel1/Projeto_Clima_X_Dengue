"""Compara o modelo v3 contra baseline de persistência (y_hat = lag1) e lista FI."""
import json, sys
from pathlib import Path
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ml_pipeline.data_ingestion import build_base_panel
from src.ml_pipeline.feature_engineering import build_ml_features

log = json.loads((ROOT / "output" / "ml_run_log_v3.json").read_text(encoding="utf-8"))
df = build_ml_features(build_base_panel(ROOT))
print("pop nula:", df["populacao"].isna().sum(), "| pop min/max:", df["populacao"].min(), df["populacao"].max())
print("\nANO | R2 modelo | R2 persist | MAE modelo | MAE persist")
for m in log["metrics_por_ano"]:
    t = df[df["year"] == m["year"]]
    r2b = r2_score(t["dengue_cases"], t["dengue_lag1"])
    maeb = mean_absolute_error(t["dengue_cases"], t["dengue_lag1"])
    print(f"{m['year']} | {m['r2']:.3f} | {r2b:.3f} | {m['mae']:.1f} | {maeb:.1f}")
print("\nTop 15 FI:")
for f, v in log["feature_importance"][:15]:
    print(f"  {f:22s} {float(v):.4f}")
