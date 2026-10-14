# RFM Customer Segmentation — Business Context Guide

Use this document to interpret RFM scores, customer segments, and behavioral patterns. For table schemas and column descriptions, refer to the separate data dictionary.

---

## RFM Methodology

RFM segments customers on three behavioral dimensions:

### Recency (R)
- **What it measures**: Days since the customer's last interaction (pageview, email engagement, purchase, sales interaction)
- **Scoring**: Lower recency = higher quartile (r_quartile 4 = most recent activity)
- **Business meaning**: Customers who interacted recently are more likely to respond to outreach

### Frequency (F)
- **What it measures**: Total number of interactions across all tracked sources
- **Scoring**: Higher frequency = higher quartile (f_quartile 4 = most interactions)
- **Business meaning**: Frequent customers show strong engagement and brand affinity

### Monetary (M)
- **What it measures**: Total order/purchase value (sum of `order_amount` across order tables)
- **Scoring**: Higher monetary = higher quartile (m_quartile 4 = highest spend)
- **Business meaning**: High-spending customers represent the most revenue potential
- **Note**: If no order data exists, all M quartiles will reflect zero-spend distributions. Monetary percentiles are computed only for values > 0.05 to avoid skew.

## Scoring Methodology

- Each dimension is independently scored using **quartile-based binning** (1-4 scale)
- Quartile boundaries use the 25th, 50th, and 75th percentiles
- Score 1 = lowest quartile, Score 4 = highest quartile
- Combined quartile label format: `R4F3M2` (stored as `rfm_quartile`)
- Overall `rfm_score` = average of (r_quartile + f_quartile + m_quartile) / 3

**Note:** The `num_bins` parameter in the YAML config controls histogram display granularity, NOT the scoring scale. Scoring always uses quartiles (1-4).

## Customer Segments

Segments are defined by R/F/M quartile combinations in the `rfm_custom.sql` scoring logic:

| Segment | R | F | M | Strategy |
|---------|---|---|---|----------|
| **Champions** | 4 | 4 | 4 | Reward, upsell, ask for referrals |
| **Loyal Customers** | 3-4 | 3-4 | 3-4 | Cross-sell, loyalty programs |
| **Potential Loyalists** | 3-4 | 2-3 | 2-3 | Nurture with onboarding, incentives |
| **Promising** | 3-4 | 2+ | 2+ | Engage to build frequency (at least one of F/M is 2+) |
| **New Customers** | 3-4 | low | low | Welcome series, first-purchase incentives |
| **Cannot lose them** | 2 | any | 3-4 | Urgent re-engagement, personal outreach — high spenders at risk of churn |
| **Need attention** | 2 | 2+ | 2 | Active but declining — re-engage before they slip |
| **Hibernating** | 2 | low | low | Low-cost re-activation or suppress |
| **High Value Sleeping** | 1 | any | 3+ (or M=2 with F>=2) | Past loyalists who stopped engaging — worth awakening |
| **Lost customers** | 1 | low | low | Lowest priority — suppress from campaigns, data hygiene |

### Segment Definitions (human-readable)

| Segment | Definition |
|---------|-----------|
| Champions | Top customers. Bought recently, buy often and spend the most. |
| Loyal Customers | Spend good money. Responsive to promotions with high activity. Very active and valuable. |
| Potential Loyalists | Recently engaged. Decent spend and frequency, but can be improved over time. |
| Promising | Bought recently. Some spend above average, but many fall below AVG. |
| New Customers | Non-Buyers. Recently engaged with low frequency. |
| Cannot lose them | High Spenders likely to Churn. Spend a lot in the past, but have not engaged in a long time. |
| Need attention | Active customers, but recency and spend is near or below AVG. |
| Hibernating | Non-Buyers. Below AVG Recency and Frequency. Not worth giving attention. |
| High Value Sleeping | Past potential loyalist sleeping. Worth awakening their loosing interests before they become unresponsive. |
| Lost customers | Non-Buyers. Lowest recency, but with some past activity. Lowest priority. |

## Data Sources

RFM scores are computed from unioned customer activity across multiple behavioral data sources. Common sources include:

| Source | Contributes To | Notes |
|--------|---------------|-------|
| Web pageviews | R, F | Site engagement signals (`order_amount: 0.0`) |
| Email events | R, F | Opens, clicks — not sends (`order_amount: 0.0`) |
| Orders/purchases | R, F, M | Transaction data with monetary value |
| Sales interactions | R, F | CRM touchpoints — calls, meetings (`order_amount: 0.0`) |
| Customer support | R, F | Support ticket activity (`order_amount: 0.0`) |

## Key Business Rules

- **Monetary value**: Only order/purchase tables contribute to the M dimension. All other sources use `order_amount: 0.0`
- **Engagement-only events**: Email 'sent' events are excluded — only open, click, conversion, etc. count as interactions
- **Valid orders only**: Cancelled and returned orders are filtered out before scoring
- **Join key consistency**: All sources must use the same configured customer identifier (for example, `td_consumer_id`, `td_canonical_id`, `canonical_id`, or `user_id`) for accurate per-profile scoring. Resolve the actual column with `DESCRIBE` before writing profile-level SQL; do not assume the example name.
- **Negative spend capped**: If total_spend is negative after summing, it's capped at 0 in the input table
