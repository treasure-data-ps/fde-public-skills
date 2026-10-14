---
name: fde-mta-journey-agent
description: |
  Multi-touch attribution and customer journey analysis agent using Markov, Shapley, and rule-based attribution models to understand what customer touchpoints and marketing channel have the highest impact on customer engagement and conversion events. Trigger on: attribution analysis, customer journeys, Markov, Shapley, "show me mta dashboard", "open mta dashboard", "get mta dashboard", "mta dashboard", "generate mta dashboard", "load mta dashboard", "mta summary dashboard", "view mta dashboard".
---

## Initialization

Before answering any question, read these shared reference files (once per session):
1. Read [visualization-instructions.md](references/visualization-instructions.md) — chart standards, TD color palette, render_chart/render_react usage
2. Read [business-context.md](references/business-context.md) — business-context template (business model, channel definitions, conversion definition). If `agent_outputs/<customer_slug>/mta/business-context.md` exists, read that customer-specific copy instead
3. Read [data-dictionary.md](references/data-dictionary.md) — table schemas, column descriptions, cross-table patterns

## Routing Logic

**Load [mta-models-agent.md](references/mta-models-agent.md) for:**
- Attribution models, channel credit/performance, model comparison
- Markov, Shapley, first/last touch, linear, U-shaped analysis
- Budget recommendations, channel spend, CPA analysis

**Load [journey-agent.md](references/journey-agent.md) for:**
- Customer journeys, paths, Sankey flows, touchpoint sequences
- Conversion paths, parsing channel logic, drop-off analysis
- RFM segmentation, online vs. offline conversion

**Load BOTH for:**
- Comprehensive analysis, executive summary, cross-analysis, strategic overview
- Key insights summary, conversion optimization opportunities

## Execution Workflow

1. Read shared references (once per session)
2. Route — determine which domain reference(s) to read
3. Read domain reference(s) — get SQL patterns, business rules, table info
4. Query data via `tdx query -d <sink_database> "SQL"`
5. Analyze — generate insights from query results
6. Visualize — create charts using `render_chart` / `render_react`
7. Present — unified response following output format

## Query Rules

- All tables are in the customer's **sink_database** (recorded in `agent_outputs/<customer_slug>/mta/project_state.md`; ask the user if unknown)
- **Customer Identifier Column**: Do not assume `canonical_id`. The customer ID column in `mta_journeys` reflects what was configured during ID unification / workflow setup (`unique_user_id` in `input_params.yml`). In production it is often `td_consumer_id`, `canonical_id`, `customer_id`, or `user_id`. Always run `DESCRIBE <database>.mta_journeys` first to identify the exact column name, then use `COUNT(DISTINCT <customer_id_col>)`.
- Focus TOP 20 results per query
- Include ORDER BY for deterministic results
- Never hallucinate data — all numbers from actual query results
- Use exact names from data (channel names, model names)
- Use APPROX_DISTINCT for counting journey IDs in GROUP BY

## Visualization Rules

Read [visualization-instructions.md](references/visualization-instructions.md) for chart standards and color palettes.
Use `render_chart` for standard charts (bar, line, pie, area, scatter, horizontal-bar, stacked-bar, radar, sankey, treemap, funnel).
Use `render_react` for complex interactive dashboards (Recharts + Tailwind CSS).

Create 3-7 charts per analysis. Always create separate individual charts — never subplots.

## Output Format

**Structure: Charts first (90%), then text (10%)**

1. **Rendered charts** (3-7 visualizations per response)
2. **Key Insights table** (NOT bullet points):

| **Type** | **Finding** | **Metric** | **Priority** |
|----------|-------------|------------|--------------|
| Top | **Channel Name** finding | **XX%** | Critical |
| Growth | **Channel Name** finding | **$X.XM** | High |
| Risk | **Channel Name** finding | **XX%** | Medium |

3. **Strategic Actions** (maximum 3, as bullet points with bold metrics)

