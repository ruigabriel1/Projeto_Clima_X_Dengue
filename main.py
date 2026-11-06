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


def command_teste_prospectivo(args):
    """Protocolo v5: teste prospectivo único em jan–ago/2026."""
    from src.ml_pipeline.teste_prospectivo import main as tp_main
    tp_main((["--confirmar"] if args.confirmar else []) + (["--forcar"] if args.forcar else []))


def command_atualizar_dados(args):
    """Atualização incremental e idempotente do banco (InfoDengue, Open-Meteo, NOAA)."""
    from src.processamento.atualizacao_incremental import main as at_main
    at_main(["--alvo", args.alvo] + (["--rodada", args.rodada] if args.rodada else []))


def command_experimento_v5(args):
    """Protocolo v5: clima parcimonioso × suscetibilidade, alvo de risco, 2025 como 2ª validação."""
    from src.ml_pipeline.experimento_v5 import main as v5_main
    v5_main(["--doenca", args.doenca])


def command_modelo_risco(args):
    """Protocolo v5: benchmark InfoDengue + modelos de produção de alerta de risco."""
    from src.ml_pipeline.alerta_risco import benchmark_infodengue, treinar_modelos_risco
    from src.ml_pipeline.data_ingestion import build_base_panel
    from src.ml_pipeline.experimento_horizontes import configurar_log
    configurar_log()
    if not args.sem_benchmark:
        print(benchmark_infodengue().round(3).to_string(index=False))
    treinar_modelos_risco(build_base_panel(Path(__file__).resolve().parent), ano_max=args.ano_max,
                          producao=args.producao)
    print("Modelos de risco em output/models/final_v5/" + (" (produção v5.1: todos os meses consolidados)" if args.producao else ""))


def command_experimento_v6(args):
    """Protocolo v6: formulação (offset de persistência), vizinhos, imunidade longa. Exige protocolo commitado."""
    from src.ml_pipeline.experimento_v6 import main as v6_main
    v6_main(["--doenca", args.doenca])


def command_modelo_v6(args):
    """Protocolo v6: modelo de produção do modo sombra (output/models/final_v6/)."""
    from src.ml_pipeline.experimento_horizontes import configurar_log
    from src.ml_pipeline.experimento_v6 import treinar_producao
    configurar_log()
    treinar_producao()
    print("Modelo v6 (modo sombra) em output/models/final_v6/")


def command_atualizar_mensal(args):
    """Produção v5.1: atualiza dados, avalia previsões passadas e emite/registra as novas."""
    from src.ml_pipeline.experimento_horizontes import configurar_log
    from src.prediction_service.rotina_mensal import executar
    configurar_log()
    executar(atualizar_dados=not args.sem_ingestao)


def command_empacotar(args):
    """Gera dist/artefatos_v5.1.zip (modelos + banco + painel, com manifesto SHA-256)."""
    from src.ml_pipeline.experimento_horizontes import configurar_log
    from src.prediction_service.artefatos import empacotar
    configurar_log()
    print(empacotar())


def command_dlnm(args):
    """Protocolo v5 (H1): efeito defasado do clima por DLNM (Poisson condicional)."""
    from src.analise_efeito.dlnm import main as dlnm_main
    dlnm_main(["--doenca", args.doenca])


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

    p_tp = subparsers.add_parser("teste-prospectivo", help="v5: teste ÚNICO em jan–ago/2026 (trava após rodar).")
    p_tp.add_argument("--confirmar", action="store_true")
    p_tp.add_argument("--forcar", action="store_true")
    p_tp.set_defaults(func=command_teste_prospectivo)

    # ---------- Protocolo v5 (docs/PROTOCOLO_V5.md) ----------
    p_at = subparsers.add_parser("atualizar-dados", help="Atualização incremental idempotente do banco.")
    p_at.add_argument("--alvo", choices=["infodengue", "openmeteo", "noaa", "todos"], default="todos")
    p_at.add_argument("--rodada", default=None, help="Identificador para retomar uma rodada interrompida")
    p_at.set_defaults(func=command_atualizar_dados)

    p_v5 = subparsers.add_parser("experimento-v5", help="Experimento v5: clima × suscetibilidade, risco.")
    p_v5.add_argument("--doenca", choices=["dengue", "chikungunya", "todas"], default="todas")
    p_v5.set_defaults(func=command_experimento_v5)

    p_mr = subparsers.add_parser("modelo-risco", help="Benchmark InfoDengue + modelos de alerta de risco (produção).")
    p_mr.add_argument("--ano-max", type=int, default=2025, help="Último ano de treino (2025 até o teste prospectivo)")
    p_mr.add_argument("--sem-benchmark", action="store_true")
    p_mr.add_argument("--producao", action="store_true",
                      help="v5.1: treina com todos os meses consolidados e calibra com OOF + teste 2026")
    p_mr.set_defaults(func=command_modelo_risco)

    p_v6 = subparsers.add_parser("experimento-v6", help="v6: formulação × vizinhos × imunidade longa (pré-registrado).")
    p_v6.add_argument("--doenca", choices=["dengue", "chikungunya", "todas"], default="todas")
    p_v6.set_defaults(func=command_experimento_v6)

    p_m6 = subparsers.add_parser("modelo-v6", help="v6: treina o modelo do modo sombra com a decisão do experimento.")
    p_m6.set_defaults(func=command_modelo_v6)

    p_am = subparsers.add_parser("atualizar-mensal", help="v5.1: ingestão + monitoramento + previsões do mês.")
    p_am.add_argument("--sem-ingestao", action="store_true", help="Não baixa dados novos (só emite e avalia)")
    p_am.set_defaults(func=command_atualizar_mensal)

    p_em = subparsers.add_parser("empacotar", help="v5.1: zip de modelos + banco para a Release / Docker.")
    p_em.set_defaults(func=command_empacotar)

    p_dl = subparsers.add_parser("dlnm", help="Efeito do clima por DLNM (Poisson condicional).")
    p_dl.add_argument("--doenca", choices=["dengue", "chikungunya", "todas"], default="todas")
    p_dl.set_defaults(func=command_dlnm)

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
