"""
Sorotipo circulante da dengue por UF e mês (SINAN, microdados do DATASUS) — protocolo v7 (H7d).

Fonte: ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/{FINAIS,PRELIM}/DENGBR{aa}.dbc (Brasil inteiro).
Para cada notificação de residente no PR (41), SC (42) ou RS (43) com SOROTIPO identificado (1 a 4) e não
descartada (CLASSI_FIN ≠ 5), conta o caso no mês dos primeiros sintomas (DT_SIN_PRI).

Tabela `ingestao_sorotipo` (recriada a cada execução; o SINAN revisa os anos recentes):
  UF, ANO, MES, n_testados (casos com sorotipo identificado), n_denv1, n_denv2, n_denv3, n_denv4, ARQUIVOS.

Os .dbc ficam em cache fora do projeto (variável PRODIGIA_SINAN_CACHE; padrão %LOCALAPPDATA%/prodigia/sinan,
para não sincronizar ~1 GB no OneDrive). O .dbf descompactado é apagado depois de lido.

Dependência só do ambiente de análise (não da API): pyreaddbc (descompacta o .dbc).

Uso:
  python main.py sorotipo                    # 2010 até o ano corrente
  python main.py sorotipo --anos 2017 2018
"""
from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import struct
from datetime import date
from ftplib import FTP
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DB_PATH

logger = logging.getLogger(__name__)

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIRS = ("/dissemin/publicos/SINAN/DADOS/FINAIS", "/dissemin/publicos/SINAN/DADOS/PRELIM")
UFS_SUL = {b"41": "PR", b"42": "SC", b"43": "RS"}
CAMPOS = ["SG_UF", "DT_SIN_PRI", "SOROTIPO", "CLASSI_FIN"]
TABELA = "ingestao_sorotipo"
ANO_INICIO = 2010


def dir_cache() -> Path:
    base = os.environ.get("PRODIGIA_SINAN_CACHE") or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "prodigia" / "sinan"
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ------------------------------------------------------------------ download
def baixar(ano: int, destino: Path | None = None) -> Path | None:
    """Baixa DENGBR{aa}.dbc (FINAIS, senão PRELIM). Reaproveita o cache se o tamanho for o mesmo do FTP."""
    destino = destino or dir_cache()
    nome = f"DENGBR{ano % 100:02d}.dbc"
    alvo = destino / nome
    with FTP(FTP_HOST, timeout=300) as ftp:
        ftp.login()
        for d in FTP_DIRS:
            try:
                ftp.cwd(d)
                tam = ftp.size(nome)
            except Exception:
                continue
            if alvo.exists() and alvo.stat().st_size == tam:
                logger.info(f"[SINAN] {nome}: em cache ({tam / 1e6:.0f} MB, {d.rsplit('/', 1)[-1]})")
                return alvo
            logger.info(f"[SINAN] baixando {nome} ({tam / 1e6:.0f} MB) de {d}")
            tmp = alvo.with_suffix(".part")
            with open(tmp, "wb") as f:
                ftp.retrbinary(f"RETR {nome}", f.write)
            tmp.replace(alvo)
            return alvo
    logger.warning(f"[SINAN] {nome} não encontrado no FTP")
    return None


# ------------------------------------------------------------------ leitura
def ler_campos_dbf(path: Path, campos: list[str]) -> dict[str, np.ndarray]:
    """Lê só os campos pedidos de um .dbf (registros de tamanho fixo) como arrays de bytes, via memmap."""
    with open(path, "rb") as f:
        cab = f.read(32)
        n, tam_cab, tam_reg = struct.unpack("<IHH", cab[4:12])
        desc = f.read(tam_cab - 32)
    pos, desloc = {}, 1                       # byte 0 de cada registro = marca de excluído
    for i in range(0, len(desc), 32):
        if desc[i] == 0x0D:
            break
        nome = desc[i:i + 11].split(b"\0")[0].decode("latin-1")
        tam = desc[i + 16]
        pos[nome] = (desloc, tam)
        desloc += tam
    faltam = [c for c in campos if c not in pos]
    if faltam:
        raise KeyError(f"{path.name}: campos ausentes {faltam}")
    mm = np.memmap(path, dtype=np.uint8, mode="r", offset=tam_cab, shape=(n, tam_reg))
    vivos = mm[:, 0] != ord("*")
    out = {}
    for c in campos:
        o, t = pos[c]
        out[c] = np.ascontiguousarray(mm[:, o:o + t]).view(f"S{t}").ravel()[vivos]
    del mm
    return out


