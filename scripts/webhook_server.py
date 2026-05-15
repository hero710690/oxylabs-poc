"""
Webhook server for receiving Oxylabs callback notifications.

FEATURE: Callback URL — job completion notification.
When a job finishes, Oxylabs POSTs a notification here with a link to fetch results.
This server receives the notification and fetches the actual results.

Note: callback_url delivers a NOTIFICATION (not full results).
For full result delivery without polling, use storage_type + storage_url (S3/GCS).

Usage:
    uvicorn scripts.webhook_server:app --host 0.0.0.0 --port 8000

    For local development with public URL:
    ngrok http 8000
    → Use the ngrok URL as callback_url when submitting jobs
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, Request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Oxylabs Webhook Receiver")


@app.post("/webhooks/oxylabs")
async def receive_oxylabs_callback(request: Request):
    """
    Receive job completion notification from Oxylabs.

    Oxylabs POSTs a notification containing:
    - Job metadata (id, status)
    - _links with a "results" URL to fetch actual data

    This handler receives the notification and fetches the full results.
    """
    data = await request.json()

    job_id = data.get("id", "unknown")
    status = data.get("status")

    logger.info(f"Received callback notification for job {job_id} (status: {status})")

    if status != "done":
        logger.warning(f"Job {job_id} status is '{status}', skipping")
        return {"status": "ignored", "reason": f"job status is {status}"}

    # Fetch actual results using the link from the notification
    results_url = None
    links = data.get("_links", [])
    for link in links:
        if link.get("rel") == "results":
            results_url = link.get("href")
            break

    if results_url:
        import requests as http_requests
        logger.info(f"Fetching results from {results_url}")
        resp = http_requests.get(
            results_url,
            auth=(config.OXYLABS_USERNAME, config.OXYLABS_PASSWORD),
            timeout=60,
        )
        resp.raise_for_status()
        results_data = resp.json()
    else:
        logger.warning(f"No results link in callback, saving notification only")
        results_data = data

    # Save results to output directory
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    filepath = os.path.join(config.OUTPUT_DIR, f"callback_{job_id}_{timestamp}.json")

    with open(filepath, "w") as f:
        json.dump(results_data, f, indent=2, default=str)

    logger.info(f"Saved results to {filepath}")
    return {"status": "received", "job_id": job_id, "saved_to": filepath}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
