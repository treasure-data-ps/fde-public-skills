# Dashboard Design Questions (Step 1c-Extended)

**When to use:** After gathering metrics, dimensions, and layout preferences in Step 1c.

**Goal:** Capture detailed dashboard design including tabs, widgets, chart types, filters, and calculations — all before Phase 3 build.

---

## Question Set 1: Tab Structure & Organization

**AskUserQuestion:**
```
header: "Dashboard Tabs"
question: "How would you like to organize your dashboard? (e.g., by metric type, by audience, by process)"
multiSelect: false
options:
  - label: "Single Tab — Everything on one page"
    description: "All metrics and charts visible at once. Simple and quick."
  - label: "Multiple Tabs by metric type"
    description: "Tab 1: Revenue, Tab 2: Orders, Tab 3: Customers, etc."
  - label: "Multiple Tabs by process/workflow"
    description: "Tab 1: Today's Goals, Tab 2: Risk Alerts, Tab 3: Historical Analysis"
  - label: "Multiple Tabs by audience"
    description: "Tab 1: Executive Summary, Tab 2: Operations Detail, Tab 3: Raw Data"
  - label: "Other — I'll describe the structure"
    description: "Custom tab organization"
```

**If multiple tabs:** Ask follow-up:
> "What would you name each tab? What metrics go on each?"

**Capture in state.md:**
```yaml
Dashboard Tabs:
  - Tab 1 Name: [name]
    Purpose: [brief description]
    Metrics: [metric1, metric2, ...]
    
  - Tab 2 Name: [name]
    Purpose: [brief description]
    Metrics: [metric1, metric2, ...]
```

---

## Question Set 2: Global Filters vs Tab-Specific Filters

**AskUserQuestion:**
```
header: "Dashboard Filters"
question: "Which filters should apply to ALL tabs (global) vs specific tabs only?"
multiSelect: true
options:
  - label: "Date Range — Global (all tabs)"
    description: "Every metric filtered by same date range"
  - label: "Region — Global (all tabs)"
    description: "Every metric filtered by same region(s)"
  - label: "Status — Global (all tabs)"
    description: "Every metric filtered by same status(es)"
  - label: "Date Range — Per tab"
    description: "Different date ranges for different tabs"
  - label: "Custom Filters — Global"
    description: "Additional filters I'll describe"
  - label: "Custom Filters — Per tab"
    description: "Tab-specific filters I'll describe"
```

**Capture in state.md:**
```yaml
Global Filters:
  - [filter_name]: [type], applies to all tabs

Tab-Specific Filters:
  - Tab [name]:
    - [filter_name]: [type]
```

---

## Question Set 3: Visualization Type per Metric

**For each metric, ask:**

```
header: "How to visualize [Metric Name]?"
question: "How should '[Metric Name]' be displayed?"
multiSelect: false
options:
  - label: "KPI Card (large number + trend)"
    description: "Prominent metric value with sparkline or arrow showing trend"
  - label: "Line Chart (time series)"
    description: "Show metric trend over time"
  - label: "Bar Chart"
    description: "Compare metric across categories (region, status, etc.)"
  - label: "Pie Chart (composition)"
    description: "Show breakdown of metric by category"
  - label: "Table (detailed data)"
    description: "Raw data rows with sorting and filtering"
  - label: "Combination (multiple on same tab)"
    description: "Show metric in multiple ways (e.g., KPI + trend chart)"
  - label: "Other"
    description: "I'll describe the visualization"
```

**Capture in state.md:**
```yaml
Metrics & Visualizations:
  - Metric: [name]
    Definition: [formula/calculation]
    Chart Type: [KPI/Line/Bar/Pie/Table/...]
    Dimensions: [sliced by: dimension1, dimension2, ...]
    Sample Calculation: [SUM/COUNT/AVG of...]
```

---

## Question Set 4: Widget Details & Calculations

**For each widget, capture:**

```yaml
Widgets:
  - Widget Name: [name]
    Tab: [tab_name]
    Metric: [metric_name]
    Chart Type: [visualization type]
    Dimensions: [what to slice by]
    Filters Applied: [which global/tab filters apply to this widget?]
    Calculation: [SUM(column) BY dimension WHERE ...]
    Definition: [business meaning in plain English]
    Drill-down: [yes/no - can user click to see detail?]
```

---

## Question Set 5: Widget Interactions & Drill-Down

**AskUserQuestion:**
```
header: "Dashboard Interactivity"
question: "How should users interact with widgets?"
multiSelect: true
options:
  - label: "Click filters to update entire dashboard"
    description: "Changing date or region updates all widgets"
  - label: "Click chart bars/slices to drill down"
    description: "Click a bar to see detail behind that value"
  - label: "Hover to see tooltips"
    description: "Detailed info appears on hover (standard)"
  - label: "Export / download data"
    description: "Users can export widget data to CSV"
  - label: "No interactivity — static view"
    description: "Read-only dashboard, no drilling or filtering"
```

---

## Question Set 6: Choose HTML Client Template

**After gathering all dashboard design details, ask user which template fits:**

