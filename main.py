import json
import logging
import os
from datetime import datetime, timezone
from typing import List

from apscheduler.schedulers.blocking import BlockingScheduler

from scraper.client import OxylabsClient
from scraper.search import search_iphones
from scraper.product import scrape_products
from scraper.pricing import get_pricing
from models import SearchResult, ProductData, ScrapedProduct
from typing import Dict
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_scrape_job() -> List[ScrapedProduct]:
    """Execute the full scraping pipeline: search → product pages → merge."""
    logger.info("=== Starting scrape job ===")
    client = OxylabsClient()

    # Phase 1: Search
    logger.info("Phase 1: Searching for top iPhone listings...")
    search_results = search_iphones(client=client)
    logger.info(f"Found {len(search_results)} listings from search")

    # Phase 2: Product pages
    logger.info("Phase 2: Scraping individual product pages...")
    product_data = scrape_products(search_results, client=client)
    logger.info(f"Got detailed data for {len(product_data)}/{len(search_results)} product pages")

    # Merge search metadata with product data
    merged = _merge_results(search_results, product_data)
    if len(product_data) == len(search_results):
        logger.info(f"All {len(merged)} products have full detail")
    else:
        logger.info(
            f"Output: {len(merged)} products total "
            f"({len(product_data)} with full detail, "
            f"{len(merged) - len(product_data)} with search-level data)"
        )

    # Phase 3: Pricing for top 5 products (demo of amazon_pricing source)
    logger.info("Phase 3: Fetching seller pricing for top 5 listings...")
    top_asins = [r.asin for r in search_results[:5]]
    for asin in top_asins:
        try:
            offers = get_pricing(asin, client=client)
            for product in merged:
                if product.asin == asin:
                    product.pricing_offers = offers
                    break
            logger.info(f"  ASIN {asin}: {len(offers)} seller offers")
        except Exception as e:
            logger.warning(f"  ASIN {asin}: pricing failed - {e}")

    return merged


def _merge_results(
    search_results: List[SearchResult],
    product_data: Dict[str, ProductData],
) -> List[ScrapedProduct]:
    """Merge search-level metadata with product page data.
    Always returns all search results — uses product data when available,
    falls back to search-level data otherwise."""
    merged = []

    for search in search_results:
        product = product_data.get(search.asin)
        if product:
            merged.append(
                ScrapedProduct(
                    position=search.position,
                    asin=search.asin,
                    title=product.title or search.title,
                    price=product.price or search.price,
                    currency=product.currency or search.currency,
                    is_sponsored=search.is_sponsored,
                    is_prime=product.is_prime,
                    description=product.description,
                    specifications=product.specifications,
                    delivery=product.delivery,
                    rating=product.rating or search.rating,
                    reviews_count=product.reviews_count or search.reviews_count,
                    sales_rank=product.sales_rank,
                    brand=product.brand,
                    coupon=product.coupon,
                    is_best_seller=search.is_best_seller,
                    is_amazons_choice=search.is_amazons_choice,
                    sales_volume=search.sales_volume,
                    url=search.url,
                )
            )
        else:
            merged.append(
                ScrapedProduct(
                    position=search.position,
                    asin=search.asin,
                    title=search.title,
                    price=search.price,
                    currency=search.currency,
                    is_sponsored=search.is_sponsored,
                    is_prime=search.is_prime,
                    description=None,
                    specifications=None,
                    delivery=None,
                    rating=search.rating,
                    reviews_count=search.reviews_count,
                    is_best_seller=search.is_best_seller,
                    is_amazons_choice=search.is_amazons_choice,
                    sales_volume=search.sales_volume,
                    url=search.url,
                )
            )

    return merged


def save_results(products: List[ScrapedProduct], output_dir: str = config.OUTPUT_DIR) -> str:
    """Save scraped products to a timestamped JSON file."""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"iphones_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    price_unavailable = sum(1 for p in products if not p.price or p.price == 0)

    output = {
        "metadata": {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_products": len(products),
            "products_with_price": len(products) - price_unavailable,
            "price_unavailable": price_unavailable,
            "query": config.SEARCH_QUERY,
            "geo_location": config.GEO_LOCATION,
            "note": "Products with price 0 are listings where Amazon either hides pricing behind 'See all buying options' (e.g., carrier-locked phones, SIM-free imports) or are currently unavailable. These still appear in Amazon's search rankings.",
        },
        "products": [p.model_dump(mode="json") for p in products],
    }

    with open(filepath, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"Results saved to {filepath}")
    return filepath


def scheduled_job():
    """Wrapper for the scheduler — runs the pipeline and saves output."""
    try:
        results = run_scrape_job()
        save_results(results)
        logger.info(f"=== Job complete: {len(results)} products scraped ===")
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)


def main():
    """Entry point: run once immediately, then schedule hourly."""
    import argparse

    parser = argparse.ArgumentParser(description="Oxylabs Amazon iPhone Scraper PoC")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no scheduler)")
    args = parser.parse_args()

    logger.info("Oxylabs PoC — Amazon iPhone Scraper")

    if args.once:
        logger.info("Single run mode (--once)")
        scheduled_job()
    else:
        logger.info("Running initial scrape...")
        scheduled_job()
        logger.info("Starting hourly scheduler...")
        scheduler = BlockingScheduler()
        scheduler.add_job(scheduled_job, "interval", hours=1)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
