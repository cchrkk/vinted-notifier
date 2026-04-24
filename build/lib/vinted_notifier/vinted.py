import logging
from urllib.parse import parse_qs, urlparse

import requests

LOGGER = logging.getLogger("vinted_notifier.vinted")


def _build_api_request(query_url: str, instance: str):
    parsed = urlparse(query_url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    params = {k: v if len(v) > 1 else v[0] for k, v in query_params.items()}
    params.setdefault("page", "1")
    params["per_page"] = 36
    api_url = f"https://www.vinted.{instance}/api/v2/catalog/items"
    return api_url, params


def _build_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-GPC": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }


def _normalize_item(raw_item, query_name, instance):
    title = raw_item.get("title") or raw_item.get("brand_title") or raw_item.get("description") or "Untitled"
    raw_price = raw_item.get("price") or raw_item.get("price_amount") or raw_item.get("price_cents")
    if isinstance(raw_price, dict):
        amount = raw_price.get("amount") or raw_price.get("amount_cents")
        currency = raw_price.get("currency_code") or raw_price.get("currency") or "EUR"
    else:
        amount = raw_price
        currency = raw_item.get("currency") or raw_item.get("price_currency") or "EUR"

    normalized_price = f"{amount} {currency}" if amount else "n/a"
    image_url = raw_item.get("photo", {}).get("full_size_url")
    if not image_url:
        photos = raw_item.get("photos") or raw_item.get("images")
        if isinstance(photos, list) and photos:
            image_url = photos[0].get("full_size_url") if isinstance(photos[0], dict) else None

    url = raw_item.get("url") or raw_item.get("item_url") or raw_item.get("web_url") or raw_item.get("path") or ""
    if url and url.startswith("/"):
        url = f"https://www.vinted.{instance}{url}"

    return {
        "id": raw_item.get("id"),
        "title": title,
        "brand": raw_item.get("brand_title") or raw_item.get("brand") or "Unknown",
        "price": normalized_price,
        "currency": currency,
        "url": url,
        "image_url": image_url,
        "query_name": query_name,
    }


def fetch_catalog_items(query):
    api_url, params = _build_api_request(query.url, query.instance)
    LOGGER.debug("Fetching Vinted search: %s params=%s", api_url, params)

    session = requests.Session()
    root_url = f"https://www.vinted.{query.instance}"
    try:
        session.post(root_url, headers=_build_headers(), timeout=15)
    except Exception as exc:
        LOGGER.warning("Could not initialize Vinted session: %s", exc)

    try:
        response = session.get(api_url, params=params, headers=_build_headers(), timeout=15)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items") or payload.get("data", {}).get("items") or []
        results = []
        for item in items:
            normalized = _normalize_item(item, query.name, query.instance)
            if normalized["id"]:
                results.append(normalized)
        return results
    except Exception as exc:
        LOGGER.error("Error fetching items for %s: %s", query.name, exc)
        return []
