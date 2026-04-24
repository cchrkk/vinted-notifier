import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import yaml


@dataclass
class QueryConfig:
    name: str
    url: str
    instance: str
    raw_query: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationConfig:
    title: str
    body: str


@dataclass
class AppConfig:
    apprise_urls: List[str]
    default_instance: str
    database: str
    run_interval: int
    notification: NotificationConfig
    queries: List[QueryConfig]


DEFAULT_CONFIG = {
    "apprise_urls": [],
    "default_instance": "it",
    "database": "./vinted.db",
    "run_interval": 600,
    "notification": {
        "title": "Vinted: {query_name} - {title}",
        "body": "New listing: {title}\nBrand: {brand}\nPrice: {price}\nLink: {url}\nQuery: {query_name}",
    },
    "queries": [],
}


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _normalize_query(url: str, default_instance: str) -> QueryConfig:
    parsed = urlparse(url)
    netloc = parsed.netloc or f"www.vinted.{default_instance}"
    instance = parsed.hostname.split(".")[-1] if parsed.hostname else default_instance
    query = parse_qs(parsed.query, keep_blank_values=True)
    return QueryConfig(
        name=query.get("search_text", [url])[0] if query.get("search_text") else url,
        url=url,
        instance=instance,
        raw_query={k: v if len(v) > 1 else v[0] for k, v in query.items()},
        metadata={"raw_url": url},
    )


def load_config(path: Path) -> AppConfig:
    config_data = DEFAULT_CONFIG.copy()
    config_data.update(_load_yaml(path))

    queries = []
    for entry in config_data.get("queries", []):
        if not isinstance(entry, dict) or "url" not in entry:
            continue
        query = _normalize_query(entry["url"], config_data["default_instance"])
        query.name = entry.get("name", query.name)
        query.instance = entry.get("instance", query.instance)
        query.metadata.update({k: v for k, v in entry.items() if k not in ("name", "url", "instance")})
        queries.append(query)

    return AppConfig(
        apprise_urls=config_data.get("apprise_urls", []),
        default_instance=config_data.get("default_instance", "it"),
        database=config_data.get("database", "./vinted.db"),
        run_interval=int(config_data.get("run_interval", 600)),
        notification=NotificationConfig(
            title=config_data["notification"].get("title", DEFAULT_CONFIG["notification"]["title"]),
            body=config_data["notification"].get("body", DEFAULT_CONFIG["notification"]["body"]),
        ),
        queries=queries,
    )


def render_template(template: str, query: QueryConfig, item: Dict[str, Any]) -> str:
    replacements = {
        "query_name": query.name,
        "title": item.get("title", "n/a"),
        "brand": item.get("brand", "n/a"),
        "price": item.get("price", "n/a"),
        "currency": item.get("currency", ""),
        "url": item.get("url", "n/a"),
    }
    return template.format(**replacements)
