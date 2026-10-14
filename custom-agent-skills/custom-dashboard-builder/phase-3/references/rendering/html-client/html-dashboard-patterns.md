# HTML Dashboard UI/UX Patterns & Components

**Reusable patterns for building interactive HTML dashboards.**

> **Theme Reference:** See `../../../../references/treasure-data-theme.md` for the complete Treasure Data theme specification (CSS variables, chart palette, component styling, custom brand color override). This document references that theme.

**Chart colors:** Use the TD palette for any Chart.js series — `["#B4E3E3", "#ABB3DB", "#D9BFDF", "#F8E1B0", "#8FD6D4", "#828DCA", "#C69ED0", "#F5D389", "#6AC8C6", "#5867B8"]` — unless the user specified brand colors during Phase 1 (check "Visual Preferences" in `state.md`).

---

## CRITICAL: Data Preparation Before Inlining

### Numeric Type Normalization

**Problem:** String numbers (e.g., `"4.33"` from database) break JavaScript arithmetic.

```python
# WRONG — string numbers
data = [
  {'avg_csat_score': '4.33', 'revenue': '125000.50'},  # These are strings!
  {'avg_csat_score': '3.88', 'revenue': '98000'}
]
# Result in HTML: KPI shows $NaNM, charts flat at 0, CSAT trend line broken

# CORRECT — convert to numeric before inlining
for row in data:
    row['avg_csat_score'] = float(row.get('avg_csat_score')) or 0.0
    row['revenue'] = float(row.get('revenue')) or 0.0
    row['booking_count'] = int(row.get('booking_count')) or 0
# Round floats to avoid long decimals
    row['avg_csat_score'] = round(row['avg_csat_score'], 2)
    row['revenue'] = round(row['revenue'], 2)
```

**Impact:**
- Without normalization: "52807.450000000004" displays in KPIs
- With normalization: "52807.45" displays correctly
- Arithmetic works: `row.revenue * row.pct` produces correct numbers

---

### Data Size Budget & Optimization

**Guidelines for self-contained HTML with inlined data:**

```
< 500KB total   → inline directly (fast load, shareable)
500KB – 2MB     → acceptable (modern browsers handle)
> 2MB           → consider alternatives (server-side, separate data.json)
```

**To reduce size:**

1. **Strip unused columns before inlining** — remove `time_processed`, `source_type`, `internal_id`, etc.
2. **Use compact JSON** — no whitespace
   ```python
# WRONG — formatted JSON with newlines
   json.dumps(data, indent=2)  # "avg_csat_score": 4.33,\n
   
# CORRECT — compact
   json.dumps(data, separators=(',', ':'))  # "avg_csat_score":4.33,
   ```
3. **Pre-aggregate where possible** — group by filter dimensions, sum metrics
   ```python
# Instead of inline 5000 detail rows, pre-aggregate to 50 rows per dimension
   grouped = data.groupby(['segment', 'churn_risk']).agg({
       'revenue': 'sum',
       'bookings': 'count'
   }).reset_index()
   ```
4. **Round floats** — avoid long decimal strings
   ```python
   row['metric'] = round(row['metric'], 2)  # "52807.45" not "52807.450000000004"
   ```

**Example compression:**
```
Original size: data.json = 2.3MB
After normalization + stripping + rounding: 1.2MB (48% reduction)
After compact JSON: 0.9MB (61% total reduction)
```

---

### Inlined vs. Separate data.json Pattern

**⚠ Never write data values into HTML by hand.** `generate-data.js` is the only way to populate data. The patterns below describe how `generate-data.js` delivers its output.

**Pattern A: `generate-data.js` injects data inline (RECOMMENDED, use when < 2MB)**

