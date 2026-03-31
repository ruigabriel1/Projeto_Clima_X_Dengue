#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE VALIDAÇÃO AUTOMÁTICA DAS TAREFAS
==========================================

Valida a integridade e funcionalidade de todas as 4 tarefas principais:
1. Mapa Dengue Agregado
2. Análise Global Log
3. El Niño vs La Niña
4. Regressão Múltipla

Uso:
    python scripts/validar_todas_tarefas.py
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

# Configurações
BASE_DIR = Path(__file__).parent.parent.parent  # raiz do projeto
SCRIPTS_DIR = BASE_DIR / "src"  # scripts distribuídos em src/{analises,mapas,...}
OUTPUT_DIR = BASE_DIR / "output"

# Cores para terminal
class Cores:
    VERDE = '\033[92m'
    VERMELHO = '\033[91m'
    AMARELO = '\033[93m'
    AZUL = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(texto):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 80)
    print(f"{Cores.BOLD}{Cores.AZUL}{texto}{Cores.RESET}")
    print("=" * 80)

def print_sucesso(texto):
    """Imprime mensagem de sucesso."""
    print(f"{Cores.VERDE}✓{Cores.RESET} {texto}")

def print_erro(texto):
    """Imprime mensagem de erro."""
    print(f"{Cores.VERMELHO}✗{Cores.RESET} {texto}")

def print_aviso(texto):
    """Imprime mensagem de aviso."""
    print(f"{Cores.AMARELO}⚠{Cores.RESET} {texto}")

def validar_script_existe(nome_script):
    """Valida se o script existe."""
    caminho = SCRIPTS_DIR / nome_script
    if caminho.exists():
        print_sucesso(f"Script encontrado: {nome_script}")
        return True
    else:
        print_erro(f"Script NÃO encontrado: {nome_script}")
        return False

def executar_script(nome_script):
    """Executa um script Python e captura o resultado."""
    caminho = SCRIPTS_DIR / nome_script
    
    print(f"\n{Cores.AZUL}→{Cores.RESET} Executando: {nome_script}")
    print("-" * 80)
    
    try:
        resultado = subprocess.run(
            [sys.executable, str(caminho)],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutos de timeout
        )
        
        # Exibe últimas 10 linhas do output
        linhas = resultado.stdout.strip().split('\n')
        for linha in linhas[-10:]:
            print(f"  {linha}")
        
        if resultado.returncode == 0:
            print_sucesso(f"Execução bem-sucedida: {nome_script}")
            return True, resultado.stdout
        else:
            print_erro(f"Erro na execução: {nome_script}")
            print(f"  {Cores.VERMELHO}Stderr:{Cores.RESET} {resultado.stderr[-500:]}")
            return False, resultado.stderr
            
    except subprocess.TimeoutExpired:
        print_erro(f"Timeout excedido (>2 min): {nome_script}")
        return False, "Timeout"
    except Exception as e:
        print_erro(f"Exceção ao executar {nome_script}: {str(e)}")
        return False, str(e)

def validar_outputs(task_name, arquivos_esperados):
    """Valida se os arquivos de output foram gerados."""
    print(f"\n{Cores.AZUL}→{Cores.RESET} Validando outputs de: {task_name}")
    
    todos_encontrados = True
    
    for arquivo in arquivos_esperados:
        # Procura arquivos com padrão (pode ter timestamp)
        if '*' in arquivo or '?' in arquivo:
            # Arquivo com wildcard
            pasta = OUTPUT_DIR / Path(arquivo).parent
            padrao = Path(arquivo).name
            
            arquivos_encontrados = list(pasta.glob(padrao))
            
            if arquivos_encontrados:
                # Pega o mais recente
                arquivo_mais_recente = max(arquivos_encontrados, key=lambda p: p.stat().st_mtime)
                print_sucesso(f"Output encontrado: {arquivo_mais_recente.name}")
            else:
                print_erro(f"Output NÃO encontrado: {arquivo}")
                todos_encontrados = False
        else:
            # Arquivo exato
            caminho = OUTPUT_DIR / arquivo
            if caminho.exists():
                print_sucesso(f"Output encontrado: {arquivo}")
            else:
                print_erro(f"Output NÃO encontrado: {arquivo}")
                todos_encontrados = False
    
    return todos_encontrados

