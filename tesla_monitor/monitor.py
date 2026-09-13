"""Orquestração: procura no inventário, filtra novidades e notifica."""
import logging

from . import state as state_mod
from . import tesla_api
from .filters import vehicle_id, vehicle_matches

logger = logging.getLogger(__name__)


def format_message(vehicle: dict, listing_url: str) -> str:
    price = vehicle.get("Price")
    price_str = f"€{price:,.0f}".replace(",", " ") if isinstance(price, (int, float)) else str(price)

    lines = [
        "🚗 <b>Novo Tesla disponível!</b>",
        f"Modelo: {vehicle.get('Model', '?')} — Trim: {vehicle.get('TrimName', '?')}",
        f"Preço: {price_str}",
        f"VIN: {vehicle.get('VIN', 'N/D')}",
    ]

    option_names = [
        entry.get("name") for entry in vehicle.get("OptionCodeData", []) or [] if entry.get("name")
    ]
    if option_names:
        lines.append("Opções: " + ", ".join(option_names))

    lines.append(listing_url)
    return "\n".join(lines)


def format_not_available_message(cfg: dict, listing_url: str) -> str:
    filters = cfg.get("filters", {}) or {}
    criteria = []
    if filters.get("price_max") is not None:
        criteria.append(f"até €{filters['price_max']:,.0f}".replace(",", " "))
    if filters.get("price_min") is not None:
        criteria.append(f"a partir de €{filters['price_min']:,.0f}".replace(",", " "))
    for key, label in [
        ("trim_contains", "trim"),
        ("exterior_contains", "cor"),
        ("interior_contains", "interior"),
        ("wheels_contains", "jantes"),
        ("autopilot_contains", "Autopilot/FSD"),
    ]:
        values = filters.get(key)
        if values:
            criteria.append(f"{label}: {', '.join(values)}")

    criteria_str = "; ".join(criteria) if criteria else "sem restrições adicionais"

    return (
        "ℹ️ <b>Sem unidades disponíveis</b>\n"
        f"Não há, neste momento, nenhum veículo em stock que corresponda aos critérios ({criteria_str}).\n"
        f"Modelo: {cfg['tesla']['model']} — Mercado: {cfg['tesla']['market']}\n"
        f"A monitorização continua ativa.\n"
        + listing_url
    )


def run_once(
    cfg: dict,
    notifiers: list,
    state_path: str,
    listing_url: str,
    notify_on_empty: bool = False,
) -> list:
    state = state_mod.load_state(state_path)
    previously_seen = set(state.get("seen_ids", []))

    all_vehicles = tesla_api.fetch_all_inventory(cfg["tesla"])
    logger.info("Inventário atual: %d veículo(s) encontrados no total", len(all_vehicles))

    current_ids = set()
    new_matches = []
    currently_matching = []
    for vehicle in all_vehicles:
        vid = vehicle_id(vehicle)
        current_ids.add(vid)
        if not vehicle_matches(vehicle, cfg.get("filters", {})):
            continue
        currently_matching.append(vehicle)
        if vid not in previously_seen:
            new_matches.append(vehicle)

    for vehicle in new_matches:
        message = format_message(vehicle, listing_url)
        for notifier in notifiers:
            try:
                notifier.send(message)
            except Exception:
                logger.exception("Falha ao notificar via %s", getattr(notifier, "name", "?"))
        logger.info("Notificado sobre o veículo %s", vehicle_id(vehicle))

    if not currently_matching:
        logger.info("Nenhuma unidade disponível corresponde aos critérios (query negativa)")
        if notify_on_empty:
            message = format_not_available_message(cfg, listing_url)
            for notifier in notifiers:
                try:
                    notifier.send(message)
                except Exception:
                    logger.exception(
                        "Falha ao enviar resposta de indisponibilidade via %s",
                        getattr(notifier, "name", "?"),
                    )

    # Substitui completamente o estado pelo snapshot atual: veículos que saem
    # do inventário deixam de estar "vistos", pelo que se reaparecerem
    # (ex.: reserva cancelada) voltam a gerar notificação.
    state["seen_ids"] = sorted(current_ids)
    state_mod.save_state(state_path, state)

    return new_matches
