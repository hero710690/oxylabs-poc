"""
FEATURE: Async/Callback + Oxylabs Scheduler + Cloud Storage delivery.

Three features that combine for a fully managed pipeline:

1. Callback URL: Notification when a job completes (not full results).
   Your server receives a ping with a link — you then GET the results.

2. Cloud Storage (storage_type + storage_url): Full result delivery to your
   S3/GCS bucket. No polling, no fetching — data lands in your bucket.

3. Scheduler: Oxylabs runs jobs on a recurring cron schedule.

Best combo for production:
    Scheduler + Cloud Storage = Oxylabs handles timing + scraping + delivery.
    TechNovaAI just reads results from their own S3 bucket.

Usage (callback mode — notification + fetch):
    1. Start webhook server: uvicorn webhook_server:app --port 8000
    2. Submit job with callback_url
    3. Receive notification, then GET results from the link provided

Usage (scheduler + cloud storage — fully managed):
    1. Create schedule with storage_type + storage_url
    2. Results appear in your S3 bucket every hour
    3. No server, no polling needed

See webhook_server.py for the callback notification receiver.
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
    callback_url: str = None,
    storage_type: str = None,
    storage_url: str = None,
    end_time: str = "2027-01-01 00:00:00",
    client: OxylabsClient = None,
) -> dict:
    """
    FEATURE: Oxylabs Scheduler — fully managed recurring pipeline.

    Creates a scheduled job that Oxylabs runs every hour.
    Results can be delivered via:
    - callback_url: notification ping (you still fetch results via GET)
    - storage_type + storage_url: full results pushed to your S3/GCS bucket

    Endpoint: POST https://data.oxylabs.io/v1/schedules
    See: https://developers.oxylabs.io/products/web-scraper-api/features/scheduler

    Args:
        callback_url: Webhook URL for job-done notification
        storage_type: "s3", "gcs", or "s3_compatible"
        storage_url: Bucket path (e.g., "my-bucket/oxylabs-results")
        end_time: When the schedule expires (format: "YYYY-MM-DD HH:MM:SS")
    """
    if client is None:
        client = OxylabsClient()

    # FEATURE: Oxylabs Scheduler — cron + items + end_time
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

    # FEATURE: callback_url — notification when job completes
    if callback_url:
        payload["callback_url"] = callback_url

    # FEATURE: Cloud Storage delivery — results pushed directly to client's bucket
    if storage_type and storage_url:
        payload["items"][0]["storage_type"] = storage_type
        payload["items"][0]["storage_url"] = storage_url

    logger.info(f"Creating scheduled job (hourly until {end_time})")
    response = client.create_schedule(payload)
    logger.info(f"Schedule created: {response}")
    return response
