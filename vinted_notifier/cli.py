import argparse
import logging
import os
import sys
import time
from pathlib import Path

from .config import load_config, render_template
from .notify import build_apprise, send_notifications
from .storage import NotificationStore
from .vinted import fetch_catalog_items

LOGGER = logging.getLogger("vinted_notifier")


def run_once(config):
    store = NotificationStore(config.database)
    notifier = build_apprise(config.apprise_urls)

    for query in config.queries:
        items = fetch_catalog_items(query)
        if not items:
            LOGGER.info("No items found for %s", query.name)
            continue

        for item in items:
            slot = f"{query.name}:{item['id']}"
            if store.was_notified(slot):
                continue

            title = render_template(config.notification.title, query=query, item=item)
            body = render_template(config.notification.body, query=query, item=item)
            send_notifications(notifier, title, body)
            store.mark_notified(slot, item)
            LOGGER.info("Notified new item %s for query %s", item["id"], query.name)


def configure_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Vinted notifier based on Apprise notifications.")
    parser.add_argument("--config", default=os.environ.get("CONFIG_FILE", "config.yaml"), help="Path to config file")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in daemon mode")
    parser.add_argument("--once", action="store_true", help="Run only once and exit")
    parser.add_argument("--interval", type=int, help="Polling interval in seconds")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args(argv)

    configure_logging(args.verbose)
    config = load_config(Path(args.config))
    if args.interval:
        config.run_interval = args.interval

    should_loop = args.daemon or os.environ.get("DAEMON", "false").lower() in ("1", "true", "yes")
    if args.once:
        should_loop = False

    LOGGER.info("Starting Vinted Notifier, instance=%s, queries=%s", config.default_instance, len(config.queries))

    try:
        while True:
            run_once(config)
            if not should_loop:
                LOGGER.info("Run complete. Exiting.")
                break
            LOGGER.info("Sleeping for %s seconds...")
            time.sleep(config.run_interval)
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by user, exiting.")
