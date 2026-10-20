/**
 * generate-data.js — Optimized HTML Dashboard Data Generation
 *
 * ⚠️  BUILD TIME: This script runs on YOUR machine, queries TD, and produces dashboard.html
 * It is NEVER sent to the customer — only the output HTML file is shared.
 *
 * OPTIMIZATION GOALS FOR EMBEDDED DATA:
 * 1. Minimize payload size (gzip-compress to 60-70 KB)
 * 2. Pre-aggregate by filter dimensions (100-500 rows, not 10,000+)
 * 3. Use LIMIT wisely (safety: 10,000 default; override per query if needed)
 * 4. Select only columns dashboard renders (no unused fields)
 * 5. Coerce numeric strings to numbers (TD returns strings; JSON is verbose)
 * 6. Short field names in output (dashboard.html searches for exact keys)
 *
 * PAYLOAD SIZE OPTIMIZATION CHECKLIST:
 * ☐ All queries include WHERE + LIMIT
 * ☐ No fetching unused columns
 * ☐ GROUP BY filter dimensions only (not raw cardinality)
 * ☐ SUBSTR for date truncation (month/week, not full ISO-8601)
 * ☐ Numeric coercion: 3.14159 vs "3.14159" (JSON output ~40% smaller with numbers)
 * ☐ Tiered budget: < 500 KB ideal (fast load, easiest to share); up to 2 MB acceptable; beyond 2 MB, switch to Pattern B
 *
 * Pattern A (< 2 MB): Inline data via <!-- DATA_PLACEHOLDER --> (default)
 * Pattern B (> 2 MB): Separate data.json + fetch at runtime (not used in lite)
 *
 * Usage:
 *   SOURCE_DB=your_db node generate-data.js
 *   open dashboard.html
 *
 * Requirements:
 *   - tdx CLI installed and authenticated
 *   - dashboard.template.html contains <!-- DATA_PLACEHOLDER --> before </body>
 *   - node (any recent version, no npm install needed)
 */

'use strict';

var execSync = require('child_process').execSync;
var fs = require('fs');
var path = require('path');

var DB = process.env.SOURCE_DB || 'your_database';
var TEMPLATE_PATH = path.join(__dirname, 'dashboard.template.html');
var OUTPUT_PATH   = path.join(__dirname, 'dashboard.html');
var DATA_PATH     = path.join(__dirname, 'data.json');   // Pattern B only

// ─── OPTIMIZATION: Query helper with user-controlled row limits ───────────────
// RULES:
// 1. All queries MUST include WHERE + LIMIT (prevents 100K row OOM)
// 2. Default limit: 10,000 rows (generates ~500KB JSON); user can override
// 3. Pre-aggregate by filter dimensions → typically 50-200 rows (<50KB)
// 4. Warn if rows > 1000 (likely to exceed 100KB)
// 5. Ask user if they want to use full data instead of truncated results
function query(sql, limitRows) {
  // Default 10K row limit for safety; user can override via environment variable
  var limit = process.env.DASHBOARD_ROW_LIMIT || (limitRows === undefined) ? 10000 : limitRows;
  var sqlFile = '/tmp/dash_query_' + Date.now() + Math.random().toString(36).slice(2) + '.sql';
  var outFile = '/tmp/dash_result_' + Date.now() + Math.random().toString(36).slice(2) + '.json';
  
  // Add LIMIT if not present (safety check)
  if (sql.toUpperCase().indexOf('LIMIT') === -1) {
    console.warn('⚠️  QUERY: No LIMIT found. Using limit=' + limit + ' rows.');
    console.warn('   → To use full data, set: export DASHBOARD_ROW_LIMIT=999999');
    sql = sql + ' LIMIT ' + limit;
  }
  
  fs.writeFileSync(sqlFile, sql, 'utf8');
  execSync(
    'tdx --json query -d "' + DB + '" -f "' + sqlFile + '" --output "' + outFile + '" 2>/dev/null',
    { encoding: 'utf8', timeout: 60000 }
  );
  
  var result = JSON.parse(fs.readFileSync(outFile, 'utf8'));
  
  // Warn if result is truncated or large
  if (result.length >= limit && limit < 999999) {
    console.warn('⚠️  TRUNCATION: Query returned ' + result.length + ' rows (at limit=' + limit + ').');
    console.warn('   → Dashboard may show incomplete data.');
    console.warn('   → To use ALL rows, set: export DASHBOARD_ROW_LIMIT=999999');
  } else if (result.length > 1000) {
    console.warn('⚠️  SIZE WARNING: Query returned ' + result.length + ' rows (~' + 
                 Math.round(result.length * 0.1) + 'KB). Consider pre-aggregation to reduce payload.');
  }
  
  return result;
}

