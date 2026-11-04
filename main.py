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
    """Executa o pipeline ML v4.1 (multi-doença)."""
    print(f"🚀 Pipeline ML v4.1 — doença={args.doenca}, modo={args.modo}")
    try:
        from src.ml_pipeline.ml_orchestrator import run_pipeline
        root = Path(__file__).resolve().parent
        results = run_pipeline(
            root,
            modo=args.modo,
            doenca=args.doenca,
        )
        if results:
            for d, (model, log) in results.items():
                n = log.get("n_samples", 0)
                feats = log.get("n_features", 0)
                metrics = log.get("metrics_por_ano", [])
                avg_r2 = sum(m["r2"] for m in metrics) / len(metrics) if metrics else 0
                print(f"  ✅ {d}: {n} amostras, {feats} features, R² médio (EW)={avg_r2:.3f}")
        else:
            print("⚠️ Nenhum modelo treinado.")
    except Exception as e:
        print(f"❌ Erro no pipeline: {e}")
        raise


def command_export_dashboard(args):
    """Exporta resultados v4 para JSON consumido pelo Dashboard."""
    print(f"📊 Exportando dashboard — doença={args.doenca}")
    try:
        from src.ml_pipeline.export_dashboard import exportar_dados_dashboard
        exportar_dados_dashboard(doenca=args.doenca, codigo_ibge=args.codigo_ibge)
        print("Exportação concluída! JSONs em output/dashboard/")
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
        raise


def command_experimento(args):
    """Fase 1: 24 rodadas (doença × horizonte × clima × corte) + baselines."""
    from src.ml_pipeline.experimento_horizontes import main as exp_main
    argv = ["--doenca", args.doenca]
    if args.amostra:
        argv += ["--amostra", str(args.amostra)]
    exp_main(argv)


def command_analise(args):
    """Fase 2: tabela comparativa, efeito do clima, SHAP e configuração sugerida."""
    from src.ml_pipeline.analise_experimento import run_analise
    from src.ml_pipeline.experimento_horizontes import configurar_log
    configurar_log()
    run_analise(com_shap=not args.sem_shap, diagnostico=args.diagnostico)
    print("Relatório: output/experimento/analise.md")


def command_teste_final(args):
    """Fase 3: teste único no holdout 2025."""
    from src.ml_pipeline.teste_final import main as tf_main
    tf_main((["--confirmar"] if args.confirmar else []) + (["--forcar"] if args.forcar else []))


def command_modelo_final(args):
    """Fase 4.1: retreino final 2015–2025 para produção."""
    from src.ml_pipeline.modelo_final import main as mf_main
    mf_main(["--sem-teste"] if args.sem_teste else [])


def command_serve(args):
    """Sobe o servidor do Dashboard."""
    try:
        import uvicorn
        print(f"🌐 Iniciando dashboard em http://localhost:{args.port}")
        uvicorn.run("app.server:app", host="0.0.0.0", port=args.port, reload=args.reload)
    except ImportError:
        print("❌ uvicorn não instalado. Rode: pip install uvicorn")


def main():
    parser = argparse.ArgumentParser(description="CLI Principal do Projeto Clima x Arboviroses")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando train
    parser_train = subparsers.add_parser(
        "train",
        help="Treina o modelo do dashboard (XGBoost Poisson, hiperparâmetros fixos, Expanding Window)."
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
    parser_train.set_defaults(func=command_train)

    # Comando export-dashboard
    parser_export = subparsers.add_parser(
        "export-dashboard",
        help="Exporta JSONs de resultados v4 para o dashboard."
    )
    parser_export.add_argument(
        "--doenca", type=str,
        choices=["dengue", "chikungunya", "zika", "todas"],
        default="todas",
        help="Doença ou 'todas'."
    )
    parser_export.add_argument(
        "--codigo_ibge", type=str, default=None,
        help="Código IBGE (6 dígitos) para filtrar uma cidade."
    )
    parser_export.set_defaults(func=command_export_dashboard)

    # ---------- Experimento final (docs/PLANO_EXPERIMENTO_FINAL.md) ----------
    p_exp = subparsers.add_parser("experimento", help="Fase 1: experimento horizontes × clima × corte P99.")
    p_exp.add_argument("--doenca", choices=["dengue", "chikungunya", "todas"], default="todas")
    p_exp.add_argument("--amostra", type=int, default=None, help="N cidades (teste rápido)")
    p_exp.set_defaults(func=command_experimento)

    p_an = subparsers.add_parser("analise", help="Fase 2: análise e configuração sugerida.")
    p_an.add_argument("--sem-shap", action="store_true")
    p_an.add_argument("--diagnostico", action="store_true",
                      help="Inclui o diagnóstico exploratório por grupo de clima (≈3 min)")
    p_an.set_defaults(func=command_analise)

    p_tf = subparsers.add_parser("teste-final", help="Fase 3: teste ÚNICO no holdout 2025.")
    p_tf.add_argument("--confirmar", action="store_true", help="Confirma a configuração revisada")
    p_tf.add_argument("--forcar", action="store_true", help="Reexecuta apesar da trava (fica registrado)")
    p_tf.set_defaults(func=command_teste_final)

    p_mf = subparsers.add_parser("modelo-final", help="Fase 4.1: retreino 2015–2025 para produção.")
    p_mf.add_argument("--sem-teste", action="store_true", help="Permite treinar antes do teste 2025")
    p_mf.set_defaults(func=command_modelo_final)

    # Comando serve
    parser_serve = subparsers.add_parser(
        "serve",
        help="Inicia o servidor do dashboard (FastAPI + Uvicorn)."
    )
    parser_serve.add_argument("--port", type=int, default=8000)
    parser_serve.add_argument("--reload", action="store_true")
    parser_serve.set_defaults(func=command_serve)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
