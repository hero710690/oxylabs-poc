# Pricing Calculation for TechNovaAI

## Usage Estimate

### Per Scraping Run
| Request Type | Count | Source |
|---|---|---|
| Search pages (amazon source, URL) | 5 | 5 pages × 1 request each |
| Product pages (amazon_product) | 100 | 1 request per product |
| Pricing pages (amazon_pricing) | 5 | Top 5 ASINs × 1 request each |
| **Total per run** | **110** | |

### Monthly Volume
| Metric | Value |
|---|---|
| Runs per day | 24 (hourly) |
| Runs per month | 720 |
| Requests per month | **79,200** |

## Pricing Plans (Web Scraper API)

Source: https://oxylabs.io/products/scraper-api/web/pricing

| Plan | Monthly Price | Rate (Amazon) | Results Included |
|------|--------------|---------------|-----------------|
| **Micro** | $49/mo | $0.50/1K | Up to 98,000 |
| **Starter** | $99/mo | $0.45/1K | Up to 220,000 |
| **Advanced** | $249/mo | $0.40/1K | Up to 622,500 |

Note: Pricing is success-based — failed attempts (5xx/6xx) are not charged.

All plans include: scheduler, batch queries, custom parser, cloud integration, headless browser, 24/7 support.

## Cost Calculation

### Option A: Micro Plan ($49/mo)
- 79,200 requests × $0.50/1K = **$39.60 usage**
- Fits within Micro plan's 98K results cap
- **Total: $49/month** (plan minimum)

### Option B: Starter Plan ($99/mo) — Recommended
- 79,200 requests × $0.45/1K = **$35.64 usage**
- Well within 220K results cap — room to scale to 2x volume
- **Total: $99/month** (plan minimum)

### Option C: Pay scale comparison
| Scenario | Requests/mo | Micro ($0.50) | Starter ($0.45) |
|----------|-------------|---------------|-----------------|
| Hourly, all day | 79,200 | $49 (plan min) | $99 (plan min) |
| Business hours only (10 runs/day) | 33,000 | $49 (plan min) | $99 (plan min) |
| Hourly + all 100 ASINs priced | 175,200 | $87.60 | $99 (plan min) |
| Hourly + all 100 ASINs + 2x search | 271,200 | Over cap | $122.04 |

## Recommendation

**Recommended plan: Micro ($49/mo)** for PoC/initial deployment.

Rationale:
- 79K requests/month fits comfortably within 98K cap
- Lowest cost to validate the pipeline in production
- Upgrade to Starter when scaling to full pricing coverage (all 100 ASINs)

**Scale path:**
1. Start with Micro ($49/mo) — current pipeline (search + products + top 5 pricing)
2. Upgrade to Starter ($99/mo) — when expanding pricing to all 100 ASINs (~175K requests)
3. Upgrade to Advanced ($249/mo) — when adding multiple categories or marketplaces

## ROI Context

For a company entering the smartphone resale market, $49–99/month for real-time competitive
intelligence on 100 listings is minimal compared to:
- Potential pricing mistakes from stale data (we detected a $170 price drop in one hour)
- Engineering cost of building/maintaining a custom scraper + proxy infrastructure
- Anti-bot evasion engineering (Oxylabs handles this — zero blocks in our PoC)
