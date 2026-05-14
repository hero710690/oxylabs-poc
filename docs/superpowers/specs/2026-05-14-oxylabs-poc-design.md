# Oxylabs Web Scraper API PoC — Design Spec

## Overview

A Python CLI application that scrapes the top 100 iPhone listings on Amazon US using Oxylabs Web Scraper API, extracts detailed product data from each listing's product page, and stores results as timestamped JSON files. Runs hourly via APScheduler.

Built for a prospective client, TechNovaAI, entering the U.S. smartphone resale market. The PoC showcases as many Oxylabs features as possible.

## Architecture

### Two-Phase Scraping

1. **Search Phase** — `amazon_search` source, paginated (3 pages, ~48 results/page) to collect 100 listings with search-level metadata (position, sponsored flag).
2. **Product Phase** — `amazon_product` source, async/polling mode, batched in chunks of 10-20. Extracts detailed product data from each individual product page.

### Data Flow

```
Scheduler triggers run
  → search.py: paginated amazon_search (3 pages)
  → collect 100 ASINs + search-level metadata (position, sponsored flag)
  → product.py: batch submit amazon_product requests (10 at a time, async/poll)
  → validate responses with Pydantic
  → merge search metadata + product data
  → write timestamped JSON to output/
```

## Oxylabs Features Showcased

| Feature | Where Used | Purpose |
|---------|-----------|---------|
| `amazon_search` source | search.py | Paginated search results |
| `amazon_product` source | product.py | Individual product page data |
| `parse: true` | Both phases | Structured auto-parsed JSON output |
| `geo_location` | Both phases | Lock results to US market |
| Pagination (`start_page`, `pages`) | search.py | Collect 100 results across 3 pages |
| Async/Polling mode | product.py | Non-blocking batch product scraping |
| Async/Callback mode | product.py (documented alternative) | Demonstrates webhook-based approach |
| Batch submission | product.py | Multiple product URLs per API call |

## Project Structure

```
oxylabs-poc/
├── main.py                    # Entry point + APScheduler (hourly trigger)
├── config.py                  # Credentials (.env), constants, batch size
├── scraper/
│   ├── search.py              # Phase 1: amazon_search (paginated)
│   ├── product.py             # Phase 2: amazon_product (batch + async polling)
│   └── client.py              # Oxylabs API wrapper (retry, logging)
├── models.py                  # Pydantic schemas for validation
├── output/                    # Timestamped JSON outputs
├── docs/
│   ├── FEATURES.md            # Feature → code location mapping
│   ├── PRICING.md             # Cost breakdown + plan recommendation
│   ├── FEEDBACK.md            # Product/developer feedback (filled during impl)
│   └── PRESENTATION_NOTES.md  # Talking points + alternative products comparison
├── requirements.txt
└── .env.example
```

## Data Model

### Output Schema (per product)

```json
{
  "position": 3,
  "asin": "B0XXXXX",
  "title": "Apple iPhone 14, 128GB, Midnight - Unlocked (Renewed)",
  "price": 301.49,
  "currency": "USD",
  "is_sponsored": false,
  "is_prime": true,
  "description": "...",
  "specifications": {
    "brand": "Apple",
    "model": "iPhone 14",
    "storage": "128GB",
    "color": "Midnight"
  },
  "delivery": "FREE delivery Tomorrow, March 4",
  "url": "https://amazon.com/dp/B0XXXXX",
  "scraped_at": "2026-05-14T10:00:00Z"
}
```

### Pydantic Validation

- All fields typed and validated
- Missing/malformed fields logged as warnings (don't block the run)
- Optional fields allowed (some products may lack specs or delivery info)

## Error Handling

- **Retry:** Exponential backoff on API failures (3 attempts)
- **Validation:** Pydantic catches missing/malformed fields
- **Resilience:** Failed products logged but don't block the full run
- **Summary:** Success/fail counts logged at end of each run

## Scheduling

- **Primary:** APScheduler (in-process) for the demo — self-contained, easy to present
- **Production recommendation:** Oxylabs built-in Scheduler or system cron (documented in PRESENTATION_NOTES.md)

## Pricing Calculation

### Per Run
- 3 search requests (3 pages to get 100 listings)
- 100 product page requests
- **Total: 103 requests per run**

### Monthly Volume
- 103 requests × 24 runs/day × 30 days = **~74,160 requests/month**

Detailed cost breakdown with plan recommendation will go in `PRICING.md` based on current Oxylabs Web Scraper API pricing tiers.

## Deliverables

1. **Working PoC** — Python scraper demonstrating the full pipeline
2. **FEATURES.md** — Inline code comments + summary doc mapping features to code
3. **PRICING.md** — Cost calculation + plan recommendation
4. **FEEDBACK.md** — Product/developer feedback (populated during implementation)
5. **PRESENTATION_NOTES.md** — Talking points + alternative Oxylabs products comparison

## Alternative Products (for presentation)

To be covered in PRESENTATION_NOTES.md:
- **E-Commerce Scraper API** — purpose-built for e-commerce, potentially better fit
- **SERP Scraper API** — if only search-level data is needed
- **Residential Proxies + custom scraper** — more control, higher complexity
- **Web Unblocker** — if client wants to build their own parser

## Out of Scope (Addressed as "Next Steps" in Presentation)

### Database Storage
Recommend PostgreSQL or a time-series DB for production — enables querying price trends, deduplication, and powering dashboards.

### Production Deployment
Recommend a generic containerized approach (Docker + any cron/scheduler). Cloud-agnostic — works on AWS, GCP, Azure, or self-hosted. No assumption about TechNovaAI's infrastructure. Presentation framing: "Here's a Dockerfile and docker-compose — deploy wherever your team already runs containers."

### Frontend/Dashboard
Combined view for TechNovaAI:
- **Market overview** — all 100 listings at a glance: position, price, Prime status, sponsored vs. organic breakdown
- **Price monitoring** — track price changes over time, alert when a competitor drops price significantly

Tools to mention: Grafana, Metabase, or a custom lightweight dashboard.

### Historical Trend Analysis
Full competitive intelligence over time:
- **Price trends** — how listing prices fluctuate hourly/daily, spot best times to buy/list
- **Competitive landscape shifts** — which sellers/products rise or fall in rankings, new entrants, delisted items
- **Delivery & Prime changes** — track shifts in fulfillment strategy
- **Sponsored spend patterns** — which competitors are paying for visibility and when

This becomes possible once data accumulates from the hourly runs + database storage.
