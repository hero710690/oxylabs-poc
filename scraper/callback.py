"""
FEATURE: Async/Callback mode — alternative to polling.

Instead of polling for job completion, Oxylabs can POST results directly
to a callback URL when the job finishes. This is more efficient for
production workloads as it eliminates polling overhead.

Usage:
    1. Set up a webhook endpoint (e.g., Flask/FastAPI server)
    2. Pass callback_url in the payload
    3. Oxylabs POSTs results to your endpoint when done

This module is a documented alternative — the main PoC uses polling mode.
See scraper/product.py for the primary implementation.
"""

import logging
from scraper.client import OxylabsClient
import config

logger = logging.getLogger(__name__)


def submit_with_callback(
    asin: str,
    callback_url: str,
    client: OxylabsClient = None,
) -> dict:
    """
    Submit an async product scrape with a callback URL.

    FEATURE: Async/Callback mode
    Instead of polling, Oxylabs will POST results to callback_url when done.

    Example callback_url: "https://your-server.com/webhooks/oxylabs"

    The callback payload will contain the same structure as a poll response
    with status "done" and the results array.
    """
    if client is None:
        client = OxylabsClient()

    # FEATURE: callback_url — Oxylabs sends results to this URL when job completes
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


# Example Flask webhook handler (for documentation purposes):
#
# from flask import Flask, request
#
# app = Flask(__name__)
#
# @app.route("/webhooks/oxylabs", methods=["POST"])
# def handle_oxylabs_callback():
#     data = request.json
#     job_id = data["id"]
#     results = data["results"]
#     # Process and store results...
#     return "", 200
