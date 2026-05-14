# Presentation Notes — TechNovaAI Demo

## Agenda
1. Problem recap: top 100 iPhone listings, hourly, structured data
2. Live demo: run the scraper, show output
3. Code walkthrough: highlight each Oxylabs feature (see FEATURES.md)
4. Pricing: walk through PRICING.md
5. Next steps & alternative products
6. Q&A

## Key Talking Points

### Why Oxylabs Web Scraper API?
- No anti-bot engineering needed — Oxylabs handles CAPTCHAs, IP rotation, fingerprinting
- Structured parsing (`parse: true`) eliminates HTML parsing maintenance
- Async mode enables scraping at scale without blocking
- Geo-targeting ensures US-specific data

### Demo Flow
1. Show `.env.example` — simple credential setup
2. Run `python main.py --once` — watch logs show search → product phases
3. Open output JSON — show structured data for all 100 products
4. Show scheduler running (or explain APScheduler config)

## Alternative Oxylabs Products

### E-Commerce Scraper API
- Purpose-built for e-commerce sites (Amazon, eBay, etc.)
- May offer higher-level abstractions for product data
- Worth evaluating if TechNovaAI expands to multiple marketplaces

### SERP Scraper API
- Optimized for search engine results pages
- Relevant if TechNovaAI also wants Google Shopping data
- Lower cost if only search-level data is needed

### Residential Proxies + Custom Scraper
- Full control over parsing logic
- Higher complexity and maintenance burden
- Only recommended if Oxylabs' parsed output doesn't meet specific needs

### Web Unblocker
- Proxy-like service that handles anti-bot for any URL
- Client builds their own parser
- More flexibility but more engineering effort

## Next Steps (Future Enhancements)

### Database Storage
- PostgreSQL or TimescaleDB for time-series price data
- Enables querying trends, deduplication, powering dashboards

### Production Deployment
- Docker container + docker-compose (cloud-agnostic)
- Works on AWS, GCP, Azure, or self-hosted
- Oxylabs built-in Scheduler as alternative to APScheduler

### Dashboard
- Market overview: all 100 listings at a glance
- Price monitoring: alerts on significant price drops
- Tools: Grafana, Metabase, or custom lightweight UI

### Historical Trend Analysis
Full competitive intelligence:
- Price fluctuation patterns (best times to buy/list)
- Ranking shifts (who's rising/falling)
- Delivery & Prime changes
- Sponsored spend patterns
