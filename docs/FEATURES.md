# Oxylabs Web Scraper API — Features Used

This document maps every Oxylabs feature used in this PoC to its location in the code.

## Feature Matrix

| # | Feature | File | Function | Purpose |
|---|---------|------|----------|---------|
| 1 | `amazon` source (URL) | `scraper/search.py` | `search_iphones()` | Scrape brand-filtered search results (Apple iPhones only) |
| 2 | `amazon_product` source | `scraper/product.py` | `_submit_jobs()` | Individual product page data extraction |
| 3 | `amazon_pricing` source | `scraper/pricing.py` | `get_pricing()` | All seller offers for an ASIN (price intelligence) |
| 4 | `parse: true` | All scraper modules | All payloads | Structured auto-parsed JSON output (no HTML parsing) |
| 5 | `geo_location` | All scraper modules | All payloads | Locks results to US market (ZIP code: 90210) |
| 6 | URL-based filtering | `scraper/search.py` | `search_iphones()` | Category + brand filter via Amazon URL params (zero waste) |
| 7 | Async/Polling mode | `scraper/product.py`, `scraper/client.py` | `async_submit()`, `async_poll()`, `async_get_results()` | Non-blocking product scraping — submit job, poll status, retrieve result |
| 8 | Realtime endpoint | `scraper/client.py` | `realtime()` | Synchronous search + pricing requests |
| 9 | `context: autoselect_variant` | `scraper/product.py` | `_submit_jobs()` | Accurate buybox pricing for variant products |
| 10 | Oxylabs Scheduler | `scripts/test_scheduler.py` | `client.create_schedule()` | Recurring jobs on cron schedule — tested: create → verify → pause → delete |

## Feature Details

### 1. amazon source with URL (Realtime)
Used for the search phase. We pass a pre-filtered Amazon search URL that includes category (Cell Phones) and brand (Apple) filters — this ensures every result is an actual iPhone, with zero wasted requests on accessories or other brands.
The `parse: true` flag means Oxylabs returns structured JSON with organic/paid results already separated — includes rating, reviews, best seller badges, and sales volume.

### 2. amazon_product (Async)
Used for product page scraping. Each product is submitted as an async job to avoid blocking. Returns 50+ fields including specifications, delivery info, sales rank, and brand.

### 3. amazon_pricing (Realtime)
Fetches all third-party seller offers for a specific ASIN. Returns each seller's price, condition, shipping cost, and fulfillment method. Used on top 5 listings for competitive price intelligence.

### 4. Structured Parsing
By setting `parse: true`, Oxylabs handles all the anti-bot logic AND returns clean structured data. Without this, we'd need to parse raw HTML ourselves.

### 5. Geo-targeting
`geo_location: "90210"` (ZIP code) ensures we see US-specific pricing, Prime eligibility, and delivery estimates — critical for TechNovaAI's US market analysis.

### 6. URL-based Filtering
By passing a filtered Amazon URL (`rh=n:7072561011,p_123:110955`), we apply category (Cell Phones) and brand (Apple) filters at the source — meaning Oxylabs only returns actual iPhones. This eliminates post-processing waste and ensures the client pays only for relevant results. We paginate across 5-7 pages to collect 100+ listings.

### 7. Async/Polling
For 100 product pages, synchronous requests would be too slow. Async mode lets us submit all jobs quickly, then poll for completion. Jobs run in parallel on Oxylabs' side.

### 8. Realtime Endpoint
Used for search (Phase 1) and pricing (Phase 3). Synchronous — blocks until result is ready. Fast enough for these use cases (3-5 seconds).

`POST https://realtime.oxylabs.io/v1/queries`

### 7-Detail. Async/Polling Mode (three API calls, one feature)
The async workflow uses three endpoints:
- **Submit** (`POST https://data.oxylabs.io/v1/queries`) — creates background job, returns `job_id`
- **Poll** (`GET https://data.oxylabs.io/v1/queries/{id}`) — check status (`pending` → `running` → `done`)
- **Retrieve** (`GET https://data.oxylabs.io/v1/queries/{id}/results`) — fetch completed result

All three are in `scraper/client.py`. Used for product pages (Phase 2) where 100 jobs run in parallel on Oxylabs' infrastructure.

### 12. autoselect_variant (Context Parameter)
iPhones come in many storage/color variants. Without `autoselect_variant: true`, the API might return pricing for a different variant than the one shown. This parameter appends `th=1&psc=1` to get accurate buybox/pricing data for the primary variant.

### 13. Oxylabs Scheduler
Oxylabs runs scraping jobs on a recurring cron schedule — no scheduling infrastructure needed on the client side. Tested in `scripts/test_scheduler.py` (create → verify → pause → delete — all confirmed working).

**API:** `POST https://data.oxylabs.io/v1/schedules`

**Payload:**
```json
{
  "cron": "0 * * * *",
  "end_time": "2027-01-01 00:00:00",
  "items": [
    {
      "source": "amazon_search",
      "query": "iPhone",
      "domain": "com",
      "parse": true,
      "geo_location": "90210"
    }
  ]
}
```

Additional Scheduler endpoints:
- `GET /v1/schedules/{id}` — check schedule info
- `PUT /v1/schedules/{id}/state` — pause/resume (`{"active": false}`)

See: https://developers.oxylabs.io/products/web-scraper-api/features/scheduler

**Note on delivery options (not tested in this PoC):** The Scheduler API also supports `callback_url` (webhook notification when job completes) and `storage_type`/`storage_url` (push results directly to S3/GCS). These are production delivery options — for TechNovaAI, the S3 approach would mean zero client-side infrastructure. Not exercised here since the PoC uses system crontab with local file output.

---

## Additional Amazon Sources Available

Beyond the sources used in this PoC, Oxylabs Web Scraper API offers additional Amazon-specific sources that TechNovaAI could leverage as the product matures:

| Source | Purpose | Use Case for TechNovaAI |
|--------|---------|------------------------|
| `amazon_sellers` | Scrape a specific seller's storefront | Monitor competitor sellers entering the iPhone resale space |
| `amazon_bestsellers` | Bestseller rankings by category | Track which iPhones are trending in real-time |

These sources follow the same patterns as our current implementation (same auth, `parse: true`, `geo_location`, async/realtime modes) and could be integrated with minimal code changes.

---

## Recommended: OxyCopilot (Web Scraper API Playground)

For teams new to web scraping or Oxylabs, [OxyCopilot](https://developers.oxylabs.io/products/web-scraper-api/web-scraper-api-playground/oxycopilot) is an AI-powered assistant built into the Oxylabs dashboard that helps build and test scraping queries without writing code.

**Three capabilities:**

| Feature | What It Does |
|---------|--------------|
| **Scraper Builder** | Generates API payloads from natural language prompts (e.g., "scrape Amazon search for iPhones in the US") |
| **Custom Parser Builder** | Analyzes page HTML and creates parsing instructions to extract specific fields |
| **Browser Instructions Builder** | Creates page interaction scripts (scroll, click, wait) from natural language |

**How it fits this project:** OxyCopilot generates standard `amazon_search` payloads as a starting point. Our PoC goes a step further by using the `amazon` source with URL-based brand filtering — an optimization that eliminates wasted requests and reduces cost. OxyCopilot is ideal for onboarding, rapid prototyping, and exploring new sources before writing production code.
