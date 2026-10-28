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


def command_train(args):
    """Executa o pipeline ML v4 (multi-doença)."""
    print(f"🚀 Pipeline ML v4 — doença={args.doenca}, modo={args.modo}")
    try:
        from src.ml_pipeline.ml_orchestrator import run_pipeline
        root = Path(__file__).resolve().parent
        results = run_pipeline(
            root,
            modo=args.modo,
            tune_hyperparams=args.tune,
            doenca=args.doenca,
        )
        if results:
            for d, (model, log) in results.items():
                n = log.get("n_samples", 0)
                feats = log.get("n_features", 0)
                metrics = log.get("metrics_por_ano", [])
                avg_r2 = sum(m["r2"] for m in metrics) / len(metrics) if metrics else 0
                print(f"  ✅ {d}: {n} amostras, {feats} features, R² médio={avg_r2:.3f}")
        else:
            print("⚠️ Nenhum modelo treinado.")
    except Exception as e:
        print(f"❌ Erro no pipeline: {e}")
        raise


def command_run_model(args):
    """Executa o motor legado de projeções SSP (mantido para retrocompatibilidade)."""
    print(f"Iniciando motor de modelagem (Projeções até 2040) no modo {args.modo.upper()}...")
    try:
        from src.processamento import motor_lote_modelagem_v2_por_latitude as motor
        motor.main(modo=args.modo)
        print("Modelagem e predições concluídas com sucesso!")
    except Exception as e:
        print(f"Erro ao rodar o modelo: {e}")


def command_export_dashboard(args):
    """Exporta dados e gráficos para o Dashboard."""
    print("Exportando dados e gráficos para o Dashboard...")
    try:
        from src.ml_pipeline.export_dashboard import exportar_dados_dashboard
        exportar_dados_dashboard(modo=args.modo, codigo_ibge=args.codigo_ibge)
        print("Exportação concluída! JSON salvo em output/prodigia_resultados_v2.json")
    except Exception as e:
        print(f"Erro na exportação: {e}")


def main():
    parser = argparse.ArgumentParser(description="CLI Principal do Projeto Clima x Arboviroses")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando train (NOVO v4)
    parser_train = subparsers.add_parser(
        "train",
        help="Treina o modelo ML v4 (XGBoost Poisson + Expanding Window)."
    )
    parser_train.add_argument(
        "--modo", type=str,
        choices=["rapido", "regional"],
        default="regional",
        help="Escopo: 'rapido' (1 cidade) ou 'regional' (todas)."
    )
    parser_train.add_argument(
        "--doenca", type=str,
        choices=["dengue", "chikungunya", "zika", "todas"],
        default="dengue",
        help="Doença-alvo ou 'todas' para loop."
    )
    parser_train.add_argument(
        "--tune", action="store_true",
        help="Tunar hiperparâmetros com RandomizedSearchCV."
    )
    parser_train.set_defaults(func=command_train)

    # Comando run-model (legado)
    parser_model = subparsers.add_parser(
        "run-model",
        help="[Legado] Executa projeções SSP com o motor antigo."
    )
    parser_model.add_argument(
        "--modo", type=str,
        choices=["rapido", "regional", "completo"],
        default="regional",
        help="Escopo de processamento."
    )
    parser_model.set_defaults(func=command_run_model)

    # Comando export-dashboard
    parser_export = subparsers.add_parser(
        "export-dashboard",
        help="Exporta o JSON e PNGs para o Dashboard."
    )
    parser_export.add_argument(
        "--modo", type=str,
        choices=["rapido", "regional", "completo"],
        default="rapido"
    )
    parser_export.add_argument(
        "--codigo_ibge", type=str, default=None
    )
    parser_export.set_defaults(func=command_export_dashboard)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
