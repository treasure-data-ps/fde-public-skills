# Table Configuration Guide

This guide explains how to configure each type of table for RFM analysis.

## Table Configuration Workflow

For each table you discover:
1. Identify the table type (pageviews, orders, emails, etc.)
2. Find required columns (time, user ID, amount if applicable)
3. Analyze filter columns (status, event_type, etc.)
4. Generate the YAML configuration

## Table Type: Pageviews / Web Activity

### Purpose
Track website/app activity for **Recency** and **Frequency** metrics.

### Required Columns
- **Timestamp**: When the pageview occurred
- **User ID**: Who viewed the page

### Configuration Template
```yaml
- src_table: database_name.table_name
  name: 'pageviews'
  unixtime_col: time
  join_key: canonical_id
  order_amount: 0.0
  custom_filter:
  apply_time_filter: 'no'
  query_type:
```

### Discovery Steps

1. **Find the table**:
```sql
-- List tables that might contain pageviews
SHOW TABLES IN database_name LIKE '%pageview%';
SHOW TABLES IN database_name LIKE '%web_event%';
SHOW TABLES IN database_name LIKE '%activity%';
```

2. **Check the schema**:
```sql
DESCRIBE database_name.enriched_pageviews;
```

3. **Sample the data**:
```sql
SELECT * FROM database_name.enriched_pageviews LIMIT 10;
```

4. **Identify columns**:
- Time column: Look for `time`, `timestamp`, `event_time`, `created_at`
- User ID: Look for `canonical_id`, `cdp_profile_id`, `user_id`, `visitor_id`

### Common Variations

| Table Name Pattern | Common Time Columns | Common User ID Columns |
|-------------------|---------------------|------------------------|
| `enriched_pageviews` | `time` | `canonical_id` |
| `web_events` | `event_time`, `timestamp` | `user_id`, `visitor_id` |
| `page_views` | `view_time`, `time` | `canonical_id`, `user_id` |
| `user_activity` | `activity_time`, `timestamp` | `user_id`, `customer_id` |

### Optional Filters

Usually no filter is needed, but you might filter out:
```yaml
# Filter bot traffic
custom_filter: "is_bot = false"

# Specific page types
custom_filter: "page_type IN (''product'', ''category'')"

# Exclude admin users
custom_filter: "user_role != 'admin'"
```

---

## Table Type: Orders / Purchases

### Purpose
Track purchase behavior for **Recency**, **Frequency**, and **Monetary** metrics.

### Required Columns
- **Timestamp**: When the order occurred
- **User ID**: Who made the order
- **Order Amount**: Revenue/value of the order
- **Order Status**: To filter valid orders

### Configuration Template
```yaml
- src_table: database_name.table_name
  name: 'order_events'
  unixtime_col: time
  join_key: canonical_id
  order_amount: unit_price
  custom_filter: "NOT REGEXP_LIKE(lower(order_status), ''cancel|return'')"
  apply_time_filter: 'no'
  query_type:
```

### Discovery Steps

1. **Find the table**:
```sql
-- List tables that might contain orders
SHOW TABLES IN database_name LIKE '%order%';
SHOW TABLES IN database_name LIKE '%purchase%';
SHOW TABLES IN database_name LIKE '%transaction%';
```

2. **Check the schema**:
```sql
DESCRIBE database_name.enriched_orders;
```

3. **Sample the data**:
```sql
SELECT * FROM database_name.enriched_orders LIMIT 10;
```

4. **Identify order statuses**:
```sql
-- Critical: Understand what statuses exist
SELECT DISTINCT order_status, COUNT(*) as count
FROM database_name.enriched_orders
GROUP BY order_status
ORDER BY count DESC;
```

5. **Identify amount columns**:
```sql
-- Look for revenue columns
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'enriched_orders'
  AND (column_name LIKE '%price%'
       OR column_name LIKE '%amount%'
       OR column_name LIKE '%revenue%'
       OR column_name LIKE '%total%');
```

### Common Variations

| Column Type | Common Names |
|------------|--------------|
| Time | `time`, `order_time`, `order_date`, `created_at`, `purchase_timestamp` |
| User ID | `canonical_id`, `user_id`, `customer_id`, `buyer_id` |
| Amount | `unit_price`, `total_amount`, `order_value`, `revenue`, `grand_total` |
| Status | `order_status`, `status`, `state`, `order_state` |

### Critical: Order Status Filtering

**Always filter out invalid orders**. Common invalid statuses:
- `cancelled`, `canceled`
- `returned`, `refunded`
- `failed`, `error`
- `pending` (sometimes - depends on business logic)
- `abandoned`, `incomplete`

**Valid order statuses** (include these):
- `completed`, `complete`
- `shipped`, `delivered`
- `paid`, `confirmed`
- `fulfilled`, `success`

### Filter Examples

**Approach 1: Exclude bad statuses (recommended)**
```yaml
custom_filter: "NOT REGEXP_LIKE(lower(order_status), ''cancel|return|refund|fail'')"
```