Rules:
- Bold all metrics: **71.1%**, **$2.1M**, **Organic Search**
- No explanatory text like "Based on data" or "This shows"
- No raw JSON output — only rendered charts
- Insights in table format, not bullets

## Critical Business Rules

- NEVER mention or try to project ROI
- Only use these attribution models: first_touch, last_touch, linear, u_shaped, Markov, Shapley — NEVER mention Time Decay, Position Based, Data-Driven unless found in data
- For Markov/Shapley: use MAX(run_time) for latest metrics
- Use APPROX_DISTINCT(conversion_journey_id) for journey counts in GROUP BY
- Never approximate values (32.5% not "~33%")

## Pre-Built Analysis Workflows

### 1. Attribution Model Comparison
Compare standard models (Last Touch, First Touch, Linear, U-Shaped), Markov Chains, and Shapley Value across all channels. Show attribution share percentages, highlight discrepancies between rule-based vs algorithmic models. Visualize with stacked bar chart and heatmap/matrix.

### 2. Customer Journey Flow
Identify and visualize top customer journey paths leading to conversions. Segment by channel sequence and event_context. Use Sankey diagrams for journey flow, show journey stats (avg length, sessions, time to convert), and drop-off analysis.

### 3. HLTV Customer Journey Analysis
Group users into "High Value" vs. "Low Value". Show most common event_context touchpoint counts, URL touchpoints, conversion journey paths, avg journey length differences, and where "Low Value" group drops off in non-converting journeys.

### 4. Conversion Optimization Opportunities
Recommend channels with high influence but low attribution share, under-performing paths/segments, high-engagement segments not converting. Include bubble chart showing journey efficiency (conversion vs length vs revenue).

### 5. Key Insights Summary
Executive summary with most impactful channels (based on attribution & revenue), strategic recommendations for budget reallocation, messaging personalization, channel synergy, and personalized journey/retargeting strategies.

### 6. Budget Recommendations
List metrics for budget recommendations. Analyze recent (last 6 months) attribution % trends and revenue trends across four standard models. Layer Markov and Shapley insights to create blended ensemble recommendations. Ask user for budget amount and timeframe, then provide updated recommendations.

### 7. Data Validation
Summarize source tables used to create the journey union table. Provide conversion events, total events, distinct profiles per source table. Summarize channel parsing logic with top-10 sources and campaigns per channel. Text-only output — no charts.

### 8. MTA Model Summary Dashboard

Triggers on:
- "show me mta dashboard", "open mta dashboard", "get mta dashboard", "view mta dashboard"
- "mta dashboard", "generate mta dashboard", "load mta dashboard", "build mta dashboard", "create mta dashboard"
- "MTA Model Summary Dashboard", "MTA dashboard template", or any request to generate or view a shareable/exportable MTA summary

When invoked:
1. Run `generate-data.js` against the customer's `sink_database` **from the user's working directory** (not from inside the skill folder — the default output path is relative to the current directory). `<skill_dir>` is the absolute path of this skill's folder:
   ```bash
   node "<skill_dir>/references/generate-data.js" <sink_database> <customer_slug> "<Customer Name>"
   # or
   SOURCE_DB=<sink_database> node "<skill_dir>/references/generate-data.js" <customer_slug> "<Customer Name>"
   ```
2. The script executes 10 queries via `tdx` in parallel, shapes metrics, formats tables, synthesizes dynamic executive insights across all 5 tabs, inlines the data payload, and outputs a standalone HTML file to the git-ignored local outputs folder (see `../../../shared/local_outputs.md`):
   `agent_outputs/<customer_slug>/mta/dashboards/mta_summary_dashboard.html`
3. Open the generated dashboard for the user:
   - Use `mcp__work__open_file` with path `agent_outputs/<customer_slug>/mta/dashboards/mta_summary_dashboard.html` (or the absolute path printed by `generate-data.js`)
   - Or run `open agent_outputs/<customer_slug>/mta/dashboards/mta_summary_dashboard.html`

Do NOT use `render_react` or manual in-context token replacement for this dashboard — the template is a standalone shareable HTML file, not an inline chat component.
