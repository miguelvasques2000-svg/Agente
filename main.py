#!/usr/bin/env python3
"""Ponto de entrada do monitor de inventário Tesla.

Exemplos:
    python main.py --once                 # corre uma verificação e termina
    python main.py                        # corre em loop contínuo (usa polling.interval_seconds)
    python main.py --test-notify          # testa os canais de notificação configurados
    python main.py --dump-raw dump.json   # guarda a resposta bruta da API para debug
"""
import argparse
import json
import logging
import time

from dotenv import load_dotenv

from tesla_monitor import monitor, tesla_api
from tesla_monitor.config import load_config
from tesla_monitor.notifiers import build_notifiers

logger = logging.getLogger("tesla_monitor")


def main():
    parser = argparse.ArgumentParser(description="Monitor de inventário Tesla")
    parser.add_argument("--config", default="config.yaml", help="Caminho para o ficheiro de configuração")
    parser.add_argument("--once", action="store_true", help="Corre uma única verificação e termina")
    parser.add_argument(
        "--test-notify", action="store_true", help="Envia uma mensagem de teste pelos canais ativos e termina"
    )
    parser.add_argument(
        "--dump-raw",
        metavar="PATH",
        help="Guarda a resposta bruta da API Tesla neste ficheiro (útil para depurar filtros)",
    )
    parser.add_argument(
        "--notify-empty",
        action="store_true",
        help="Envia também uma mensagem quando não há nenhuma unidade disponível (query negativa)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()

    cfg = load_config(args.config)

    if args.test_notify:
        notifiers = build_notifiers(cfg)
        for notifier in notifiers:
            notifier.send("✅ Teste do monitor de inventário Tesla — está tudo a funcionar!")
            logger.info("Mensagem de teste enviada via %s", notifier.name)
        return

    if args.dump_raw:
        results = tesla_api.fetch_all_inventory(cfg["tesla"])
        with open(args.dump_raw, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info("Guardados %d resultado(s) em %s", len(results), args.dump_raw)
        return

    notifiers = build_notifiers(cfg)
    listing_url = cfg.get("listing_url", "https://www.tesla.com/pt_PT/inventory/new")
    state_path = cfg.get("state_file", "state/seen_vehicles.json")

    if args.once:
        try:
            matches = monitor.run_once(
                cfg, notifiers, state_path, listing_url, notify_on_empty=args.notify_empty
            )
        except Exception:
            logger.exception("Erro durante a verificação de inventário")
            raise SystemExit(1)
        logger.info("Verificação concluída: %d veículo(s) novo(s) correspondente(s)", len(matches))
        return

    interval = cfg.get("polling", {}).get("interval_seconds", 300)
    logger.info("A iniciar loop de monitorização contínuo (intervalo: %ds)", interval)
    while True:
        try:
            matches = monitor.run_once(
                cfg, notifiers, state_path, listing_url, notify_on_empty=args.notify_empty
            )
            if matches:
                logger.info("Notificados %d veículo(s) novo(s)", len(matches))
        except Exception:
            logger.exception("Erro durante a verificação de inventário")
        time.sleep(interval)


if __name__ == "__main__":
    main()
