# Knowledge Base Template — Business Context

This template captures Phase 2 validated business facts, metrics, personas, and data context that the agent uses to answer questions correctly.

**Usage**: Fill in the bracketed sections with customer-specific values from Phase 2 discovery.

---

# Business Context — [CUSTOMER_NAME] Dashboard

## Company Overview
- **Customer:** [CUSTOMER_NAME]
- **Industry:** [Industry — e.g., "Automotive — dealership/OEM"]
- **Business model:** [Revenue model — e.g., "Revenue from vehicle service + test drive → purchase conversions"]
- **Portfolio:** [Key entity counts — e.g., "1,000 customers, 1,266 active vehicles, 20 dealers, 15 active email campaigns"]

## Dashboard Purpose
Multi-area operational dashboard covering [N] business domains:
1. **[Area 1]** — [Description and key metric range]
2. **[Area 2]** — [Description and key metric range]
3. **[Area 3]** — [Description and key metric range]
4. **[Area N]** — [Description]

## Primary Revenue Metric
**[Definition of primary revenue].** [Clarifications on what's NOT available — e.g., "no sales transactions table", "no purchase price column"]

## Audience & Personas

| Persona | What they care about | Preferred format |
|---------|---------------------|------------------|
| Executive | 3–5 KPI headlines, trend direction | 2–3 bullet summary |
| Manager | Breakdowns by [dimension], MoM trends, rankings | Table + description |
| Analyst | Raw numbers, SQL, full drill-downs, anomalies | Detailed with calculations |

## Key Metrics Confirmed (Phase 2 Validated)

| Metric | Value | Source |
|--------|-------|--------|
| [Metric 1] | [Value] | [Table] |
| [Metric 2] | [Value] | [Table] |
| [Metric 3] | [Value] | [Table] |

## Seasonality & Context
- **Data range:** [START_DATE] — present
- **[N] [entities]** — named ([examples])
- **Constraints:** [List unavailable tables/columns that came up in discovery]

Examples:
- **No inventory table** — days-on-lot unavailable
- **No purchase price column** — gross profit per sale unavailable
- **Fan-out:** [Table] has N rows but M unique [entity]

## Open Items Resolved (Phase 2)
- **[Metric/Assumption 1]:** [How it was resolved — e.g., "Customer confirmed AVG(satisfaction_score) is correct"]
- **[Metric/Assumption 2]:** [How it was resolved]

## Business Goals
- [Goal 1 — e.g., "Daily leadership review of all operational areas"]
- [Goal 2 — e.g., "Replace manual reporting (reduce time-to-answer from hours to minutes)"]
- [Goal 3 — e.g., "Monitor [dimension] performance — benchmarks or watch-list"]
---

**Version:** 1.0.0
**Last Updated:** 23 June 2026
**Author:** FDE Team