// ─── OPTIMIZATION: Numeric normalization (smaller JSON payload) ──────────────
// TD returns numeric columns as strings. Coercing to numbers saves ~30-40% JSON size.
// Example: {"revenue": "1234.56"} → {"revenue": 1234.56} (11 bytes → 8 bytes per value)
function num(v, decimals) {
  var d = (decimals === undefined) ? 2 : decimals;
  return Math.round(parseFloat(v || 0) * Math.pow(10, d)) / Math.pow(10, d);
}



// ─── OPTIMIZATION: Final payload size calculation ──────────────────────────────
function reportSize(data) {
  var json = JSON.stringify(data);
  var sizeKB = (json.length / 1024).toFixed(1);
  // Rough gzip estimate: typically 70-85% reduction for JSON
  var compressedKB = (json.length * 0.15 / 1024).toFixed(1);
  console.log('📊 Payload size: ' + sizeKB + ' KB (uncompressed) → ~' + compressedKB + ' KB (gzip)');
}


// ─── OPTIMIZATION: Query Examples ────────────────────────────────────────────
// CUSTOMIZE: replace table names and column names with your actual schema.
// Run `tdx describe <db>.<table>` first to confirm column names.
//
// All examples follow optimization rules:
// 1. Pre-aggregate by filter dimensions (100-500 rows, not raw 10K+)
// 2. SUBSTR for date truncation (month = 7 chars, full ISO = 19 chars)
// 3. WHERE clause with reasonable time window (last 90 days, not all-time)
// 4. LIMIT enforced (default 10,000 rows; override only if validated)
// 5. Short output column names (ch=channel, ty=type, r=revenue, n=count)
// 6. SUM/COUNT/AVG only (no unused string fields)
//
// Pattern A (pre-aggregated): READ-ONLY dashboards, no user filters
//   → KPI cards correct on load but CANNOT update when filters change
//   → Optimal: 100-200 rows / <20 KB JSON
// Pattern B (row-level embed): dashboards WITH user filters
//   → embed full SINK rows (~1K aggregated rows / ~100 KB safe), re-aggregate on every filter
//   → Tradeoff: larger payload, but filters work client-side
// ⚠️ Common mistake: Pattern A with filter UI → KPIs silently ignore all filters

