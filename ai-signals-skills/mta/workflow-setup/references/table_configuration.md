# MTA Journey Analytics — Table Configuration Guide

This guide explains how to configure each type of source table for the MTA Journey Analytics workflow. Each table becomes a touchpoint source in the unified journey.

## MTA Table Columns (vs RFM)

MTA tables require channel-identification columns that RFM does not:

| Column | Purpose | Web Tables | Email | Sales | Orders |
|--------|---------|-----------|-------|-------|--------|
| `url_col` | Page URL | `td_url` | `CAST(NULL AS VARCHAR)` | `CAST(NULL AS VARCHAR)` | `CAST(NULL AS VARCHAR)` |
| `referral_col` | Traffic referrer | `td_referrer` | `'email'` | `CAST(NULL AS VARCHAR)` | `CAST(NULL AS VARCHAR)` |
| `medium_col` | Marketing medium | UTM extraction | `'email'` | `'sales_rep_interactions'` | `CAST(NULL AS VARCHAR)` |
| `source_col` | Marketing source | UTM extraction | `'sfmc'` | column or hardcoded | `CAST(NULL AS VARCHAR)` |
| `campaign_col` | Campaign name | UTM extraction | campaign column | topic column | `CAST(NULL AS VARCHAR)` |
| `utm_mailing_col` | Mailing ID | UTM extraction | campaign column | topic column | `CAST(NULL AS VARCHAR)` |
| `context_col` | Touchpoint context | page title | email name | topic | order type |
| `event_type` | Event label | `'web activity'` | `CONCAT('email_', event_type)` | `CONCAT('sales_rep_interactions_', source)` | `CONCAT(lower(order_type), '_order')` |
| `conversion_flag` | Is this a conversion? | URL pattern match | `0.0` | `0.0` | `1.0` |
| `item_price` | Revenue value | `1.0` (pageview count) | `0.0` | `0.0` | revenue column |

## Table Type: Pageviews / Web Activity

### Purpose
Web touchpoints with UTM-based channel attribution. Can also define web-based conversions (e.g., thank-you page).

### Required Columns
- **Timestamp**: `time`
- **User ID**: `canonical_id`
- **URL**: `td_url` or `page_url` (for UTM extraction and conversion pattern matching)

### Discovery Steps — Run all steps in order before configuring

**Step 1 — Identify the URL column name:**
```sql
DESCRIBE database_name.web_table;
```
Look for a column named `td_url`, `page_url`, `url`, `landing_url`, etc. Use the actual name as `<url_col>` in the steps below.

**Step 2 — REQUIRED: Check UTM coverage (substitute actual `<url_col>` from Step 1):**
```sql
SELECT
  COUNT(*) AS total_rows,
  COUNT(CASE WHEN url_extract_parameter(<url_col>, 'utm_source') IS NOT NULL THEN 1 END) AS has_utm_source,
  COUNT(CASE WHEN url_extract_parameter(<url_col>, 'utm_medium') IS NOT NULL THEN 1 END) AS has_utm_medium,
  COUNT(CASE WHEN url_extract_parameter(<url_col>, 'utm_campaign') IS NOT NULL THEN 1 END) AS has_utm_campaign
FROM database_name.web_table;
```
> ⚠️ **Do NOT assume UTM absence from visual inspection of sample URL values. You must run this query.** Clean-looking path values (e.g. `/blog/best-suvs-2025`) may still have UTM params on a large fraction of rows.

**Step 3 — If UTMs present (> 0 rows), sample the values:**
```sql
SELECT
  url_extract_parameter(<url_col>, 'utm_source') AS utm_source,
  url_extract_parameter(<url_col>, 'utm_medium') AS utm_medium,
  url_extract_parameter(<url_col>, 'utm_campaign') AS utm_campaign,
  COUNT(*) AS cnt
FROM database_name.web_table
WHERE <url_col> LIKE '%utm_%'
GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 20;
```

**Step 4 — Check for conversion URL patterns:**
```sql
SELECT td_path, COUNT(*) FROM database_name.web_table
WHERE REGEXP_LIKE(lower(td_path), 'thank|confirm|success|checkout')
GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
```

### Configuration Template

