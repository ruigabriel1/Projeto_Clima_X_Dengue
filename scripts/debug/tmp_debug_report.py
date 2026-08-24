import traceback
import pandas as pd
from src.processamento.motor_lote_modelagem_v2_por_latitude import (
    ROOT_DATA_DIR,
    build_base_panel,
    train_local_intercept,
    calibrate_region,
    project_city,
    save_pdf_reports,
    CoverageInfo,
)

panel, lookup = build_base_panel(ROOT_DATA_DIR)
codes = panel['code'].drop_duplicates().head(30).tolist()
psub = panel[panel['code'].isin(codes)].copy()

local_intercepts = {}
for code, g in psub.groupby('code'):
    local_intercepts[code] = train_local_intercept(g)

calib = calibrate_region(psub, local_intercepts)
all_proj = []
for code, g in psub.groupby('code'):
    p = project_city(g, local_intercepts.get(code, 0.0), calib)
    if not p.empty:
        all_proj.append(p)

projections = pd.concat(all_proj, ignore_index=True)
coverage = CoverageInfo(municipios_sul_total=1191, municipios_com_dados=int(psub['code'].nunique()))

try:
    save_pdf_reports(ROOT_DATA_DIR, psub, projections, calib, coverage)
    print('OK')
except Exception as exc:
    print('ERR:', exc)
    traceback.print_exc()
