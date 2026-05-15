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
Phase 1: Search        → Find top 100 iPhone listings (paginated)
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
python main.py --once
```

**What you'll see in the logs:**
1. Phase 1: 7 search pages → 100 listings found
2. Phase 2: 10 batches of 10 products → async submission + polling
3. Phase 3: 5 pricing requests → multi-seller offers

**Output:** Timestamped JSON file in `output/` with all 100 products merged

**Scheduler mode:** Remove `--once` and it runs automatically every hour via APScheduler. We have two output files from different runs proving this works.

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
- 86% Apple, 6% Google, 8% accessories/other
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

## Slide 7: Pricing Intelligence Deep Dive (Beyond Requirements)

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

## Slide 8: Oxylabs Features Powering This

| # | Feature | What It Does |
|---|---------|--------------|
| 1 | `amazon_search` | Paginated search results with rich metadata |
| 2 | `amazon_product` | Full product page extraction (50+ fields) |
| 3 | `amazon_pricing` | All seller offers for competitive pricing |
| 4 | `parse: true` | Structured JSON — no HTML parsing needed |
| 5 | `geo_location` | US market data (ZIP code targeting) |
| 6 | Pagination | 7 pages → 100+ results |
| 7 | Async/Polling | Non-blocking batch processing |
| 8 | Async/Callback | Webhook-based delivery (production alternative) |
| 9 | Batch submission | 10 products per batch, 10 batches total |
| 10 | Realtime endpoint | Instant results for search + pricing |
| 11 | Async endpoint | Background job submission |
| 12 | `autoselect_variant` | Accurate pricing for iPhone variants |
| 13 | Async results retrieval | Separate endpoint for completed jobs |

**Total: 13 distinct Oxylabs features demonstrated in one PoC**

---

## Slide 9: Architecture

```
┌─────────────────────────────────────────────────────┐
│                    APScheduler                        │
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

## Slide 10: Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Language | Python 3.11+ | Rapid prototyping, rich ecosystem |
| HTTP Client | requests + tenacity | Retry with exponential backoff |
| Validation | Pydantic | Type-safe data, clear error messages |
| Scheduling | APScheduler | Lightweight, no external deps |
| Config | python-dotenv | Secure credential management |
| Output | JSON files | Simple, portable, pipeline-ready |

**Lines of code:** ~500 (excluding tests)
**Setup time:** Under 5 minutes (clone, install, add credentials, run)

---

## Slide 11: Cost Breakdown

**Per hourly run: 112 API requests**
| Request Type | Count |
|---|---|
| Search pages (`amazon_search`) | 7 |
| Product pages (`amazon_product`) | 100 |
| Pricing pages (`amazon_pricing`) | 5 |

**Monthly estimate (24 runs/day):**
| Item | Requests | Cost |
|------|----------|------|
| Search | 5,040 | ~$15.12 |
| Product | 72,000 | ~$216.00 |
| Pricing | 3,600 | ~$10.80 |
| **Total** | **80,640** | **~$241.92/month** |

**Cost optimization options:**
- Business hours only (10 runs/day) → ~$100/month
- Top 20 hourly, rest daily → ~$150/month
- Volume discount from Oxylabs sales team

---

## Slide 12: ROI Context

