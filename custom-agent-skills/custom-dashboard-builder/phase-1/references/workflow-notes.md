# Stage B: Discovery Notes & Edge Cases

## Pre-Stage B Setup Checklist

Before starting Stage B data discovery, verify:

1. **Resume vs New Check**
   - If **new**: Proceed to Step 2a (fresh Stage B)
   - If **resuming**: Read **state.md** (created in Stage A)
     - Verify "Current phase" = "Stage B"
     - Check "Last updated" date (verify freshness)
     - Read "Next Action" for explicit handoff

2. **Verify Stage A Complete**
   - [ ] `state.md` created and approved (Session Setup block written in Stage A)
   - [ ] Dashboard Complexity Score (0-6) calculated and confirmed
   - [ ] `skip_workflow` flag set (`false` / `true` / `partial` / `tbd`) — if missing, go back to Stage A Setup

**If any Stage A deliverable is missing:** Do not start Stage B. Go back and complete Stage A first.

---

## Large Table Performance Handling

### When to Optimize

If Stage B discovers a table with:
- Billions of rows
- Query timeout risk in Presto
- Performance concerns for dashboard rendering

### Optimization Steps

1. **Apply Stage A filters first** (date range, status, dimensions)
   - Don't run bare `SELECT SUM(revenue) FROM orders`
   - Instead: `SELECT SUM(revenue) FROM orders WHERE order_date >= DATE_SUB(...) AND status != 'cancelled'`

2. **Try Hive if Presto times out**
   - Use: `SET hive.exec.parallel=true;`
   - Hive often faster on large tables

3. **Contact TD Skills**
   - `sql-skills:trino-optimizer` — Query optimization
   - `sql-skills:time-filtering` — Time-window patterns

4. **Document findings for the build**
   - Performance baseline: "Presto: 8 sec, Hive: 3 sec"
   - Large table may require: Workflow pre-aggregation (Phase 2) since the HTML Client build inlines data at build time and is a poor fit for very large record-level exports

---

## Conflict Resolution

### Detecting Conflicts

| Stage A Requirement | Stage B Finding | Type |
|---|---|---|
| "daily refresh" | Data updates weekly | ⚠️ Conflict |
| "6 regions" | Data has 10 regions | ✅ OK (superset) |
| metric X | Column doesn't exist | ⚠️ Blocker |
| "exclude cancelled" | Can't identify cancelled | ⚠️ Blocker |

### Resolution Process

1. **APPEND conflict note** to `state.md` (new dated entry — never edit prior entries)
2. **Ask the user directly, in-session** if blocker (missing metric, unclear exclusion rule)
3. **Propose workaround:**
   - "Metric X doesn't exist, but metric Y is similar — can we use that?"
   - "We can't identify 'cancelled' in this column; can you clarify which column defines status?"
4. **Update state.md** if the user changes a Stage A answer
5. **Re-validate the Stage A score** if changes are significant

### When to Proceed Despite Minor Conflicts

Minor conflicts (superset data, better freshness than required) are acceptable:
- ✅ Stage A: "at least 5 regions" → Stage B: Found 10 regions
- ✅ Stage A: "daily refresh needed" → Stage B: Data updates hourly (better than required)

Major conflicts (blocking metrics, missing dimensions, excluded data) require resolving with the user before proceeding:
- ⚠️ Stage A: "Revenue metric" → Stage B: No revenue column found
- ⚠️ Stage A: "Exclude test data" → Stage B: No way to identify test data

---

## Stale Data Detection

### Quality Gate: Data Freshness

```
IF last_update > 1 week ago:
  → Document staleness in Stage B findings
  
IF last_update > 30 days ago AND Stage A requires "daily refresh":
  → **Ask the user directly**
  → Data may not support the Stage A requirement
  → Update state.md with staleness note
```

---

## Exclusion Rule Handling

### Simple SQL Expressions

