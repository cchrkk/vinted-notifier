import logging
import time
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from apprise import Apprise

LOGGER = logging.getLogger("vinted_notifier.notify")


def _normalize_discord_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme == "discord" or (
        parsed.scheme in ("http", "https")
        and parsed.netloc.lower().endswith("discord.com")
        and "/api/webhooks/" in parsed.path
    ):
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if "image" not in query:
            query["image"] = "No"
            parsed = parsed._replace(query=urlencode(query, doseq=True))
            return urlunparse(parsed)
    return url


def build_apprise(urls):
    apprise = Apprise()
    if isinstance(urls, str):
        urls = [urls]
    for url in urls or []:
        normalized_url = _normalize_discord_url(url)
        apprise.add(normalized_url)
        LOGGER.debug("Loaded Apprise target: %s", normalized_url)
    return apprise


def _has_discord_target(apprise) -> bool:
    for url in apprise.urls() or []:
        parsed = urlparse(url)
        if parsed.scheme == "discord":
            return True
        if parsed.scheme in ("http", "https") and parsed.netloc.lower().endswith("discord.com"):
            return True
    return False


def _notify_with_retries(apprise, title: str, body: str, attach: Iterable[str] | None, retry_attempts: int, retry_delay: float) -> bool:
    attempt = 0
    while attempt <= retry_attempts:
        attempt += 1
        if attempt > 1:
            LOGGER.info("Retrying notification (attempt %d) after failure", attempt)
            time.sleep(retry_delay)

        success = apprise.notify(title=title, body=body, attach=list(attach) if attach else None)
        if success:
            return True

    return False


def send_notifications(
    apprise,
    title: str,
    body: str,
    attach: Iterable[str] | None = None,
    delay: float = 0.0,
    retry_attempts: int = 1,
    retry_delay: float = 5.0,
) -> bool:
    LOGGER.info("Sending notification: %s", title)
    if not apprise or len(apprise.urls()) == 0:
        LOGGER.warning("No Apprise URLs configured; skipping notification")
        return False

    success = _notify_with_retries(apprise, title, body, attach, retry_attempts, retry_delay)
    if not success:
        LOGGER.error("Failed to send notification: %s", title)

    actual_delay = delay
    if delay > 0 and _has_discord_target(apprise):
        actual_delay = max(delay, 3.0)

    if actual_delay > 0:
        LOGGER.debug("Sleeping %.2fs before next notification", actual_delay)
        time.sleep(actual_delay)

    return success
