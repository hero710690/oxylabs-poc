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
    Phase 1: Search Amazon for iPhones using paginated requests.
    Returns up to `limit` SearchResult objects with position and sponsored metadata.
    """
    if client is None:
        client = OxylabsClient()

    all_results: List[SearchResult] = []

    for page_num in range(1, pages + 1):
        if len(all_results) >= limit:
            break

        # FEATURE: amazon_search source — structured search results
        # FEATURE: parse: true — auto-parsed JSON output
        # FEATURE: geo_location — lock to US market
        # FEATURE: Pagination (start_page) — collect across multiple pages
        payload = {
            "source": "amazon_search",
            "query": config.SEARCH_QUERY,
            "domain": config.SEARCH_DOMAIN,
            "start_page": page_num,
            "parse": True,
            "geo_location": config.GEO_LOCATION,
        }

        logger.info(f"Searching page {page_num}/{pages}")
        response = client.realtime(payload)

        page_results = _parse_search_response(response, len(all_results))
        all_results.extend(page_results)

    return all_results[:limit]


def _parse_search_response(response: dict, offset: int) -> List[SearchResult]:
    """Parse Oxylabs search response into SearchResult models."""
    results = []
    content = response["results"][0]["content"]["results"]

    # Parse organic results
    for item in content.get("organic", []):
        results.append(
            SearchResult(
                position=offset + len(results) + 1,
                asin=item["asin"],
                title=item.get("title", ""),
                price=item.get("price"),
                currency=item.get("currency"),
                is_sponsored=False,
                url=f"https://www.amazon.com/dp/{item['asin']}",
            )
        )

    # Parse sponsored/paid results
    for item in content.get("paid", []):
        results.append(
            SearchResult(
                position=offset + len(results) + 1,
                asin=item["asin"],
                title=item.get("title", ""),
                price=item.get("price"),
                currency=item.get("currency"),
                is_sponsored=True,
                url=f"https://www.amazon.com/dp/{item['asin']}",
            )
        )

    return results