`generate-data.js` reads a template HTML and injects the query results:
```javascript
// generate-data.js (excerpt)
const data = await runQueries();
const dataBlock = `<script>var RAW = ${JSON.stringify(data, null, 0)};<\/script>`;
const html = fs.readFileSync('dashboard-template.html', 'utf8')
               .replace('<!-- DATA_PLACEHOLDER -->', dataBlock);
fs.writeFileSync('dashboard.html', html);
```

The resulting `dashboard.html` is fully self-contained:
```html
<script>var RAW = {"overview":[...],"by_segment":[...]};</script>
<!-- rendering code reads RAW -->
<script>renderDashboard(RAW);</script>
```

✅ Works everywhere (email, Confluence, file attachment, offline)
✅ One file to share
❌ File size limit ~2MB

**Pattern B: `generate-data.js` writes a separate data.json (only if > 2MB)**

```javascript
// generate-data.js (excerpt)
const data = await runQueries();
fs.writeFileSync('data.json', JSON.stringify(data));
```

The HTML fetches at runtime:
```html
<script>
  fetch('data.json')
    .then(r => r.json())
    .then(RAW => renderDashboard(RAW))
</script>
```

❌ Does NOT work by double-click (CORS blocks file:// fetches in Chrome/Firefox)
❌ Requires a web server or same directory — distribute as zip with both files
✅ Supports unlimited data size

---

## Quick Reference: Common Patterns

```
Filters → Charts → Tables
  ↓        ↓        ↓
Forms    Viz      Data

Each has proven patterns & code examples below.
```

---

## SECTION 1: Filter UI Patterns

### Pattern 1: Dropdown Filters (Most Common)

**When to use:** Single selection, limited options (< 20)

```html
<div class="filter-group">
  <label for="statusFilter">Status</label>
  <select id="statusFilter" onchange="applyFilters()">
    <option value="all">All Statuses</option>
    <option value="Completed">Completed</option>
    <option value="Pending">Pending</option>
    <option value="Failed">Failed</option>
  </select>
</div>
```

**CSS:**
```css
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-group label {
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: #495057;
  letter-spacing: 0.5px;
}

.filter-group select {
  padding: 10px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-group select:hover {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.filter-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}
```

---

### Pattern 2: Multi-Select Checkboxes

**When to use:** Multiple selection, medium options (3-10)

```html
<div class="filter-group">
  <label>Booking Type</label>
  <div class="checkbox-group">
    <label class="checkbox">
      <input type="checkbox" value="Flight" onchange="applyFilters()">
      Flight
    </label>
    <label class="checkbox">
      <input type="checkbox" value="Hotel" onchange="applyFilters()">
      Hotel
    </label>
    <label class="checkbox">
      <input type="checkbox" value="Package" onchange="applyFilters()">
      Package
    </label>
  </div>
</div>
```

**CSS:**
```css
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.checkbox input[type="checkbox"] {
  cursor: pointer;
  accent-color: #667eea;
}
```

---

### Pattern 3: Search/Autocomplete Filter

**When to use:** Many options (100+), user needs to search

```html
<div class="filter-group">
  <label for="customerSearch">Customer</label>
  <input 
    id="customerSearch" 
    type="text" 
    placeholder="Search customers..."
    oninput="handleSearch(this.value)"
    style="padding: 10px 12px; border: 1px solid #dee2e6; border-radius: 6px;"
  >
  <div id="searchResults" class="search-results" style="display: none;">
    <!-- Dropdown results appear here -->
  </div>
</div>
```

**JavaScript:**
```javascript
function handleSearch(query) {
  if (query.length < 2) {
    document.getElementById('searchResults').style.display = 'none';
    return;
  }
  
  const results = data.filter(d => 
    d.customer.toLowerCase().includes(query.toLowerCase())
  );
  
  const html = results.slice(0, 5).map(r => 
    `<div onclick="selectCustomer('${r.customer}')">${r.customer}</div>`
  ).join('');
  
  document.getElementById('searchResults').innerHTML = html;
  document.getElementById('searchResults').style.display = 'block';
}
```

---

### Pattern 4: Date Range Filter

**When to use:** Time-based filtering

```html
<div class="filter-group">
  <label>Date Range</label>
  <div class="date-range">
    <input type="date" id="startDate" onchange="applyFilters()" />
    <span>to</span>
    <input type="date" id="endDate" onchange="applyFilters()" />
  </div>
</div>
```

**CSS:**
```css
.date-range {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-range input {
  padding: 8px 10px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 14px;
}
```

---

### Pattern 5: Reset Filters Button

**Always include this**

```html
<button onclick="resetFilters()" class="reset-btn">
  ↻ Reset Filters
</button>
```

**CSS:**
```css
.reset-btn {
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.reset-btn:hover {
  background: #5a6268;
}
```

**JavaScript:**
```javascript
function resetFilters() {
  document.getElementById('statusFilter').value = 'all';
  document.getElementById('channelFilter').value = 'all';
  document.getElementById('typeFilter').value = 'all';
  applyFilters();
}
```

---

## SECTION 2: Chart Patterns

### Pattern 1: Bar Chart (Comparison)

**When to use:** Compare values across categories

```html
<div class="chart-container">
  <h3>Revenue by Channel</h3>
  <canvas id="barChart"></canvas>
</div>
```

**JavaScript:**
```javascript
const ctx = document.getElementById('barChart').getContext('2d');
const barChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Web', 'App', 'Phone', 'Email'],
    datasets: [{
      label: 'Revenue',
      data: [45000, 32000, 28000, 15000],
      backgroundColor: '#667eea',
      borderRadius: 4,
      borderSkipped: false
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: true,
    indexAxis: 'y', // Horizontal bar
    plugins: {
      legend: { display: false }
    },
    scales: {
      x: { beginAtZero: true }
    }
  }
});
```

---

### Pattern 2: Pie/Doughnut Chart (Distribution)

**When to use:** Show part-to-whole relationships

```html
<div class="chart-container">
  <h3>Booking Status Distribution</h3>
  <canvas id="pieChart"></canvas>
</div>
```

**JavaScript:**
```javascript
const ctx = document.getElementById('pieChart').getContext('2d');
const pieChart = new Chart(ctx, {
  type: 'pie',
  data: {
    labels: ['Completed', 'Pending', 'Failed', 'Cancelled'],
    datasets: [{
      data: [3831, 789, 546, 282],
      backgroundColor: [
        '#667eea',  // Blue
        '#764ba2',  // Purple
        '#f093fb',  // Pink
        '#4facfe'   // Light blue
      ],
      borderColor: 'white',
      borderWidth: 2
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { position: 'bottom' }
    }
  }
});
```

---

### Pattern 3: Line Chart (Trends)

**When to use:** Show trends over time

```html
<div class="chart-container">
  <h3>Revenue Trend</h3>
  <canvas id="lineChart"></canvas>
</div>
```

**JavaScript:**
```javascript
const ctx = document.getElementById('lineChart').getContext('2d');
const lineChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'],
    datasets: [{
      label: 'Revenue',
      data: [50000, 48000, 52000, 55000, 60000],
      borderColor: '#667eea',
      backgroundColor: 'rgba(102, 126, 234, 0.1)',
      fill: true,
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { display: true }
    }
  }
});
```

---

### Pattern 4: Updating Charts on Filter Change

**Most important for interactive dashboards**

```javascript
async function applyFilters() {
  const filters = {
    status: document.getElementById('statusFilter').value,
    channel: document.getElementById('channelFilter').value
  };
  
  const queryString = new URLSearchParams(filters).toString();
  const data = await fetch(`/api/by-status?${queryString}`).then(r => r.json());
  
  // Update chart data
  barChart.data.labels = data.map(d => d.status);
  barChart.data.datasets[0].data = data.map(d => d.revenue);
  barChart.update();
}
```

---

## SECTION 3: Table Patterns

### Pattern 1: Simple Data Table

**HTML:**
```html
<div class="table-container">
  <h3>Top Destinations</h3>
  <table>
    <thead>
      <tr>
        <th>Destination</th>
        <th>Bookings</th>
        <th>Revenue</th>
        <th>Avg Value</th>
      </tr>
    </thead>
    <tbody id="destinationTable">
      <!-- Rows populated by JavaScript -->
    </tbody>
  </table>
</div>
```

**CSS:**
```css
.table-container {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th {
  background: #f8f9fa;
  border-bottom: 2px solid #e9ecef;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #495057;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

td {
  padding: 12px;
  border-bottom: 1px solid #e9ecef;
  color: #495057;
}

tr:hover {
  background: #f8f9fa;
}
```

**JavaScript:**
```javascript
function renderTable(data) {
  const html = data.map(row => `
    <tr>
      <td>${row.destination}</td>
      <td>${row.bookings.toLocaleString()}</td>
      <td>$${(row.revenue || 0).toLocaleString()}</td>
      <td>$${(row.revenue / row.bookings).toFixed(0)}</td>
    </tr>
  `).join('');
  
  document.getElementById('destinationTable').innerHTML = html;
}
```

---

### Pattern 2: Sortable Table Header

```html
<th onclick="sortTable('destination')">
  Destination 
  <span id="sortIcon-destination">⬍</span>
</th>
```

**JavaScript:**
```javascript
let sortColumn = null;
let sortOrder = 'asc';

function sortTable(column) {
  if (sortColumn === column) {
    sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn = column;
    sortOrder = 'asc';
  }
  
  data.sort((a, b) => {
    const aVal = a[column];
    const bVal = b[column];
    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });
  
  renderTable(data);
}
```

---

### Pattern 3: Pagination

```html
<div class="pagination">
  <button onclick="previousPage()">← Previous</button>
  <span id="pageNumber">1</span>
  <button onclick="nextPage()">Next →</button>
</div>
```

**JavaScript:**
```javascript
const itemsPerPage = 10;
let currentPage = 1;
let allData = [];

function renderPage(page) {
  const start = (page - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const pageData = allData.slice(start, end);
  
  renderTable(pageData);
  document.getElementById('pageNumber').textContent = page;
}

function nextPage() {
  const maxPages = Math.ceil(allData.length / itemsPerPage);
  if (currentPage < maxPages) {
    currentPage++;
    renderPage(currentPage);
  }
}

function previousPage() {
  if (currentPage > 1) {
    currentPage--;
    renderPage(currentPage);
  }
}
```

---

## SECTION 4: KPI Cards Pattern

```html
<div class="kpi-grid">
  <div class="kpi-card">
    <h3>Total Revenue</h3>
    <div class="value" id="kpiRevenue">-</div>
    <div class="change">↑ 12% vs last month</div>
  </div>
  
  <div class="kpi-card">
    <h3>Bookings</h3>
    <div class="value" id="kpiBookings">-</div>
    <div class="change">5,448 total</div>
  </div>
</div>
```

**CSS:**
```css
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.kpi-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
}

.kpi-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.kpi-card h3 {
  font-size: 12px;
  text-transform: uppercase;
  color: #6c757d;
  margin-bottom: 8px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.kpi-card .value {
  font-size: 28px;
  font-weight: 700;
  color: #212529;
}

.kpi-card .change {
  font-size: 12px;
  color: #6c757d;
  margin-top: 8px;
}
```

---

## SECTION 5: Responsive Design Patterns

### Mobile-First Base

```css
/* Mobile first (default) */
.container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  padding: 20px;
}

.filters-section {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

/* Tablet and up */
@media (min-width: 768px) {
  .filters-section {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .filters-section {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .charts-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Large desktop */
@media (min-width: 1400px) {
  .charts-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

---

## SECTION 6: Dark Mode Support

```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --text-primary: #212529;
  --text-secondary: #495057;
  --border: #e9ecef;
  --accent: #667eea;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1e1e1e;
    --bg-secondary: #2d2d2d;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --border: #3d3d3d;
    --accent: #8b9eff;
  }
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
}