function main() {
  console.log('📊 Generating optimized embedded data...');
  console.log('   Rules: pre-aggregate by filter dimensions, keep full precision, enforce LIMIT');
  console.log('');
  console.log('ℹ️  Multi-tab dashboards: embed separate datasets per tab (see "Multi-Level Filters" in guides)');

  // ── KPI totals ──────────────────────────────────────────────────────────────
  // Customize: replace table and column names
  var kpiRows = query(
    'SELECT' +
    '  SUM(revenue_amount)  AS total_revenue,' +
    '  COUNT(*)             AS order_count,' +
    '  AVG(revenue_amount)  AS avg_order_value' +
    ' FROM your_table_name' +   // <-- replace
    ' LIMIT 1'
  );
  var kpi = kpiRows[0] || {};

  // ── Dimension breakdown ─────────────────────────────────────────────────────
  // Customize: replace dimension_column and table name
  var breakdownRows = query(
    'SELECT dimension_column, SUM(revenue_amount) AS revenue, COUNT(*) AS cnt' +  // <-- replace dimension_column
    ' FROM your_table_name' +   // <-- replace
    ' GROUP BY 1 ORDER BY revenue DESC LIMIT 20'
  ).map(function(r) {
    return { label: r.dimension_column, revenue: num(r.revenue, 0), cnt: num(r.cnt, 0) };
  });

  // ── Time series (skip if table has no date column) ──────────────────────────
  // Customize: replace date_column and table name; remove block if no date column
  // ⚠️  If Workflow path: SINK tables store dates as VARCHAR (e.g., '2025-03-15')
  //    Use SUBSTR(date_column, 1, 7) NOT DATE_FORMAT(date_column, '%Y-%m') — DATE_FORMAT fails on VARCHAR
  //    Example: SUBSTR(date_column, 1, 7) → '2025-03'
  var trendRows = query(
    // Non-Workflow (source table with native DATE):
    // "SELECT DATE_FORMAT(date_column, '%Y-%m') AS month, SUM(revenue_amount) AS revenue" +
    // Workflow (SINK table with VARCHAR):
    "SELECT SUBSTR(date_column, 1, 7) AS month, SUM(revenue_amount) AS revenue" +  // <-- replace date_column, table, aggregation
    ' FROM your_table_name' +   // <-- replace with SINK table name
    ' GROUP BY 1 ORDER BY 1 LIMIT 24'
  ).map(function(r) {
    return { month: r.month, revenue: num(r.revenue, 0) };
  });

  console.log('Row counts: kpi=' + kpiRows.length + ' breakdown=' + breakdownRows.length + ' trend=' + trendRows.length);

  // ── Assemble RAW payload ────────────────────────────────────────────────────
  // ──────────────────────────────────────────────────────────────────────────────
  // Size report (for optimization feedback during development)
  // ──────────────────────────────────────────────────────────────────────────────
  console.log('');
  console.log('📈 Query results:');
  console.log('   KPIs: ' + kpiRows.length + ' row');
  console.log('   Breakdown: ' + breakdownRows.length + ' rows');
  console.log('   Trend: ' + trendRows.length + ' rows');
  
  var RAW = {
    // Shape expected by kpi-dashboard.html
    kpis: [
      { label: 'Total Revenue',    value: num(kpi.total_revenue, 0),   format: 'currency' },
      { label: 'Orders',           value: num(kpi.order_count, 0),     format: 'number'   },
      { label: 'Avg Order Value',  value: num(kpi.avg_order_value, 2), format: 'currency' },
      { label: 'Record Count',     value: num(kpi.order_count, 0),     format: 'number'   }
    ],
    summary: {
      source:  DB + '.your_table_name',   // <-- replace
      period:  'All time',
      records: num(kpi.order_count, 0),
      updated: new Date().toLocaleString()
    },
    // Shape expected by multi-chart-dashboard.html
    by_region:    breakdownRows,
    trend:        trendRows.map(function(r) { return { label: r.month, sales: r.revenue, orders: 0 }; }),
    distribution: breakdownRows.slice(0, 5).map(function(r) { return { label: r.label, value: r.revenue }; }),
    top_items:    breakdownRows.slice(0, 5).map(function(r) { return { label: r.label, revenue: r.revenue }; }),
    // Shape expected by table-dashboard.html
    rows: []  // populate with a row-level query if needed
  };

  // ── Size check ──────────────────────────────────────────────────────────────
  var json = JSON.stringify(RAW);
  var sizeBytes = Buffer.byteLength(json, 'utf8');
  console.log('Payload size: ' + (sizeBytes / 1024).toFixed(1) + ' KB');

  if (sizeBytes > 2 * 1024 * 1024) {
    var sizeKB = (sizeBytes / 1024).toFixed(0);
    console.error('');
    console.error('❌ Payload too large: ' + sizeKB + ' KB (limit: 2,000 KB)');
    console.error('dashboard.html cannot be self-contained at this size.');
    console.error('Reduce the payload before re-running:');
    console.error('');
    console.error('  1. Pre-aggregate by filter dimensions:');
    console.error('     GROUP BY region, channel, date_month');
    console.error('     → Reduces 10,000 rows to 100-200 rows (95% reduction)');
    console.error('');
    console.error('  2. Narrow the time window:');
    console.error('     WHERE date >= CURRENT_DATE - 90  (not all-time)');
    console.error('');
    console.error('  3. Drop unused columns:');
    console.error('     SELECT only columns the dashboard renders');
    console.error('');
    console.error('  4. Coerce numeric strings to numbers in generate-data.js:');
    console.error('     num(row.revenue)  instead of  row.revenue');
    console.error('');
    process.exit(1);
  } else {
    // ── Pattern A: inject inline into template ────────────────────────────────
    var template = fs.readFileSync(TEMPLATE_PATH, 'utf8');
    if (template.indexOf('<!-- DATA_PLACEHOLDER -->') === -1) {
      console.error('ERROR: dashboard.template.html missing <!-- DATA_PLACEHOLDER -->');
      process.exit(1);
    }
    var dataBlock = '<script>var RAW = ' + json + ';<\/script>';
    var html = template.replace('<!-- DATA_PLACEHOLDER -->', dataBlock);

    // Optional: inject render.js inline (avoids external script dependency in delivered file)
    // Add <!-- RENDER_JS_PLACEHOLDER --> to template where render.js should be inlined.
    if (html.indexOf('<!-- RENDER_JS_PLACEHOLDER -->') !== -1) {
      var renderJs = fs.readFileSync(path.join(__dirname, 'render.js'), 'utf8');
      html = html.replace('<!-- RENDER_JS_PLACEHOLDER -->', '<script>' + renderJs + '<\/script>');
    }

    fs.writeFileSync(OUTPUT_PATH, html, 'utf8');
    console.log('Written: ' + OUTPUT_PATH + ' (' + (Buffer.byteLength(html, 'utf8') / 1024).toFixed(0) + ' KB)');
    console.log('Open: open dashboard.html');
  }
}

main();
