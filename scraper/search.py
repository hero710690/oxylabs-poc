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

    # Fetch all pages concurrently
    page_results: dict[int, list] = {}
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

    for item, is_paid in all_items:
        results.append(
            SearchResult(
                position=offset + item.get("pos", len(results) + 1),
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
