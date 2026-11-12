# NBA AI Signal Summary Dashboard — Build & Data Guide

A 3-tab standalone HTML dashboard for the latest Next Best Action run: the learned policy vs past decisions, the action mix, and run history.

---

> **Use as-is.** The dashboard template and `generate-data.js` are pre-validated: run the command once and use the result as it is. Do not take screenshots, run browser, QA or validation scripts, re-check the data, or edit the generated HTML, and do not apply other visualization or design skills to it. If something looks wrong, tell the user instead of fixing it.

## 1. Generate with `generate-data.js`

`generate-data.js` queries `{{sink_database}}` via `tdx` in parallel, shapes the values, writes the insight bullets and bakes all data into the template.

```bash
# Run from the Work Folder root (where agent_outputs/ lives).
node ".claude/skills/{{agent_name}}/references/generate-data.js" {{sink_database}} {{project_slug}} "{{project_name}}" \
  -P {{pred_table}} -o "{{engagement_dir}}/dashboards/nba_ai_signal_dashboard.html"
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SOURCE_DB` | Env / Arg 1 | Required | Sink database with the `nba_ais_*` tables and the recommendations |
| `PROJECT_SLUG` | Env / Arg 2 | `nba-ai-signal` | Project slug — default output folder `agent_outputs/<project_slug>/dashboards/` |
| `PROJECT_NAME` | Env / Arg 3 | Title-cased slug | Display name in the header |
| `PRED_TABLE` / `-P, --pred-table` | Env / Flag | `nba_ais_actions` | The workflow's `pred_output_table` (here `{{pred_table}}`); `<pred_table>_history` is read for the history |
| `-o, --output` | String | `agent_outputs/<project_slug>/dashboards/nba_ai_signal_dashboard.html` | Output file path |
| `-t, --template` | String | `dashboard_template.html` next to the script | Template path |
| `-v, --verbose` | Flag | `false` | Query timings and row counts |

Open the result with `open "{{engagement_dir}}/dashboards/nba_ai_signal_dashboard.html"` or, in Treasure Work, `mcp__work__open_file`. It needs internet access for the Plotly CDN.

## 2. Source queries (run by `generate-data.js`)

The `nba_ais_*` logs are appended: the latest run is the newest row by `time`; action stats and tuning are reduced to their latest session / run id.

| Query | Table | Powers |
|---|---|---|
| Q1 latest training run | `nba_ais_run_log` (latest row) | Header, Tab 1 KPIs, policy chart, run table |
| Q2 training history | `nba_ais_run_log` ordered by `time` | Tab 3 policy-value trend |
| Q3 action mix | `nba_ais_action_stats` (latest session) | Tab 2 KPIs, charts and table |
| Q4 latest recommendations | `{{pred_table}}` | Header and Tab 2 customers scored, actions used |
| Q5 tuning best trials | `nba_ais_tuning_results` (latest `run_id`, `is_best = 'true'`) | Tab 1 tuning table — empty when tuning never ran |
| Q6 scoring history | `{{pred_table}}_history` grouped by session and action | Tab 3 stacked customers per action |

A query on a missing table (tuning off) returns nothing and the section shows its "not run" note.

## 3. Tabs

- **Header** — project, sink database, training session, run date, recommendations table, model name and policy type (`tuned` when tuning chose it), actions, customers scored, number of training runs.
- **Tab 1 — Policy Performance** — logged average reward, estimated policy value, its 95% interval, estimated lift, evidence pill (interval above the logged reward = confident improvement; estimate above but interval includes it = likely, not proven; otherwise no improvement); bar chart with the interval as whiskers; run table; tuning table (best trial per phase with the chosen settings, hold-out value and lift vs random); insights.
- **Tab 2 — Action Mix** — customers scored, actions recommended, top action, biggest shift; logged vs recommended share; average logged reward per action (labelled raw, not the effect); action table; insights (never-recommended actions, actions with < 200 logged rows).
- **Tab 3 — Historic Tracker** — policy value with its interval band and the logged reward per training run; recommended customers per action per scoring run; a single-run callout until a second run exists.

## 4. Programmatic access (`window.RAW`)

```javascript
// { project: { name, slug, database, predTable },
//   meta: { sessionId, predSessionId, modelName, modelType, tuned, customersScored },
//   training: { latest, historic: [...] },
//   tuning: [...best trial per phase],
//   actions: [{ action, loggedRows, loggedShare, loggedReward, recommended, recommendedShare, shift }],
//   scoring: { latest, sessions: [...], series: [{ action, customers: [...] }] } }
```
