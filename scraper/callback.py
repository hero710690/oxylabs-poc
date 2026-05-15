"""
FEATURE: Async/Callback mode + Oxylabs Scheduler.

Two related features:
1. Callback mode: Instead of polling, Oxylabs POSTs results to your endpoint.
2. Scheduler: Oxylabs runs jobs on a recurring schedule and delivers via callback.

Combined, these eliminate both polling AND cron — Oxylabs handles everything.

Usage:
    1. Start the webhook server: uvicorn webhook_server:app --port 8000
    2. Expose publicly (dev): ngrok http 8000
    3. Submit a scheduled job: python -c "from scraper.callback import submit_scheduled; submit_scheduled('https://your-ngrok-url/webhooks/oxylabs')"

See webhook_server.py for the receiving endpoint.
"""

import logging
from typing import List

from scraper.client import OxylabsClient
import config

logger = logging.getLogger(__name__)


def submit_with_callback(
    asin: str,
    callback_url: str,
    client: OxylabsClient = None,
) -> dict:
    """
    FEATURE: Async/Callback mode
    Submit a single product scrape with callback delivery.
    """
    if client is None:
        client = OxylabsClient()

    payload = {
        "source": "amazon_product",
        "query": asin,
        "domain": config.SEARCH_DOMAIN,
        "parse": True,
        "geo_location": config.GEO_LOCATION,
        "callback_url": callback_url,
    }

    logger.info(f"Submitting ASIN {asin} with callback to {callback_url}")
    return client.async_submit(payload)


def submit_scheduled(
    callback_url: str,
    client: OxylabsClient = None,
) -> dict:
    """
    FEATURE: Oxylabs Scheduler — recurring job with callback delivery.

    Submits a search job that Oxylabs will run on a schedule (every hour)
    and POST results to the callback URL. No cron, no polling needed.

    See: https://developers.oxylabs.io/products/web-scraper-api/features/scheduler
    """
    if client is None:
        client = OxylabsClient()

    # FEATURE: Oxylabs Scheduler — schedule_at with recurring interval
    # FEATURE: callback_url — results delivered via webhook
    payload = {
        "source": "amazon_search",
        "query": config.SEARCH_QUERY,
        "domain": config.SEARCH_DOMAIN,
        "parse": True,
        "geo_location": config.GEO_LOCATION,
        "callback_url": callback_url,
        "schedule": {
            "frequency": "hourly",
        },
    }

    logger.info(f"Submitting scheduled job (hourly) with callback to {callback_url}")
    response = client.async_submit(payload)
    logger.info(f"Scheduled job created: {response.get('id')}")
    return response
