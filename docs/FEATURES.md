# Oxylabs Web Scraper API — Features Used

This document maps every Oxylabs feature used in this PoC to its location in the code.

## Feature Matrix

| # | Feature | File | Function | Purpose |
|---|---------|------|----------|---------|
| 1 | `amazon_search` source | `scraper/search.py` | `search_iphones()` | Paginated search results for "iPhone" on Amazon US |
| 2 | `amazon_product` source | `scraper/product.py` | `_process_batch()` | Individual product page data extraction |
| 3 | `amazon_pricing` source | `scraper/pricing.py` | `get_pricing()` | All seller offers for an ASIN (price intelligence) |
| 4 | `parse: true` | All scraper modules | All payloads | Structured auto-parsed JSON output (no HTML parsing) |
| 5 | `geo_location` | All scraper modules | All payloads | Locks results to US market (ZIP code: 90210) |
| 6 | Pagination (`start_page`) | `scraper/search.py` | `search_iphones()` loop | Collects 100 results across 7 pages |
| 7 | Async/Polling mode | `scraper/product.py` | `_poll_until_done()` | Non-blocking batch product scraping |
| 8 | Async/Callback mode | `scraper/callback.py` | `submit_with_callback()` | Documented alternative — webhook-based delivery |
| 9 | Batch submission | `scraper/product.py` | `scrape_products()` | Processes 100 products in chunks of 10 |
| 10 | Realtime endpoint | `scraper/client.py` | `realtime()` | Synchronous search + pricing requests |
| 11 | Async endpoint | `scraper/client.py` | `async_submit()` | Background job submission |
| 12 | Async results retrieval | `scraper/client.py` | `async_get_results()` | Fetch completed job results |
| 13 | `context: autoselect_variant` | `scraper/product.py` | `_process_batch()` | Accurate buybox pricing for variant products |
| 14 | Oxylabs Scheduler | `scraper/callback.py` | `submit_scheduled()` | Recurring jobs on cron schedule (no infrastructure needed) |
| 15 | Cloud Storage delivery | `scraper/callback.py` | `submit_scheduled()` | Results pushed directly to client's S3/GCS bucket |

## Feature Details

### 1. amazon_search (Realtime)
Used for the search phase. Sends a synchronous request to get paginated search results.
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

### 6. Pagination
Amazon shows ~16 organic results per page. We request 7 pages (`start_page: 1..7`) to
collect 100+ results, then trim to exactly 100.

### 7. Async/Polling
For 100 product pages, synchronous requests would be too slow. Async mode lets us
submit all jobs quickly, then poll for completion. Jobs run in parallel on Oxylabs' side.

### 8. Async/Callback (Alternative)
For production, a callback URL eliminates polling overhead entirely. Oxylabs POSTs
results to your endpoint when each job completes. See `scraper/callback.py`.

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
Oxylabs runs scraping jobs on a recurring cron schedule — no cron, APScheduler,
or scheduling infrastructure needed on the client side.

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
