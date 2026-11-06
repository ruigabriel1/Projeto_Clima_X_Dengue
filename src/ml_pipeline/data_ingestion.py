"""
Módulo responsável por construir o painel base a partir do banco de dados (SQLite).
Separa a preocupação de IO e queries SQL da lógica do modelo.

v3 — Corrige ENSO (lê da tabela real), junta população, remove colunas
     de vazamento (CASOS_EST_*), e aplica validação de qualidade.
"""
import sqlite3
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Colunas que jamais devem entrar no painel (duplicatas exatas dos alvos)
_COLS_PROIBIDAS = {
    "CASOS_EST_DENGUE",       # 100% idêntica a CASOS_DENGUE
    "CASOS_EST_CHIKUNGUNYA",  # idêntica a CASOS_CHIKUNGUNYA
    "CASOS_EST_ZIKA",         # idêntica a CASOS_ZIKA
}

# Doenças disponíveis no banco: nome -> coluna-alvo interna
DOENCAS = {
    "dengue": "dengue_cases",
    "chikungunya": "chik_cases",
    "zika": "zika_cases",  # atenção: só existe até início de 2024
}


def build_base_panel(root_dir: Path, modo: str = "regional") -> pd.DataFrame:
    """
    Lê as tabelas desacopladas do SQLite e devolve um DataFrame unificado,
    pronto para a engenharia de features.

    Tabelas lidas: ingestao_saude, ingestao_clima, ingestao_enso, ingestao_populacao.
    """
    db_path = root_dir / "data" / "processed" / "dengue_analytics.db"

    logger.info("build_base_panel -> Lendo tabelas desacopladas do SQLite (Saúde + Clima + ENSO + População)")

    if not db_path.exists():
        raise FileNotFoundError(f"Banco da API não encontrado em {db_path}. Execute os robôs de ingestão.")

    conn = sqlite3.connect(db_path)

    # ---------- 1. Saúde (InfoDengue) ----------
    try:
        df_saude = pd.read_sql_query("SELECT * FROM ingestao_saude", conn)
        logger.info(f"Tabela de Saúde lida: {len(df_saude)} registros.")
    except Exception:
        df_saude = pd.DataFrame()

    # ---------- 2. Clima (Open-Meteo) ----------
    try:
        df_clima = pd.read_sql_query("SELECT * FROM ingestao_clima", conn)
        logger.info(f"Tabela de Clima lida: {len(df_clima)} registros.")
    except Exception:
        df_clima = pd.DataFrame()

    # ---------- 3. ENSO / ONI (NOAA) ----------
    try:
        df_enso = pd.read_sql_query("SELECT ANO, MES, ENSO_ONI FROM ingestao_enso", conn)
        logger.info(f"Tabela ENSO lida: {len(df_enso)} registros (ONI range {df_enso['ENSO_ONI'].min():.2f} a {df_enso['ENSO_ONI'].max():.2f}).")
    except Exception:
        df_enso = pd.DataFrame()
        logger.warning("Tabela ingestao_enso não encontrada. ENSO ficará zerado.")

    # ---------- 4. População (IBGE SIDRA) ----------
    try:
        df_pop = pd.read_sql_query("SELECT * FROM ingestao_populacao", conn)
        logger.info(f"Tabela População lida: {len(df_pop)} registros, {df_pop['CODIGO_MUNICIPIO'].nunique()} municípios.")
    except Exception:
        df_pop = pd.DataFrame()
        logger.warning("Tabela ingestao_populacao não encontrada. Sem dados de população.")

    conn.close()

    if df_saude.empty and df_clima.empty:
        raise ValueError("Nenhuma tabela tem dados. Rode o ingestor primeiro.")

    # ---------- Merge Saúde + Clima ----------
    if not df_saude.empty and not df_clima.empty:
        # Remover colunas redundantes do clima (já presentes na saúde). INGERIDO_EM fica só o da saúde:
        # é ele que define se o mês de casos já consolidou (com os dois, o merge gerava _x/_y e o filtro
        # de meses não consolidados deixava de funcionar).
        cols_to_drop = ["LATITUDE", "LONGITUDE", "FAIXA_LATITUDE", "NOME_MUNICIPIO", "INGERIDO_EM"]
        df_clima = df_clima.drop(columns=[c for c in cols_to_drop if c in df_clima.columns])
        panel = pd.merge(df_saude, df_clima, on=["CODIGO_MUNICIPIO", "ANO", "MES"], how="inner")
    else:
        panel = df_saude if not df_saude.empty else df_clima

    # ---------- Remover colunas proibidas (vazamento) ----------
    cols_para_remover = [c for c in _COLS_PROIBIDAS if c in panel.columns]
    if cols_para_remover:
        panel = panel.drop(columns=cols_para_remover)
        logger.info(f"Removidas colunas de vazamento: {cols_para_remover}")

    # ---------- Merge ENSO ----------
    if not df_enso.empty:
        panel = panel.merge(df_enso, on=["ANO", "MES"], how="left")
        n_nulos = panel["ENSO_ONI"].isna().sum()
        if n_nulos > 0:
            panel["ENSO_ONI"] = panel["ENSO_ONI"].fillna(0.0)
            logger.warning(f"ENSO: {n_nulos} linhas sem correspondência, preenchidas com 0.0")
    else:
        panel["ENSO_ONI"] = 0.0

    # ---------- Merge População ----------
    if not df_pop.empty:
        # Garantir tipo compatível
        df_pop["CODIGO_MUNICIPIO"] = df_pop["CODIGO_MUNICIPIO"].astype(str).str[:6].astype(int)
        df_pop["ANO"] = df_pop["ANO"].astype(int)
        df_pop["POPULACAO"] = df_pop["POPULACAO"].astype(int)

        # Interpolar anos faltantes (2022-2023 do Censo) por cidade
        all_anos = sorted(panel["ANO"].unique())
        interp_rows = []
        for code, grp in df_pop.groupby("CODIGO_MUNICIPIO"):
            grp = grp.set_index("ANO").reindex(all_anos)
            grp["CODIGO_MUNICIPIO"] = code
            grp["POPULACAO"] = grp["POPULACAO"].interpolate(method="linear").ffill().bfill()
            grp = grp.reset_index().rename(columns={"index": "ANO"})
            interp_rows.append(grp)
        if interp_rows:
            df_pop_full = pd.concat(interp_rows, ignore_index=True)
            df_pop_full["POPULACAO"] = df_pop_full["POPULACAO"].round().astype(int)
            panel = panel.merge(
                df_pop_full[["CODIGO_MUNICIPIO", "ANO", "POPULACAO"]],
                on=["CODIGO_MUNICIPIO", "ANO"],
                how="left",
            )
            n_sem_pop = panel["POPULACAO"].isna().sum()
            if n_sem_pop > 0:
                logger.warning(f"População: {n_sem_pop} linhas sem dados, serão preenchidas com mediana da faixa.")
                # Fallback: mediana da faixa de latitude × ano
                if "FAIXA_LATITUDE" in panel.columns:
                    panel["POPULACAO"] = panel.groupby(["FAIXA_LATITUDE", "ANO"])["POPULACAO"].transform(
                        lambda s: s.fillna(s.median())
                    )
                # Último fallback: mediana global por ano
                panel["POPULACAO"] = panel.groupby("ANO")["POPULACAO"].transform(
                    lambda s: s.fillna(s.median())
                )
        else:
            panel["POPULACAO"] = np.nan
    else:
        panel["POPULACAO"] = np.nan

    # ---------- Limpeza de umidade ----------
    for col_umid in ["umidmed", "umidmax", "umidmin"]:
        if col_umid in panel.columns:
            # Cortar valores fisicamente impossíveis
            panel[col_umid] = panel[col_umid].clip(upper=100.0)
            # Imputar nulos pela climatologia da cidade × mês
            panel[col_umid] = panel.groupby(["CODIGO_MUNICIPIO", "MES"])[col_umid].transform(
                lambda s: s.fillna(s.median())
            )
            # Fallback: mediana do mês
            panel[col_umid] = panel.groupby("MES")[col_umid].transform(
                lambda s: s.fillna(s.median())
            )

    # ---------- Renomear para padrão interno ----------
    rename_map = {
        "CODIGO_MUNICIPIO": "code",
        "NOME_MUNICIPIO": "city_name",
        "ANO": "year",
        "MES": "month",
        "LATITUDE": "latitude",
        "LONGITUDE": "longitude",
        "FAIXA_LATITUDE": "lat_faixa_id",
        "CASOS_DENGUE": "dengue_cases",
        "CASOS_CHIKUNGUNYA": "chik_cases",
        "CASOS_ZIKA": "zika_cases",
        "ENSO_ONI": "enso",
        "POPULACAO": "populacao",
    }
    panel = panel.rename(columns={k: v for k, v in rename_map.items() if k in panel.columns})

    if "code" in panel.columns:
        panel["code"] = panel["code"].astype(str).str.extract(r"(\d{6})", expand=False)

    # ---------- log(população) e incidência ----------
    if "populacao" in panel.columns:
        panel["log_pop"] = np.log1p(panel["populacao"].fillna(0))

    return panel


