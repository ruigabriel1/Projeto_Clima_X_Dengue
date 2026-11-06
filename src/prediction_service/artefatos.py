"""
Artefatos de execução (o que o git não versiona): modelos de produção, snapshot do banco e JSONs do painel.

    python main.py empacotar                    → dist/artefatos_v5.1.zip (com manifesto e SHA-256)
    python -m src.prediction_service.artefatos garantir
        → se os artefatos não existirem, baixa o zip de ARTEFATOS_URL (padrão: GitHub Release),
          confere os hashes do manifesto e extrai. Usado na inicialização do container.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from src.config import BASE_DIR, DB_PATH, OUTPUT_DIR

logger = logging.getLogger(__name__)

VERSAO = "v5.1"
NOME_ZIP = f"artefatos_{VERSAO}.zip"
URL_PADRAO = f"https://github.com/ruigabriel1/Projeto_Clima_X_Dengue/releases/download/modelo-{VERSAO}/{NOME_ZIP}"
MANIFESTO = "manifesto.json"


def _arquivos() -> list[Path]:
    """Caminhos (absolutos) que entram no pacote."""
    modelos = sorted((OUTPUT_DIR / "models" / "final_v5").rglob("*"))
    painel = [OUTPUT_DIR / "dashboard" / f"resultados_{d}.json" for d in ("dengue", "chikungunya")]   # zika fora
    outros = [DB_PATH, *painel, OUTPUT_DIR / "monitoramento" / "previsoes.csv"]
    return [p for p in [*modelos, *outros] if p.is_file()]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def empacotar(destino: Path = BASE_DIR / "dist") -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    zpath = destino / NOME_ZIP
    arquivos = _arquivos()
    meta = json.loads((OUTPUT_DIR / "models" / "final_v5" / "dengue" / "metadata.json").read_text(encoding="utf-8"))
    manifesto = {"versao": VERSAO, "criado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "periodo_treino": meta.get("periodo_treino"), "git_commit": meta.get("git_commit"),
                 "arquivos": {p.relative_to(BASE_DIR).as_posix(): _sha256(p) for p in arquivos}}
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in arquivos:
            z.write(p, p.relative_to(BASE_DIR).as_posix())
        z.writestr(MANIFESTO, json.dumps(manifesto, indent=1, ensure_ascii=False))
    logger.info(f"{zpath} ({zpath.stat().st_size / 1e6:.1f} MB, {len(arquivos)} arquivos)")
    return zpath


def extrair(zpath: Path, raiz: Path = BASE_DIR) -> dict:
    """Extrai o zip conferindo cada arquivo contra o manifesto. Recusa caminhos fora da raiz."""
    raiz = raiz.resolve()
    with zipfile.ZipFile(zpath) as z:
        manifesto = json.loads(z.read(MANIFESTO))
        for nome, esperado in manifesto["arquivos"].items():
            alvo = (raiz / nome).resolve()
            if raiz not in alvo.parents:
                raise ValueError(f"Caminho inválido no pacote: {nome}")
            dados = z.read(nome)
            if hashlib.sha256(dados).hexdigest() != esperado:
                raise ValueError(f"Hash não confere: {nome}")
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_bytes(dados)
    return manifesto


def garantir(url: str | None = None) -> bool:
    """Garante modelos e banco locais. Retorna True se precisou baixar."""
    if DB_PATH.exists() and (OUTPUT_DIR / "models" / "final_v5" / "dengue" / "metadata.json").exists():
        logger.info("Artefatos já presentes.")
        return False
    import requests
    url = url or os.environ.get("ARTEFATOS_URL", URL_PADRAO)
    logger.info(f"Baixando artefatos de {url}")
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / NOME_ZIP
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(zpath, "wb") as f:
                for bloco in r.iter_content(1 << 20):
                    f.write(bloco)
        m = extrair(zpath)
    logger.info(f"Artefatos {m['versao']} extraídos ({len(m['arquivos'])} arquivos, treino {m.get('periodo_treino')}).")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "garantir"
    if cmd == "garantir":
        garantir()
    elif cmd == "empacotar":
        print(empacotar())
    else:
        raise SystemExit(f"Comando desconhecido: {cmd}")
