"""
FEATURE: amazon_pricing source — fetch all seller offers for an ASIN.

This provides full price intelligence: every third-party seller's price,
condition, shipping cost, and fulfillment method for a specific product.
Valuable for competitive analysis in the resale market.
"""

import logging
from typing import Dict, List, Optional

from scraper.client import OxylabsClient
from models import PricingOffer
import config

logger = logging.getLogger(__name__)


def get_pricing(
    asin: str,
    client: OxylabsClient = None,
) -> List[PricingOffer]:
    """
    Fetch all seller offers for a given ASIN using amazon_pricing source.
    Returns a list of PricingOffer objects (one per seller).
    """
    if client is None:
        client = OxylabsClient()

    # FEATURE: amazon_pricing source — all seller offers for an ASIN
    # FEATURE: parse: true — structured pricing data
    # FEATURE: geo_location — US market pricing
    payload = {
        "source": "amazon_pricing",
        "query": asin,
        "domain": config.SEARCH_DOMAIN,
        "parse": True,
        "geo_location": config.GEO_LOCATION,
    }

    logger.info(f"Fetching pricing for ASIN {asin}")
    response = client.realtime(payload)

    return _parse_pricing_response(response)


def get_pricing_batch(
    asins: List[str],
    client: OxylabsClient = None,
) -> Dict[str, List[PricingOffer]]:
    """
    Fetch pricing for multiple ASINs.
    Returns dict keyed by ASIN with list of offers.
    """
    if client is None:
        client = OxylabsClient()

    results: Dict[str, List[PricingOffer]] = {}
    for asin in asins:
        try:
            offers = get_pricing(asin, client=client)
            results[asin] = offers
        except Exception as e:
            logger.warning(f"Failed to get pricing for ASIN {asin}: {e}")

    return results


def _parse_pricing_response(response: dict) -> List[PricingOffer]:
    """Parse Oxylabs pricing response into PricingOffer models."""
    offers = []
    try:
        content = response["results"][0]["content"]
        raw_offers = content.get("product_pricing", [])

        for item in raw_offers:
            offers.append(
                PricingOffer(
                    seller_name=item.get("seller_name"),
                    price=item.get("price"),
                    currency=item.get("currency"),
                    condition=item.get("condition"),
                    shipping_price=item.get("shipping_price"),
                    is_prime=item.get("is_prime", False),
                    is_fulfilled_by_amazon=item.get("is_fulfilled_by_amazon", False),
                )
            )
    except (KeyError, IndexError) as e:
        logger.warning(f"Failed to parse pricing response: {e}")

    return offers