**Approach 2: Include only good statuses**
```yaml
custom_filter: "order_status IN (''completed'', ''shipped'', ''delivered'')"
```

**Approach 3: Additional business rules**
```yaml
# Exclude negative amounts and invalid statuses
custom_filter: "order_status IN (''completed'', ''shipped'') AND total_amount > 0"
```

### Amount Column Selection

Choose the right revenue column:

```yaml
# Line item price (most common)
order_amount: unit_price

# Total order value
order_amount: total_amount

# Revenue after discounts
order_amount: net_revenue

# Grand total with tax and shipping
order_amount: grand_total
```

**Important**: Verify the column contains numeric values:
```sql
SELECT MIN(unit_price), MAX(unit_price), AVG(unit_price)
FROM database_name.enriched_orders
WHERE order_status = 'completed';
```

---

## Table Type: Email Events

### Purpose
Track email engagement for **Recency** and **Frequency** metrics.

### Required Columns
- **Timestamp**: When the email event occurred
- **User ID**: Who the email was sent to
- **Event Type**: Type of email event (sent, open, click, etc.)

### Configuration Template
```yaml
- src_table: database_name.table_name
  name: 'email_activity'
  unixtime_col: time
  join_key: canonical_id
  order_amount: 0.0
  custom_filter: "event_type IN (''friendforward'', ''webform'', ''open'', ''click'', ''conversion'', ''unsubscribe'', ''reply'')"
  apply_time_filter: 'no'
  query_type:
```

### Discovery Steps

1. **Find the table**:
```sql
SHOW TABLES IN database_name LIKE '%email%';
SHOW TABLES IN database_name LIKE '%message%';
```

2. **Identify event types**:
```sql
-- Critical: Understand event types
SELECT DISTINCT event_type, COUNT(*) as count
FROM database_name.enriched_email_events
GROUP BY event_type
ORDER BY count DESC;
```

### Common Event Types

| Event Type | Include? | Reason |
|-----------|----------|--------|
| `sent` | ❌ No | Not engagement - just delivery |
| `open` | ✅ Yes | Active engagement |
| `click` | ✅ Yes | Strong engagement |
| `conversion` | ✅ Yes | Strongest engagement |
| `reply` | ✅ Yes | Active engagement |
| `forward` | ✅ Yes | Active engagement |
| `unsubscribe` | ✅ Yes | Negative but still engagement |
| `bounce` | ❌ No | Technical failure, not engagement |
| `spam` | ❌ No | Not valid engagement |
| `delivered` | ❌ No | Technical event, not engagement |

### Filter Examples

**Standard engagement filter**:
```yaml
custom_filter: "event_type IN (''open'', ''click'', ''conversion'', ''reply'')"
```

**Include all engagement (even negative)**:
```yaml
custom_filter: "event_type IN (''friendforward'', ''webform'', ''open'', ''click'', ''conversion'', ''unsubscribe'', ''reply'')"
```

**Only strong positive engagement**:
```yaml
custom_filter: "event_type IN (''click'', ''conversion'', ''reply'')"
```

**Exclude only non-engagement**:
```yaml
custom_filter: "event_type NOT IN (''sent'', ''delivered'', ''bounce'', ''spam'')"
```

### Common Variations

| Table Pattern | Time Column | User ID Column | Event Type Column |
|--------------|-------------|----------------|-------------------|
| `enriched_email_events` | `time` | `canonical_id` | `event_type` |
| `email_activity` | `event_time` | `user_id` | `event` |
| `email_engagement` | `timestamp` | `email_address`, `user_id` | `action_type` |

---

## Table Type: Sales Interactions / CRM

### Purpose
Track sales team interactions for **Recency** and **Frequency** metrics.

### Required Columns
- **Timestamp**: When the interaction occurred
- **User ID**: Customer/prospect ID

### Configuration Template
```yaml
- src_table: database_name.table_name
  name: 'sales_rep_interactions'
  unixtime_col: time
  join_key: canonical_id
  order_amount: 0.0
  custom_filter:
  apply_time_filter: 'no'
  query_type:
```

### Discovery Steps

1. **Find the table**:
```sql
SHOW TABLES IN database_name LIKE '%sales%';
SHOW TABLES IN database_name LIKE '%crm%';
SHOW TABLES IN database_name LIKE '%interaction%';
```

2. **Sample the data**:
```sql
SELECT * FROM database_name.sales_rep_interactions LIMIT 10;
```

### Common Variations

| Table Pattern | Time Column | User ID Column |
|--------------|-------------|----------------|
| `sales_rep_interactions` | `time`, `interaction_time` | `canonical_id`, `customer_id` |
| `crm_activity` | `activity_date`, `timestamp` | `contact_id`, `lead_id` |
| `sales_touches` | `touch_time`, `created_at` | `canonical_id`, `prospect_id` |

### Optional Filters

```yaml
# Only successful interactions
custom_filter: "interaction_type IN (''call'', ''meeting'', ''demo'')"

# Exclude automated touches
custom_filter: "is_automated = false"

# Specific interaction outcomes
custom_filter: "outcome IN (''interested'', ''qualified'', ''opportunity'')"
```

