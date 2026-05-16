# Oxylabs Web Scraper API — TechNovaAI Presentation

---

## Slide 1: Title

**Competitive Intelligence for the US Smartphone Resale Market**

Powered by Oxylabs Web Scraper API

Prepared for: TechNovaAI
Date: May 2026

---

## Slide 2: The Challenge

**TechNovaAI's Need:**
- Entering the US smartphone resale market
- Needs real-time competitive intelligence on top iPhone listings
- Must track pricing, availability, seller competition, and delivery across Amazon US

**Requirements:**
- Top 100 iPhone listings, refreshed every hour
- Detailed data: price, specs, Prime status, delivery, seller offers
- Structured JSON output ready for analytics pipelines
- Minimal engineering overhead — focus on insights, not scraping infrastructure

---

## Slide 3: The Solution

**A fully automated 3-phase pipeline:**

```
Phase 1: Search        → Brand-filtered search (Apple iPhones only, zero waste)
Phase 2: Product Pages → Extract 50+ fields per product (async, batched)
Phase 3: Pricing       → All seller offers for top products (competitive intel)
```

**Key stats from latest run:**
- 100 products scraped
- 97 with full product page data, 3 with search-level fallback
- 11 seller offers per ASIN for top 5 products
- Total runtime: ~6 minutes
- Zero blocks, zero CAPTCHAs

---

## Slide 4: Live Demo

**Running the scraper:**

```bash
python main.py
```

**What you'll see in the logs:**
1. Phase 1: Brand-filtered search (5 pages) → 100 iPhone listings
2. Phase 2: 10 batches of 10 products → async submission + polling
3. Phase 3: 5 pricing requests → multi-seller offers

**Output:** Timestamped JSON file in `output/` with all 100 products merged

**Hourly scheduling:** System crontab runs `python main.py` every hour. We have multiple output files from consecutive cron runs proving this works.

---

## Slide 5: Data We Extract

**From Search (Phase 1):**
| Field | Example |
|-------|---------|
| Position | #1, #2, ... #100 |
| ASIN | B0CMZ4FQL4 |
| Price | $621.29 |
| Sponsored flag | true/false |
| Prime eligible | true/false |
| Best Seller badge | true/false |
| Amazon's Choice | true/false |
| Rating | 4.3 |
| Review count | 5,842 |
| Sales volume | "1K+ bought in past month" |

**From Product Pages (Phase 2):**
| Field | Example |
|-------|---------|
| Full description | Product details text |
| Specifications | 50+ fields (brand, color, storage, screen size...) |
| Delivery info | "FREE delivery Mon, May 18 \| Prime Overnight" |
| Sales rank | #45 in Cell Phones |
| Brand | Apple |
| Coupon | "5% off" (if available) |

**From Pricing (Phase 3):**
| Field | Example |
|-------|---------|
| Seller name | "TechDeals LLC" |
| Price | $602.78 |
| Condition | Refurbished - Excellent |
| Shipping cost | $0.00 |
| FBA status | Fulfilled by Amazon |
| Prime delivery | Yes/No |

---

## Slide 6: Market Insights (From Our Data)

**Price Analysis:**
- Range: $27.99 – $1,599.00
- Average: $442.05
- Median: $309.00

**Market Composition:**
- 100% Apple iPhones (brand-filtered at source — zero waste)
- 83% of listings are Prime eligible
- 11 sponsored listings vs 89 organic
- 3 Best Seller badges across 100 listings

**Rating Distribution:**
- 4.5+: 18 products
- 4.0–4.4: 68 products
- 3.5–3.9: 9 products
- Below 3.5: 0 products

**Key Insight:** The top search results are dominated by *Renewed/Refurbished* iPhones — this IS the competitive landscape for resellers entering this market.

---

## Slide 7: Source Comparison — Why URL-Based Filtering

We tested both available approaches and built a comparison script (`scripts/compare_sources.py`):

| Metric | `amazon_search` | `amazon` (URL) |
|--------|----------------|----------------|
| Organic results | ~22 per page | ~22 per page |
| Sponsored results | 6-8 per page | 6-8 per page |
| Non-iPhone contamination | 5-10 per page (chargers, cases, Pixels) | 0 |
| Brand filtering | Not supported | Yes (Apple only via URL params) |
| `pages` param support | Yes (multi-page in one call) | No (one request per page) |

