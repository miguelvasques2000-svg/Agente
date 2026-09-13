"""Lógica de correspondência entre um veículo do inventário e os critérios do utilizador."""


def _option_names(vehicle: dict) -> list:
    names = []
    for entry in vehicle.get("OptionCodeData", []) or []:
        name = entry.get("name")
        if name:
            names.append(str(name))
    return names


def _contains_any(haystack_items: list, needles: list) -> bool:
    """True se `needles` estiver vazio, ou se algum needle for substring de algum item."""
    if not needles:
        return True
    haystack = " | ".join(haystack_items).lower()
    return any(str(needle).lower() in haystack for needle in needles)


def vehicle_matches(vehicle: dict, filters: dict) -> bool:
    filters = filters or {}
    price = vehicle.get("Price")

    price_max = filters.get("price_max")
    if price_max is not None and isinstance(price, (int, float)) and price > price_max:
        return False

    price_min = filters.get("price_min")
    if price_min is not None and isinstance(price, (int, float)) and price < price_min:
        return False

    trim = str(vehicle.get("TrimName", ""))
    option_names = _option_names(vehicle)
    all_text = [trim] + option_names

    if not _contains_any(all_text, filters.get("trim_contains", [])):
        return False
    if not _contains_any(option_names, filters.get("exterior_contains", [])):
        return False
    if not _contains_any(option_names, filters.get("interior_contains", [])):
        return False
    if not _contains_any(option_names, filters.get("wheels_contains", [])):
        return False
    if not _contains_any(option_names, filters.get("autopilot_contains", [])):
        return False

    vins_only = filters.get("vin_whitelist")
    if vins_only:
        if str(vehicle.get("VIN", "")) not in vins_only:
            return False

    return True


def vehicle_id(vehicle: dict) -> str:
    """Identificador estável para um veículo, usado para detetar novidades entre execuções."""
    vin = vehicle.get("VIN")
    if vin:
        return f"vin:{vin}"
    fallback_id = vehicle.get("id")
    if fallback_id:
        return f"id:{fallback_id}"
    codes = sorted(
        str(entry.get("code", "")) for entry in vehicle.get("OptionCodeData", []) or []
    )
    return "spec:" + "-".join([str(vehicle.get("TrimName", "")), str(vehicle.get("Price", "")), *codes])
