import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from scraper.client import OxylabsClient
from models import SearchResult
import config

logger = logging.getLogger(__name__)


def search_iphones(
    client: OxylabsClient = None,
    pages: int = config.SEARCH_PAGES,
    limit: int = config.RESULTS_LIMIT,
) -> List[SearchResult]:
    """
    Phase 1: Search Amazon for iPhones using brand-filtered URL.
    Uses the `amazon` source with a pre-filtered URL (Cell Phones + Apple brand)
    to ensure only actual iPhone listings are returned — no accessories, no other brands.
    All pages are fetched concurrently.
    """
    if client is None:
        client = OxylabsClient()

    def fetch_page(page_num: int):
        payload = {
            "source": "amazon",
            "url": f"{config.SEARCH_URL}&page={page_num}",
            "parse": True,
            "geo_location": config.GEO_LOCATION,
        }
        logger.info(f"Searching page {page_num}/{pages}")
        for attempt in range(3):
            response = client.realtime(payload)
            result = response["results"][0]
            results_content = result.get("content", {}).get("results", None)
            # Valid response: results is a non-empty dict with organic/paid keys
            if isinstance(results_content, dict) and results_content:
                return page_num, result
            logger.warning(f"Page {page_num} returned empty/malformed content (attempt {attempt + 1}/3), retrying...")
        return page_num, result  # return last attempt regardless

    # Fetch all pages concurrently
    page_results = {}
    with ThreadPoolExecutor(max_workers=pages) as executor:
        futures = {executor.submit(fetch_page, p): p for p in range(1, pages + 1)}
        for future in as_completed(futures):
            try:
                page_num, result = future.result()
                page_results[page_num] = result
            except Exception as e:
                logger.warning(f"Page {futures[future]} failed: {e}")

    # Merge in page order to preserve position ordering
    all_results: List[SearchResult] = []
    for page_num in sorted(page_results):
        offset = len(all_results)
        all_results.extend(_parse_search_response(page_results[page_num], offset))

    # Deduplicate by ASIN, keeping first occurrence (lowest position)
    seen = set()
    deduped = []
    for r in all_results:
        if r.asin not in seen:
            seen.add(r.asin)
            deduped.append(r)

    if len(deduped) < len(all_results):
        logger.info(f"Removed {len(all_results) - len(deduped)} duplicate ASINs across pages")

    # Re-assign sequential positions after dedup
    for idx, r in enumerate(deduped, start=1):
        r.position = idx

    logger.info(f"Search returned {len(deduped)} unique results, using top {limit}")
    return deduped[:limit]


def _parse_search_response(page_result: dict, offset: int) -> List[SearchResult]:
    """Parse a single page result from Oxylabs search response."""
    results = []
    content = page_result["content"]["results"]

    # Oxylabs occasionally returns results as an empty list instead of a dict
    if isinstance(content, list):
        if not content:
            logger.warning(f"Page returned empty results list, skipping")
            return results
        # Non-empty list — unexpected, log and skip
        logger.warning(f"Unexpected non-empty list for results, skipping: {str(content)[:200]}")
        return results

    # Combine organic and sponsored, sort by actual page position
    organic = content.get("organic", [])
    paid = content.get("paid", [])

    all_items = [(item, False) for item in organic] + [(item, True) for item in paid]
    all_items.sort(key=lambda x: x[0].get("pos", 9999))

    for idx, (item, is_paid) in enumerate(all_items, start=1):
        results.append(
            SearchResult(
                position=offset + idx,
                asin=item["asin"],
                title=item.get("title", ""),
                price=item.get("price"),
                currency=item.get("currency"),
                is_sponsored=is_paid,
                is_prime=item.get("is_prime", False),
                rating=item.get("rating"),
                reviews_count=item.get("reviews_count"),
                is_best_seller=item.get("best_seller", False),
                is_amazons_choice=item.get("is_amazons_choice", False),
                sales_volume=item.get("sales_volume"),
                url=f"https://www.amazon.com/dp/{item['asin']}",
            )
        )

    return results
