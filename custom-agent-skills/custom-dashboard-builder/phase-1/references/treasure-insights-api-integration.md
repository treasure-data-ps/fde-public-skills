# Treasure Insights Data Model API Integration

When a user provides a **Treasure Insights datamodel name or OID** during Setup-E instead of a `.dash` file, use the Treasure Insights Reporting API to fetch the live schema and auto-prefill Phase 1 requirements.

---

## Regional API Endpoints

Target the correct endpoint for your Treasure Data region:

| Region | Endpoint |
|--------|----------|
| US | `https://api.treasuredata.com` |
| Japan | `https://api.treasuredata.co.jp` |
| EU | `https://api.eu01.treasuredata.com` |
| Korea | `https://api.ap02.treasuredata.com` |

---

## Authentication

All API requests require your Master API Key via the `Authorization` header:

```
Authorization: TD1 <your_api_key>
```

The user's tdx CLI config already has this key (`~/.treasuredata/td.conf` or environment variable `TD_API_KEY`).

---

## Core Endpoints Used

### 1. Fetch Datamodel Details
**Get the full schema of a datamodel by name or OID**

```http
GET /reporting/datamodels/{datamodel_id}
Authorization: TD1 <api_key>
```

**Response includes:**
- `name` — datamodel name
- `datasets` — array of datasets (tables)
  - `dataset` — dataset name
  - `table` — table name
  - `columns` — array of column metadata
    - `name` — column name
    - `type` — data type (string, numeric, date, etc.)
    - `aggregations` — if this is a measure (sum, count, avg, etc.)
- `relations` — join definitions between tables

**Example Response (truncated):**
```json
{
  "id": "datamodel_123",
  "name": "sales_model",
  "datasets": [
    {
      "dataset": "analytics",
      "table": "orders",
      "columns": [
        { "name": "order_id", "type": "numeric" },
        { "name": "customer_id", "type": "string" },
        { "name": "order_date", "type": "date" },
        { "name": "total_amount", "type": "numeric", "aggregations": ["sum", "avg"] },
        { "name": "region", "type": "string" }
      ]
    },
    {
      "dataset": "analytics",
      "table": "customers",
      "columns": [
        { "name": "customer_id", "type": "string" },
        { "name": "customer_name", "type": "string" },
        { "name": "segment", "type": "string" }
      ]
    }
  ],
  "relations": [
    {
      "definition": [
        { "dataset": "analytics", "table": "orders", "column": "customer_id" },
        { "dataset": "analytics", "table": "customers", "column": "customer_id" }
      ]
    }
  ]
}
```

### 2. List All Datamodels (if user doesn't know the exact OID)
```http
GET /reporting/datamodels
Authorization: TD1 <api_key>
```

Returns a list of all datamodels on the account with `name` and `id` fields.

---

## Extraction Logic: API Response → Phase 1 Requirements

### Metrics (from columns with `aggregations`)
```
For each column where aggregations.length > 0:
  → This is a MEASURE (metric)
  → Name: column.name
  → Formula: "{table}.{column}" with suggested aggregation (sum/count/avg)
```

**Example:**
- `orders.total_amount` with aggregations `["sum", "avg"]`
  → Metrics: "Total Amount (SUM)", "Average Amount"

### Dimensions (from non-aggregation columns, especially type=string)
```
For each column where aggregations.empty AND type in (string, date, numeric):
  → This is a DIMENSION (filter/grouping)
  → Name: column.name
  → Table: dataset.table
```

**Example:**
- `orders.region` (type=string)
  → Dimension: "Region" (for dashboard-level or tab-level filter)
- `orders.order_date` (type=date)
  → Dimension: "Order Date" (for date range filter)

### Tables & Joins
```
For each dataset.table:
  → Primary data source
  
For each relation:
  → Join relationship (prefill as "confirmed join key" in Stage B)
```

**Example:**
- Tables: `orders`, `customers`
- Relation: `orders.customer_id` → `customers.customer_id`
  → Prefill: "Join on customer_id"

---

## Error Handling

### Invalid Datamodel Name/OID
**Error:** `404 Not Found`

```json
{ "error": "datamodel not found" }
```

**Action:** Ask user to confirm:
1. Datamodel name is correct (case-sensitive)
2. Datamodel exists in their account
3. Call `/reporting/datamodels` to list available models

### Authentication Failure
**Error:** `401 Unauthorized`

```json
{ "error": "invalid api key" }
```

**Action:** Ask user to confirm:
1. API key is correct (from `tdx auth show` or `TD_API_KEY`)
2. Account has access to Treasure Insights
3. Re-authenticate via `tdx auth setup` if needed

### API Rate Limit
**Error:** `429 Too Many Requests`

**Action:** Retry with exponential backoff (1s, 2s, 4s max)

---

## Implementation Notes

1. **Use tdx environment:** Extract API key from `tdx auth show` or `$TD_API_KEY` env var
2. **Auto-detect region:** Read from tdx config (`endpoint` field in `~/.treasuredata/td.conf`)
3. **Fallback to US:** If region unknown, default to `https://api.treasuredata.com`
4. **Cache the response:** Store fetched datamodel schema in `project_state.md` under "Data Source Metadata" for Phase 2/3 reference
5. **Always confirm:** Show user the discovered schema ("Extracted X metrics, Y dimensions from model 'sales_model'") before auto-prefilling

---

## Limitations

- **Read-only schema discovery** — this flow does not modify the datamodel, only reads it
- **No business logic inference** — metrics are identified by `aggregations` field; if a column has no aggregations set, it won't be suggested as a metric even if it's numeric
- **Join assumptions** — only relations explicitly defined in the datamodel are prefilled; hidden joins are not detected
- **Data not queried** — to validate metrics/dimensions work, Phase 1 Stage B still runs queries against the source tables (Treasure Data databases), not the datamodel itself

---

## See Also

- **Treasure Insights Reporting API official docs:** [Treasure Data API reference](https://docs.treasuredata.com)
- **Phase 1 Special Case (`.dash` flow):** `steps-1pre.md` (Treasure Insights/Sisense Special Case section)
- **Helper script:** `<skill_dir>/tools/insights-api-helper.py`

