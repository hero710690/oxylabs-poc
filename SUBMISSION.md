# Submission Overview

## What I Built

A fully working proof-of-concept that scrapes the top 100 iPhone listings on Amazon US using Oxylabs Web Scraper API, extracts detailed product data from each listing's product page, fetches multi-seller pricing intelligence for the top 5 products, and runs hourly via system crontab.

Built for **TechNovaAI** — a prospective client entering the U.S. smartphone resale market who needs competitive intelligence on pricing, availability, and delivery.

See [README.md](README.md) for setup instructions, project structure, and how to run it.

---

## Oxylabs Features Executed (10)

| # | Feature | Where |
|---|---------|-------|
| 1 | `amazon` source (URL) | `scraper/search.py` |
| 2 | `amazon_product` source | `scraper/product.py` |
| 3 | `amazon_pricing` source | `scraper/pricing.py` |
| 4 | `parse: true` | All modules |
| 5 | `geo_location` (ZIP code) | All modules |
| 6 | URL-based category + brand filtering | `scraper/search.py` |
| 7 | Async/Polling mode | `scraper/product.py`, `scraper/client.py` |
| 8 | Realtime endpoint | `scraper/client.py` |
| 9 | `autoselect_variant` context | `scraper/product.py` |
| 10 | Oxylabs Scheduler API | `scripts/test_scheduler.py` |

**Explored but not executed:** Async/Callback (needs public URL), Cloud Storage delivery (needs S3/GCS bucket)

See [docs/FEATURES.md](docs/FEATURES.md) for detailed explanations of each feature.

---

## Key Design Decisions

1. **URL-based filtering over `amazon_search`** — Eliminates non-iPhone contamination at the source. The client pays only for relevant results. See [docs/FEATURES.md](docs/FEATURES.md) for the side-by-side comparison.

2. **System crontab over APScheduler** — Simpler, no extra dependency, battle-tested. The Oxylabs Scheduler was explored but can't chain jobs (Phase 2 needs ASINs from Phase 1) — documented as a feature request in [docs/FEEDBACK.md](docs/FEEDBACK.md).

3. **Parallel submission and polling** — All 100 jobs submitted concurrently, all 100 jobs polled simultaneously. Total runtime ~30-35 seconds (down from ~6 minutes sequential).

4. **Async/Polling for product pages, Realtime for search + pricing** — Product pages take 5–20 seconds each; async mode lets all 100 run in parallel. Search and pricing are fast enough for realtime.

---

## Scheduling — Proven with Real Data

System crontab runs `python main.py` every hour. The `output/cron.log` shows consecutive successful runs:

- Run 1: `2026-05-15T11:01:54` → 100 products, 100 with full detail
- Run 2: `2026-05-15T12:05:34` → 100 products, 100 with full detail

**What changed in one hour:** 11 price changes (including a $170 drop), 78 rank shifts, 13 listings rotated out.

---

## Testing

18 unit tests covering all modules:

```bash
pytest tests/ -v
```

---

## Documentation

- [docs/FEATURES.md](docs/FEATURES.md) — 10 features mapped to code with explanations
- [docs/PRICING.md](docs/PRICING.md) — Cost breakdown (~$49/month on Micro plan)
- [docs/FEEDBACK.md](docs/FEEDBACK.md) — Developer experience feedback + feature request
- Presentation — attached separately as PDF
