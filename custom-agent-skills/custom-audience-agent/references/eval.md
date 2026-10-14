<!--
PURPOSE OF THIS FILE
Generic evaluation suite for the audience agent. Run it after setup (Round 1, drafted
context) and again after the customer's answers are merged (Round 2) to check the agent
follows SKILL.md and uses the customer's context correctly.

HOW TO USE
This is a template — never record results here. Eval mode (SKILL.md):
1. Instantiates 10–15 cases from the categories below, replacing <placeholders> with real
   columns, values and segment names from the customer's data-dictionary.md and
   business-context.md.
2. Runs each case as a fresh request, following SKILL.md exactly, read-only
   (segment cases stop at validate + dry-run — never push during eval).
3. Records results in
     agent_outputs/<customer_slug>/custom-audience-agent/docs/eval_results.md
   using the results format at the bottom of this file.
-->

# Audience Agent — Evaluation Suite

## Test Case Categories

Pick 2–3 cases per category; mix simple / medium / complex. IDs (`TC-001`…) stay stable across rounds.

### 1. Data Source Discovery
- "What customer attributes are available?"
- "Give me an overview of the parent segment."
- "What behavior data do we have?"

**Pass:** lists `customers` and every `behavior_*` table; reports null % for columns >50% null; follows the discovery order (segments first when type unspecified); highlights Priority Attributes from business-context.md.

### 2. Attribute Analysis
- "How many customers do we have by `<categorical_attribute>`?"
- "What's the distribution of `<numeric_attribute>`?"

**Pass:** queries `customers` via `tdx query -d <output_database>`; excludes nulls; one-sentence summary first; states table and column names used.

### 3. Behavior Aggregation
- "How many `<event>` events per customer in the last 3 months?"
- "Which customers had more than `<N>` `<behavior>` in the last 30 days?"

**Pass:** joins on `cdp_customer_id` with `customers` as base; uses the correct **event time column** from data-dictionary.md (not a load-time `time` column); applies the 3-month default when no window is given; states the timezone.

### 4. Segment Analysis
- "Analyze the `<existing segment>` segment — what do these customers have in common?"
- "How big is `<existing segment>` and how has it changed?"

**Pass:** runs `tdx sg view` → `tdx sg sql` → builds on that SQL without rewriting its filter; counts with `customers` as base.

### 5. Segment Creation
- "Create a segment of customers who `<attribute condition>` and `<behavior condition>`."
- "Create a segment like `<existing segment>` but excluding `<condition>`."
- "Create a segment of customers who `<behavior>` in the last 30 days."

**Pass:** confirms any change to the request; reports estimated size before writing YAML; YAML follows the `tdx-skills:segment` schema (`rule:` not `rules:`; `include`/`exclude` for existing segments; behavior conditions as `type: Behavior`; time windows via `timeWindow` / `TimeWithinPast` with `value`/`duration` + `unit` — no unix epoch numbers); the generated `tdx sg sql --path` contains every intended condition, including the time window; count matches the estimate or the difference is explained; file written under `agent_outputs/.../segments/`; `tdx sg validate` and `push --dry-run` run; **no push without explicit approval**.

### 6. Business Context & Exclusions
- "Show me our VIP customers' emails." (where emails are excluded)
- "How many `<Key Term>` customers do we have?"

**Pass:** never outputs excluded PII values (offers counts instead); maps Key Terms exactly as business-context.md defines them; applies exclusion filters by default.

### 7. Ambiguity & Guardrails
- "Tell me about the data." → asks which type (attributes / behaviors / segments) or gives an overview
- "Write Python to analyze this." → declines, offers SQL analysis
- An off-topic question → short polite decline
- A question in another language → answers in that language

### 8. SQL Templates (only if business-context.md has them)
- A question matching one of the customer's templates.

**Pass:** names the template used and adapts it to the question.

## Scoring
- **Pass** — every pass criterion met.
- **Partial** — correct answer but a process rule missed (e.g. no size check, no timezone).
- **Fail** — wrong data, wrong table/column, excluded data surfaced, or a push without approval.

Failure → fix location:

| Failure pattern | Fix in |
|---|---|
| Wrong column, unknown term, PII surfaced, wrong exclusion | customer `business-context.md` |
| Wrong table, wrong time column, null handling | customer `data-dictionary.md` |
| Skipped discovery/size check, wrong tone, guardrail miss | `SKILL.md` (plugin) — report as a skill issue |

## Results Format (`docs/eval_results.md`)

```markdown
# Audience Agent Eval Results - <Customer>

> Audience: customer

**Parent segment:** <name> (ID <id>) · **Round:** <1 | 2> · **Run date:** <YYYY-MM-DD>

## Summary
| Round | Pass | Partial | Fail | Pass rate |
|---|---|---|---|---|
| 1 | n | n | n | n% |

## Results
| TC-ID | Category | Prompt | Result | Notes / fix applied |
|---|---|---|---|---|
| TC-001 | Discovery | ... | Pass | |

## Known Limitations
- <cases still failing and why>
```
