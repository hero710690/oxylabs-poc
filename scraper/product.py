import logging
import time
from typing import List, Optional

from scraper.client import OxylabsClient
from models import SearchResult, ProductData
import config

logger = logging.getLogger(__name__)


def scrape_products(
    search_results: List[SearchResult],
    client: OxylabsClient = None,
    batch_size: int = config.BATCH_SIZE,
) -> List[ProductData]:
    """
    Phase 2: Scrape individual product pages using async/polling mode.
    Submits requests in batches, polls for completion, returns ProductData list.
    """
    if client is None:
        client = OxylabsClient()

    all_products: List[ProductData] = []

    # FEATURE: Batch submission — process products in chunks
    for i in range(0, len(search_results), batch_size):
        batch = search_results[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(search_results) + batch_size - 1) // batch_size
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} products)")

        batch_products = _process_batch(client, batch)
        all_products.extend(batch_products)

    logger.info(f"Scraped {len(all_products)}/{len(search_results)} products successfully")
    return all_products


def _process_batch(client: OxylabsClient, batch: List[SearchResult]) -> List[ProductData]:
    """Submit a batch of product requests and poll for results."""
    jobs = []

    for item in batch:
        # FEATURE: amazon_product source — individual product page data
        # FEATURE: parse: true — structured auto-parsed output
        # FEATURE: geo_location — US market
        # FEATURE: Async/Polling mode — non-blocking product scraping
        payload = {
            "source": "amazon_product",
            "query": item.asin,
            "domain": config.SEARCH_DOMAIN,
            "parse": True,
            "geo_location": config.GEO_LOCATION,
        }

        try:
            job = client.async_submit(payload)
            jobs.append({"job_id": job["id"], "search_result": item})
        except Exception as e:
            logger.warning(f"Failed to submit job for ASIN {item.asin}: {e}")

    # Poll all jobs for completion
    products = []
    for job_info in jobs:
        try:
            result = _poll_until_done(
                client,
                job_info["job_id"],
                timeout=config.POLL_TIMEOUT,
                interval=config.POLL_INTERVAL,
            )
            product = _parse_product_response(result)
            if product:
                products.append(product)
        except Exception as e:
            asin = job_info["search_result"].asin
            logger.warning(f"Failed to get product data for ASIN {asin}: {e}")

    return products


def _poll_until_done(
    client: OxylabsClient,
    job_id: str,
    timeout: int = config.POLL_TIMEOUT,
    interval: int = config.POLL_INTERVAL,
) -> dict:
    """Poll an async job until status is 'done' or timeout."""
    start_time = time.time()

    while True:
        result = client.async_poll(job_id)
        status = result.get("status")

        if status == "done":
            return result
        if status == "faulted":
            raise RuntimeError(f"Job {job_id} faulted: {result}")

        elapsed = time.time() - start_time
        if elapsed >= timeout:
            raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

        time.sleep(interval)


def _parse_product_response(response: dict) -> Optional[ProductData]:
    """Parse Oxylabs product response into ProductData model."""
    try:
        content = response["results"][0]["content"]
        return ProductData(
            title=content.get("title", "Unknown"),
            price=content.get("price"),
            currency=content.get("currency"),
            description=content.get("description"),
            specifications=content.get("specifications"),
            is_prime=content.get("is_prime", False),
            delivery=content.get("delivery_info"),
        )
    except (KeyError, IndexError) as e:
        logger.warning(f"Failed to parse product response: {e}")
        return None
