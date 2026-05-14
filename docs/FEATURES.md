# Oxylabs Web Scraper API — Features Used

This document maps every Oxylabs feature used in this PoC to its location in the code.

## Feature Matrix

| # | Feature | File | Line/Function | Purpose |
|---|---------|------|---------------|---------|
| 1 | `amazon_search` source | `scraper/search.py` | `search_iphones()` | Paginated search results for "iPhone" on Amazon US |
| 2 | `amazon_product` source | `scraper/product.py` | `_process_batch()` | Individual product page data extraction |
| 3 | `parse: true` | `scraper/search.py`, `scraper/product.py` | Both payload constructions | Structured auto-parsed JSON output (no manual HTML parsing) |
| 4 | `geo_location` | `scraper/search.py`, `scraper/product.py` | Both payloads | Locks results to United States market |
| 5 | Pagination (`start_page`) | `scraper/search.py` | `search_iphones()` loop | Collects 100 results across 3 pages |
| 6 | Async/Polling mode | `scraper/product.py` | `_poll_until_done()` | Non-blocking batch product scraping |
| 7 | Async/Callback mode | `scraper/callback.py` | `submit_with_callback()` | Documented alternative — webhook-based results delivery |
| 8 | Batch submission | `scraper/product.py` | `scrape_products()` | Processes 100 products in chunks of 10 |
| 9 | Realtime endpoint | `scraper/client.py` | `realtime()` | Synchronous search requests |
| 10 | Async endpoint | `scraper/client.py` | `async_submit()` | Background job submission |

## Feature Details

### 1. amazon_search (Realtime)
Used for the search phase. Sends a synchronous request to get paginated search results.
The `parse: true` flag means Oxylabs returns structured JSON with organic/paid results already
separated — no HTML parsing needed.

### 2. amazon_product (Async)
Used for product page scraping. Each product is submitted as an async job to avoid
blocking. Results are polled in parallel across the batch.

### 3. Structured Parsing
By setting `parse: true`, Oxylabs handles all the anti-bot logic AND returns clean
structured data. Without this, we'd need to parse raw HTML ourselves.

### 4. Geo-targeting
`geo_location: "United States"` ensures we see US-specific pricing, Prime eligibility,
and delivery estimates — critical for TechNovaAI's US market analysis.

### 5. Pagination
Amazon shows ~48 results per page. We request 3 pages (`start_page: 1, 2, 3`) to
collect 100+ results, then trim to exactly 100.

### 6. Async/Polling
For 100 product pages, synchronous requests would be too slow. Async mode lets us
submit all jobs quickly, then poll for completion. Jobs run in parallel on Oxylabs' side.

### 7. Async/Callback (Alternative)
For production, a callback URL eliminates polling overhead entirely. Oxylabs POSTs
results to your endpoint when each job completes. See `scraper/callback.py`.

### 8. Batch Processing
We chunk 100 products into groups of 10. This balances throughput with manageability —
we can track progress, handle failures per-batch, and avoid overwhelming the API.
