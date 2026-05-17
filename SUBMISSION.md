# Submission Overview

## What This Is

A fully working proof-of-concept that scrapes the top 100 iPhone listings on Amazon US using Oxylabs Web Scraper API. It extracts detailed product data from each listing's product page, fetches multi-seller pricing intelligence for the top 5 products, and runs hourly via system crontab.

Built for **TechNovaAI** — a prospective client entering the U.S. smartphone resale market who needs competitive intelligence on pricing, availability, and delivery.

## What's Included

### Core Pipeline (`main.py`)
- **Phase 1:** Brand-filtered search using `amazon` source with URL params (Apple iPhones only, zero wasted requests)
- **Phase 2:** Async batch `amazon_product` scraping (100 products submitted concurrently, all jobs polled in parallel)
- **Phase 3:** `amazon_pricing` for top 5 ASINs (all seller offers — price intelligence)
- Output: timestamped JSON with 100 products, 50+ fields each

### Oxylabs Features Executed (13)
| # | Feature | Where |
|---|---------|-------|
| 1 | `amazon` source (URL) | `scraper/search.py` |
| 2 | `amazon_product` source | `scraper/product.py` |
| 3 | `amazon_pricing` source | `scraper/pricing.py` |
| 4 | `parse: true` | All modules |
| 5 | `geo_location` (ZIP code) | All modules |
| 6 | URL-based category + brand filtering | `scraper/search.py` |
| 7 | Async/Polling mode | `scraper/product.py` |
| 8 | Batch submission | `scraper/product.py` |
| 9 | Realtime endpoint | `scraper/client.py` |
| 10 | Async endpoint | `scraper/client.py` |
| 11 | Async results retrieval | `scraper/client.py` |
| 12 | `autoselect_variant` context | `scraper/product.py` |
| 13 | Oxylabs Scheduler API | `scripts/test_scheduler.py` |

**Explored but not executed:** Async/Callback (needs public URL), Cloud Storage delivery (needs S3/GCS bucket)

### Scripts (Demo/Testing)
- `scripts/compare_sources.py` — Side-by-side comparison of `amazon_search` vs `amazon` (URL) source, showing why URL-based filtering eliminates waste
- `scripts/test_scheduler.py` — Full Oxylabs Scheduler API test (create → verify → pause → delete)
- `scripts/webhook_server.py` — FastAPI callback notification receiver
- `scripts/report.py` — HTML dashboard generator from output JSON

### Scheduling (Proven)
- System crontab runs `python main.py` every hour
- Cron log (`output/cron.log`) shows consecutive successful runs
- Between two hourly runs: 11 price changes (including a **$170 drop**), 78 rank shifts, 13 listings rotated out

### Documentation
- `docs/FEATURES.md` — 13 features mapped to code with explanations
- `docs/PRICING.md` — Cost breakdown (~$49/month on Micro plan)
- `docs/FEEDBACK.md` — Developer experience feedback + feature request (Scheduler job chaining)
- `docs/PRESENTATION.md` — Full 17-slide presentation (excluded from repo — will be shared as PDF)

### Testing
- 18 unit tests covering all modules (`pytest tests/ -v`)

## Quick Start

```bash
git clone https://github.com/hero710690/oxylabs-poc.git
cd oxylabs-poc
pip install -r requirements.txt
cp .env.example .env   # Add your Oxylabs credentials
python main.py         # Run the full pipeline once
```

## Key Design Decisions

1. **URL-based filtering over `amazon_search`** — Eliminates non-iPhone contamination at the source. Client pays only for relevant results.
2. **System crontab over APScheduler** — Simpler, no extra dependency, battle-tested.
3. **Parallel submission and polling** — All 10 batches submitted concurrently, all 100 jobs polled simultaneously. Total runtime ~23 seconds (down from ~6 minutes sequential).
4. **Oxylabs Scheduler explored but not used for main pipeline** — It can't chain jobs (Phase 2 needs ASINs from Phase 1). Documented as a feature request in FEEDBACK.md.
