# Knowledge Base Template — Data Dictionary & Metrics Catalog

Fill in from `tdx describe <sink_db>.<table>` output and Phase 2 requirements doc.

---

# Data Dictionary — [CUSTOMER_NAME] Dashboard

## SINK Database

**Database:** `[sink_db_name]`  
**Created by:** [workflow_project_name] (Phase 3)  
**Refresh schedule:** [daily/weekly — e.g., "Daily at 2 AM UTC"]  
**Source database:** `[source_db_name]`

---

## SINK Tables

### [fact_table_1] — [human label, e.g., "Booking KPIs"]

**Grain:** One row per [dimensions — e.g., "month × booking_type × destination"]  
**Row count (Phase 3 validated):** ~[N] rows  
**Use in dashboard:** [Tab/section — e.g., "Bookings tab, all charts"]

| Column | Type | Business Meaning | Notes |
|--------|------|-----------------|-------|
| [col_1] | VARCHAR | [Plain English definition] | [Exclusions/caveats — e.g., "Excludes Cancelled status"] |
| [col_2] | BIGINT | [Definition] | |
| [col_3] | DOUBLE | [Definition — e.g., "Total booking revenue in USD"] | [Source — e.g., "SUM(amount) from bookings table"] |
| [date_col] | VARCHAR | [Date format — e.g., "YYYY-MM, month boundary"] | [Range — e.g., "Jan 2024 – present"] |

### [fact_table_2] — [human label]

**Grain:** One row per [dimensions]  
**Row count (Phase 3 validated):** ~[N] rows  
**Use in dashboard:** [Tab/section]

| Column | Type | Business Meaning | Notes |
|--------|------|-----------------|-------|
| [col_1] | VARCHAR | [Definition] | |

---

## Source Tables (Fallback)

When SINK tables are unavailable, queries fall back to:

| SINK Table | Source Table | Key difference |
|---|---|---|
| `[sink_db].[fact_1]` | `[source_db].[raw_table]` | [What the SINK pre-aggregates that source doesn't — e.g., "SINK pre-groups by month; source is row-level"] |

---

# Metrics Catalog — [CUSTOMER_NAME] Dashboard

One row per dashboard metric. Used to answer "what does X mean?" and "why is X different from Y?"

| Metric Name (as shown) | SQL Formula | Source Table | Exclusion Rules | Phase 2 Validated Value | Notes |
|---|---|---|---|---|---|
| Total Bookings | `COUNT(*)` | `[fact_table]` | Excludes: [e.g., "status = 'Test'"] | [N] | |
| Total Revenue | `SUM(amount)` | `[fact_table]` | Excludes: [e.g., "Cancelled bookings"] | $[N]M | [e.g., "USD only"] |
| Avg Booking Value | `ROUND(SUM(amount)/COUNT(*), 2)` | `[fact_table]` | Same as Total Revenue | $[N] | |
| [Metric N] | [Formula] | [Table] | [Rules] | [Value] | [Notes] |

**Verified by:** [Customer contact name] on [Phase 2 date]

---

**Version:** 1.0.0
**Last Updated:** 23 June 2026
**Author:** FDE Team