---

## Column Name Discovery Checklist

For each table, verify:

### ✅ Time Column
```sql
-- Check if column exists and has data
SELECT MIN(time), MAX(time), COUNT(*)
FROM database_name.table_name
WHERE time IS NOT NULL;
```

### ✅ User ID Column
```sql
-- Check uniqueness and nulls
SELECT COUNT(DISTINCT canonical_id), COUNT(*)
FROM database_name.table_name;

-- Should have many unique IDs, few/no nulls
```

### ✅ Join Key Consistency
```sql
-- Verify same user IDs across tables
SELECT COUNT(DISTINCT t1.canonical_id) as pageview_users,
       COUNT(DISTINCT t2.canonical_id) as order_users,
       COUNT(DISTINCT CASE WHEN t1.canonical_id = t2.canonical_id THEN t1.canonical_id END) as overlap
FROM database_name.enriched_pageviews t1
FULL OUTER JOIN database_name.enriched_orders t2
  ON t1.canonical_id = t2.canonical_id;
```

### ✅ Amount Column (for orders)
```sql
-- Verify numeric and reasonable
SELECT MIN(unit_price), MAX(unit_price), AVG(unit_price),
       COUNT(CASE WHEN unit_price IS NULL THEN 1 END) as nulls
FROM database_name.enriched_orders;
```

### ✅ Filter Column Values (status, event_type)
```sql
-- Always check distinct values before filtering
SELECT DISTINCT status_column, COUNT(*)
FROM database_name.table_name
GROUP BY status_column;
```

---

## Complete Example: Configuring All Tables

Here's a complete workflow for a customer with all table types:

### 1. Discovered Tables
- `<source_database>.enriched_pageviews`
- `<source_database>.enriched_orders`
- `<source_database>.enriched_email_events`
- `<source_database>.sales_rep_interactions`

### 2. Column Analysis

**Pageviews**:
```sql
DESCRIBE <source_database>.enriched_pageviews;
-- Found: time, canonical_id
```

**Orders**:
```sql
DESCRIBE <source_database>.enriched_orders;
SELECT DISTINCT order_status FROM <source_database>.enriched_orders;
-- Found: time, canonical_id, unit_price, order_status
-- Statuses: completed, shipped, cancelled, returned
```

**Email Events**:
```sql
DESCRIBE <source_database>.enriched_email_events;
SELECT DISTINCT event_type FROM <source_database>.enriched_email_events;
-- Found: time, canonical_id, event_type
-- Types: sent, open, click, bounce, conversion
```

**Sales Interactions**:
```sql
DESCRIBE <source_database>.sales_rep_interactions;
-- Found: time, canonical_id
```

### 3. Generated Configuration

```yaml
aggregate_metrics_tables:
  - src_table: <source_database>.enriched_pageviews
    name: 'pageviews'
    unixtime_col: time
    join_key: canonical_id
    order_amount: 0.0
    custom_filter:
    apply_time_filter: 'no'
    query_type:

  - src_table: <source_database>.enriched_orders
    name: 'order_events'
    unixtime_col: time
    join_key: canonical_id
    order_amount: unit_price
    custom_filter: "NOT REGEXP_LIKE(lower(order_status), ''cancel|return'')"
    apply_time_filter: 'no'
    query_type:

  - src_table: <source_database>.enriched_email_events
    name: 'email_activity'
    unixtime_col: time
    join_key: canonical_id
    order_amount: 0.0
    custom_filter: "event_type IN (''open'', ''click'', ''conversion'')"
    apply_time_filter: 'no'
    query_type:

  - src_table: <source_database>.sales_rep_interactions
    name: 'sales_rep_interactions'
    unixtime_col: time
    join_key: canonical_id
    order_amount: 0.0
    custom_filter:
    apply_time_filter: 'no'
    query_type:
```

---

## Troubleshooting

### Problem: Column not found
**Solution**: Query the schema again, look for similar column names
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'your_table' AND column_name LIKE '%time%';
```

### Problem: Joins not working
**Solution**: Verify join_key is same column across tables
```sql
SELECT 'pageviews' as source, COUNT(DISTINCT canonical_id) FROM <source_database>.enriched_pageviews
UNION ALL
SELECT 'orders', COUNT(DISTINCT canonical_id) FROM <source_database>.enriched_orders;
```

### Problem: No monetary data
**Solution**: Check if amount column has values
```sql
SELECT COUNT(*), SUM(unit_price), AVG(unit_price)
FROM <source_database>.enriched_orders
WHERE unit_price > 0;
```

### Problem: Too many/few rows after filtering
**Solution**: Test the filter query first
```sql
SELECT COUNT(*) as unfiltered FROM <source_database>.enriched_orders;
SELECT COUNT(*) as filtered FROM <source_database>.enriched_orders
WHERE NOT REGEXP_LIKE(lower(order_status), ''cancel|return'');
```
