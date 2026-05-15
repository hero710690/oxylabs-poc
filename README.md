# Oxylabs Web Scraper API — Amazon iPhone Scraper PoC

A working proof-of-concept that scrapes the top 100 iPhone listings on Amazon US using [Oxylabs Web Scraper API](https://oxylabs.io/products/scraper-api/web), extracts detailed product data from each listing's product page, and stores results as timestamped JSON files. Runs hourly via APScheduler.

Built for **TechNovaAI** — a prospective client entering the U.S. smartphone resale market who needs competitive intelligence on pricing, availability, and delivery across top iPhone listings.

## How It Works

```
Scheduler triggers hourly run
  → Phase 1: Paginated amazon_search (7 pages → 100 listings)
  → Phase 2: Batch async amazon_product (10 at a time, poll for results)
  → Phase 3: amazon_pricing for top 5 ASINs (all seller offers)
  → Validate with Pydantic models
  → Merge search metadata + product page data + pricing intelligence
  → Write timestamped JSON to output/
```

## Oxylabs Features Used

| # | Feature | Where | Purpose |
|---|---------|-------|---------|
| 1 | `amazon_search` source | `scraper/search.py` | Paginated search results for "iPhone" |
| 2 | `amazon_product` source | `scraper/product.py` | Individual product page data extraction |
| 3 | `amazon_pricing` source | `scraper/pricing.py` | All seller offers for an ASIN (price intelligence) |
| 4 | `parse: true` | All scraper modules | Structured auto-parsed JSON (no HTML parsing) |
| 5 | `geo_location` | All scraper modules | Lock results to US market (ZIP code) |
| 6 | Pagination (`start_page`) | `scraper/search.py` | Collect 100 results across 7 pages |
| 7 | Async/Polling mode | `scraper/product.py` | Non-blocking batch product scraping |
| 8 | Async/Callback mode | `scraper/callback.py` | Documented alternative (webhook-based) |
| 9 | Batch submission | `scraper/product.py` | Process 100 products in chunks of 10 |
| 10 | Realtime endpoint | `scraper/client.py` | Synchronous search + pricing requests |
| 11 | Async endpoint | `scraper/client.py` | Background job submission + results retrieval |
| 12 | `context: autoselect_variant` | `scraper/product.py` | Accurate buybox pricing for variant products |
| 13 | Async results retrieval | `scraper/client.py` | Fetch completed job results from separate endpoint |

See [docs/FEATURES.md](docs/FEATURES.md) for detailed explanations of each feature.

## Data Extracted Per Product

- Position in search results
- Price & currency
- Product title & description
- Product specifications (50+ fields)
- Prime eligibility
- Sponsored vs. organic
- Delivery details
- Rating & review count
- Sales rank & sales volume
- Best Seller / Amazon's Choice badges
- Brand & coupon info
- **Pricing intelligence** (top 5): all seller offers with condition, shipping, FBA status

## Quick Start

```bash
# Clone
git clone https://github.com/hero710690/oxylabs-poc.git
cd oxylabs-poc

# Install dependencies
pip install -r requirements.txt

# Set up credentials
cp .env.example .env
# Edit .env with your Oxylabs username and password

# Run once
python main.py --once

# Run with hourly scheduler (APScheduler)
python main.py

# --- Docker (production) ---

# One-shot run
docker compose run --rm scraper

# Self-scheduling (cron inside container, runs every hour)
docker compose up -d scraper-cron

# View logs
docker compose exec scraper-cron tail -f /var/log/scraper.log
```

## Project Structure

```
oxylabs-poc/
├── main.py                    # Entry point + APScheduler
├── Dockerfile                 # Single-run container (for external schedulers)
├── Dockerfile.cron            # Self-scheduling container (cron inside)
├── docker-compose.yml         # Both modes: one-shot + hourly cron
├── crontab                    # Cron schedule definition
├── config.py                  # Credentials, constants
├── models.py                  # Pydantic validation schemas
├── scraper/
│   ├── client.py              # Oxylabs API wrapper (retry, async)
│   ├── search.py              # Phase 1: paginated search
│   ├── product.py             # Phase 2: batch async product pages
│   ├── pricing.py             # Phase 3: multi-seller pricing
│   └── callback.py            # Callback mode (documented alternative)
├── output/                    # Timestamped JSON outputs + analysis
├── tests/                     # Unit tests
└── docs/
    ├── FEATURES.md            # Feature → code mapping
    ├── PRICING.md             # Cost breakdown + plan recommendation
    ├── FEEDBACK.md            # API developer experience feedback
    └── PRESENTATION_NOTES.md  # Demo talking points
```

## Output Example

```json
{
  "metadata": {
    "scraped_at": "2026-05-14T04:38:31.135Z",
    "total_products": 100,
    "query": "iPhone",
    "geo_location": "90210"
  },
  "products": [
    {
      "position": 1,
      "asin": "B0CMPMY9ZZ",
      "title": "Apple iPhone 15, 128GB, Black - Unlocked (Renewed)",
      "price": 426.77,
      "currency": "USD",
      "is_sponsored": false,
      "is_prime": true,
      "description": "Apple iPhone 15, 128GB, Black - Unlocked (Renewed)",
      "specifications": {
        "brand": "Apple",
        "color": "Black",
        "storage": "128GB",
        "screen_size": "6.1 Inches"
      },
      "delivery": "FREE delivery Monday, May 18 | Prime members Overnight, 7 AM - 11 AM",
      "url": "https://www.amazon.com/dp/B0CMPMY9ZZ",
      "scraped_at": "2026-05-14T04:38:31.135Z"
    }
  ]
}
```

## Scheduling Options

| Option | Best For | How |
|--------|----------|-----|
| **APScheduler** (built-in) | Development/testing | `python main.py` (runs in-process) |
| **Docker + cron** | Production self-hosted | `docker compose up -d scraper-cron` |
| **External scheduler** | Cloud deployment | Trigger `docker compose run --rm scraper` via AWS EventBridge, GCP Cloud Scheduler, K8s CronJob |
| **Oxylabs Scheduler** | Fully managed timing | Oxylabs runs jobs on a cron schedule — no cron infrastructure needed. Results retrieved via polling. |

**Note on Oxylabs Scheduler:** Eliminates scheduling infrastructure (no cron, no APScheduler), but results must be polled — `callback_url` is not supported on the Scheduler endpoint. For callback delivery, use regular async submissions with `callback_url` (see `scraper/callback.py` + `webhook_server.py`).

For this PoC, we use **Docker + cron** — self-contained, no external dependencies, runs anywhere.

## Running Tests

```bash
pytest tests/ -v
```

## Documentation

- [FEATURES.md](docs/FEATURES.md) — Detailed feature usage guide
- [PRICING.md](docs/PRICING.md) — Cost calculation (~$242/month) and plan recommendation
- [FEEDBACK.md](docs/FEEDBACK.md) — Developer experience feedback for Oxylabs
- [PRESENTATION_NOTES.md](docs/PRESENTATION_NOTES.md) — Demo agenda and talking points