```yaml
- src_table: database_name.enriched_pageviews
  table_description: 'Web Activity data'
  name: pageviews
  unixtime_col: time
  url_col: td_url
  referral_col: td_referrer
  medium_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_medium'), url_extract_parameter(LOWER(td_url),'medium'))"
  source_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_source'), url_extract_parameter(LOWER(td_url),'source'))"
  campaign_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_campaign'), url_extract_parameter(LOWER(td_url),'campaign'))"
  utm_mailing_col: "COALESCE(url_extract_parameter(LOWER(td_url),'utm_mailing'), url_extract_parameter(LOWER(td_url),'mailing'))"
  context_col: td_title
  event_type: "'web activity'"
  custom_filter: "${unique_user_id} IS NOT NULL"
  conversion_flag: "IF(REGEXP_LIKE(lower(td_path), 'thank_you'), 1.0, 0.0)"
  item_price: 1.0
  apply_time_filter: false
  query_type:
```

### Key Decisions
- **conversion_flag**: Customize the URL regex to match the customer's conversion pages
- **custom_filter**: Add language filter, bot exclusion, etc. as needed
- **item_price**: Use `1.0` as a count proxy, or a real revenue column if available

### Common URL Column Variations

| Table Pattern | URL Column | Referrer Column | Path Column |
|--------------|-----------|----------------|-------------|
| `enriched_pageviews` | `td_url` | `td_referrer` | `td_path` |
| `web_events` | `page_url` | `referrer_url` | `page_path` |
| `page_views` | `url` | `referrer` | `path` |

---

## Table Type: Email Events

### Purpose
Email channel touchpoints. Not conversions — `conversion_flag: 0.0`.

### Required Columns
- **Timestamp**: `time`
- **User ID**: `canonical_id`
- **Event type**: `event_type` (to filter out 'send' events)
- **Campaign name**: `campaign_name` or `email_name`

### Discovery Steps

```sql
SHOW TABLES IN database_name LIKE '%email%';
DESCRIBE database_name.enriched_email_events;

-- Check event types
SELECT DISTINCT event_type, COUNT(*) FROM database_name.enriched_email_events
GROUP BY 1 ORDER BY 2 DESC;

-- Check campaign names
SELECT DISTINCT campaign_name, COUNT(*) FROM database_name.enriched_email_events
GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
```

### Configuration Template

```yaml
- src_table: database_name.enriched_email_events
  table_description: 'Email activity from [ESP name]'
  name: email_events
  unixtime_col: time
  url_col: CAST(NULL AS VARCHAR)
  referral_col: "'email'"
  medium_col: "'email'"
  source_col: "'sfmc'"
  campaign_col: "REGEXP_REPLACE(lower(campaign_name), '[- ]', '_')"
  utm_mailing_col: "REGEXP_REPLACE(lower(campaign_name), '[- ]', '_')"
  context_col: "REGEXP_REPLACE(lower(email_name), '[- ]', '_')"
  event_type: "CONCAT('email_', event_type)"
  custom_filter: "${unique_user_id} IS NOT NULL AND NOT REGEXP_LIKE(lower(event_type), 'send')"
  conversion_flag: 0.0
  item_price: 0.0
  apply_time_filter: false
  query_type:
```

### Key Decisions
- **source_col**: Hardcode to ESP name — `'sfmc'`, `'marketo'`, `'braze'`, `'hubspot'`
- **custom_filter**: Always exclude 'send' events. Add other exclusions as needed (bounce, spam).
- **campaign_col**: Normalize campaign names (lowercase, replace spaces/hyphens with underscores)

### Email Event Types Reference

| Event Type | Include? | Reason |
|-----------|----------|--------|
| `sent` / `send` | No | Not engagement |
| `delivered` | No | Technical event |
| `open` | Yes | Engagement |
| `click` | Yes | Strong engagement |
| `conversion` | Yes | Strongest engagement |
| `reply` | Yes | Engagement |
| `forward` / `friendforward` | Yes | Engagement |
| `unsubscribe` | Yes | Negative but still engagement signal |
| `bounce` | No | Technical failure |
| `spam` | No | Not valid engagement |

---

## Table Type: Sales Rep Interactions / CRM

### Purpose
Offline/sales channel touchpoints. Not conversions — `conversion_flag: 0.0`.

### Required Columns
- **Timestamp**: `time`
- **User ID**: `canonical_id`
- **Source/Topic**: For channel labeling

### Discovery Steps

```sql
SHOW TABLES IN database_name LIKE '%sales%';
SHOW TABLES IN database_name LIKE '%crm%';
DESCRIBE database_name.enriched_sales_rep_interactions;
SELECT * FROM database_name.enriched_sales_rep_interactions LIMIT 10;

-- Check sources and topics
SELECT DISTINCT source, COUNT(*) FROM database_name.enriched_sales_rep_interactions GROUP BY 1 ORDER BY 2 DESC;
SELECT DISTINCT topic, COUNT(*) FROM database_name.enriched_sales_rep_interactions GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
```

