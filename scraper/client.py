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
