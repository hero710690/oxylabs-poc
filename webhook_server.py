"""
Webhook server for receiving Oxylabs Scheduler callback results.

FEATURE: Oxylabs Scheduler + Callback URL
Instead of running our own cron/scheduler, Oxylabs can run jobs on a schedule
and POST results directly to this endpoint when done.

Usage:
    uvicorn webhook_server:app --host 0.0.0.0 --port 8000

    For local development with public URL:
    ngrok http 8000
    → Use the ngrok URL as callback_url when submitting jobs
"""

import json
import logging
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Request

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
    Receive scraping results from Oxylabs via callback.

    Oxylabs POSTs the same JSON structure as their async results endpoint:
    {
        "id": "job_id",
        "status": "done",
        "results": [{"content": {...}}]
    }
    """
    data = await request.json()

    job_id = data.get("id", "unknown")
    status = data.get("status")
    results = data.get("results", [])

    logger.info(f"Received callback for job {job_id} (status: {status}, results: {len(results)})")

    if status != "done":
        logger.warning(f"Job {job_id} status is '{status}', skipping")
        return {"status": "ignored", "reason": f"job status is {status}"}

    # Save results to output directory
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    filepath = os.path.join(config.OUTPUT_DIR, f"callback_{job_id}_{timestamp}.json")

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info(f"Saved callback results to {filepath}")
    return {"status": "received", "job_id": job_id, "saved_to": filepath}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
