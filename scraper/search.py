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
        response = client.realtime(payload)
        return page_num, response["results"][0]

    # Fetch pages, retrying failed ones until we have enough results
    page_results = {}
    next_page = pages + 1
    pages_to_fetch = list(range(1, pages + 1))

    while len([r for results in page_results.values() for r in results]) < limit:
        with ThreadPoolExecutor(max_workers=len(pages_to_fetch)) as executor:
            futures = {executor.submit(fetch_page, p): p for p in pages_to_fetch}
            for future in as_completed(futures):
                try:
                    page_num, result = future.result()
                    parsed = _parse_search_response(result, 0)  # offset applied later
                    page_results[page_num] = parsed
                except Exception as e:
                    logger.warning(f"Page {futures[future]} failed: {e}")

        # Check if any pages returned empty (malformed response) — fetch extras
        failed_pages = [p for p in pages_to_fetch if p not in page_results or not page_results[p]]
        total_results = sum(len(r) for r in page_results.values())

        if not failed_pages or total_results >= limit:
            break

        logger.info(f"Fetching extra page {next_page} to replace {len(failed_pages)} failed page(s)")
        pages_to_fetch = [next_page]
        next_page += 1

        if next_page > pages + 5:  # safety limit
            break

    # Merge in page order with correct offsets
    all_results: List[SearchResult] = []
    for page_num in sorted(page_results):
        offset = len(all_results)
        for item in page_results[page_num]:
            item.position = offset + (item.position)
        all_results.extend(page_results[page_num])

    # Re-assign sequential positions
    for idx, item in enumerate(all_results, start=1):
        item.position = idx

    logger.info(f"Search returned {len(all_results)} results, using top {limit}")
    return all_results[:limit]


def _parse_search_response(page_result: dict, offset: int) -> List[SearchResult]:
    """Parse a single page result from Oxylabs search response."""
    results = []
    content = page_result["content"]["results"]

    if not isinstance(content, dict):
        logger.warning(f"Unexpected search results type: {type(content)}, skipping page")
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
