import argparse
import sys
from pathlib import Path

# Força a saída para UTF-8 no Windows para suportar emojis (❌, ✅, 📊)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Adiciona o diretório atual ao path para facilitar imports de src
sys.path.insert(0, str(Path(__file__).resolve().parent))

def command_process_data(args):
    print("Iniciando consolidação de dados...")
    try:
        import src.consolidar_dados as cd
        cd.main()
        print("Dados consolidados com sucesso.")
    except Exception as e:
        print(f"Erro ao processar dados: {e}")

def command_run_model(args):
    print("Iniciando motor de modelagem (Projeções até 2040)...")
    try:
        from src.processamento import motor_lote_modelagem_v2_por_latitude as motor
        motor.main()
        print("Modelagem e predições concluídas com sucesso!")
    except Exception as e:
        print(f"Erro ao rodar o modelo: {e}")

def command_generate_reports(args):
    print("Iniciando geração de relatórios...")
    try:
        import src.pipeline as pipeline
        if args.file:
            pipeline.pipeline_completo(args.file)
        else:
            from src.config import DATA_PROCESSED_DIR
            arquivo = DATA_PROCESSED_DIR / 'dados_consolidados.csv'
            pipeline.pipeline_completo(str(arquivo))
    except Exception as e:
        print(f"Erro ao gerar relatórios: {e}")

def main():
    parser = argparse.ArgumentParser(description="CLI Principal do Projeto Clima x Dengue")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando process-data
    parser_process = subparsers.add_parser("process-data", help="Limpa e consolida dados brutos.")
    parser_process.set_defaults(func=command_process_data)

    # Comando run-model
    parser_model = subparsers.add_parser("run-model", help="Executa as projeções e modelos de ML.")
    parser_model.set_defaults(func=command_run_model)

    # Comando generate-reports
    parser_reports = subparsers.add_parser("generate-reports", help="Roda o pipeline estatístico para relatórios.")
    parser_reports.add_argument("--file", type=str, help="Caminho opcional do arquivo processado.", default=None)
    parser_reports.set_defaults(func=command_generate_reports)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
