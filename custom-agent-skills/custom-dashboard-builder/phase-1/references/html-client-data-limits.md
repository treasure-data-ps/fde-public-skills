# HTML Client Data Limits & Validation (Phase 1)

**Goal:** Validate that the dashboard design is feasible for HTML Client before Phase 3 build.

**Critical Constraint:** HTML Client stores all data INLINE in the HTML file (not fetched from API). This creates hard limits on:
- Total data volume
- Number of rows per dataset
- File size (affects load time)
- Browser performance

---

## Data Limits & Performance Tiers

| Metric | Optimal | Acceptable | Problematic |
|--------|---------|-----------|-------------|
| **HTML File Size** | < 10 MB | 10-50 MB | > 50 MB (breaks on load) |
| **Total Data Rows (soft limit)** | < 100K | 100K-500K | > 500K (test required) |
| **Datasets per Dashboard** | < 5 | 5-10 | > 10 (slows significantly) |
| **Load Time** | < 2s | 2-5s | > 5s (UX failure) |

**Note on 100K soft limit:**
- **< 100K rows** → Dashboard loads in < 2s, filters respond instantly (optimal)
- **100K-500K rows** → Dashboard loads in 2-5s, filters respond in 1-2s (acceptable, requires Phase 3 testing)
- **> 500K rows** → Risk of load failure, requires explicit user approval + performance testing in Phase 3

---

## Step 1: Estimate Data Volume for Each Widget

For each widget in dashboard design, calculate:

```yaml
Widget: [Widget Name]
Chart Type: [KPI/Line/Bar/Table/...]
Data Source: [table name]
Query: [SQL]

Expected Rows:
  - Pre-aggregated? [yes/no]
  - Time period: [X days]
  - Group by: [dimensions]
  - Distinct combinations: [estimate]
  
Sample Calculation:
  • If metrics by (Date, Region, Status):
    • Dates: 90 days
    • Regions: 6 values
    • Status: 4 values
    • Expected rows: 90 × 6 × 4 = 2,160 rows
    
  • If raw events (non-aggregated):
    • Events in date range: 2.1M
    • ❌ TOO LARGE for HTML Client
```

---

## Step 2: Calculate Filter Data Size

**Filter options also add to data.json! For EACH filter, calculate:**

```
Global Filters:
  • Date Range Filter: No data (just min/max dates)
  • Region Filter: 6 values × ~30 bytes = ~180 bytes
  • Order Status Filter: 4 values × ~30 bytes = ~120 bytes
  • Subtotal: ~300 bytes

Tab-Specific Filters (if any):
  • Category Filter (Tab 2): 42 values × ~30 bytes = ~1,260 bytes
  • Channel Filter (Tab 3): 5 values × ~30 bytes = ~150 bytes
  • Subtotal: ~1,410 bytes

Total Filter Data: ~1,710 bytes ≈ ~2 KB
```

**⚠️ WARNING CASE: High-cardinality filters**
```
If you have a filter with 100K+ unique values (e.g., customer_id):
  • 100,000 values × 30 bytes = ~3 MB just for filter options
  • This alone breaks HTML Client
  
SOLUTION:
  • Use search/autocomplete instead of dropdown (don't load all options)
  • Filter by aggregated dimension (region, category) not raw IDs
  • Don't include high-cardinality filters in data.json
```

---

## Step 3: Calculate Total HTML File Size

**Formula:**
```
Total Size ≈ (Widget Data) + (Filter Data) + (JavaScript + HTML markup)

Avg bytes per row:
  • Numeric columns (int, float): 8 bytes
  • Date columns: 10 bytes
  • Text columns: ~50 bytes average
  • JSON overhead: +20% for structure

Example:
  Widget 1 (KPI): 1 row × 5 columns (4 numeric, 1 text) ≈ 100 bytes
  Widget 2 (Bar Chart): 2,160 rows × 8 columns (6 numeric, 2 text) ≈ 2,160 × 120 = 259 KB
  Widget 3 (Trend Line): 90 rows × 3 columns (2 numeric, 1 date) ≈ 90 × 50 = 4.5 KB
  
  Subtotal (widget data): ~264 KB
  Filter data: ~2 KB
  JS/HTML/CSS: ~50 KB
  JSON wrapper: +20% = ~53 KB
  
  ➜ Total: ~369 KB ✅ SAFE
```