Most exclusion rules can be expressed in SQL:
- "Exclude cancelled orders" → `WHERE status != 'cancelled'`
- "Exclude test data" → `WHERE environment != 'test'`
- "Exclude refunds" → `WHERE amount > 0`

**Action:**
1. Validate rule can be expressed in SQL
2. Run test query to see % of data excluded
3. If >50% excluded: **Flag to the user** (may indicate wrong metric definition)

### Complex Business Logic

If exclusion rule is complex or unclear:
- "Exclude low-quality profiles based on our custom scoring"
- "Exclude duplicate IDs from fuzzy matching"

**Action:**
1. Ask the user directly: "How do we identify [X] in the database?"
2. May need custom transformation or manual check
3. Document approach in Stage B findings

---

## Join Path Validation

### Testing Joins

```sql
-- Check join cardinality (should be 1-to-1)
SELECT o.order_id, COUNT(*) as join_count
FROM orders o 
JOIN customers c ON o.customer_id = c.customer_id 
GROUP BY o.order_id 
HAVING COUNT(*) > 1;
```

Expected result: **ZERO rows** (no duplicates)

### If Join Creates Duplicates

**This is a DATA QUALITY ISSUE:**
- Many-to-many join (wrong join key?)
- Behavior table has multiple rows per key
- Time-varying dimension (slow-changing dimension issue?)

**Action:**
1. **Flag this to the user:** "The join creates duplicates; this may produce incorrect metrics"
2. Investigate root cause (is customer_id duplicated? Is join key wrong?)
3. Propose solution:
   - Use a different join key?
   - Dedup the attribute table first?
   - Adjust the metric calculation?
4. **Document in Stage B findings**

---

## Stage B → Phase 2 (Workflow) vs Stage B → Phase 3 (Build) Continuity

### Stage B (Data Discovery) → Phase 2 (Workflow) — Workflow Path

After the Stage B routing decision (Step 2f), if the user chooses the **Workflow path**:

1. **Phase 2**: Workflow setup using Stage A/B data discovery — single continuous session, no pause

### Stage B (Data Discovery) → Phase 3 (Build Dashboard) — Non-Workflow Path

After the Stage B routing decision (Step 2f), if the user chooses the **Non-Workflow path**:

1. **No pause**: Continue immediately to Phase 3
2. **Phase 3**: Build the HTML Client dashboard using Stage B discovery directly

---

## Stage B Deliverables Checklist

At end of Stage B (Step 2f complete):
- [ ] Database selected and verified
- [ ] Tables discovered and confirmed (Behavior/Attribute/Aggregate/Snapshot)
- [ ] Time column identified per table (business event datetime or snapshot flag)
- [ ] Metrics validated with **real sample queries** (NOT estimates)
- [ ] Dimensions validated with actual DISTINCT values
- [ ] Filter scope map produced (dashboard/tab/widget-level)
- [ ] Tab grouping proposed and confirmed
- [ ] Join paths validated (if multi-table)
- [ ] Data freshness confirmed and documented
- [ ] Stale data issues identified (if any) and logged
- [ ] Stage A/B conflicts identified and resolved with the user
- [ ] Exclusion rules validated in SQL
- [ ] Large table performance assessed (queries optimized)
- [ ] Rendering confirmed as HTML Client (fixed, no selection needed)
- [ ] **Path chosen and confirmed (Phase 2 OR Phase 3)**
- [ ] Conflicts documented in `state.md` (if any)

---

## Tools & Resources

### Treasure Data CLI
```bash
tdx databases                           # List databases
tdx tables --in <database>              # List tables (NOT "tdx table <database>")
tdx describe <database>.<table>         # Column details — always requires a table, no bare-database or wildcard form
tdx query "SELECT ..." -d <database>    # Run queries (database is a -d flag, not positional)
```

### Query Patterns
See `validation-queries.md` for:
- Metric validation queries
- Attribute discovery queries
- Join path validation
- Large table optimization
- Performance troubleshooting

### Discovery Guidance
See `stage-b-database-discovery.md` for core discovery patterns across all table types and source kinds.
---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