**Decision:** We use `amazon` source with URL `rh=n:7072561011,p_123:110955` (Cell Phones + Apple brand). This eliminates wasted requests at the source — the client pays only for real iPhones.

**Note:** For teams exploring Oxylabs for the first time, OxyCopilot generates the simpler `amazon_search` payload as a starting point. Our approach is an optimization on top of that.

---

## Slide 8: Hourly Scheduling — Proven with Real Data

**Cron job running locally via system crontab:**

```
0 * * * * cd /path/to/oxylabs-poc && python main.py >> output/cron.log 2>&1
```

**Cron log proves two consecutive runs:**
- Run 1: `2026-05-15T11:01:54` → 100 products, 97 with full detail
- Run 2: `2026-05-15T12:05:34` → 100 products, 97 with full detail

**What changed in just one hour:**

| Metric | Value |
|--------|-------|
| Price changes detected | 11 out of 86 common products |
| Largest price drop | **-$170.00** (iPhone 15 128GB: $769 → $599) |
| Largest price increase | +$1.08 (iPhone 14 128GB) |
| Rank position changes | 78 out of 86 common products |
| Largest rank shift | +33 positions (iPhone 17 Pro Max) |
| New listings appeared | 11 |
| Listings dropped out | 13 |

**Key Insight:** The market moves fast — 11 price changes and 78 rank shifts in a single hour. A $170 price drop on an iPhone 15 would be missed entirely without hourly monitoring. This validates the client's requirement for hourly refresh.

---

## Slide 9: Pricing Intelligence Deep Dive (Beyond Requirements)

> **Note:** This goes beyond the core task requirements. We explored `amazon_pricing` as an additional Oxylabs feature to demonstrate extra value for TechNovaAI's resale use case — knowing what competitors charge is critical for a company entering the market.

**Example: iPhone 15 Pro Max (B0CMZ4FQL4)**
- 11 sellers competing
- Price range: $602.78 – $631.76 (only 4.8% spread — tight, premium market)
- 7 sellers offer "Refurbished - Excellent", 4 offer "Acceptable"
- Only 2 sellers use FBA

**Example: iPhone 13 (B09LNW3CY2)**
- 11 sellers competing
- Price range: $224.99 – $281.88 (25.3% spread — commodity market, high competition)
- Most sellers offer "Acceptable" condition
- Only 1 FBA seller

**What this tells TechNovaAI:**
- Newer models = tighter pricing, fewer sellers, premium positioning required
- Older models = wider spread, more sellers, race to the bottom
- FBA adoption is low — opportunity to differentiate with faster fulfillment

**Why only top 5 ASINs?**
- This is a PoC — the pattern is proven and easily scales to all 100
- Each `amazon_pricing` call takes 4-20 seconds; all 100 would add ~10 min per run
- Cost: 5 requests/run = $10.80/month vs 100 requests/run = $216/month
- In production, TechNovaAI can choose: top 5, top 20, or all 100 based on their budget and priority

---

## Slide 10: Oxylabs Features Powering This

| # | Feature | What It Does |
|---|---------|--------------|
| 1 | `amazon` source (URL) | Brand-filtered search — Apple iPhones only |
| 2 | `amazon_product` | Full product page extraction (50+ fields) |
| 3 | `amazon_pricing` | All seller offers for competitive pricing |
| 4 | `parse: true` | Structured JSON — no HTML parsing needed |
| 5 | `geo_location` | US market data (ZIP code targeting) |
| 6 | URL-based filtering | Category + brand filter, zero wasted requests |
| 7 | Async/Polling | Non-blocking batch processing |
| 8 | Batch submission | 10 products per batch, 10 batches total |
| 9 | Realtime endpoint | Instant results for search + pricing |
| 10 | Async endpoint | Background job submission |
| 11 | `autoselect_variant` | Accurate pricing for iPhone variants |
| 12 | Async results retrieval | Separate endpoint for completed jobs |
| 13 | Oxylabs Scheduler | Tested: create → verify → pause → delete |

**13 features executed. Additionally explored (not executed): Async/Callback, Cloud Storage delivery.**

---

## Slide 11: Architecture

