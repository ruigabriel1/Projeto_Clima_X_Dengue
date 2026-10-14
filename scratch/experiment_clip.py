"""Experimento: efeito do clipping e das features do mês corrente no R² v3."""
import logging, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)
from src.ml_pipeline.data_ingestion import build_base_panel
from src.ml_pipeline.feature_engineering import build_ml_features, get_feature_columns
from src.ml_pipeline.model_training import train_model

df = build_ml_features(build_base_panel(ROOT))
feats = get_feature_columns(df)
# Features "forecast puro": remove clima/receptividade do mês corrente (desconhecidos 1 mês antes)
corrente = {"umidmed", "umidmax", "umidmin", "temp_media", "temp_maxima", "temp_minima",
            "precipitacao", "vel_vento_max", "rajada_vento_max", "temp_solo", "enso",
            "amplitude_termica", "receptivo_num"}
feats_fc = [f for f in feats if f not in corrente]

for nome, fs, clip in [("A clip99 + todas", feats, 99.0),
                       ("B sem clip + todas", feats, None),
                       ("C sem clip + forecast puro", feats_fc, None)]:
    _, m, _ = train_model(df, fs, clip_percentile=clip)
    r2 = [x["r2"] for x in m]; mae = [x["mae"] for x in m]
    print(f"{nome:28s} R2 medio={np.mean(r2):.3f}  MAE medio={np.mean(mae):.1f}  por ano={r2}", flush=True)