.table-container {
  background: var(--bg-primary);
  border: 1px solid var(--border);
}
```

---

## SECTION 7: Loading States & Empty States

### Loading Spinner

```html
<div class="loading">
  <div class="spinner"></div>
  <p>Loading data...</p>
</div>
```

**CSS:**
```css
.loading {
  text-align: center;
  padding: 40px;
  color: #6c757d;
}

.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid #e9ecef;
  border-radius: 50%;
  border-top-color: #667eea;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

### Empty State

```html
<div class="empty-state">
  <svg><!-- empty icon --></svg>
  <p>No data available</p>
  <small>Try adjusting your filters</small>
</div>
```

**CSS:**
```css
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
}

.empty-state p {
  font-size: 16px;
  font-weight: 600;
  margin: 10px 0;
}

.empty-state small {
  font-size: 12px;
  display: block;
  margin-top: 5px;
}
```

---

## SECTION 8: Tab Navigation Pattern

```html
<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('overview')">
    Overview
  </button>
  <button class="tab-btn" onclick="switchTab('details')">
    Details
  </button>
  <button class="tab-btn" onclick="switchTab('analysis')">
    Analysis
  </button>
</div>

<div id="overview" class="tab-content active"><!-- Content --></div>
<div id="details" class="tab-content"><!-- Content --></div>
<div id="analysis" class="tab-content"><!-- Content --></div>
```