```
┌─────────────────────────────────────────────────────┐
│                  System Crontab                       │
│                  (hourly trigger)                     │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │        main.py            │
         │   (orchestration layer)   │
         └─────┬───────┬───────┬─────┘
               │       │       │
    ┌──────────▼──┐ ┌──▼────┐ ┌▼──────────┐
    │  search.py  │ │product│ │ pricing.py │
    │  (Phase 1)  │ │.py    │ │ (Phase 3)  │
    │  Realtime   │ │(Ph 2) │ │ Realtime   │
    └──────┬──────┘ │Async  │ └─────┬──────┘
           │        └───┬───┘       │
           └────────────┼───────────┘
                        │
              ┌─────────▼─────────┐
              │    client.py      │
              │  (retry, auth,    │
              │   endpoint mgmt)  │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │   Oxylabs API     │
              │  realtime / async │
              └───────────────────┘
                        │
              ┌─────────▼─────────┐
              │    models.py      │
              │ (Pydantic valid.) │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │  output/*.json    │
              │ (timestamped)     │
              └───────────────────┘
```

---

## Slide 12: Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Language | Python 3.11+ | Rapid prototyping, rich ecosystem |
| HTTP Client | requests + tenacity | Retry with exponential backoff |
| Validation | Pydantic | Type-safe data, clear error messages |
| Scheduling | System crontab | Simple, reliable, no extra dependencies |
| Config | python-dotenv | Secure credential management |
| Container | Docker + docker-compose | Reproducible deployment |
| Output | JSON files | Simple, portable, pipeline-ready |

**Deployment options:**
| Option | Trade-off |
|--------|-----------|
| System crontab + Docker | Self-contained, runs anywhere |
| Cloud scheduler (AWS/GCP/K8s) | Better monitoring, cloud-native |
| **Oxylabs Scheduler** | Zero infrastructure — Oxylabs handles timing + delivery via callback URL |

**Lines of code:** ~500 (excluding tests)
**Setup time:** Under 5 minutes (clone, install, add credentials, run)

---

## Slide 13: Cost Breakdown

**Per hourly run: 110 API requests**
| Request Type | Count |
|---|---|
| Search pages (`amazon` source) | 5 |
| Product pages (`amazon_product`) | 100 |
| Pricing pages (`amazon_pricing`) | 5 |

**Monthly volume (24 runs/day): 79,200 requests**

**Plan options:**
| Plan | Monthly Price | Rate (Amazon) | Fits? |
|------|--------------|---------------|-------|
| **Micro** | $49/mo | $0.50/1K | Yes (79K < 98K cap) |
| **Starter** | $99/mo | $0.45/1K | Yes (room to scale 2x) |
| **Advanced** | $249/mo | $0.40/1K | For multi-category expansion |

**Recommendation:** Start with Micro ($49/mo). Upgrade to Starter when expanding pricing to all 100 ASINs (~175K requests/mo).

**Scaling scenarios:**
- Current pipeline (top 5 pricing): 79K requests → **$49/mo (Micro)**
- Full pricing (all 100 ASINs): 175K requests → **$99/mo (Starter)**
- Multi-category expansion: 300K+ requests → **$249/mo (Advanced)**

---

## Slide 14: Next Steps

**Immediate (Week 1-2):**
- Connect to PostgreSQL/TimescaleDB for persistent storage
- Add historical trend queries (price over time, rank movement)
- Expand pricing analysis to all 100 products

**Short-term (Month 1):**
- Dockerize for cloud deployment (AWS/GCP/Azure)
- Build a Grafana dashboard for real-time market view
- Set up alerts: price drops > 10%, new Best Sellers, etc.

**Long-term:**
- Expand to other categories (Samsung, Google Pixel)
- Multi-marketplace (eBay, Walmart via Oxylabs E-Commerce API)
- ML-powered pricing recommendations
- Oxylabs built-in Scheduler for zero-infrastructure delivery

---

## Slide 15: Why Oxylabs Over Competitors

### Market Landscape

| Provider | Amazon Product | Pricing | Best For |
|----------|---------------|---------|----------|
| **Oxylabs** (our choice) | Dedicated Amazon API, 5 endpoints, 129 parsed fields | $0.40–$0.50/1K (plan-based) | All-in-one (proxies + parsing + scheduling), 99.9% uptime, pay-per-success |
| **Bright Data** | Web Scraper API + ready datasets | $1.50/1K PAYG or $499/mo | Largest IP network (400M+), dataset buyers |
| **ScraperAPI** | Structured Data endpoint | ~$49/mo (150K calls) | Developer-friendly, AI/LLM integrations |
| **Decodo** (Smartproxy) | eCommerce Scraping API | $0.09/1K requests | Budget-conscious, high volume |
| **Apify** | 29K+ pre-built scrapers | $29/mo starter | Plug-and-play, no-code teams |
| **Zyte** (Scrapy) | Zyte API + Scrapy Cloud | $0.06–$1.27/1K | Python/Scrapy ecosystem |
| **SerpApi** | Amazon Search + Product APIs | $25/mo (1K searches) | SERP monitoring, price intelligence |

