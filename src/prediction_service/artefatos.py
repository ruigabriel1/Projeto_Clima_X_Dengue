"""
Artefatos de execução (o que o git não versiona): modelos de produção, snapshot do banco e JSONs do painel.

    python main.py empacotar                    → dist/artefatos_v5.1.zip (com manifesto e SHA-256)
    python -m src.prediction_service.artefatos garantir
        → se os artefatos não existirem, baixa o zip de ARTEFATOS_URL (padrão: GitHub Release),
          confere o SHA-256 do zip inteiro contra SHA256_ZIP (versionado no git), depois os hashes do
          manifesto, e extrai. Usado na inicialização do container e no workflow do site.

Segurança: os modelos são .joblib (pickle), e abrir um pickle pode executar código. O manifesto fica dentro
do próprio zip, então sozinho não prova a origem: quem trocasse o zip trocaria o manifesto junto. Por isso o
hash do zip é fixado aqui, no código. Ao publicar artefatos novos: `main.py empacotar` mostra o hash →
atualizar SHA256_ZIP e commitar → subir o zip na Release. Com outra ARTEFATOS_URL, informe ARTEFATOS_SHA256.
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
# SHA-256 do zip publicado na Release modelo-v5.1 (conferido com o digest da Release em 2026-11-08)
SHA256_ZIP = "61226994a99324a97fbf7052613f3e05c7fa7191fef8542ceef0881bf3b2b74f"


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


def _snapshot_banco(destino: Path) -> Path:
    """Cópia consistente do SQLite (API de backup), segura mesmo com uma ingestão gravando no banco."""
    import sqlite3
    origem, copia = sqlite3.connect(DB_PATH, timeout=120), sqlite3.connect(destino)
    try:
        origem.backup(copia)
    finally:          # o "with" do sqlite3 não fecha a conexão; no Windows o arquivo ficaria preso
        copia.close()
        origem.close()
    return destino


def empacotar(destino: Path = BASE_DIR / "dist") -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    zpath = destino / NOME_ZIP
    arquivos = _arquivos()
    meta = json.loads((OUTPUT_DIR / "models" / "final_v5" / "dengue" / "metadata.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        fontes = {p.relative_to(BASE_DIR).as_posix(): p for p in arquivos}
        if DB_PATH in arquivos:
            fontes[DB_PATH.relative_to(BASE_DIR).as_posix()] = _snapshot_banco(Path(tmp) / DB_PATH.name)
        manifesto = {"versao": VERSAO, "criado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                     "periodo_treino": meta.get("periodo_treino"), "git_commit": meta.get("git_commit"),
                     "arquivos": {rel: _sha256(p) for rel, p in fontes.items()}}
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for rel, p in fontes.items():
                z.write(p, rel)
            z.writestr(MANIFESTO, json.dumps(manifesto, indent=1, ensure_ascii=False))
    logger.info(f"{zpath} ({zpath.stat().st_size / 1e6:.1f} MB, {len(arquivos)} arquivos)")
    logger.info(f"SHA-256 do zip: {_sha256(zpath)} → atualize SHA256_ZIP em artefatos.py e commite "
                f"antes de subir o zip na Release")
    return zpath


def conferir_zip(zpath: Path, esperado: str) -> None:
    """Recusa o zip se o SHA-256 não for o fixado no código (antes de abrir qualquer arquivo dele)."""
    obtido = _sha256(zpath)
    if obtido != esperado.lower():
        raise ValueError(f"Hash do pacote não confere: esperado {esperado}, obtido {obtido}. "
                         f"O zip da Release mudou sem atualizar SHA256_ZIP no código.")


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
    esperado = os.environ.get("ARTEFATOS_SHA256") or (SHA256_ZIP if url == URL_PADRAO else None)
    if not esperado:
        raise ValueError("ARTEFATOS_URL personalizada exige ARTEFATOS_SHA256 (hash do zip), "
                         "senão não há como confirmar a origem dos modelos.")
    logger.info(f"Baixando artefatos de {url}")
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / NOME_ZIP
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(zpath, "wb") as f:
                for bloco in r.iter_content(1 << 20):
                    f.write(bloco)
        conferir_zip(zpath, esperado)
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
