import logging
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
    """
    if client is None:
        client = OxylabsClient()

    all_results: List[SearchResult] = []

    for page_num in range(1, pages + 1):
        if len(all_results) >= limit:
            break

        # FEATURE: amazon source with URL — scrape brand-filtered search results
        # FEATURE: parse: true — auto-parsed JSON output
        # FEATURE: geo_location — lock to US market
        payload = {
            "source": "amazon",
            "url": f"{config.SEARCH_URL}&page={page_num}",
            "parse": True,
            "geo_location": config.GEO_LOCATION,
        }

        logger.info(f"Searching page {page_num}/{pages}")
        response = client.realtime(payload)

        page_results = _parse_search_response(response["results"][0], len(all_results))
        all_results.extend(page_results)

    logger.info(f"Search returned {len(all_results)} results, using top {limit}")
    return all_results[:limit]


def _parse_search_response(page_result: dict, offset: int) -> List[SearchResult]:
    """Parse a single page result from Oxylabs search response."""
    results = []
    content = page_result["content"]["results"]

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
