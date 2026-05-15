# Oxylabs Web Scraper API — Amazon iPhone Scraper PoC

A working proof-of-concept that scrapes the top 100 iPhone listings on Amazon US using [Oxylabs Web Scraper API](https://oxylabs.io/products/scraper-api/web), extracts detailed product data from each listing's product page, fetches multi-seller pricing intelligence, and stores results as timestamped JSON files. Runs hourly via system crontab.

Built for **TechNovaAI** — a prospective client entering the U.S. smartphone resale market who needs competitive intelligence on pricing, availability, and delivery across top iPhone listings.

## How It Works

```
Scheduler triggers hourly run
  → Phase 1: Brand-filtered search (Cell Phones + Apple → 100 iPhones only)
  → Phase 2: Batch async amazon_product (10 at a time, poll for results)
  → Phase 3: amazon_pricing for top 5 ASINs (all seller offers)
  → Validate with Pydantic models
  → Merge search metadata + product page data + pricing intelligence
  → Write timestamped JSON to output/
```

## Oxylabs Features Used

| # | Feature | Where | Purpose |
|---|---------|-------|---------|
| 1 | `amazon` source (URL) | `scraper/search.py` | Brand-filtered search (Apple iPhones only, zero waste) |
| 2 | `amazon_product` source | `scraper/product.py` | Individual product page data extraction |
| 3 | `amazon_pricing` source | `scraper/pricing.py` | All seller offers for an ASIN (price intelligence) |
| 4 | `parse: true` | All scraper modules | Structured auto-parsed JSON (no HTML parsing) |
| 5 | `geo_location` | All scraper modules | Lock results to US market (ZIP code) |
| 6 | URL-based filtering | `scraper/search.py` | Category + brand filter via Amazon URL params |
| 7 | Async/Polling mode | `scraper/product.py` | Non-blocking batch product scraping |
| 8 | Async/Callback mode | `scripts/webhook_server.py` | Webhook-based delivery notification receiver |
| 9 | Batch submission | `scraper/product.py` | Process 100 products in chunks of 10 |
| 10 | Realtime endpoint | `scraper/client.py` | Synchronous search + pricing requests |
| 11 | Async endpoint | `scraper/client.py` | Background job submission + results retrieval |
| 12 | `context: autoselect_variant` | `scraper/product.py` | Accurate buybox pricing for variant products |
| 13 | Async results retrieval | `scraper/client.py` | Fetch completed job results from separate endpoint |
| 14 | Oxylabs Scheduler | `scripts/test_scheduler.py` | Recurring jobs on cron schedule (tested: create → pause → delete) |
| 15 | Cloud Storage delivery | `scraper/client.py` | Results pushed directly to client's S3/GCS via storage_type param |

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

# Run once (demo/testing)
python main.py

# Generate HTML report from latest output
python scripts/report.py

# Test Oxylabs Scheduler API (create → verify → pause → delete)
python scripts/test_scheduler.py

# Compare amazon_search vs amazon (URL) source
python scripts/compare_sources.py

# Schedule hourly via system crontab
# crontab -e, then add:
# 0 * * * * cd /path/to/oxylabs-poc && python main.py >> output/cron.log 2>&1

# --- Docker (optional, for production) ---
docker compose run --rm scraper
```

## Project Structure

```
oxylabs-poc/
├── main.py                    # Entry point (single run, cron handles scheduling)
├── config.py                  # Credentials, constants
├── models.py                  # Pydantic validation schemas
├── Dockerfile                 # Container image
├── docker-compose.yml         # Docker run config
├── scraper/
│   ├── client.py              # Oxylabs API wrapper (retry, async, scheduler)
│   ├── search.py              # Phase 1: brand-filtered search (Apple iPhones only)
│   ├── product.py             # Phase 2: batch async product pages
│   └── pricing.py             # Phase 3: multi-seller pricing
├── scripts/
│   ├── report.py              # HTML report/dashboard generator
│   ├── test_scheduler.py      # Oxylabs Scheduler API test script
│   ├── compare_sources.py     # amazon_search vs amazon (URL) comparison
│   └── webhook_server.py      # FastAPI callback notification receiver
├── output/                    # Timestamped JSON outputs + HTML report
├── tests/                     # Unit tests (18 tests)
└── docs/
    ├── FEATURES.md            # Feature → code mapping (15 features)
    ├── PRICING.md             # Cost breakdown (~$238/month)
    ├── FEEDBACK.md            # API developer experience feedback
    └── PRESENTATION.md        # Full presentation (19 slides)
```

## Output Example

```json
{
  "metadata": {
    "scraped_at": "2026-05-15T05:22:46.214Z",
    "total_products": 100,
    "query": "iPhone",
    "geo_location": "90210"
  },
  "products": [
    {
      "position": 1,
      "asin": "B0CMPMY9ZZ",
      "title": "Apple iPhone 15, 128GB, Black - Unlocked (Renewed)",
      "price": 399.00,
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
      "pricing_offers": [
        {
          "seller_name": "Ships from Macalegin Electronics",
          "price": 387.11,
          "condition": "Refurbished - Excellent",
          "is_fulfilled_by_amazon": false
        }
      ],
      "url": "https://www.amazon.com/dp/B0CMPMY9ZZ",
      "scraped_at": "2026-05-15T05:22:46.214Z"
    }
  ]
}
```

## Scheduling Options

| Option | Best For | How |
|--------|----------|-----|
| **System crontab** | Local / self-hosted | `0 * * * * cd /path && python main.py` |
| **Docker + crontab** | Production self-hosted | `0 * * * * docker compose run --rm scraper` |
| **Cloud scheduler** | Cloud deployment | AWS EventBridge / GCP Cloud Scheduler / K8s CronJob triggers container |
| **Oxylabs Scheduler** | Zero infrastructure | Oxylabs runs jobs on their side, delivers to S3/GCS or webhook |

**Architecture note:** Our 3-phase pipeline (search → product → pricing) requires our own scheduler since it chains multiple API calls. The Oxylabs Scheduler is ideal for simpler single-source jobs with direct delivery to cloud storage. Both approaches are implemented and tested in this PoC.

## Running Tests

```bash
pytest tests/ -v
# 18 tests covering search, product, pricing, client, models, and main
```

## Documentation

- [FEATURES.md](docs/FEATURES.md) — Detailed feature usage guide (15 features + additional sources)
- [PRICING.md](docs/PRICING.md) — Cost calculation (~$238/month) and plan recommendation
- [FEEDBACK.md](docs/FEEDBACK.md) — Developer experience feedback for Oxylabs
- [PRESENTATION.md](docs/PRESENTATION.md) — Full 17-slide presentation for TechNovaAI