```
header: "HTML Template Type"
question: "Which template best matches your dashboard needs?"
multiSelect: false
options:
  - label: "KPI Dashboard (Executive Summary)"
    description: "4 large numbers + summary. Best for status reports, exec briefings. Email-friendly."
    
  - label: "Table Dashboard (Data Explorer)"
    description: "Sortable/searchable rows + metrics. Best for operators needing detail, compliance reports."
    
  - label: "Multi-Chart Dashboard (Analysis)"
    description: "Line/bar/pie charts + KPI cards. Best for trends, benchmarking, storytelling."
    
  - label: "Not sure — I'll decide based on data"
    description: "I'll recommend based on your metrics, dimensions, and audience."
```

**Mapping to template:**

| Your Needs | Template | Why |
|-----------|----------|-----|
| "Show executives 5 key metrics" | KPI | Simple, scan-friendly, decision-focused |
| "Let teams explore order details" | Table | Sortable columns, search, CSV export |
| "Show me sales trends vs targets" | Multi-Chart | Line chart for trends, bar for comparison |
| "Display compliance audit data" | Table | Detail-oriented, row-level drilling |
| "Executive status report to email" | KPI | Self-contained, portable, no interaction needed |
| "BI team needs multiple views" | Multi-Chart | Multiple visualizations tell the story |

**Capture in state.md:**
```yaml
HTML Template Selection:
  - Chosen Template: [KPI / Table / Multi-Chart]
  - Reasoning: [Why this template fits their needs]
  - Customizations needed: [Additional charts, fields, colors, etc.]
```

---

## Why 3 Templates Exist

**Different audiences need different UX:**

```
KPI Dashboard
├─ Audience: Executives, Leadership
├─ Use Case: Status reports, briefings
├─ UI Style: Scan-friendly (4 big numbers)
├─ Interaction: Read-only
└─ Share method: Email, Confluence

Table Dashboard
├─ Audience: Operators, Analysts
├─ Use Case: Data exploration, compliance
├─ UI Style: Detail-oriented (rows + columns)
├─ Interaction: Sort, search, export
└─ Share method: Web link, Zip file

Multi-Chart Dashboard
├─ Audience: Business Analysts, PMs
├─ Use Case: Trends, benchmarking, storytelling
├─ UI Style: Story-focused (multiple charts)
├─ Interaction: Visualizations, tooltips
└─ Share method: Email, embedded link
```

---

## Example: Complete Dashboard Design Specification

```yaml
# Sales Performance Dashboard

Global Filters:
  - Date Range: date-picker (default: Last 90 days)
  - Region: dropdown (North America, Europe, APAC, LATAM)
  - Order Status: multi-select (Completed, Pending, Cancelled)

Tabs:
  - Name: Revenue Overview
    Purpose: Executive view of revenue trends and composition
    Widgets:
      - Widget 1:
          Name: Total Revenue
          Chart Type: KPI card with sparkline
          Metric: Total Revenue
          Calculation: SUM(amount) WHERE status = 'Completed'
          Filters: Date Range, Region, Order Status
          Definition: Sum of completed order amounts
          
      - Widget 2:
          Name: Revenue by Region
          Chart Type: Horizontal Bar Chart
          Metric: Revenue by Region
          Calculation: SUM(amount) BY region WHERE status = 'Completed'
          Filters: Date Range, Order Status (NOT Region — shown in chart)
          Drill-down: Yes (click region bar to see detail)
          Definition: Revenue comparison across geographic regions
          
      - Widget 3:
          Name: Revenue Trend
          Chart Type: Line Chart
          Metric: Daily Revenue
          Calculation: SUM(amount) BY DATE(order_date) WHERE status = 'Completed'
          Filters: Date Range, Region, Order Status
          Drill-down: No
          Definition: Daily revenue trend over selected period

  - Name: Orders & Customers
    Purpose: Operational view of order volume and customer metrics
    Widgets:
      - Widget 1:
          Name: Order Count
          Chart Type: KPI card
          Metric: Order Count
          Calculation: COUNT(*) FROM orders
          Filters: Date Range, Region, Order Status
          Definition: Total number of orders placed
          
      - Widget 2:
          Name: Orders by Status
          Chart Type: Data Table
          Metric: Multiple (Count, Revenue, Avg Value)
          Calculation: COUNT(*), SUM(amount), AVG(amount) BY status
          Filters: Date Range, Region (NOT Order Status — shown in table)
          Definition: Detailed breakdown by order status

Interactivity:
  - Filter controls update all widgets
  - Chart bars/regions support drill-down where indicated
  - Hover tooltips show exact values
  - Export enabled for data tables
```

---

## How This Feeds Into Phase 3 Build

During Phase 3, this dashboard design specification becomes the **build blueprint**:

1. **Tabs** → Phase 3 creates HTML sections/tabs
2. **Widgets** → Phase 3 generates charts/KPI cards/tables from this spec
3. **Calculations** → Phase 3 translates to SQL WHERE/GROUP BY
4. **Filters** → Phase 3 wires filter controls to SQL
5. **Drill-down** → Phase 3 implements click handlers if specified

**Result:** Phase 3 build is ~80% faster because the design is already validated with the user in Phase 1.

---

**Version:** 1.0.0
**Last Updated:** 22 July 2026