def agregar(campos: dict[str, np.ndarray]) -> pd.DataFrame:
    """Casos com sorotipo identificado (1–4), não descartados, de residentes no Sul: UF, ANO, MES, sorotipo."""
    uf = np.char.strip(campos["SG_UF"])
    soro = np.char.strip(campos["SOROTIPO"])
    classi = np.char.strip(campos["CLASSI_FIN"])
    m = np.isin(uf, list(UFS_SUL)) & np.isin(soro, [b"1", b"2", b"3", b"4"]) & (classi != b"5")
    if not m.any():
        return pd.DataFrame(columns=["UF", "ANO", "MES", "sorotipo"])
    dt = pd.to_datetime(pd.Series(campos["DT_SIN_PRI"][m]).str.decode("latin-1"), format="%Y%m%d", errors="coerce")
    df = pd.DataFrame({"UF": [UFS_SUL[u] for u in uf[m]], "ANO": dt.dt.year, "MES": dt.dt.month,
                       "sorotipo": soro[m].astype(int)}).dropna(subset=["ANO"])
    return df.astype({"ANO": int, "MES": int})


def contar(casos: pd.DataFrame) -> pd.DataFrame:
    """Contagem por UF × mês: n_testados (com sorotipo identificado) e n_denv1..4."""
    cols = ["UF", "ANO", "MES", "n_testados", "n_denv1", "n_denv2", "n_denv3", "n_denv4"]
    if casos.empty:
        return pd.DataFrame(columns=cols)
    t = (casos.assign(n=1).pivot_table(index=["UF", "ANO", "MES"], columns="sorotipo", values="n",
                                       aggfunc="sum", fill_value=0)
         .reindex(columns=[1, 2, 3, 4], fill_value=0))
    t.columns = [f"n_denv{s}" for s in t.columns]
    t.insert(0, "n_testados", t.sum(axis=1))
    return t.reset_index()[cols]


def processar_ano(ano: int, destino: Path | None = None) -> pd.DataFrame:
    import pyreaddbc
    dbc = baixar(ano, destino)
    if dbc is None:
        return pd.DataFrame()
    dbf = dbc.with_suffix(".dbf")
    pyreaddbc.dbc2dbf(str(dbc), str(dbf))
    try:
        casos = agregar(ler_campos_dbf(dbf, CAMPOS))
    finally:
        dbf.unlink(missing_ok=True)
    logger.info(f"[SINAN] {dbc.name}: {len(casos)} casos com sorotipo no Sul")
    return casos.assign(ARQUIVO=dbc.name)


def executar(anos: list[int] | None = None, db_path=DB_PATH) -> pd.DataFrame:
    anos = anos or list(range(ANO_INICIO, date.today().year + 1))
    partes = [p for p in (processar_ano(a) for a in anos) if not p.empty]
    casos = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=["ARQUIVO"])
    arquivos = ",".join(sorted(casos["ARQUIVO"].unique()))
    tab = contar(casos.drop(columns="ARQUIVO"))
    tab = tab[tab["ANO"] >= ANO_INICIO].assign(ARQUIVOS=arquivos)   # sintomas antes de 2010 ficam fora
    with sqlite3.connect(db_path) as conn:
        tab.to_sql(TABELA, conn, if_exists="replace", index=False)
    logger.info(f"[SINAN] {TABELA}: {len(tab)} linhas UF×mês, {int(tab['n_testados'].sum())} casos com sorotipo")
    return tab


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sorotipo da dengue por UF e mês (SINAN)")
    ap.add_argument("--anos", type=int, nargs="*", default=None)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", force=True)
    executar(args.anos)


if __name__ == "__main__":
    main()
