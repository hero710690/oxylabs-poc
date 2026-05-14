# Pricing Calculation for TechNovaAI

## Usage Estimate

### Per Scraping Run
| Request Type | Count | Source |
|---|---|---|
| Search pages (amazon_search) | 7 | 7 pages × 1 request each |
| Product pages (amazon_product) | 100 | 1 request per product |
| Pricing pages (amazon_pricing) | 5 | Top 5 ASINs × 1 request each |
| **Total per run** | **112** | |

### Monthly Volume
| Metric | Value |
|---|---|
| Runs per day | 24 (hourly) |
| Runs per month | 720 |
| Requests per month | **80,640** |

## Pricing Tiers (Web Scraper API)

*Note: Verify current pricing at oxylabs.io — rates below are based on publicly available information.*

### Pay As You Go
- Amazon search: ~$3.00 per 1,000 requests
- Amazon product: ~$3.00 per 1,000 requests

**Estimated monthly cost:**
- Search: 7 × 720 = 5,040 requests → ~$15.12
- Product: 100 × 720 = 72,000 requests → ~$216.00
- Pricing: 5 × 720 = 3,600 requests → ~$10.80
- **Total: ~$241.92/month**

### Subscription Plans
Higher volume plans typically offer discounts:
- Starter plans may reduce per-request cost by 20-30%
- Enterprise plans offer custom pricing for sustained high volume

## Recommendation

**Recommended plan: Subscription (Starter or Growth tier)**

Rationale:
- 80K requests/month is consistent and predictable
- Subscription plans offer better per-request rates
- TechNovaAI's use case is long-running (competitive monitoring), not one-off

**Cost optimization tips:**
1. If only hourly data is needed during business hours (8am-6pm), reduce to 10 runs/day → ~30,900 requests/month
2. Consider if all 100 products need hourly refresh, or if top 20 could be hourly with rest daily
3. Ask Oxylabs sales for volume discount at 80K/month sustained

## ROI Context

For a company entering the smartphone resale market, $200-250/month for real-time competitive
intelligence on 100 listings is minimal compared to:
- Potential pricing mistakes from stale data
- Engineering cost of building/maintaining a custom scraper
- Anti-bot evasion engineering (Oxylabs handles this entirely)
