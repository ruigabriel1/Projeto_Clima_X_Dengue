"""
Script de validação dos mapas de latitude gerados
Verifica se todos os arquivos foram criados corretamente
"""

from pathlib import Path
import pandas as pd
from PIL import Image
import json

# ===== CONFIGURAÇÃO =====
PASTA_BASE = Path(__file__).parent.parent.parent  # raiz do projeto
PASTA_MAPAS = PASTA_BASE / "output" / "mapas_latitude"
PASTA_CSVS = PASTA_BASE / "output" / "csvs_latitude"

def verificar_arquivos_csv():
    """Verifica se todos os CSVs de entrada existem"""
    print("\n[1/4] Verificando arquivos CSV de entrada...")
    
    esperados = [f"dengue_faixa_latitude_{i}.csv" for i in range(1, 9)]
    encontrados = 0
    tamanho_total = 0
    
    for arquivo in esperados:
        caminho = PASTA_CSVS / arquivo
        if caminho.exists():
            tamanho = caminho.stat().st_size / (1024 * 1024)  # MB
            print(f"    ✓ {arquivo:<35} - {tamanho:.2f} MB")
            encontrados += 1
            tamanho_total += tamanho
        else:
            print(f"    ✗ {arquivo:<35} - NÃO ENCONTRADO")
    
    print(f"\n    Total: {encontrados}/8 arquivos ({tamanho_total:.2f} MB)")
    return encontrados == 8

def verificar_mapas_individuais():
    """Verifica se todos os mapas individuais foram criados"""
    print("\n[2/4] Verificando mapas individuais por ano...")
    
    anos = range(2015, 2024)
    encontrados = 0
    
    for ano in anos:
        arquivo = PASTA_MAPAS / f"mapa_faixas_latitude_{ano}.png"
        if arquivo.exists():
            try:
                img = Image.open(arquivo)
                largura, altura = img.size
                tamanho = arquivo.stat().st_size / 1024  # KB
                print(f"    ✓ {arquivo.name:<35} - {largura}x{altura}px ({tamanho:.0f} KB)")
                encontrados += 1
            except Exception as e:
                print(f"    ⚠ {arquivo.name:<35} - ERRO ao abrir: {e}")
        else:
            print(f"    ✗ {arquivo.name:<35} - NÃO ENCONTRADO")
    
    print(f"\n    Total: {encontrados}/9 mapas individuais")
    return encontrados == 9

def verificar_paineis_comparativos():
    """Verifica se os painéis comparativos foram criados"""
    print("\n[3/4] Verificando painéis comparativos...")
    
    arquivos_esperados = [
        "painel_comparativo_2015_2023.png",
        "evolucao_temporal_faixas_latitude.png"
    ]
    
    encontrados = 0
    
    for arquivo in arquivos_esperados:
        caminho = PASTA_MAPAS / arquivo
        if caminho.exists():
            try:
                img = Image.open(caminho)
                largura, altura = img.size
                tamanho = caminho.stat().st_size / 1024  # KB
                print(f"    ✓ {arquivo:<45} - {largura}x{altura}px ({tamanho:.0f} KB)")
                encontrados += 1
            except Exception as e:
                print(f"    ⚠ {arquivo:<45} - ERRO ao abrir: {e}")
        else:
            print(f"    ✗ {arquivo:<45} - NÃO ENCONTRADO")
    
    print(f"\n    Total: {encontrados}/2 painéis comparativos")
    return encontrados == 2

def verificar_estatisticas_dados():
    """Verifica estatísticas básicas dos dados"""
    print("\n[4/4] Verificando estatísticas dos dados...")
    
    try:
        estatisticas = {}
        
        for ano in range(2015, 2024):
            dados_ano = []
            
            for i in range(1, 9):
                arquivo = PASTA_CSVS / f"dengue_faixa_latitude_{i}.csv"
                if arquivo.exists():
                    df = pd.read_csv(arquivo)
                    df_ano = df[df['ANO'] == ano]
                    if len(df_ano) > 0:
                        dados_ano.append(df_ano)
            
            if dados_ano:
                df_completo = pd.concat(dados_ano, ignore_index=True)
                
                # Agregar por município
                df_agregado = df_completo.groupby('CODIGO_MUNICIPIO').agg({
                    'CASOS_DENGUE': 'sum'
                }).reset_index()
                
                total_casos = df_agregado['CASOS_DENGUE'].sum()
                media_casos = df_agregado['CASOS_DENGUE'].mean()
                num_municipios = len(df_agregado)
                
                estatisticas[ano] = {
                    'total_casos': total_casos,
                    'media_casos': media_casos,
                    'num_municipios': num_municipios
                }
                
                print(f"    {ano}: {total_casos:>8,} casos | Média: {media_casos:>6.2f} | Municípios: {num_municipios}")
        
        # Resumo
        anos_com_dados = len(estatisticas)
        total_geral = sum(e['total_casos'] for e in estatisticas.values())
        media_geral = sum(e['media_casos'] for e in estatisticas.values()) / anos_com_dados if anos_com_dados > 0 else 0
        
        print(f"\n    Resumo: {anos_com_dados} anos | Total geral: {total_geral:,} casos | Média geral: {media_geral:.2f}")
        
        return True
        
    except Exception as e:
        print(f"    ⚠ Erro ao calcular estatísticas: {e}")
        return False

