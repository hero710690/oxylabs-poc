# Product & Developer Feedback

Feedback on the developer experience of using Oxylabs Web Scraper API, collected during PoC implementation.

## First Impressions

Getting started was straightforward — username/password auth, simple JSON payloads, and the realtime endpoint gave instant results. The mental model is easy to grasp: pick a source, send a query, get structured data back. Felt productive within minutes.

## What Felt Great

- **Structured parsing is the killer feature.** Setting `parse: true` and getting back a clean JSON object with 50+ fields per product felt like magic. No HTML parsing, no CSS selectors to maintain, no worrying about layout changes breaking things.
- **Anti-bot handling is invisible.** Zero CAPTCHAs, zero blocks across 100+ product requests. It just works. This is exactly the value prop for a team like TechNovaAI who doesn't want to deal with this.
- **Response speed.** Search results in 3-4 seconds, product pages in 5-15 seconds via async. Fast enough to feel interactive during development.
- **Async job reliability.** Submitted 100 product jobs across 10 batches — every single one completed without faulting. The pending → running → done state machine is clean.
- **Rich data.** The `product_details` field alone has 50+ fields per iPhone listing. `amazon_pricing` gives every seller's offer in one call. More data than we expected.
- **Feature depth.** `autoselect_variant`, `context` parameters, multiple sort options — once you learn these exist, they unlock precise control over what data you get.

## What Felt Rough

- **Field naming differs between sources.** Search results use `is_prime`, product pages use `is_prime_eligible`. Small thing, but it adds friction when merging data from both sources.
- **`description` field type is inconsistent.** Some products return a string, others return a list of image URLs. Requires defensive coding for what should be a simple field.
- **Results per page is lower than expected.** Amazon search returned ~16 organic results per page. Not a bug, but it meant more pagination than anticipated (~7 pages for 100 results instead of 3).

## The "Feel" Summary

It feels like a powerful, reliable product. The hard stuff (anti-bot, parsing, reliability, data richness) is excellent. The API is well-designed with good separation of concerns (realtime vs async, different sources for different data needs).

Minor friction points are around field consistency across sources — would be nice if `amazon_search` and `amazon_product` used identical field names for the same concepts. But these are easily worked around once you know about them.

Overall: the API does what it promises, reliably, with rich data. Exactly what a team without scraping expertise needs.
