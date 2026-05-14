# Product & Developer Feedback

Feedback on the developer experience of using Oxylabs Web Scraper API, collected during PoC implementation.

## First Impressions

Getting started was straightforward — username/password auth, simple JSON payloads, and the realtime endpoint gave instant results. The mental model is easy to grasp: pick a source, send a query, get structured data back. Felt productive within minutes.

## What Felt Great

- **Structured parsing is the killer feature.** Setting `parse: true` and getting back a clean JSON object with 50+ fields per product felt like magic. No HTML parsing, no CSS selectors to maintain, no worrying about layout changes breaking things.
- **Anti-bot handling is invisible.** Zero CAPTCHAs, zero blocks across 100+ product requests. It just works. This is exactly the value prop for a team like TechNovaAI who doesn't want to deal with this.
- **Response speed.** Search results in 3-4 seconds, product pages in 5-15 seconds via async. Fast enough to feel interactive during development.
- **Async job reliability.** Submitted 100 product jobs across 10 batches — every single one completed without faulting. The pending → running → done state machine is clean.

## What Felt Rough

- **The async workflow has a hidden step.** When a job hits "done" status, the results aren't in the poll response. You need to know to hit a separate `/results` endpoint. This tripped us up — all 100 product requests silently returned no data until we discovered the extra fetch. Most async APIs include results in the final status response.
- **`geo_location` format is non-obvious.** We tried `"United States"` and got a 400 with no hint of what format is expected. Turns out it wants a ZIP code (`"90210"`). Trial and error shouldn't be needed for a core parameter.
- **Fewer results per page than expected.** Amazon search returned ~16 organic results per page, not ~48. Not a bug, but it meant more API calls (and cost) than we planned for.
- **Field naming differs between sources.** Search results use `is_prime`, product pages use `is_prime_eligible`. Small thing, but it adds friction when merging data from both sources.
- **`description` field type is inconsistent.** Some products return a string, others return a list of image URLs. Requires defensive coding for what should be a simple field.

## The "Feel" Summary

It feels like a product built by infrastructure engineers who deeply understand the scraping problem, but the developer-facing layer could use more polish. The hard stuff (anti-bot, parsing, reliability) is excellent. The easy stuff (error messages, field consistency, documentation of workflows) has some gaps that slow down first-time integration.

Once you get past the initial gotchas, it's a pleasure to use. The data quality is genuinely impressive.