def gerar_relatorio_json():
    """Gera relatório de validação em JSON"""
    print("\n[EXTRA] Gerando relatório de validação...")
    
    try:
        relatorio = {
            "data_validacao": "2025-01-03",
            "status": "OK",
            "arquivos_verificados": {},
            "estatisticas": {}
        }
        
        # Verificar CSVs
        csvs_ok = sum(1 for i in range(1, 9) if (PASTA_CSVS / f"dengue_faixa_latitude_{i}.csv").exists())
        relatorio["arquivos_verificados"]["csvs_entrada"] = {
            "esperados": 8,
            "encontrados": csvs_ok,
            "status": "OK" if csvs_ok == 8 else "INCOMPLETO"
        }
        
        # Verificar mapas individuais
        mapas_ok = sum(1 for ano in range(2015, 2024) if (PASTA_MAPAS / f"mapa_faixas_latitude_{ano}.png").exists())
        relatorio["arquivos_verificados"]["mapas_individuais"] = {
            "esperados": 9,
            "encontrados": mapas_ok,
            "status": "OK" if mapas_ok == 9 else "INCOMPLETO"
        }
        
        # Verificar painéis
        paineis_ok = sum(1 for f in ["painel_comparativo_2015_2023.png", "evolucao_temporal_faixas_latitude.png"] 
                        if (PASTA_MAPAS / f).exists())
        relatorio["arquivos_verificados"]["paineis_comparativos"] = {
            "esperados": 2,
            "encontrados": paineis_ok,
            "status": "OK" if paineis_ok == 2 else "INCOMPLETO"
        }
        
        # Status geral
        relatorio["status"] = "OK" if (csvs_ok == 8 and mapas_ok == 9 and paineis_ok == 2) else "INCOMPLETO"
        
        # Salvar
        arquivo_json = PASTA_BASE / "validacao_mapas_latitude.json"
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print(f"    ✓ Relatório salvo: {arquivo_json.name}")
        
    except Exception as e:
        print(f"    ⚠ Erro ao gerar relatório: {e}")

def main():
    """Função principal de validação"""
    print("=" * 80)
    print("VALIDAÇÃO DOS MAPAS DE LATITUDE - PROJETO DENGUE")
    print("=" * 80)
    
    # Executar verificações
    csv_ok = verificar_arquivos_csv()
    mapas_ok = verificar_mapas_individuais()
    paineis_ok = verificar_paineis_comparativos()
    stats_ok = verificar_estatisticas_dados()
    
    # Gerar relatório
    gerar_relatorio_json()
    
    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO DA VALIDAÇÃO")
    print("=" * 80)
    
    status_geral = csv_ok and mapas_ok and paineis_ok and stats_ok
    
    print(f"\n    Arquivos CSV de entrada:      {'✅ OK' if csv_ok else '❌ FALHOU'}")
    print(f"    Mapas individuais (2015-2023): {'✅ OK' if mapas_ok else '❌ FALHOU'}")
    print(f"    Painéis comparativos:          {'✅ OK' if paineis_ok else '❌ FALHOU'}")
    print(f"    Estatísticas dos dados:        {'✅ OK' if stats_ok else '❌ FALHOU'}")
    
    print("\n" + "=" * 80)
    if status_geral:
        print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
        print("Todos os arquivos foram gerados corretamente.")
    else:
        print("⚠ VALIDAÇÃO APRESENTOU PROBLEMAS")
        print("Verifique os itens marcados acima.")
    print("=" * 80)

if __name__ == "__main__":
    main()
