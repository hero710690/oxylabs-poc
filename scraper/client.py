import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

import config

logger = logging.getLogger(__name__)


class OxylabsClient:
    """Low-level wrapper around Oxylabs Web Scraper API."""

    def __init__(self, username: str = None, password: str = None):
        self.username = username or config.OXYLABS_USERNAME
        self.password = password or config.OXYLABS_PASSWORD
        self.auth = (self.username, self.password)

    # FEATURE: Realtime endpoint — synchronous request/response
    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=config.RETRY_BACKOFF_BASE),
        reraise=True,
    )
    def realtime(self, payload: dict) -> dict:
        """Send a synchronous request to the realtime endpoint."""
        logger.info(f"Realtime request: source={payload.get('source')}")
        response = requests.post(
            config.REALTIME_URL,
            json=payload,
            auth=self.auth,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    # FEATURE: Async endpoint — submit job for background processing
    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=config.RETRY_BACKOFF_BASE),
        reraise=True,
    )
    def async_submit(self, payload: dict) -> dict:
        """Submit an async job. Returns job metadata including ID."""
        logger.info(f"Async submit: source={payload.get('source')}")
        response = requests.post(
            config.ASYNC_URL,
            json=payload,
            auth=self.auth,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    # FEATURE: Async polling — check job status
    def async_poll(self, job_id: str) -> dict:
        """Poll for async job status/results."""
        url = f"{config.ASYNC_URL}/{job_id}"
        response = requests.get(url, auth=self.auth, timeout=30)
        response.raise_for_status()
        return response.json()

    # FEATURE: Async results retrieval — fetch completed job results
    def async_get_results(self, job_id: str) -> dict:
        """Fetch results for a completed async job."""
        url = f"{config.ASYNC_URL}/{job_id}/results"
        response = requests.get(url, auth=self.auth, timeout=60)
        response.raise_for_status()
        return response.json()

    # FEATURE: Oxylabs Scheduler — CRUD for recurring scheduled jobs
    SCHEDULES_URL = "https://data.oxylabs.io/v1/schedules"

    def create_schedule(self, payload: dict) -> dict:
        """Create a scheduled job on Oxylabs Scheduler."""
        logger.info(f"Creating schedule: cron={payload.get('cron')}")
        response = requests.post(self.SCHEDULES_URL, json=payload, auth=self.auth, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_schedule(self, schedule_id: str) -> dict:
        """Fetch a schedule by ID."""
        response = requests.get(f"{self.SCHEDULES_URL}/{schedule_id}", auth=self.auth, timeout=30)
        response.raise_for_status()
        return response.json()

    def pause_schedule(self, schedule_id: str) -> None:
        """Pause (deactivate) a schedule."""
        response = requests.put(
            f"{self.SCHEDULES_URL}/{schedule_id}/state",
            json={"active": False},
            auth=self.auth,
            timeout=30,
        )
        response.raise_for_status()

    def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule."""
        response = requests.delete(f"{self.SCHEDULES_URL}/{schedule_id}", auth=self.auth, timeout=30)
        response.raise_for_status()