### Configuration Template

```yaml
- src_table: database_name.enriched_sales_rep_interactions
  table_description: 'Sales rep notes from SFDC'
  name: sales_rep_interactions
  unixtime_col: time
  url_col: CAST(NULL AS VARCHAR)
  referral_col: CAST(NULL AS VARCHAR)
  medium_col: "'sales_rep_interactions'"
  source_col: source
  campaign_col: topic
  utm_mailing_col: topic
  context_col: topic
  event_type: "CONCAT('sales_rep_interactions_', source)"
  custom_filter: ${unique_user_id} IS NOT NULL
  conversion_flag: 0.0
  item_price: 0.0
  apply_time_filter: false
  query_type:
```

---

## Table Type: Orders / Conversion Events

### Purpose
These ARE the conversion events. `conversion_flag: 1.0`.

### Required Columns
- **Timestamp**: `time`
- **User ID**: `canonical_id`
- **Order status**: To filter valid orders only
- **Revenue column**: `unit_price`, `total_amount`, etc.

### Discovery Steps

```sql
SHOW TABLES IN database_name LIKE '%order%';
DESCRIBE database_name.enriched_orders;

-- Check order statuses
SELECT DISTINCT order_status, COUNT(*) FROM database_name.enriched_orders GROUP BY 1 ORDER BY 2 DESC;

-- Check revenue column
SELECT MIN(unit_price), MAX(unit_price), AVG(unit_price)
FROM database_name.enriched_orders WHERE order_status IN ('COMPLETE', 'PROCESSING');

-- Check order types
SELECT DISTINCT order_type, COUNT(*) FROM database_name.enriched_orders GROUP BY 1 ORDER BY 2 DESC;
```

### Configuration Template

```yaml
- src_table: database_name.enriched_orders
  table_description: 'Order history with item price and status'
  name: order_events
  unixtime_col: time
  url_col: CAST(NULL AS VARCHAR)
  referral_col: CAST(NULL AS VARCHAR)
  medium_col: CAST(NULL AS VARCHAR)
  source_col: CAST(NULL AS VARCHAR)
  campaign_col: CAST(NULL AS VARCHAR)
  utm_mailing_col: CAST(NULL AS VARCHAR)
  context_col: order_type
  event_type: "CONCAT(lower(order_type), '_order')"
  custom_filter: "${unique_user_id} IS NOT NULL AND order_status IN ('COMPLETE', 'PROCESSING')"
  conversion_flag: 1.0
  item_price: unit_price
  apply_time_filter: false
  query_type: 'custom'
```

### Key Decisions
- **conversion_flag: 1.0** — this marks the conversion goal for attribution
- **item_price**: Revenue column for spend/ROI analysis
- **custom_filter**: Only valid order statuses (exclude cancelled, returned, failed)
- **query_type: 'custom'**: Use when complex SQL is needed — put it in `sql/union_src_tables/order_events.sql`
- **Channel columns all NULL**: Orders don't belong to a marketing channel — they're the goal

### Order Status Filtering

Always check distinct statuses first. Common patterns:

**Include (valid conversions):** `COMPLETE`, `PROCESSING`, `completed`, `shipped`, `delivered`, `paid`
**Exclude (not conversions):** `cancelled`, `returned`, `refunded`, `failed`, `abandoned`

---

## Troubleshooting

### No UTM parameters in web data
If `url_extract_parameter` returns NULL for most rows, check if UTM params are in a different column or format:
```sql
SELECT td_url, COUNT(*) FROM database_name.enriched_pageviews
WHERE url_extract_parameter(td_url, 'utm_source') IS NOT NULL
GROUP BY 1 LIMIT 10;
```
Fallback: use `td_referrer` to derive source, or hardcode `medium_col: "'direct'"`.

### Too many channels (noisy output)
Increase `top_k_channel_perc` (e.g., `0.05`) to collapse more low-frequency channels into 'others'.

### No conversions detected
Verify `conversion_flag` logic:
```sql
-- For web conversions
SELECT COUNT(*) FROM database_name.enriched_pageviews
WHERE REGEXP_LIKE(lower(td_path), 'thank_you');

-- For order conversions
SELECT COUNT(*) FROM database_name.enriched_orders
WHERE order_status IN ('COMPLETE', 'PROCESSING');
```
