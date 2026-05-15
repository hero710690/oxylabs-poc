"""
FEATURE: Async/Callback mode + Oxylabs Scheduler.

Two features that combine to create a fully managed pipeline:

1. Callback mode: Oxylabs POSTs results to your endpoint when done (no polling).
2. Scheduler: Oxylabs runs jobs on a recurring cron schedule (no cron infrastructure).

Combined: Oxylabs handles BOTH timing AND delivery — zero infrastructure needed
beyond a webhook receiver.

Usage:
    1. Start the webhook server: uvicorn webhook_server:app --port 8000
    2. Expose publicly (dev): ngrok http 8000
    3. Create schedule with callback:
       python -c "from scraper.callback import submit_scheduled; submit_scheduled('https://your-ngrok-url/webhooks/oxylabs')"
    4. Done — Oxylabs runs hourly and POSTs results to your server.

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
    end_time: str = "2027-01-01 00:00:00",
    client: OxylabsClient = None,
) -> dict:
    """
    FEATURE: Oxylabs Scheduler + Callback — fully managed recurring pipeline.

    Creates a scheduled job that Oxylabs runs every hour and delivers
    results via callback URL. No cron, no polling needed.

    Endpoint: POST https://data.oxylabs.io/v1/schedules
    See: https://developers.oxylabs.io/products/web-scraper-api/features/scheduler

    Args:
        callback_url: Webhook URL to receive results
        end_time: When the schedule expires (format: "YYYY-MM-DD HH:MM:SS")
    """
    if client is None:
        client = OxylabsClient()

    # FEATURE: Oxylabs Scheduler — cron + items + end_time
    # FEATURE: callback_url — supported both at schedule level and per-item
    payload = {
        "cron": "0 * * * *",  # Every hour at minute 0
        "end_time": end_time,
        "callback_url": callback_url,
        "items": [
            {
                "source": "amazon_search",
                "query": config.SEARCH_QUERY,
                "domain": config.SEARCH_DOMAIN,
                "parse": True,
                "geo_location": config.GEO_LOCATION,
            },
        ],
    }

    logger.info(f"Creating scheduled job (hourly until {end_time}) with callback to {callback_url}")
    response = client.create_schedule(payload)
    logger.info(f"Schedule created: {response}")
    return response