**CSS:**
```css
.tabs {
  display: flex;
  border-bottom: 2px solid #e9ecef;
  margin-bottom: 20px;
  gap: 5px;
}

.tab-btn {
  padding: 12px 24px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-weight: 600;
  color: #6c757d;
  transition: all 0.2s;
  font-size: 14px;
}

.tab-btn.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.tab-btn:hover {
  color: #667eea;
}

.tab-content {
  display: none;
}

.tab-content.active {
  display: block;
}
```

**JavaScript:**
```javascript
function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  
  document.getElementById(tabName).classList.add('active');
  event.target.classList.add('active');
}
```

---

## SECTION 9: Color Palette Reference

**Use consistently throughout dashboard:**

```
Primary: #667eea (accent blue)
Secondary: #764ba2 (purple)
Tertiary: #f093fb (pink)
Success: #43e97b (green)
Warning: #ffa502 (orange)
Error: #ff6b6b (red)

Neutral:
  #ffffff (white)
  #f8f9fa (light gray bg)
  #e9ecef (light border)
  #dee2e6 (medium border)
  #adb5bd (medium text)
  #6c757d (dark text)
  #495057 (darker text)
  #212529 (darkest text)
```

---

## SECTION 10: Complete Dashboard Layout Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard</title>
  <!-- Chart.js is inlined directly (no CDN, works fully offline) — see templates/*.html for the actual inlined <script> block -->
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; background: #f8f9fa; }
    .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
    .header h1 { font-size: 32px; margin-bottom: 8px; }
    .filters { padding: 20px 30px; background: #f8f9fa; border-bottom: 1px solid #e9ecef; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
    .content { padding: 30px; }
    /* ... more styles ... */
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Sales Dashboard</h1>
    </div>
    
    <div class="filters">
      <!-- Filter dropdowns here -->
    </div>
    
    <div class="content">
      <div class="kpi-grid">
        <!-- KPI cards -->
      </div>
      
      <div class="tabs">
        <!-- Tab buttons -->
      </div>
      
      <div class="charts-grid">
        <!-- Charts -->
      </div>
      
      <div class="table-container">
        <!-- Tables -->
      </div>
    </div>
  </div>
</body>
</html>
```

---

## Related Files

- `html-deployment-guide.md` - Deployment options
- `../../testing-troubleshooting.md` - Quality validation

---

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
