"""
FEATURE: Async/Callback mode + Oxylabs Scheduler.

Two separate features that solve different parts of the problem:

1. Callback mode (on regular async /v1/queries):
   - Eliminates polling — Oxylabs POSTs results to your endpoint when done.
   - You still need to trigger the job yourself (cron/scheduler).

2. Scheduler (/v1/schedules):
   - Eliminates cron — Oxylabs runs jobs on a recurring schedule.
   - You poll to retrieve results (callback_url is NOT supported on Scheduler).

Together with Docker+cron or a cloud scheduler, these cover all production needs.

Usage (callback mode):
    1. Start the webhook server: uvicorn webhook_server:app --port 8000
    2. Expose publicly (dev): ngrok http 8000
    3. Submit job with callback: python -c "from scraper.callback import submit_with_callback; submit_with_callback('B0CMPMY9ZZ', 'https://your-ngrok-url/webhooks/oxylabs')"

Usage (scheduler mode):
    1. Create schedule: python -c "from scraper.callback import submit_scheduled; submit_scheduled()"
    2. Poll for results periodically or retrieve via /v1/queries/{id}/results

See webhook_server.py for the callback receiving endpoint.
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
    end_time: str = "2027-01-01 00:00:00",
    client: OxylabsClient = None,
) -> dict:
    """
    FEATURE: Oxylabs Scheduler — recurring job execution.

    Creates a scheduled job that Oxylabs runs every hour automatically.
    Results are retrieved via polling (callback_url not supported on Scheduler).

    Endpoint: POST https://data.oxylabs.io/v1/schedules
    See: https://developers.oxylabs.io/products/web-scraper-api/features/scheduler

    Args:
        end_time: When the schedule expires (format: "YYYY-MM-DD HH:MM:SS")
    """
    if client is None:
        client = OxylabsClient()

    # FEATURE: Oxylabs Scheduler — cron expression + items + end_time
    payload = {
        "cron": "0 * * * *",  # Every hour at minute 0
        "end_time": end_time,
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

    logger.info(f"Creating scheduled job (hourly until {end_time})")
    response = client.create_schedule(payload)
    logger.info(f"Schedule created: {response}")
    return response
