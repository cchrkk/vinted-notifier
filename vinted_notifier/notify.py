import logging
from typing import Iterable

from apprise import Apprise

LOGGER = logging.getLogger("vinted_notifier.notify")


def build_apprise(urls):
    apprise = Apprise()
    if isinstance(urls, str):
        urls = [urls]
    for url in urls or []:
        apprise.add(url)
        LOGGER.debug("Loaded Apprise target: %s", url)
    return apprise


def send_notifications(apprise, title: str, body: str):
    LOGGER.info("Sending notification: %s", title)
    if not apprise or len(apprise.urls()) == 0:
        LOGGER.warning("No Apprise URLs configured; skipping notification")
        return
    success = apprise.notify(title=title, body=body)
    if not success:
        LOGGER.error("Failed to send notification: %s", title)