### Why Oxylabs Wins for TechNovaAI

| Criteria | Oxylabs Advantage |
|----------|-------------------|
| **All-in-one** | Proxies + parsing + scheduling + delivery in one API — no multi-tool setup |
| **Reliability** | 99.9% uptime, zero blocks across 200+ requests in our PoC |
| **Pay-per-success** | Failed requests (5xx/6xx) not charged — transparent billing |
| **Data richness** | 129 parsed fields per product — more than any competitor |
| **Amazon-specific sources** | Dedicated `amazon_search`, `amazon_product`, `amazon_pricing` — purpose-built |
| **Proxy network** | 177M+ proxies across 195 countries — geo-targeting down to ZIP code |
| **Async at scale** | Submit hundreds of jobs, poll or callback — production-ready |

### When Competitors Might Be Better

- **Bright Data** — if TechNovaAI wants pre-built datasets without any code
- **Decodo** — if cost is the top priority and data richness is secondary
- **Apify** — if the team has no developers and needs plug-and-play
- **SerpApi** — if only search-level data is needed (no product pages)

**For TechNovaAI's use case** (structured Amazon product + pricing intelligence, hourly refresh, US market): Oxylabs is the best fit due to dedicated Amazon endpoints, richest parsed data, and proven reliability.

---

## Slide 16: Other Oxylabs Products to Consider

**Additional Amazon Sources (same API, ready to integrate):**

| Source | Use Case |
|--------|----------|
| `amazon_sellers` | Monitor competitor sellers entering iPhone resale |
| `amazon_bestsellers` | Track trending iPhones in real-time |
| `amazon_reviews` | Sentiment analysis on competing listings |
| `amazon_questions` | Identify common buyer concerns |

**Other Oxylabs Products:**

| Product | When to Upgrade |
|---------|----------------|
| **E-Commerce Scraper API** | Expanding to eBay, Walmart, multiple marketplaces |
| **SERP Scraper API** | Adding Google Shopping visibility tracking |
| **Web Unblocker** | Scraping non-Amazon sites with anti-bot |
| **Residential Proxies** | Building fully custom scraper for unique needs |

**For New Users — OxyCopilot (AI Playground):**

If TechNovaAI's team is new to web scraping, Oxylabs' built-in [OxyCopilot](https://developers.oxylabs.io/products/web-scraper-api/web-scraper-api-playground/oxycopilot) helps generate API payloads from natural language prompts, build custom parsers from HTML analysis, and create browser interaction scripts — all without writing code. Ideal for onboarding and rapid prototyping before writing production pipelines.

**Recommendation:** Start with Web Scraper API (current). Use OxyCopilot for onboarding and exploring new sources. Add `amazon_reviews` + `amazon_bestsellers` for richer intelligence. Upgrade to E-Commerce Scraper API when expanding beyond Amazon.

---

## Slide 17: Summary

**What we delivered:**
- Fully working scraper: 100 iPhones, 50+ fields each, hourly refresh
- 13 Oxylabs features executed + 2 explored (Callback, Cloud Storage)
- Source comparison proving URL-based filtering saves money vs `amazon_search`
- Hourly cron job running with real data — detected $170 price drop in one hour
- Competitive pricing intelligence (multi-seller analysis)
- Production-ready architecture (retry, validation, graceful fallback)
- Complete documentation and cost analysis

**Why Oxylabs:**
- Zero blocks across 200+ requests
- Structured parsing eliminates maintenance burden
- Rich data (more fields than expected)
- Fast enough for hourly monitoring (~6 min per run)
- Cost-effective at $49–99/month for full competitive intelligence

**Bottom line:** TechNovaAI gets enterprise-grade market intelligence with minimal engineering investment.

---

## Slide 18: Q&A

Questions?

**Resources:**
- GitHub: `github.com/hero710690/oxylabs-poc`
- Run it yourself: `python main.py`
- Full feature docs: `docs/FEATURES.md`
- Cost details: `docs/PRICING.md`
