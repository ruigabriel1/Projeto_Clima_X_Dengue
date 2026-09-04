"""
Script para criar cache dos geodados (executar uma única vez)
"""
import json
import urllib.request
import time
from pathlib import Path

print("Baixando geodados do Brasil...")
print("Aguarde, isso pode levar alguns segundos...")

url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"
cache_file = Path(__file__).parent.parent.parent / "data" / "geodados" / "cache_geodados.json"

# Aguardar antes de fazer a requisição
time.sleep(3)

try:
    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.loads(response.read().decode())
    
    # Salvar cache
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    
    print(f"\n✅ Cache criado com sucesso!")
    print(f"Arquivo: {cache_file.absolute()}")
    print(f"Tamanho: {cache_file.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"\nAgora você pode executar os scripts de geração de mapas sem problemas de rate limit.")
    
except Exception as e:
    print(f"\n❌ Erro ao baixar geodados: {e}")
    print("\nTente novamente em alguns minutos ou baixe manualmente de:")
    print(url)
