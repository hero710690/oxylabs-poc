"""
Generate an HTML report/dashboard from the latest scraper output.

Usage:
    python scripts/report.py                    # Uses latest output file
    python scripts/report.py output/file.json   # Uses specific file
"""

import json
import os
import sys
from datetime import datetime
from statistics import mean, median

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)
import config


def load_data(filepath: str = None) -> dict:
    """Load the most recent output JSON, or a specific file."""
    if filepath:
        with open(filepath) as f:
            return json.load(f)

    files = sorted(
        [f for f in os.listdir(config.OUTPUT_DIR) if f.startswith("iphones_") and f.endswith(".json")],
        reverse=True,
    )
    if not files:
        raise FileNotFoundError("No output files found in output/")

    with open(os.path.join(config.OUTPUT_DIR, files[0])) as f:
        return json.load(f)


def generate_report(data: dict) -> str:
    """Generate HTML report from scraped data."""
    products = data["products"]
    metadata = data["metadata"]

    prices = [p["price"] for p in products if p.get("price") and p["price"] > 0]
    prime_count = sum(1 for p in products if p.get("is_prime"))
    sponsored_count = sum(1 for p in products if p.get("is_sponsored"))
    best_seller_count = sum(1 for p in products if p.get("is_best_seller"))
    with_specs = sum(1 for p in products if p.get("specifications"))
    with_pricing = sum(1 for p in products if p.get("pricing_offers"))

    avg_price = mean(prices) if prices else 0
    med_price = median(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    # Rating distribution
    ratings = [p["rating"] for p in products if p.get("rating")]
    rating_45 = sum(1 for r in ratings if r >= 4.5)
    rating_40 = sum(1 for r in ratings if 4.0 <= r < 4.5)
    rating_35 = sum(1 for r in ratings if 3.5 <= r < 4.0)
    rating_below = sum(1 for r in ratings if r < 3.5)

    # Build product rows
    product_rows = ""
    for p in products:
        price_str = f"${p['price']:.2f}" if p.get("price") and p["price"] > 0 else "N/A"
        rating_str = f"{p['rating']:.1f}" if p.get("rating") else "—"
        reviews_str = f"{p['reviews_count']:,}" if p.get("reviews_count") else "—"
        badges = []
        if p.get("is_prime"):
            badges.append('<span class="badge badge-prime">Prime</span>')
        if p.get("is_sponsored"):
            badges.append('<span class="badge badge-sponsored">Sponsored</span>')
        if p.get("is_best_seller"):
            badges.append('<span class="badge badge-bestseller">Best Seller</span>')
        if p.get("is_amazons_choice"):
            badges.append('<span class="badge badge-choice">Amazon\'s Choice</span>')
        badges_str = " ".join(badges)

        offers_str = ""
        if p.get("pricing_offers"):
            offers_str = f'<span class="badge badge-offers">{len(p["pricing_offers"])} offers</span>'

        product_rows += f"""
        <tr>
            <td>{p['position']}</td>
            <td class="product-title">
                <a href="{p.get('url', '#')}" target="_blank">{p['title'][:60]}{'...' if len(p.get('title', '')) > 60 else ''}</a>
                <div class="badges">{badges_str} {offers_str}</div>
            </td>
            <td class="price">{price_str}</td>
            <td>{rating_str}</td>
            <td>{reviews_str}</td>
            <td>{p.get('brand', '—')}</td>
        </tr>"""

    # Build pricing section for products with offers
    pricing_section = ""
    products_with_pricing = [p for p in products if p.get("pricing_offers")]
    if products_with_pricing:
        pricing_rows = ""
        for p in products_with_pricing:
            offers = p["pricing_offers"]
            offer_prices = [o["price"] for o in offers if o.get("price")]
            price_range = f"${min(offer_prices):.2f} – ${max(offer_prices):.2f}" if offer_prices else "N/A"
            fba_count = sum(1 for o in offers if o.get("is_fulfilled_by_amazon"))
            pricing_rows += f"""
            <tr>
                <td><a href="{p.get('url', '#')}" target="_blank">{p['title'][:50]}...</a></td>
                <td>{len(offers)}</td>
                <td>{price_range}</td>
                <td>{fba_count}</td>
            </tr>"""

        pricing_section = f"""
        <div class="section">
            <h2>Pricing Intelligence (Top ASINs)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Sellers</th>
                        <th>Price Range</th>
                        <th>FBA Sellers</th>
                    </tr>
                </thead>
                <tbody>{pricing_rows}</tbody>
            </table>
        </div>"""

    # Build new listings section (no rating yet)
    no_rating_section = ""
    no_rating_products = [p for p in products if not p.get("rating")]
    if no_rating_products:
        no_rating_rows = ""
        for p in no_rating_products:
            price_str = f"${p['price']:.2f}" if p.get("price") and p["price"] > 0 else "N/A"
            no_rating_rows += f"""
            <tr>
                <td>{p['position']}</td>
                <td><a href="{p.get('url', '#')}" target="_blank">{p['title'][:60]}{'...' if len(p.get('title', '')) > 60 else ''}</a></td>
                <td class="price">{price_str}</td>
                <td>{p['asin']}</td>
            </tr>"""

        no_rating_section = f"""
        <div class="section">
            <h2>New Listings — No Reviews Yet ({len(no_rating_products)} products)</h2>
            <p style="color: #666; font-size: 0.85rem; margin-bottom: 1rem;">These products are too new to have accumulated ratings. Relevant for resale strategy — no social proof means less buyer confidence but also less competition.</p>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Product</th>
                        <th>Price</th>
                        <th>ASIN</th>
                    </tr>
                </thead>
                <tbody>{no_rating_rows}</tbody>
            </table>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iPhone Market Report — TechNovaAI</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
        header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        header p {{ opacity: 0.8; font-size: 0.9rem; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: white; border-radius: 8px; padding: 1.2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
        .stat-card .label {{ font-size: 0.75rem; text-transform: uppercase; color: #666; letter-spacing: 0.05em; }}
        .stat-card .value {{ font-size: 1.5rem; font-weight: 700; color: #1a1a2e; margin-top: 0.25rem; }}
        .stat-card .value.green {{ color: #10b981; }}
        .stat-card .value.blue {{ color: #3b82f6; }}
        .stat-card .value.orange {{ color: #f59e0b; }}
        .section {{ background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
        .section h2 {{ font-size: 1.2rem; margin-bottom: 1rem; color: #1a1a2e; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
        thead th {{ text-align: left; padding: 0.75rem; border-bottom: 2px solid #e5e7eb; color: #666; font-weight: 600; }}
        tbody td {{ padding: 0.75rem; border-bottom: 1px solid #f3f4f6; }}
        tbody tr:hover {{ background: #f9fafb; }}
        .product-title a {{ color: #3b82f6; text-decoration: none; }}
        .product-title a:hover {{ text-decoration: underline; }}
        .price {{ font-weight: 600; color: #10b981; }}
        .badges {{ margin-top: 0.25rem; }}
        .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; }}
        .badge-prime {{ background: #dbeafe; color: #1d4ed8; }}
        .badge-sponsored {{ background: #fef3c7; color: #92400e; }}
        .badge-bestseller {{ background: #d1fae5; color: #065f46; }}
        .badge-choice {{ background: #ede9fe; color: #5b21b6; }}
        .badge-offers {{ background: #fce7f3; color: #9d174d; }}
        .footer {{ text-align: center; color: #999; font-size: 0.8rem; margin-top: 2rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>iPhone Market Intelligence Report</h1>
            <p>Amazon US &bull; Top 100 Listings &bull; Scraped {metadata['scraped_at'][:19].replace('T', ' ')} UTC</p>
            <p>Query: "{metadata['query']}" &bull; Geo: {metadata['geo_location']} &bull; Powered by Oxylabs Web Scraper API</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Products</div>
                <div class="value">{len(products)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Avg Price</div>
                <div class="value green">${avg_price:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">Price Range</div>
                <div class="value">${min_price:.0f} – ${max_price:.0f}</div>
            </div>
            <div class="stat-card">
                <div class="label">Prime Eligible</div>
                <div class="value blue">{prime_count}%</div>
            </div>
            <div class="stat-card">
                <div class="label">Sponsored</div>
                <div class="value orange">{sponsored_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">Best Sellers</div>
                <div class="value">{best_seller_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">With Full Specs</div>
                <div class="value">{with_specs}</div>
            </div>
            <div class="stat-card">
                <div class="label">With Pricing Intel</div>
                <div class="value">{with_pricing}</div>
            </div>
        </div>

        <div class="section">
            <h2>Rating Distribution</h2>
            <div class="stats-grid">
                <div class="stat-card"><div class="label">4.5+ Stars</div><div class="value">{rating_45}</div></div>
                <div class="stat-card"><div class="label">4.0 – 4.4</div><div class="value">{rating_40}</div></div>
                <div class="stat-card"><div class="label">3.5 – 3.9</div><div class="value">{rating_35}</div></div>
                <div class="stat-card"><div class="label">Below 3.5</div><div class="value">{rating_below}</div></div>
            </div>
        </div>

        {pricing_section}

        {no_rating_section}

        <div class="section">
            <h2>All Products</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Product</th>
                        <th>Price</th>
                        <th>Rating</th>
                        <th>Reviews</th>
                        <th>Brand</th>
                    </tr>
                </thead>
                <tbody>{product_rows}</tbody>
            </table>
        </div>

        <div class="footer">
            <p>Generated by Oxylabs PoC &bull; TechNovaAI Market Intelligence &bull; {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC</p>
        </div>
    </div>
</body>
</html>"""

    return html


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    data = load_data(filepath)

    html = generate_report(data)

    output_path = os.path.join(config.OUTPUT_DIR, "report.html")
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Report generated: {output_path}")
    print(f"Open in browser: file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
