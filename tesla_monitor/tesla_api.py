"""Cliente para a API (não oficial) de inventário da Tesla.

A Tesla não publica documentação oficial para este endpoint - é o mesmo
usado pela própria página de inventário (www.tesla.com/.../inventory/...).
O esquema pode mudar sem aviso; usa `--dump-raw` no main.py para inspecionar
a resposta bruta se os filtros deixarem de funcionar como esperado.
"""
import json
import logging

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.tesla.com/inventory/api/v4/inventory-results"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.tesla.com/",
}


class TeslaAPIError(RuntimeError):
    pass


def _build_query(tesla_cfg: dict, offset: int, count: int) -> dict:
    return {
        "query": {
            "model": tesla_cfg["model"],
            "condition": tesla_cfg.get("condition", "new"),
            "options": tesla_cfg.get("options", {}) or {},
            "arrangeby": tesla_cfg.get("arrangeby", "Price"),
            "order": tesla_cfg.get("order", "asc"),
            "market": tesla_cfg["market"],
            "language": tesla_cfg.get("language", "en"),
            "super_region": tesla_cfg.get("super_region", "europe"),
            "lng": tesla_cfg.get("lng"),
            "lat": tesla_cfg.get("lat"),
            "zip": tesla_cfg.get("zip"),
            "range": tesla_cfg.get("range", 0),
        },
        "offset": offset,
        "count": count,
        "outsideOffset": 0,
        "outsideSearch": False,
    }


def fetch_inventory_page(tesla_cfg: dict, offset: int = 0, count: int = 50, timeout: int = 20):
    """Devolve (resultados, total_encontrado) para uma única página da API."""
    query = _build_query(tesla_cfg, offset, count)
    params = {"query": json.dumps(query), "count": count, "offset": offset}
    resp = requests.get(BASE_URL, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
    if resp.status_code != 200:
        raise TeslaAPIError(f"Tesla API devolveu HTTP {resp.status_code}: {resp.text[:300]}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise TeslaAPIError(f"Resposta da Tesla API não é JSON válido: {resp.text[:300]}") from exc

    results = data.get("results", [])
    total = data.get("total_matches_found", len(results))
    return results, total


def fetch_all_inventory(tesla_cfg: dict, page_size: int = 50, max_pages: int = 20):
    """Percorre todas as páginas de resultados até esgotar o total reportado."""
    all_results = []
    offset = 0
    for _ in range(max_pages):
        results, total = fetch_inventory_page(tesla_cfg, offset=offset, count=page_size)
        all_results.extend(results)
        offset += page_size
        if not results or offset >= total:
            break
    else:
        logger.warning("Atingido o limite de %d páginas sem esgotar o inventário", max_pages)
    return all_results
