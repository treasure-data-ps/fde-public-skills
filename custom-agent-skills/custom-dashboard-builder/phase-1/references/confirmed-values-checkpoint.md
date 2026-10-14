# Confirmed Values Checkpoint (Stage B → Phases 2–4)

**Purpose:** Write metric/dimension values once after Stage B discovery is confirmed with the user. Reference in Phases 2, 3, and 4 instead of re-running identical tdx queries.

**Why:** Prevents redundant query round-trips per phase. Estimated savings: 15-20% per validation phase.

---

## When to Populate

**End of Stage B, after Steps 2c/2d values are confirmed with the user in-session:**

In `state.md` Stage B block, add:

```yaml
confirmed_values:
  # Metrics confirmed with real values
  total_revenue: 4319297.65
  order_count: 6561
  average_order_value: 658.33
  active_customers: 737
  avg_customer_ltv: 16225.60
  
  # Dimensions confirmed with actual distributions
  churn_risk_distribution:
    low: 489
    medium: 320
    high: 191
  
  loyalty_membership_coverage: "600 of 1000 (60%)"
  
  support_ticket_outcomes:
    resolved: "69.2%"
    pending: "21.4%"
    escalated: "9.5%"
  
  email_open_rates:
    unique_recipients: "78.8%"
    total_opens_to_sends: "46.1%"
  
  # Metadata for validation
  data_freshness_timestamp: "2026-07-06 12:00 UTC"
  validation_timestamp: "2026-07-06 14:30 UTC"
  validated_by: "<your name>"
  notes: "All Stage B queries validated; values ready for Phase 2/3/4 reference"
```

---

## How to Use

### Phase 2 (Workflow Deployment)
**Instead of:** Running `SELECT SUM(amount) FROM transactions WHERE ...` to verify workflow output

**Do:** Read from confirmed_values
```
confirmed_values.total_revenue == 4319297.65 ✅
```

If workflow produces a different value → Flag as a data issue (not a change in source data).

### Phase 3 (Build Dashboard)
**Instead of:** Running `SELECT COUNT(DISTINCT customer_id) ...` to validate dashboard KPIs

**Do:** Reference confirmed_values
```
Dashboard Widget: Active Customers = 737 ✓ (matches confirmed_values)
```

### Phase 4 Track A/B (Automation & Agents)
**Instead of:** Re-querying metrics for Track A knowledge base or Track B Foundry agent

**Do:** Reference confirmed_values in knowledge sources

```yaml
# Track B agent knowledge_bases/metrics.yml
metrics:
  total_revenue:
    value: 4319297.65  # From confirmed_values
    source: "state.md Stage B — validated 2026-07-06"
    cardinality_check: ✅ (all 6,561 transactions sum correctly)
```

---

## What to Include

**Essential:**
- Top-level metrics (revenue, counts, averages)
- Dimension distributions (segment %, churn risk split, etc.)
- Cardinality checks (e.g., "737 of 1000 customers")
- Coverage rates (e.g., "60% loyalty membership")

**Metadata:**
- Validation timestamp
- Notes about any special calculations or assumptions

**Optional:**
- Query performance times (if relevant to Phase 2/3)
- Data freshness timestamp
- Any flags or caveats (e.g., "90-day window was the user's decision")

---

## Troubleshooting

**Q: What if a Phase 2/3/4 query returns a different value?**

1. Check your query logic — did you include the same filters/exclusions?
2. Check data freshness — has source data changed since Stage B?
3. Document the discrepancy in `state.md` Phase 2/3/4 block
4. Investigate root cause before proceeding

**Q: Can we update confirmed_values after Stage B?**

Only if:
- Source data genuinely changed (new records, backfill, etc.)
- The Stage B query had a bug (unlikely if validated)

Otherwise, keep it frozen as ground truth.

**Q: What if a value was uncertain and needed the user's input mid-discovery?**

Use the final value after the user confirms it directly (in the same session). Document in "notes" if the definition changed during discovery.

---

## Integration with Phase Workflow

```
Stage B — End:
  ├─ All metrics confirmed with the user (no open questions)
  ├─ Write confirmed_values to state.md
  └─ Complete Stage B → route to Phase 2 or Phase 3

Phase 2/3/4 — Validation Steps:
  ├─ Read confirmed_values from state.md
  ├─ Spot-check outputs against confirmed_values
  ├─ If match: ✅ (no re-query needed)
  ├─ If differ: 🚩 (investigate)
  └─ Continue build
```

---

**Cost Savings:** ~15-20% per validation phase (eliminates redundant queries)

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
