# Product & Developer Feedback

Feedback collected during PoC implementation for the Oxylabs product team.

## API Usability / Developer Experience

### geo_location parameter format
- **Issue:** The `geo_location` parameter for Amazon sources does not accept country names like `"United States"`. It requires a US ZIP code (e.g., `"90210"`).
- **Impact:** We got a `400 Bad Request` with message `"geo_location 'United States' is not valid."` — no guidance on what format is expected.
- **Suggestion:** Either accept country names as aliases, or include expected format in the error message (e.g., "Use a 5-digit US ZIP code for Amazon US").

### Async results require separate endpoint
- **Issue:** After polling shows status `"done"`, the results are NOT included in the poll response. You must make an additional GET to `{job_id}/results`.
- **Impact:** Our initial implementation expected results in the poll response (like many other async APIs). This caused all product scraping to silently fail with `KeyError: 'results'`.
- **Suggestion:** Either include results in the final poll response when status is "done", or make this two-step process more prominent in documentation.

### Search results per page
- **Issue:** We expected ~48 results per page (standard Amazon desktop view), but only got ~16-17 organic + 1-2 paid per page.
- **Impact:** Had to increase pagination from 3 to 7 pages to collect 100 results (more API calls = higher cost).
- **Suggestion:** Document expected results-per-page for each source, or offer a `results_per_page` parameter.

## Documentation

- The async workflow (submit → poll → fetch results) needs a clearer end-to-end example showing the separate results fetch step.
- `geo_location` accepted formats should be documented per source type (Amazon uses ZIP codes).

## Parsing Accuracy (`parse: true`)

### What worked well:
- `title`, `price`, `currency`, `asin` — always present and accurate
- `product_details` — rich specifications dictionary (52 fields for an iPhone listing)
- `is_prime_eligible` — correct boolean
- `delivery` — structured array with type + date

### Issues found:
- **`description` field returns image URLs as a list** on some products instead of the text description. 4 out of 100 products had `description` as a list of image URLs rather than a string. Required defensive handling.
- **Field naming inconsistency:** `is_prime_eligible` (product page) vs `is_prime` (search results) — different field names for the same concept across sources.

## Feature Requests

1. **Consistent field naming** across `amazon_search` and `amazon_product` sources (e.g., both use `is_prime` or both use `is_prime_eligible`)
2. **Include results in final poll response** when status is "done" (save an extra API call)
3. **Better error messages** with expected parameter formats
4. **`results_per_page` control** for search sources

## Error Messages / Debugging

- `400 Bad Request` for invalid `geo_location` — message says the value is "not valid" but doesn't suggest the correct format
- No issues with authentication errors (clear 401 on bad credentials)
- Async job status transitions (pending → running → done) work cleanly

## Overall Impressions

**Strengths:**
- Structured parsing (`parse: true`) delivers excellent data quality — product_details alone has 52 fields
- Async mode works reliably for batch product scraping
- Response times are fast (3-4s for search, 5-15s for async product jobs)
- Anti-bot handling is completely invisible to us (no CAPTCHAs, no blocks)

**Areas for improvement:**
- Developer experience on first integration has some "gotcha" moments (geo_location format, async results endpoint)
- Documentation could better highlight these patterns
- 96/100 success rate on first real run is good, but the 4 failures were due to inconsistent `description` field types
