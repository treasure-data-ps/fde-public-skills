# NBP — Table Configuration Guide

This guide explains how to configure each type of source table for the NBP workflow. NBP has one primary input (transactions) and one optional enrichment input (item info).

## NBP Table Columns (vs MTA)

NBP tables are simpler than MTA — no channel/attribution columns needed:

| Column | Purpose | Transaction Table | Item Info Table |
|--------|---------|-------------------|-----------------|
| `original_user_id_column_name` | User identifier | `td_canonical_id` | N/A |
| `original_item_id_column_name` | Item/product identifier | `item_sku` | `item_id` |
| `original_timestamp_name` | Event timestamp (unix) | `time` | N/A |
| `original_item_name_column_name` | Human-readable item name | `item_name` (if same table) | `product_name` |
| `original_item_category_column_name` | Item category/department | `item_category` (if same table) | `category` |

## Table Type: Transaction / Order-Item

### Purpose
Primary input — user-item interactions for collaborative filtering. Each row must represent **one user interacting with one item** (item-level granularity).

### Required Columns
- **User ID**: `td_canonical_id`, `canonical_id`, `user_id`, `customer_id`
- **Item ID**: `item_sku`, `product_id`, `item_id`, `sku`
- **Timestamp**: `time`, `timestamp`, `event_time` (unix timestamp)

### Discovery Steps

```sql
-- Find candidate tables
SHOW TABLES IN database_name LIKE '%order%';
SHOW TABLES IN database_name LIKE '%item%';
SHOW TABLES IN database_name LIKE '%purchase%';
SHOW TABLES IN database_name LIKE '%transaction%';
SHOW TABLES IN database_name LIKE '%product%';
SHOW TABLES IN database_name LIKE '%interaction%';
SHOW TABLES IN database_name LIKE '%rating%';

-- TD CDP enriched tables
SHOW TABLES IN database_name LIKE 'enriched_%';
SHOW TABLES IN database_name LIKE 'enrich_%';

-- Check schema
DESCRIBE database_name.candidate_table;
SELECT * FROM database_name.candidate_table LIMIT 10;

-- Verify item-level granularity
SELECT COUNT(*) AS rows,
       COUNT(DISTINCT user_col) AS users,
       COUNT(DISTINCT item_col) AS items,
       CAST(COUNT(*) AS DOUBLE) / COUNT(DISTINCT user_col) AS avg_items_per_user
FROM database_name.candidate_table;
```

### Granularity Verification (Critical)

**Good** — item-level granularity:
```
td_canonical_id | item_sku | item_name      | item_category | time
u001            | SKU123   | Running Shoes  | Footwear      | 1700000000
u001            | SKU456   | T-Shirt        | Apparel       | 1700000001
u002            | SKU123   | Running Shoes  | Footwear      | 1700000002
```

**Bad** — order-level (no item column):
```
td_canonical_id | order_total | time
u001            | 150.00      | 1700000000
```

**Bad** — aggregated (one row per user):
```
td_canonical_id | total_orders | total_spend
u001            | 15           | 2500.00
```

### Configuration Template

```yaml
in_db: gldn
original_item_transactions_table: enrich_orders
original_user_id_column_name: td_canonical_id
original_item_id_column_name: item_sku
original_timestamp_name: time
orders_lookback: ''
```

### Key Decisions
- **Table selection**: Must have item-level rows, not order-level or aggregated
- **Multi-event tables**: If multiple event types exist (view, add_to_cart, purchase), filter to the strongest signal: `purchase` > `add_to_cart` > `view`
- **orders_lookback**: Empty for all history, or integer for days (e.g., `180`)

### NOT Suitable as Primary Source

- **Order-level tables** (one row per order, no item column) — need line-item granularity
- **Aggregated/summary tables** (`user_summary`, `rfm_output`) — no item detail
- **User profile tables** (`customer_attributes`) — no item interactions
- **Event tables without item IDs** (`pageviews`, `sessions`) — no item mapping

### Common Table Name Patterns

| Pattern | Likely Content | Suitable? |
|---------|---------------|-----------|
| `enrich_orders`, `enriched_orders` | CDP-enriched order items | Yes |
| `order_items`, `line_items` | Order line items | Yes |
| `transactions`, `purchases` | Purchase records | Check granularity |
| `product_interactions`, `ratings` | User-item interactions | Yes |
| `orders` (no "item") | May be order-level | Check for item column |
| `user_summary`, `customer_360` | Aggregated | No |

---

## Table Type: Item Info / Product Catalog

### Purpose
Enrichment — provides item names and categories for the recommendation output. Can be the **same table** as transactions or a **separate catalog table**.

### Required Columns
- **Item ID**: Must match the transaction table's item ID (after VARCHAR cast)
- **Item Name**: `item_name`, `product_name`, `title`
- **Item Category**: `item_category`, `category`, `department`, `brand`

### Discovery Steps