# ==================== DEFINIÇÃO DAS TAREFAS ====================

TAREFAS = {
    'Task 1 - Mapa Dengue Agregado': {
        'script': 'mapas/criar_mapa_dengue_agregado_total.py',  # movido para src/mapas/
        'outputs': [
            'mapas/mapa_dengue_agregado_2015_2024_*.png',
            'mapas/dengue_agregado_2015_2024.csv'
        ]
    },
    'Task 2 - Análise Global Log': {
        'script': 'analises/analise_global_dengue_log_pdf.py',  # movido para src/analises/
        'outputs': [
            'analise_estatistica/analise_global_dengue_log_*.pdf',
            'analise_estatistica/dados_analise_global.csv'
        ]
    },
    'Task 3 - El Niño vs La Niña': {
        'script': 'analises/analise_el_nino_la_nina_latitude_pdf.py',  # movido para src/analises/
        'outputs': [
            'analise_estatistica/analise_el_nino_la_nina_latitude_*.pdf',
            'analise_estatistica/dados_enso_latitude_processados.csv',
            'analise_estatistica/resumo_el_nino_la_nina.txt'
        ]
    },
    'Task 4 - Regressão Múltipla': {
        'script': 'analises/analise_regressao_multipla_pdf.py',  # movido para src/analises/
        'outputs': [
            'analise_estatistica/analise_regressao_multipla_*.pdf',
            'analise_estatistica/dados_regressao_multipla.csv',
            'analise_estatistica/predicoes_regressao_multipla.csv',
            'analise_estatistica/resumo_regressao_multipla.txt'
        ]
    }
}

# ==================== FUNÇÃO PRINCIPAL ====================

def main():
    """Função principal de validação."""
    print_header("VALIDAÇÃO AUTOMÁTICA DAS TAREFAS")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    resultados = {}
    
    # Para cada tarefa
    for task_name, task_info in TAREFAS.items():
        print_header(task_name)
        
        resultado_task = {
            'script_existe': False,
            'execucao_ok': False,
            'outputs_ok': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Valida se script existe
        if validar_script_existe(task_info['script']):
            resultado_task['script_existe'] = True
            
            # 2. Executa script
            sucesso, output = executar_script(task_info['script'])
            resultado_task['execucao_ok'] = sucesso
            
            if sucesso:
                # 3. Valida outputs
                outputs_ok = validar_outputs(task_name, task_info['outputs'])
                resultado_task['outputs_ok'] = outputs_ok
        
        resultados[task_name] = resultado_task
    
    # ==================== RESUMO FINAL ====================
    print_header("RESUMO FINAL DA VALIDAÇÃO")
    
    total_tarefas = len(TAREFAS)
    tarefas_ok = sum(1 for r in resultados.values() if r['execucao_ok'] and r['outputs_ok'])
    
    print(f"\nTotal de tarefas: {total_tarefas}")
    print(f"Tarefas validadas: {tarefas_ok}")
    print(f"Taxa de sucesso: {(tarefas_ok/total_tarefas)*100:.1f}%\n")
    
    for task_name, resultado in resultados.items():
        status = "✅ OK" if (resultado['execucao_ok'] and resultado['outputs_ok']) else "❌ FALHOU"
        print(f"{status}  {task_name}")
        
        if not resultado['script_existe']:
            print(f"     → Script não encontrado")
        elif not resultado['execucao_ok']:
            print(f"     → Erro na execução")
        elif not resultado['outputs_ok']:
            print(f"     → Outputs incompletos")
    
    # Salva relatório JSON
    relatorio_path = BASE_DIR / f"validacao_tarefas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Cores.AZUL}→{Cores.RESET} Relatório JSON salvo: {relatorio_path.name}")
    
    # Retorna código de saída
    if tarefas_ok == total_tarefas:
        print(f"\n{Cores.VERDE}{Cores.BOLD}✓ TODAS AS TAREFAS VALIDADAS COM SUCESSO!{Cores.RESET}\n")
        return 0
    else:
        print(f"\n{Cores.VERMELHO}{Cores.BOLD}✗ ALGUMAS TAREFAS FALHARAM NA VALIDAÇÃO{Cores.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
