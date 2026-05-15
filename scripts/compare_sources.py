"""
Compare amazon_search vs amazon (URL) source for iPhone search results.

Demonstrates why we chose the URL-based approach for the production pipeline:
- amazon_search: simpler, supports `pages` param, but can't filter by brand
- amazon (URL): precise brand filtering, zero wasted requests, client saves money

Both return structured JSON with organic vs sponsored separation.

Usage:
    python scripts/compare_sources.py
"""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.client import OxylabsClient
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def search_with_amazon_search(client: OxylabsClient) -> dict:
    """Use amazon_search source with category_id context."""
    payload = {
        "source": "amazon_search",
        "query": config.SEARCH_QUERY,
        "domain": config.SEARCH_DOMAIN,
        "start_page": 1,
        "pages": 1,
        "parse": True,
        "geo_location": config.GEO_LOCATION,
        "context": [
            {"key": "category_id", "value": "7072561011"},
        ],
    }

    logger.info("amazon_search: Fetching page 1 with category_id filter...")
    response = client.realtime(payload)
    return response["results"][0]["content"]["results"]


def search_with_amazon_url(client: OxylabsClient) -> dict:
    """Use amazon source with brand-filtered URL."""
    payload = {
        "source": "amazon",
        "url": f"{config.SEARCH_URL}&page=1",
        "parse": True,
        "geo_location": config.GEO_LOCATION,
    }

    logger.info("amazon (URL): Fetching page 1 with brand filter...")
    response = client.realtime(payload)
    return response["results"][0]["content"]["results"]


def analyze_results(results: dict, source_name: str):
    """Analyze organic vs sponsored and non-iPhone contamination."""
    organic = results.get("organic", [])
    paid = results.get("paid", [])
    all_items = organic + paid

    non_iphone = [r for r in all_items if "iphone" not in r.get("title", "").lower()]

    print(f"\n{'=' * 60}")
    print(f"  Source: {source_name}")
    print(f"{'=' * 60}")
    print(f"  Organic results: {len(organic)}")
    print(f"  Sponsored (paid) results: {len(paid)}")
    print(f"  Total: {len(all_items)}")
    print(f"  Non-iPhone contamination: {len(non_iphone)}")

    if non_iphone:
        print(f"\n  Non-iPhone products (wasted requests):")
        for r in non_iphone:
            print(f"    - {r.get('title', '')[:65]}")

    print(f"\n  Sample organic results:")
    for r in organic[:3]:
        print(f"    #{r.get('pos', '?')} {r.get('title', '')[:60]}")
        print(f"       Price: ${r.get('price', 'N/A')} | Prime: {r.get('is_prime', 'N/A')}")

    if paid:
        print(f"\n  Sample sponsored results:")
        for r in paid[:2]:
            print(f"    [SPONSORED] {r.get('title', '')[:55]}")
            print(f"       Price: ${r.get('price', 'N/A')} | Prime: {r.get('is_prime', 'N/A')}")


def main():
    client = OxylabsClient()

    print("\n" + "=" * 60)
    print("  Comparing Oxylabs Sources for iPhone Search")
    print("=" * 60)

    # Source 1: amazon_search
    results_search = search_with_amazon_search(client)
    analyze_results(results_search, "amazon_search (+ category_id context)")

    # Source 2: amazon with URL
    results_url = search_with_amazon_url(client)
    analyze_results(results_url, "amazon (URL with brand filter)")

    # Summary
    organic_search = results_search.get("organic", [])
    paid_search = results_search.get("paid", [])
    all_search = organic_search + paid_search
    non_iphone_search = len([r for r in all_search if "iphone" not in r.get("title", "").lower()])

    organic_url = results_url.get("organic", [])
    paid_url = results_url.get("paid", [])
    all_url = organic_url + paid_url
    non_iphone_url = len([r for r in all_url if "iphone" not in r.get("title", "").lower()])

    print(f"\n{'=' * 60}")
    print(f"  COMPARISON SUMMARY")
    print(f"{'=' * 60}")
    print(f"  {'Metric':<30} {'amazon_search':<18} {'amazon (URL)':<18}")
    print(f"  {'-' * 66}")
    print(f"  {'Organic results':<30} {len(organic_search):<18} {len(organic_url):<18}")
    print(f"  {'Sponsored results':<30} {len(paid_search):<18} {len(paid_url):<18}")
    print(f"  {'Non-iPhone (wasted)':<30} {non_iphone_search:<18} {non_iphone_url:<18}")
    print(f"  {'Brand filtering':<30} {'No':<18} {'Yes (Apple)':<18}")
    print(f"  {'pages param support':<30} {'Yes':<18} {'No':<18}")
    print()
    print("  Conclusion: amazon (URL) is preferred for production because it")
    print("  eliminates non-iPhone results at the source — zero wasted requests.")
    print("  amazon_search is simpler but returns accessories and other brands")
    print("  that the client pays for but doesn't need.")
    print()


if __name__ == "__main__":
    main()
