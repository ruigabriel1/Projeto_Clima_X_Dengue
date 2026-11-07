"""Leitura do SINAN (DBF) e contagem de sorotipos por UF × mês (protocolo v7, H7d). Dados sintéticos."""
import struct

import numpy as np

from src.processamento import ingestor_sinan_sorotipo as s


def _dbf(path, campos, linhas, excluidas=()):
    """Escreve um .dbf mínimo (campos texto/data de tamanho fixo)."""
    tam_reg = 1 + sum(t for _, _, t in campos)
    tam_cab = 32 + 32 * len(campos) + 1
    cab = struct.pack("<BBBBIHH20x", 3, 126, 1, 1, len(linhas), tam_cab, tam_reg)
    desc = b"".join(n.encode().ljust(11, b"\0") + tp.encode() + b"\0" * 4 + bytes([t]) + b"\0" * 15
                    for n, tp, t in campos)
    regs = b""
    for i, ln in enumerate(linhas):
        regs += (b"*" if i in excluidas else b" ") + b"".join(
            str(v).encode().ljust(t)[:t] for v, (_, _, t) in zip(ln, campos))
    path.write_bytes(cab + desc + b"\r" + regs + b"\x1a")


CAMPOS = [("TP_NOT", "C", 1), ("SG_UF", "C", 2), ("DT_SIN_PRI", "D", 8), ("SOROTIPO", "C", 1), ("CLASSI_FIN", "C", 2)]


def test_le_campos_e_conta_por_uf_mes(tmp_path):
    linhas = [
        ("2", "41", "20240115", "1", "10"),   # PR jan DENV-1
        ("2", "41", "20240120", "2", "10"),   # PR jan DENV-2
        ("2", "41", "20240210", "2", "11"),   # PR fev DENV-2
        ("2", "43", "20240301", "3", ""),     # RS mar DENV-3 (sem classificação ainda: conta)
        ("2", "42", "20240301", "4", "5"),    # SC descartado: não conta
        ("2", "35", "20240301", "1", "10"),   # SP: fora do Sul
        ("2", "41", "20240301", "", "10"),    # sem sorotipo: não conta
        ("2", "41", "20240301", "1", "10"),   # excluído no arquivo
    ]
    p = tmp_path / "x.dbf"
    _dbf(p, CAMPOS, linhas, excluidas={7})
    c = s.ler_campos_dbf(p, s.CAMPOS)
    assert len(c["SG_UF"]) == 7
    t = s.contar(s.agregar(c)).set_index(["UF", "MES"])
    assert t.loc[("PR", 1), "n_testados"] == 2 and t.loc[("PR", 1), "n_denv1"] == 1
    assert t.loc[("PR", 2), "n_denv2"] == 1 and t.loc[("RS", 3), "n_denv3"] == 1
    assert ("SC", 3) not in t.index and len(t) == 3
    assert (t["n_testados"] == t[["n_denv1", "n_denv2", "n_denv3", "n_denv4"]].sum(axis=1)).all()


def test_campo_ausente_e_vazio(tmp_path):
    p = tmp_path / "y.dbf"
    _dbf(p, CAMPOS[:3], [("2", "41", "20240115")])
    try:
        s.ler_campos_dbf(p, s.CAMPOS)
        raise AssertionError("deveria falhar")
    except KeyError:
        pass
    assert s.contar(s.agregar({k: np.array([], dtype="S2") for k in s.CAMPOS})).empty
