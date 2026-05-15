# Oxylabs Web Scraper API — Features Used

This document maps every Oxylabs feature used in this PoC to its location in the code.

## Feature Matrix

| # | Feature | File | Function | Purpose |
|---|---------|------|----------|---------|
| 1 | `amazon` source (URL) | `scraper/search.py` | `search_iphones()` | Scrape brand-filtered search results (Apple iPhones only) |
| 2 | `amazon_product` source | `scraper/product.py` | `_process_batch()` | Individual product page data extraction |
| 3 | `amazon_pricing` source | `scraper/pricing.py` | `get_pricing()` | All seller offers for an ASIN (price intelligence) |
| 4 | `parse: true` | All scraper modules | All payloads | Structured auto-parsed JSON output (no HTML parsing) |
| 5 | `geo_location` | All scraper modules | All payloads | Locks results to US market (ZIP code: 90210) |
| 6 | URL-based filtering | `scraper/search.py` | `search_iphones()` | Category + brand filter via Amazon URL params (zero waste) |
| 7 | Async/Polling mode | `scraper/product.py` | `_poll_until_done()` | Non-blocking batch product scraping |
| 8 | Async/Callback mode | `scripts/webhook_server.py` | `receive_oxylabs_callback()` | Webhook-based delivery notification receiver |
| 9 | Batch submission | `scraper/product.py` | `scrape_products()` | Processes 100 products in chunks of 10 |
| 10 | Realtime endpoint | `scraper/client.py` | `realtime()` | Synchronous search + pricing requests |
| 11 | Async endpoint | `scraper/client.py` | `async_submit()` | Background job submission |
| 12 | Async results retrieval | `scraper/client.py` | `async_get_results()` | Fetch completed job results |
| 13 | `context: autoselect_variant` | `scraper/product.py` | `_process_batch()` | Accurate buybox pricing for variant products |
| 14 | Oxylabs Scheduler | `scripts/test_scheduler.py` | `client.create_schedule()` | Recurring jobs on cron schedule (tested: create → verify → pause → delete) |
| 15 | Cloud Storage delivery | `scraper/client.py` | `create_schedule()` | Results pushed directly to client's S3/GCS via storage_type param |

## Feature Details

### 1. amazon source with URL (Realtime)
Used for the search phase. We pass a pre-filtered Amazon search URL that includes
category (Cell Phones) and brand (Apple) filters — this ensures every result is an
actual iPhone, with zero wasted requests on accessories or other brands.
The `parse: true` flag means Oxylabs returns structured JSON with organic/paid results
already separated — includes rating, reviews, best seller badges, and sales volume.

### 2. amazon_product (Async)
Used for product page scraping. Each product is submitted as an async job to avoid
blocking. Returns 50+ fields including specifications, delivery info, sales rank, and brand.

### 3. amazon_pricing (Realtime)
Fetches all third-party seller offers for a specific ASIN. Returns each seller's price,
condition, shipping cost, and fulfillment method. Used on top 5 listings for competitive
price intelligence.

### 4. Structured Parsing
By setting `parse: true`, Oxylabs handles all the anti-bot logic AND returns clean
structured data. Without this, we'd need to parse raw HTML ourselves.

### 5. Geo-targeting
`geo_location: "90210"` (ZIP code) ensures we see US-specific pricing, Prime eligibility,
and delivery estimates — critical for TechNovaAI's US market analysis.

### 6. URL-based Filtering
By passing a filtered Amazon URL (`rh=n:7072561011,p_123:110955`), we apply category
(Cell Phones) and brand (Apple) filters at the source — meaning Oxylabs only returns
actual iPhones. This eliminates post-processing waste and ensures the client pays only
for relevant results. We paginate across 5-7 pages to collect 100+ listings.

### 7. Async/Polling
For 100 product pages, synchronous requests would be too slow. Async mode lets us
submit all jobs quickly, then poll for completion. Jobs run in parallel on Oxylabs' side.

### 8. Async/Callback (Alternative)
For production, a callback URL eliminates polling overhead entirely. Oxylabs POSTs
a notification to your endpoint when each job completes. See `scripts/webhook_server.py`
for the FastAPI receiver implementation.

### 9. Batch Processing
We chunk 100 products into groups of 10. This balances throughput with manageability —
we can track progress, handle failures per-batch, and avoid overwhelming the API.

### 10-12. Endpoint Architecture
- **Realtime** (`realtime.oxylabs.io`) — synchronous, used for search and pricing
- **Async submit** (`data.oxylabs.io`) — submit background jobs
- **Async results** (`data.oxylabs.io/{id}/results`) — retrieve completed results

### 13. autoselect_variant (Context Parameter)
iPhones come in many storage/color variants. Without `autoselect_variant: true`,
the API might return pricing for a different variant than the one shown. This parameter
appends `th=1&psc=1` to get accurate buybox/pricing data for the primary variant.

### 14. Oxylabs Scheduler
Oxylabs runs scraping jobs on a recurring cron schedule — no scheduling
infrastructure needed on the client side. Tested in `scripts/test_scheduler.py`
(create → verify → pause → delete — all confirmed working).

**API:** `POST https://data.oxylabs.io/v1/schedules`

**Payload:**
```json
{
  "cron": "0 * * * *",
  "end_time": "2027-01-01 00:00:00",
  "callback_url": "https://your-server.com/webhooks/oxylabs",
  "items": [
    {
      "source": "amazon_search",
      "query": "iPhone",
      "domain": "com",
      "parse": true,
      "geo_location": "90210",
      "storage_type": "s3",
      "storage_url": "my-bucket/oxylabs-results"
    }
  ]
}
```

**Result delivery options:**
- `callback_url` — notification only (job done ping + link to fetch results)
- `storage_type` + `storage_url` — full results pushed directly to client's bucket

Additional Scheduler endpoints:
- `GET /v1/schedules/{id}` — check schedule info
- `PUT /v1/schedules/{id}/state` — pause/resume (`{"active": false}`)

See: https://developers.oxylabs.io/products/web-scraper-api/features/scheduler

### 15. Cloud Storage Delivery
Results can be pushed directly to the client's cloud storage bucket — no polling,
no webhook server, no infrastructure needed beyond the bucket itself.

**Supported providers:**
| Provider | `storage_type` | `storage_url` format |
|----------|---------------|---------------------|
| Amazon S3 | `s3` | `bucket-name/path` |
| Google Cloud Storage | `gcs` | `bucket-name/path` |
| S3-compatible (Alibaba OSS, etc.) | `s3_compatible` | `https://KEY:SECRET@endpoint/bucket/path` |

**Setup:** Grant Oxylabs' service account write access to your bucket (one-time).
Then every scheduled job drops `{job_id}.json` into your bucket automatically.

This is the recommended production approach for TechNovaAI — results land in S3
every hour with zero client-side infrastructure.

---

## Additional Amazon Sources Available

Beyond the sources used in this PoC, Oxylabs Web Scraper API offers additional Amazon-specific sources that TechNovaAI could leverage as the product matures:

| Source | Purpose | Use Case for TechNovaAI |
|--------|---------|------------------------|
| `amazon_sellers` | Scrape a specific seller's storefront | Monitor competitor sellers entering the iPhone resale space |
| `amazon_bestsellers` | Bestseller rankings by category | Track which iPhones are trending in real-time |
| `amazon_reviews` | Product reviews for an ASIN | Sentiment analysis on competing listings |
| `amazon_questions` | Q&A section for a product | Identify common buyer concerns to address in listings |

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
