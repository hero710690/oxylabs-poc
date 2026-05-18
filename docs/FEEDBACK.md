# Product & Developer Feedback

Feedback on the developer experience of using Oxylabs Web Scraper API, collected during PoC implementation.

## First Impressions

Getting started was straightforward — username/password auth, simple JSON payloads, and the realtime endpoint gave instant results. The mental model is easy to grasp: pick a source, send a query, get structured data back. Felt productive within minutes.

## What Felt Great

- **Structured parsing is the killer feature.** Setting `parse: true` and getting back a clean JSON object with 50+ fields per product felt like magic. No HTML parsing, no CSS selectors to maintain, no worrying about layout changes breaking things.
- **Anti-bot handling is invisible.** Zero CAPTCHAs, zero blocks across 100+ product requests. It just works. This is exactly the value prop for a team like TechNovaAI who doesn't want to deal with this.
- **Response speed.** Search results in 3-4 seconds, product pages in 5-15 seconds via async. Fast enough to feel interactive during development.
- **Async job reliability.** Submitted 100 product jobs concurrently (50/s chunks to respect the documented rate limit) — every single one completed without faulting. The pending → running → done state machine is clean.
- **Rich data.** The `product_details` field alone has 50+ fields per iPhone listing. `amazon_pricing` gives every seller's offer in one call. More data than we expected.
- **Feature depth.** `autoselect_variant`, `context` parameters, multiple sort options — once you learn these exist, they unlock precise control over what data you get.

## What Felt Rough

- **Field naming differs between sources.** Search results use `is_prime`, product pages use `is_prime_eligible`. Same concept, different field names — adds friction when merging data.
  - Evidence: `amazon_search` response → `"is_prime": true`
  - Evidence: `amazon_product` response (same ASIN) → `"is_prime_eligible": true`
  - Workaround: `search.py` reads `item.get("is_prime")`, `product.py` reads `content.get("is_prime_eligible")`

- **`description` field type is inconsistent.** Some products return a string, others return a list of image URLs. Requires defensive coding for what should be a simple field.
  - Evidence: ASIN B0CMPMY9ZZ → `"description": "Apple iPhone 15, 128GB..."` (string)
  - Evidence: ASIN B0F7LP2K5D → `"description": ["https://m.media-amazon.com/images/S/aplus-media-library-service-media/9e91bec9...", ...]` (list of 10 image URLs)
  - Workaround: `if isinstance(description, list): description = None`


## Feature Request: Scheduler Job Chaining

The Scheduler supports multiple `items` in a single schedule, but all must be defined statically at creation time. There's no way to **chain jobs** — where the output of one job (e.g., ASINs discovered from a search) feeds as input to the next job (e.g., product page scraping for those ASINs).

Our pipeline requires 3 phases: search → product pages → pricing. The ASINs change every hour (we observed 13 listings rotate out in a single hour), so we can't hardcode them. This forces us to maintain our own scheduling infrastructure (crontab + Python orchestration) instead of using the Oxylabs Scheduler end-to-end.

**What would help:** A pipeline/workflow mode in the Scheduler that supports job dependencies — "when job A completes, extract field X from results, and use those values as `query` for job B." This would let teams like TechNovaAI replace custom orchestration entirely with a fully managed Oxylabs solution.

---

## The "Feel" Summary

It feels like a powerful, reliable product. The hard stuff (anti-bot, parsing, reliability, data richness) is excellent. The API is well-designed with good separation of concerns (realtime vs async, different sources for different data needs).

Minor friction points are around field consistency across sources. It would be nice if `amazon_search` and `amazon_product` used identical field names for the same concepts. But these are easily worked around once you know about them.

Overall: the API does what it promises, reliably, with rich data. Exactly what a team without scraping expertise needs.