**Better way: Test with real data:**
```bash
# Run the Phase 3 query to get actual row count
tdx query --output json < query.sql > data.json

# Check file size
ls -lh data.json
# If < 5 MB: ✅ Safe
# If 5-20 MB: ⚠️ Warning (monitor performance)
# If > 20 MB: ❌ May break
```

---

## Step 3: Identify Data Size Issues & Solutions

### Issue 0: High-Cardinality Filters

**Problem:** Filter with too many unique values (e.g., customer_id with 100K+ values).

**Why it breaks:**
```
If you show all options in a dropdown:
  100,000 customer IDs × 30 bytes = ~3 MB just for filter options ❌

Plus all the widget data:
  Total: > 50 MB ❌ BREAKS
```

**Solution:**
- ❌ Don't include high-cardinality filters in dashboard
- ✅ Options:
  1. **Use search/autocomplete:** Let users TYPE customer ID (don't load all options)
  2. **Filter by aggregated dimension:** Filter by Region (6 values) not Customer ID (100K)
  3. **Pre-filter:** Show only "top 100 customers by revenue" instead of all
  4. **Split across dashboards:** Customer-level dashboard is separate from region/status dashboard

**Example:**
```yaml
❌ BAD Filter Design:
  Filters:
    - Date Range
    - Region (6 values)
    - Order Status (4 values)
    - Customer ID (100,000 values) ❌ TOO MANY
    - Product ID (50,000 values) ❌ TOO MANY

✅ GOOD Filter Design:
  Global Filters:
    - Date Range
    - Region (6 values) — dropdown
    - Order Status (4 values) — dropdown
  
  Search (not filter):
    - Customer search box (autocomplete, don't load all)
    - Product search box (autocomplete, don't load all)
```

---

### Issue 1: Too Many Rows (Raw Events)

**Problem:** User wants to display raw events (e.g., all 2.1M orders in a table).

**Solution:**
- ❌ Not feasible for HTML Client
- ✅ Options:
  1. **Aggregate first:** GROUP BY region/date (reduce 2.1M → 2,160 rows)
  2. **Filter scope:** Show last 7 days instead of 90 (reduce proportionally)
  3. **Use pagination:** Show top 1,000 rows only in table
  4. **Move to Phase 4:** Build a backend API + real dashboard server (beyond HTML Client scope)

### Issue 2: Too Many Dimensions

**Problem:** Dashboard slices by (Date, Region, Status, Category, Channel) = explosion of combinations.

**Example:**
```
365 days × 6 regions × 4 statuses × 42 categories × 5 channels 
= 3,075,600 rows ❌ BREAKS
```

**Solution:**
- Reduce dimensions:
  1. Remove least-used dimension (e.g., drop Channel)
  2. Keep only top 10 categories instead of all 42
  3. Aggregate by month instead of day
  4. Split into multiple dashboards (one per region)

### Issue 3: Too Many Filters (Multiplier Effect)

**Problem:** Dashboard has 5 global filters + 3 tab-specific filters = lots of filter data.

**Why it matters:**
```
If each filter needs to show all unique values:
  • Region: 6 values
  • Status: 4 values  
  • Category: 42 values
  • Channel: 8 values
  • Customer Segment: 12 values
  
  Filter data = 6 + 4 + 42 + 8 + 12 = 72 dropdown options
  72 × ~30 bytes = ~2 KB (acceptable)
  
BUT if you add:
  • Product ID: 5,000 values ❌
  • Customer ID: 100,000 values ❌
  
  Then: 5,000 + 100,000 = 105,000 options × 30 = ~3 MB just filters
```

**Solution:**
- Limit dropdown filters to < 50 options each
- Use search/autocomplete for high-cardinality dimensions
- Per-tab filters are OK (only load when tab is active, but still in data.json)
- Recommended max:
  - Global filters: 3-5 (all visible, always loaded)
  - Tab-specific filters: 1-2 per tab

---

### Issue 4: Too Many Tabs (Multiplier Effect)

**Problem:** Dashboard has 10+ tabs with different data.

**Why it matters:**
```
Each tab can have different metric combinations.
If tabs are:
  1. Revenue Overview (2 KB data)
  2. Orders Detail (3 KB data)
  3. Customer Analysis (4 KB data)
  4. Trends (5 KB data)
  5. Geographic (3 KB data)
  
  Total: 17 KB ✅ Safe

BUT if you have:
  1-10: Regional dashboards (one per region)
        Each with 2.1M rows = 10 × 2.1M = 21M rows ❌ BREAKS
```

**Solution:**
- Limit to 3-5 tabs per dashboard
- If you need per-region views, split into multiple dashboards (one per region)
- All tab data is loaded upfront (even if user doesn't visit tab)

---

### Issue 5: High Time Resolution

**Problem:** Widget shows daily data for 3 years = 1,095 rows per series.

**If dashboard has 10 time-series widgets:**
- 1,095 rows × 10 widgets × 3 columns = 32,850 rows
- ~4 MB data
- ✅ Safe, but monitor

**Solution:** Aggregate to weekly or monthly if not needed daily.

---

## Step 4: Update Dashboard Plan with Data Validation

**Add to Phase 1 state.md:**

```yaml
### HTML Client Data Validation

**Estimated Data Volume:**

Widget | Type | Rows | Size | Status
--------|------|------|------|--------
Total Revenue (KPI) | KPI | 1 | < 1 KB | ✅ Safe
Revenue by Region (Bar) | Bar | 6 | < 10 KB | ✅ Safe
Revenue Trend (Line) | Line | 90 | < 50 KB | ✅ Safe
Orders by Status (Table) | Table | 4 | < 5 KB | ✅ Safe

**Total Estimated Size:**
- Data only: ~65 KB
- With HTML/JS/CSS: ~200 KB
- Final HTML file: ~250 KB

**Status:** ✅ SAFE FOR HTML CLIENT

---

OR (if problems found):

**Total Estimated Size:**
- Data only: ~45 MB
- Final HTML file: ~50+ MB

**Status:** ⚠️ WARNING - May be slow to load
**Recommended Action:** Reduce scope (remove raw events table, aggregate by month instead of day)

---

OR (if critical):

**Total Estimated Size:**
- Data only: ~150 MB
- Final HTML file: > 100 MB

**Status:** ❌ NOT FEASIBLE FOR HTML CLIENT
**Required Action:** 
1. Aggregate data more (weekly instead of daily)
2. Filter to smaller time window (last 30 days instead of 90)
3. Remove raw data table
4. OR: Recommend alternative approach (Phase 4 backend + API)
```

---

## Question to Ask User During Phase 1

**Add to Step 1c (after layout preferences):**

```
AskUserQuestion:
  header: "Data Volume & Performance"
  question: "How much data detail do you need? (affects file size)"
  multiSelect: false
  options:
    - label: "Summary & Aggregates (Recommended for HTML Client)"
      description: "KPI cards + trend charts + dimension summaries. Fast load, small file."
    - label: "Summary + Some Detail"
      description: "Aggregates + a table with top 1,000 rows. Moderate file size (~5-10 MB)."
    - label: "All Raw Detail"
      description: "Full dataset with no aggregation. May be slow or fail. Not recommended for HTML."
    - label: "Not sure — Let's estimate first"
      description: "I'll estimate based on your data. Then you decide."
```

---

## Validation Script (For Phase 1 Agent)

**During Stage B, run this check:**

```python
# Pseudo-code for estimating HTML file size (including filters)

def estimate_html_size(widgets, filters):
    total_rows = 0
    total_bytes = 0
    
    # Widget data
    for widget in widgets:
        query_result = run_query(widget['query'])
        rows = len(query_result)
        cols = len(query_result[0])
        avg_col_bytes = 100  # conservative estimate
        
        widget_bytes = rows * cols * avg_col_bytes
        total_rows += rows
        total_bytes += widget_bytes
        
        print(f"{widget['name']}: {rows} rows, {widget_bytes/1024:.0f} KB")
    
    # Filter data
    filter_bytes = 0
    print("\n=== FILTER DATA ===")
    for filter_obj in filters:
        cardinality = run_query(f"SELECT COUNT(DISTINCT {filter_obj['column']}) FROM {filter_obj['table']}")
        
        if cardinality > 10_000:
            print(f"❌ {filter_obj['name']}: {cardinality:,} values - TOO MANY (use search)")
            return None  # Not feasible
        elif cardinality > 100:
            print(f"⚠️  {filter_obj['name']}: {cardinality:,} values - Consider search autocomplete")
        else:
            print(f"✅ {filter_obj['name']}: {cardinality:,} values")
        
        filter_bytes += cardinality * 30  # ~30 bytes per value
    
    total_bytes += filter_bytes
    print(f"\nFilter data: {filter_bytes/1024:.1f} KB")
    
    # Add overhead
    js_html_css = 50_000  # ~50 KB
    json_overhead = total_bytes * 0.2
    
    final_size = total_bytes + js_html_css + json_overhead
    
    print(f"\n=== TOTAL SIZE ===")
    print(f"Total rows: {total_rows:,}")
    print(f"Widget data: {(total_bytes - filter_bytes)/1024/1024:.1f} MB")
    print(f"Filter data: {filter_bytes/1024:.1f} KB")
    print(f"HTML/JS/CSS: 50 KB")
    print(f"JSON overhead: {json_overhead/1024:.1f} KB")
    print(f"Final HTML file: {final_size/1024/1024:.1f} MB")
    
    if final_size < 10_000_000:  # 10 MB
        print("\n✅ SAFE for HTML Client")
    elif final_size < 50_000_000:  # 50 MB
        print("\n⚠️  WARNING - Monitor performance")
    else:
        print("\n❌ NOT FEASIBLE - Reduce scope")
    
    return final_size
```

---

## Recommendations by Use Case

| Dashboard | Feasibility | Recommendation |
|-----------|-------------|-----------------|
| KPI dashboard (5 metrics, no history) | ✅ Always OK | Build with HTML Client |
| Weekly trend dashboard (52 rows per chart) | ✅ Always OK | Build with HTML Client |
| Monthly trend dashboard (36 rows per chart) | ✅ Always OK | Build with HTML Client |
| Daily trend 2 years (730 rows per chart) | ⚠️ OK if < 5 charts | Aggregate to weekly or use 1 year history |
| Raw transaction table (1M+ rows) | ❌ Never OK | Aggregate, paginate, or use backend API |
| Real-time dashboard (updates every minute) | ❌ Never OK for HTML | Use backend + API in Phase 4 (out of scope) |

---

## Recommended Filter Architecture for HTML Client

| Filter Type | Safe Range | Example | Notes |
|------------|-----------|---------|-------|
| **Global filters** (apply to all tabs) | 3-5 | Date, Region, Status | All loaded upfront |
| **Low-cardinality** (< 50 values) | Any | Region (6), Status (4), Category (42) | Dropdown safe |
| **Medium-cardinality** (50-500) | Use with caution | Product (100), Segment (50) | Monitor file size |
| **High-cardinality** (> 500) | ❌ Don't use | Customer ID (100K), User ID (1M) | Use search/autocomplete |
| **Tab-specific filters** | 1-2 per tab | Only on Tab 2: Category | Reduces global complexity |
| **Drill-down** | Reasonable | Click region → see detail | Avoid if already have many filters |

**Best Practice Configuration:**

```yaml
Dashboard: Sales Performance

Global Filters (always visible):
  - Date Range: [date picker]
  - Region: [dropdown, 6 values]
  - Order Status: [dropdown, 4 values]

Tab 1: Revenue Overview
  - No additional filters
  - Uses global filters only

Tab 2: Orders Detail
  - Tab filter: Category [dropdown, 42 values]
  - Uses global filters + category

Tab 3: Customer Analysis
  - Tab filter: Segment [dropdown, 12 values]
  - Uses global filters + segment

NOT included (would break):
  - Customer ID filter (100K values) ❌
  - Product ID filter (50K values) ❌
  - Full order table (2.1M rows) ❌

If needed: Use search box (autocomplete, don't load all values)
```

---

**Version:** 1.0.0
**Last Updated:** 22 July 2026
