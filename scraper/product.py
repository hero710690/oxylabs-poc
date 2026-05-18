import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    Submits all jobs upfront, then polls all concurrently.
    batch_size controls how many jobs are submitted at once to avoid overwhelming the API.
    Returns dict keyed by ASIN for easy merging with search results.
    """
    if client is None:
        client = OxylabsClient()

    # FEATURE: Batch submission — submit all jobs concurrently, then poll all concurrently
    batches = [search_results[i:i + batch_size] for i in range(0, len(search_results), batch_size)]
    total_batches = len(batches)
    logger.info(f"Submitting {len(search_results)} jobs in {total_batches} batch(es), all concurrently...")

    jobs = []
    with ThreadPoolExecutor(max_workers=total_batches) as executor:
        futures = {executor.submit(_submit_jobs, client, batch): idx for idx, batch in enumerate(batches)}
        for future in as_completed(futures):
            try:
                jobs.extend(future.result())
            except Exception as e:
                logger.warning(f"Batch submission failed: {e}")

    logger.info(f"All {len(jobs)} jobs submitted, polling concurrently...")
    all_products = _poll_all_jobs(client, jobs)

    # Retry failed products (up to 2 attempts)
    failed = [r for r in search_results if r.asin not in all_products]
    retries = 0
    while failed and retries < 2:
        retries += 1
        logger.info(f"Retrying {len(failed)} failed products (attempt {retries}/2)")
        retry_jobs = _submit_jobs(client, failed)
        retry_products = _poll_all_jobs(client, retry_jobs)
        all_products.update(retry_products)
        failed = [r for r in failed if r.asin not in all_products]

    if failed:
        logger.warning(
            f"Product pages: {len(all_products)}/{len(search_results)} succeeded "
            f"({len(failed)} failed after retries)"
        )
    else:
        logger.info(f"Product pages: {len(all_products)}/{len(search_results)} succeeded")

    return all_products


def _submit_jobs(client: OxylabsClient, items: List[SearchResult]) -> list:
    """Submit async jobs for a list of search results concurrently. Returns list of {job_id, asin}."""
    def submit_one(item):
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
            "context": [{"key": "autoselect_variant", "value": True}],
        }
        job = client.async_submit(payload)
        return {"job_id": job["id"], "asin": item.asin}

    jobs = []
    with ThreadPoolExecutor(max_workers=len(items)) as executor:
        futures = {executor.submit(submit_one, item): item.asin for item in items}
        for future in as_completed(futures):
            asin = futures[future]
            try:
                jobs.append(future.result())
            except Exception as e:
                logger.warning(f"Failed to submit job for ASIN {asin}: {e}")
    return jobs


def _poll_all_jobs(client: OxylabsClient, jobs: list) -> Dict[str, ProductData]:
    """Poll all jobs concurrently and return results keyed by ASIN."""
    def poll_job(job_info: dict):
        result = _poll_until_done(
            client,
            job_info["job_id"],
            timeout=config.POLL_TIMEOUT,
            interval=config.POLL_INTERVAL,
        )
        asin = job_info["asin"]
        product = _parse_product_response(result, asin)
        if product and not product.specifications:
            logger.warning(f"ASIN {asin}: parsed OK but no product_details in response")
        return asin, product

    products: Dict[str, ProductData] = {}
    if not jobs:
        return products

    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        futures = {executor.submit(poll_job, j): j["asin"] for j in jobs}
        for future in as_completed(futures):
            asin = futures[future]
            try:
                asin, product = future.result()
                if product:
                    products[asin] = product
                else:
                    logger.warning(f"ASIN {asin}: _parse_product_response returned None")
            except Exception as e:
                logger.warning(f"Failed to get product data for ASIN {asin}: {e}", exc_info=True)

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


def _parse_product_response(response: dict, asin: str = "") -> Optional[ProductData]:
    """Parse Oxylabs product response into ProductData model."""
    try:
        content = response["results"][0]["content"]

        if not isinstance(content, dict):
            logger.warning(f"ASIN {asin}: unexpected content type {type(content).__name__}, raw: {str(content)[:300]}")
            return None

        # Extract delivery info as a readable string
        delivery_raw = content.get("delivery", [])
        delivery_str = None
        if delivery_raw and isinstance(delivery_raw, list):
            parts = []
            for d in delivery_raw:
                if not isinstance(d, dict):
                    continue
                dtype = d.get("type", "")
                date_val = d.get("date", {})
                date_by = date_val.get("by", "") if isinstance(date_val, dict) else ""
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
