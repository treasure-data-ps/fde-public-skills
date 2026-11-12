# Visualization Instructions — Next Best Action Model

## Available Tools

### render_chart
For standard chart types. Parameters:
- `type` — bar, line, pie, area, scatter, horizontal-bar, stacked-bar, radar, funnel
- `title` — chart title
- `labels` — X-axis labels (bar/line/area), segments (pie/funnel)
- `datasets` — array of `{label, data}` objects for each series
- `x_axis_title`, `y_axis_title` — axis labels

### render_react
For complex interactive dashboards using Recharts + Tailwind CSS inside the Treasure Work chat (not for shareable/exportable files):
- Write a single component: `export default function ComponentName({ data })`
- React hooks (useState, useEffect, useMemo) and all Recharts components are available as globals — do NOT import them
- Use Tailwind CSS for styling with `dark:` variants for dark mode
- `isDark` boolean and `theme` string are available in scope
- Use for: multi-chart dashboards, interval (error-bar) charts, heatmaps, complex layouts

### Templated HTML dashboard (`dashboard_template.html`)
Use this when the user asks for a **shareable, exportable, standalone HTML dashboard** (an artifact they can email, host, or open offline). Don't reach for `render_react` for this — that's chat-only.

- Template lives at `references/dashboard_template.html`
- Run `references/generate-data.js` from the user's working directory; it runs its queries concurrently, substitutes the tokens and writes to `agent_outputs/<project_slug>/dashboards/nba_ai_signal_dashboard.html` (git-ignored)
- Open the generated file with `mcp__work__open_file`
- See SKILL.md "Generate an HTML dashboard" pattern for the full procedure
- Keep TD palette, layout CSS, and chart shapes intact — only the data behind the tokens changes

## TD Color Palette

Primary (use in order for chart series):
```
["#B4E3E3", "#ABB3DB", "#D9BFDF", "#F8E1B0", "#8FD6D4", "#828DCA", "#C69ED0", "#F5D389", "#6AC8C6", "#5867B8", "#B37EC0", "#F1C461", "#44BAB8", "#2E41A6", "#8CC97E", "#A05EB0"]
```

Semantic colors for next best action:
```
Logged (past decisions):     "#ABB3DB" (lavender)
Recommended (policy):        "#44BAB8" (teal)
Estimated policy value:      "#2E41A6" (dark blue) — with its interval as error bars
Random baseline (tuning):    "#F1C461" (amber)
Decline / shift away:        "#A05EB0" (purple)
```

Keep one color per action across every chart of an answer (palette order by the action's size in the latest run).

## Chart Standards

- Legends must be visible for multi-series charts
- Always create **separate individual charts** — never combine into subplots
- Rewards and policy values with 4 decimal places (e.g., 0.0731), or as "N in 100" for 0/1 rewards
- Shares and lifts with 1 decimal place (e.g., 23.4%)
- Always show the confidence interval next to an estimated policy value
- Bold all metrics in text output
- Clear axis labels with business context (the customer's action names)
- Create 3-7 charts per analysis response

## Chart Type Selection

| Analysis Type | Tool & Type |
|---|---|
| Policy value vs logged reward (with interval) | `render_react` bar with error bars, or `render_chart` type: "bar" + interval in the text |
| Logged vs recommended action mix | `render_chart` type: "bar" (grouped) |
| Recommended customers per action | `render_chart` type: "horizontal-bar" or "pie" (≤ 6 actions) |
| Average logged reward per action | `render_chart` type: "bar" |
| Policy value across training runs | `render_chart` type: "line" |
| Customers per action across scoring runs | `render_chart` type: "stacked-bar" |
| Tuning trials (score per trial, by phase) | `render_chart` type: "scatter" |
| Context of customers per action (feature averages) | `render_chart` type: "bar" (grouped) or `render_react` heatmap |
| Followed vs other action (live check) | `render_chart` type: "bar" |

## Visualization Templates

### Logged vs Recommended Mix (Grouped Bar)
```
render_chart:
  type: bar
  title: "Action Mix — Past Decisions vs Model Recommendations"
  labels: [action names]
  datasets:
    - {label: "Logged share", data: [values]}
    - {label: "Recommended share", data: [values]}
  y_axis_title: "Share of decisions"
```

### Policy Value vs Logged Reward
```
render_chart:
  type: bar
  title: "Expected Success per Customer"
  labels: ["Past decisions (logged)", "Model policy (estimated)"]
  datasets: [{label: "Average reward", data: [logged_avg_reward, estimated_policy_value]}]
  y_axis_title: "Average reward"
```
State the interval (`ci_lower`–`ci_upper`) in the caption, or draw it as error bars with `render_react`.