**$242/month buys you:**
- Real-time competitive intelligence on 100 listings
- Multi-seller pricing data (who's undercutting whom)
- Delivery & fulfillment tracking
- Zero engineering time on anti-bot, proxy management, HTML parsing

**Compare to alternatives:**
| Approach | Monthly Cost | Engineering Effort |
|----------|-------------|-------------------|
| Oxylabs Web Scraper API | ~$242 | Low (this PoC) |
| Build custom scraper + proxies | $500+ (proxies alone) | High (ongoing maintenance) |
| Manual monitoring | $0 | Impossible at scale |
| Third-party data provider | $1,000+ | Medium (integration) |

---

## Slide 13: Next Steps

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
- Oxylabs built-in Scheduler to replace APScheduler

---

## Slide 14: Why Oxylabs Over Competitors

### Market Landscape

| Provider | Amazon Product | Pricing | Best For |
|----------|---------------|---------|----------|
| **Oxylabs** (our choice) | Dedicated Amazon API, 5 endpoints, 129 parsed fields | ~$3.00/1K requests | Enterprise structured data, high reliability |
| **Bright Data** | Web Scraper API + ready datasets | $1.50/1K PAYG or $499/mo | Largest IP network (400M+), dataset buyers |
| **ScraperAPI** | Structured Data endpoint | ~$49/mo (150K calls) | Developer-friendly, AI/LLM integrations |
| **Decodo** (Smartproxy) | eCommerce Scraping API | $0.09/1K requests | Budget-conscious, high volume |
| **Apify** | 29K+ pre-built scrapers | $29/mo starter | Plug-and-play, no-code teams |
| **Zyte** (Scrapy) | Zyte API + Scrapy Cloud | $0.06–$1.27/1K | Python/Scrapy ecosystem |
| **SerpApi** | Amazon Search + Product APIs | $25/mo (1K searches) | SERP monitoring, price intelligence |

### Why Oxylabs Wins for TechNovaAI

| Criteria | Oxylabs Advantage |
|----------|-------------------|
| **Data richness** | 129 parsed fields per product — more than any competitor |
| **Amazon-specific sources** | Dedicated `amazon_search`, `amazon_product`, `amazon_pricing` — purpose-built |
| **Reliability** | Zero blocks across 200+ requests in our PoC, self-healing parsers |
| **Structured output** | `parse: true` returns clean JSON — no HTML parsing maintenance |
| **Async at scale** | Submit hundreds of jobs, poll or callback — production-ready |
| **Geo-targeting** | ZIP-code level precision for US market data |

### When Competitors Might Be Better

- **Bright Data** — if TechNovaAI wants pre-built datasets without any code
- **Decodo** — if cost is the top priority and data richness is secondary
- **Apify** — if the team has no developers and needs plug-and-play
- **SerpApi** — if only search-level data is needed (no product pages)

**For TechNovaAI's use case** (structured Amazon product + pricing intelligence, hourly refresh, US market): Oxylabs is the best fit due to dedicated Amazon endpoints, richest parsed data, and proven reliability.

---

## Slide 15: Other Oxylabs Products to Consider

| Product | When to Upgrade |
|---------|----------------|
| **E-Commerce Scraper API** | Expanding to eBay, Walmart, multiple marketplaces |
| **SERP Scraper API** | Adding Google Shopping visibility tracking |
| **Web Unblocker** | Scraping non-Amazon sites with anti-bot |
| **Residential Proxies** | Building fully custom scraper for unique needs |

**Recommendation:** Start with Web Scraper API (current). Upgrade to E-Commerce Scraper API when TechNovaAI expands beyond Amazon.

---

## Slide 16: Summary

**What we delivered:**
- Fully working scraper: 100 iPhones, 50+ fields each, hourly refresh
- 13 Oxylabs features demonstrated
- Competitive pricing intelligence (multi-seller analysis)
- Production-ready architecture (retry, validation, graceful fallback)
- Complete documentation and cost analysis

**Why Oxylabs:**
- Zero blocks across 200+ requests
- Structured parsing eliminates maintenance burden
- Rich data (more fields than expected)
- Fast enough for hourly monitoring (~6 min per run)
- Cost-effective at $242/month for full competitive intelligence

**Bottom line:** TechNovaAI gets enterprise-grade market intelligence with minimal engineering investment.

---

## Slide 17: Q&A

Questions?

**Resources:**
- GitHub: `github.com/hero710690/oxylabs-poc`
- Run it yourself: `python main.py --once`
- Full feature docs: `docs/FEATURES.md`
- Cost details: `docs/PRICING.md`
