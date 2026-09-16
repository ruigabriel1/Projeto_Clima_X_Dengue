import argparse
import sys
from pathlib import Path

# Força a saída para UTF-8 no Windows para suportar emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Adiciona o diretório atual ao path para facilitar imports de src
sys.path.insert(0, str(Path(__file__).resolve().parent))

def command_run_model(args):
    print(f"Iniciando motor de modelagem (Projeções até 2040) no modo {args.modo.upper()}...")
    try:
        from src.processamento import motor_lote_modelagem_v2_por_latitude as motor
        motor.main(modo=args.modo)
        print("Modelagem e predições concluídas com sucesso!")
    except Exception as e:
        print(f"Erro ao rodar o modelo: {e}")

def main():
    parser = argparse.ArgumentParser(description="CLI Principal do Projeto Clima x Dengue")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando run-model
    parser_model = subparsers.add_parser("run-model", help="Executa as projeções e modelos de ML.")
    parser_model.add_argument("--modo", type=str, choices=["rapido", "regional", "completo"], default="regional", help="Escopo de processamento.")
    parser_model.set_defaults(func=command_run_model)

    # Comando build-dw
    def command_build_dw(args):
        print("Construindo Data Warehouse SQLite...")
        try:
            from src.processamento import build_data_warehouse
            build_data_warehouse.build_dw()
        except Exception as e:
            print(f"Erro ao construir DW: {e}")

    parser_dw = subparsers.add_parser("build-dw", help="Constrói o Data Warehouse SQLite (Analytics).")
    parser_dw.set_defaults(func=command_build_dw)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