def validate_panel(panel: pd.DataFrame) -> dict:
    """
    Valida o painel base e retorna um dicionário-relatório de qualidade.
    Levanta ValueError se alguma invariante crítica falhar.
    """
    report = {}

    # 1. Chaves únicas
    dup = panel.duplicated(subset=["code", "year", "month"])
    n_dup = dup.sum()
    report["duplicatas"] = int(n_dup)
    if n_dup > 0:
        logger.error(f"VALIDAÇÃO: {n_dup} linhas duplicadas (code, year, month)!")

    # 2. Cobertura temporal
    anos = sorted(panel["year"].unique())
    n_cidades = panel["code"].nunique()
    meses_esperados = len(anos) * 12
    cobertura = panel.groupby("code").size()
    report["cidades"] = int(n_cidades)
    report["anos"] = anos
    report["meses_por_cidade_mediana"] = int(cobertura.median())
    report["cidades_incompletas"] = int((cobertura < meses_esperados).sum())

    # 3. Faixas físicas plausíveis
    checks = {
        "temp_media": (-10, 45),
        "precipitacao": (0, 1000),
        "umidmed": (0, 100.01),
        "enso": (-3, 3.5),
        "dengue_cases": (0, 100000),
    }
    fora = {}
    for col, (lo, hi) in checks.items():
        if col in panel.columns:
            n_fora = ((panel[col] < lo) | (panel[col] > hi)).sum()
            if n_fora > 0:
                fora[col] = int(n_fora)
    report["valores_fora_faixa"] = fora

    # 4. Nulos residuais
    nulos = {c: int(panel[c].isna().sum()) for c in panel.columns if panel[c].isna().any()}
    report["nulos_residuais"] = nulos

    # 5. ENSO com variância
    if "enso" in panel.columns:
        enso_var = panel["enso"].var()
        report["enso_variancia"] = round(float(enso_var), 4)
        if enso_var < 0.001:
            logger.error("VALIDAÇÃO: ENSO sem variância! Provavelmente não foi carregado corretamente.")

    # 6. Alvos (uma entrada por doença)
    report["doencas"] = {}
    for nome, col in DOENCAS.items():
        if col not in panel.columns:
            continue
        s = panel[col]
        anos_validos = sorted(panel.loc[s.notna(), "year"].unique().tolist())
        report["doencas"][nome] = {
            "total_casos": float(s.sum()),
            "zeros_pct": round(float((s == 0).mean() * 100), 1),
            "nulos_pct": round(float(s.isna().mean() * 100), 1),
            "p99": float(s.quantile(0.99)),
            "max": float(s.max()),
            "cidades_com_caso": int(panel.loc[s > 0, "code"].nunique()),
            "anos_com_dado": [int(a) for a in anos_validos],
        }

    # 7. Vazamento
    vazamento = [c for c in _COLS_PROIBIDAS if c in panel.columns]
    report["colunas_vazamento_presentes"] = vazamento
    if vazamento:
        raise ValueError(f"VALIDAÇÃO FALHOU: colunas de vazamento presentes: {vazamento}")

    logger.info(f"Validação do painel: {report}")
    return report
