import logging
import time
from typing import Dict, List, Optional

from scraper.client import OxylabsClient
from models import SearchResult, ProductData
import config

logger = logging.getLogger(__name__)


def scrape_products(
    search_results: List[SearchResult],
    client: OxylabsClient = None,
    batch_size: int = config.BATCH_SIZE,
) -> Dict[str, ProductData]:
    """
    Phase 2: Scrape individual product pages using async/polling mode.
    Submits requests in batches, polls for completion.
    Returns dict keyed by ASIN for easy merging with search results.
    """
    if client is None:
        client = OxylabsClient()

    all_products: Dict[str, ProductData] = {}

    # FEATURE: Batch submission — process products in chunks
    for i in range(0, len(search_results), batch_size):
        batch = search_results[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(search_results) + batch_size - 1) // batch_size
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} products)")

        batch_products = _process_batch(client, batch)
        all_products.update(batch_products)

    logger.info(
        f"Product pages: {len(all_products)}/{len(search_results)} succeeded "
        f"({len(search_results) - len(all_products)} will use search-level fallback)"
    )
    return all_products


def _process_batch(client: OxylabsClient, batch: List[SearchResult]) -> Dict[str, ProductData]:
    """Submit a batch of product requests and poll for results."""
    jobs = []

    for item in batch:
        # FEATURE: amazon_product source — individual product page data
        # FEATURE: parse: true — structured auto-parsed output
        # FEATURE: geo_location — US market
        # FEATURE: Async/Polling mode — non-blocking product scraping
        # FEATURE: context/autoselect_variant — accurate buybox pricing for variant products
        payload = {
            "source": "amazon_product",
            "query": item.asin,
            "domain": config.SEARCH_DOMAIN,
            "parse": True,
            "geo_location": config.GEO_LOCATION,
            "context": [
                {"key": "autoselect_variant", "value": True},
            ],
        }

        try:
            job = client.async_submit(payload)
            jobs.append({"job_id": job["id"], "asin": item.asin})
        except Exception as e:
            logger.warning(f"Failed to submit job for ASIN {item.asin}: {e}")

    # Poll all jobs for completion
    products: Dict[str, ProductData] = {}
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
                products[job_info["asin"]] = product
        except Exception as e:
            logger.warning(f"Failed to get product data for ASIN {job_info['asin']}: {e}")

    return products


def _poll_until_done(
    client: OxylabsClient,
    job_id: str,
    timeout: int = config.POLL_TIMEOUT,
    interval: int = config.POLL_INTERVAL,
) -> dict:
    """Poll an async job until status is 'done', then fetch results."""
    start_time = time.time()

    while True:
        result = client.async_poll(job_id)
        status = result.get("status")

        if status == "done":
            # FEATURE: Async results retrieval — separate endpoint for job results
            return client.async_get_results(job_id)
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

        # Extract delivery info as a readable string
        delivery_raw = content.get("delivery", [])
        delivery_str = None
        if delivery_raw and isinstance(delivery_raw, list):
            parts = []
            for d in delivery_raw:
                dtype = d.get("type", "")
                date_by = d.get("date", {}).get("by", "")
                parts.append(f"{dtype} {date_by}".strip())
            delivery_str = " | ".join(parts) if parts else None

        # Description can sometimes be a list (image URLs) instead of string
        description = content.get("description")
        if isinstance(description, list):
            description = None

        return ProductData(
            title=content.get("title", "Unknown"),
            price=content.get("price"),
            currency=content.get("currency"),
            description=description,
            specifications=content.get("product_details"),
            is_prime=content.get("is_prime_eligible", False),
            delivery=delivery_str,
            rating=content.get("rating"),
            reviews_count=content.get("reviews_count"),
            sales_rank=content.get("sales_rank"),
            brand=content.get("brand"),
            coupon=content.get("coupon") or None,
        )
    except (KeyError, IndexError) as e:
        logger.warning(f"Failed to parse product response: {e}")
        return None