```sql
-- Check if transaction table already has item metadata
SELECT
  COUNT(DISTINCT item_sku) AS total_items,
  COUNT(DISTINCT CASE WHEN item_name IS NOT NULL THEN item_sku END) AS items_with_name,
  COUNT(DISTINCT CASE WHEN item_category IS NOT NULL THEN item_sku END) AS items_with_category
FROM database_name.transaction_table;

-- If coverage > 90%, use the same table
-- Otherwise, find a separate catalog:
SHOW TABLES IN database_name LIKE '%product%';
SHOW TABLES IN database_name LIKE '%catalog%';
SHOW TABLES IN database_name LIKE '%item%';
SHOW TABLES IN database_name LIKE '%master%';

-- Verify the join will work
SELECT
  (SELECT COUNT(DISTINCT CAST(item_sku AS VARCHAR)) FROM database_name.transactions) AS tx_items,
  (SELECT COUNT(DISTINCT CAST(item_id AS VARCHAR)) FROM database_name.product_catalog) AS catalog_items;

-- Sample the join
SELECT t.item_sku, i.product_name, i.category
FROM database_name.transactions t
JOIN database_name.product_catalog i ON CAST(t.item_sku AS VARCHAR) = CAST(i.item_id AS VARCHAR)
LIMIT 10;
```

### Configuration Templates

**Same table** — item metadata alongside transactions:
```yaml
original_item_transactions_table: enrich_orders
original_item_info_table: enrich_orders
original_item_name_column_name: item_name
original_item_category_column_name: item_category
```

**Separate table** — product catalog is distinct from transactions:
```yaml
original_item_transactions_table: order_items
original_item_info_table: product_catalog
original_item_name_column_name: product_name
original_item_category_column_name: category
```

### Key Decisions
- **Same vs separate**: Use same table if it has `item_name` + `item_category` with > 90% coverage
- **Join column**: The workflow joins on item ID cast to VARCHAR — values must match exactly after casting
- **Category granularity**: Choose the most useful level (e.g., `department` vs `sub_category` vs `brand`)

### Join Failure Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Zero rows from join | ID format mismatch (`12345` vs `SKU-12345`) | Standardize IDs or use SQL expression |
| Partial join (< 50% match) | Different ID systems | Verify same ID space, check for prefixes |
| NULL names after join | Name column has NULLs in catalog | Use COALESCE with item_id as fallback |

---

## Exclusion Filter Configuration

### Purpose
Remove unwanted items from training and/or recommendations.

### Two-Stage Filtering

| Stage | Parameter | SQL File | Purpose |
|-------|-----------|----------|---------|
| Training | `exclude_product_train` | `queries/create_transaction_table_filters.sql` | Remove items from model training |
| Recommendations | `exclude_product_recs` | `queries/filter_products_recs.sql` | Remove items from final output |

### Method 1: Column-based regex

```yaml
exclusion_column: item_category
exclusion_values: 'Gift Card|Membership|Discontinued'
exclude_product_train: yes
exclude_product_recs: no
```

### Method 2: Custom SQL query

```yaml
exclusion_column: item
exclusion_values: query
exclude_product_train: yes
exclude_product_recs: no
```

Example custom SQL for `queries/create_transaction_table_filters.sql`:
```sql
WITH exclude AS (
  SELECT DISTINCT itemid
  FROM ${prefix}transaction_unfiltered
  WHERE item_category IN ('Gift Card', 'Membership')
     OR LOWER(item_name) LIKE '%test%'
     OR itemid IN ('INTERNAL_001', 'INTERNAL_002')
)
SELECT * FROM ${prefix}transaction_unfiltered
WHERE itemid NOT IN (SELECT itemid FROM exclude)
```

### Common Exclusion Candidates

| Category | Reason |
|----------|--------|
| Gift cards | Not a product preference signal |
| Memberships / subscriptions | Recurring, not preference-driven |
| Discontinued products | Can't be recommended |
| Test / internal products | Not real interactions |
| Very low-volume items (1-2 purchases) | Too sparse for similarity |

### Discovery Queries

```sql
-- Check item categories for exclusion candidates
SELECT item_category, COUNT(*) AS purchases
FROM database_name.table_name
GROUP BY 1 ORDER BY 2 DESC;

-- Check for test/internal products
SELECT item_name, COUNT(*)
FROM database_name.table_name
WHERE LOWER(item_name) LIKE '%test%' OR LOWER(item_name) LIKE '%sample%'
GROUP BY 1;

-- Check for low-volume items
SELECT item_sku, item_name, COUNT(*) AS purchases
FROM database_name.table_name
GROUP BY 1, 2 ORDER BY 3 ASC LIMIT 20;
```

---

## Troubleshooting

### No item-level table found
If the customer only has order-level data (one row per order, no item breakdown):
- Ask if they have a separate `order_items` or `line_items` table
- Check if an upstream ETL can produce item-level rows
- NBP cannot work without item-level granularity

### Too few items (< 10) or users (< 100)
- Check if the table is pre-filtered or aggregated
- Check if `orders_lookback` is too restrictive
- NBP needs sufficient diversity — discuss with customer if data volume is genuinely low

### Item info join returns zero matches
- Check if item ID types differ (int vs string) — workflow casts to VARCHAR but `12345` vs `SKU-12345` won't match
- Check for leading/trailing whitespace: `TRIM(CAST(item_id AS VARCHAR))`
- Verify both tables use the same ID system

### Multi-event table with mixed signals
```sql
-- Check event types and pick the strongest signal
SELECT DISTINCT event_type, COUNT(*)
FROM database_name.user_events
GROUP BY event_type ORDER BY COUNT(*) DESC;
```
Signal strength: `purchase` > `add_to_cart` > `view` > `click`
Filter to strongest available signal in the config's custom filter or pre-processing.
