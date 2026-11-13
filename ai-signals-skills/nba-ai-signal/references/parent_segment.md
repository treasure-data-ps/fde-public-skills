# NBA AI Signal — Parent Segment Update Spec

This file is the solution-specific "what" for Phase 5 Step 1. The process (approval gates, push mechanics, section placement rules) is in `../../shared/parent_segment_update.md`. Read both files together before making any changes.

---

## Source Table

**Source table:** `<sink_database>.<pred_output_table>` (default `nba_ais_actions`) — replaced at the end of every `predict.dig` run: one row per user from the latest scoring run. Never use `<pred_output_table>_history` — it is appended on every run, so a profile would match one row per run.

**Join key:** `user_id` ↔ the Parent Segment's customer ID matching the configured `user_column`.

## Attribute Block

**Block name:** the decision in business words (e.g. `Next Best Offer`, `Next Best Campaign`) — confirm with the user.

| Column | Type | Label |
|--------|------|-------|
| `next_best_action` | string | `<Decision>` (e.g. Next Best Offer) |
| `scored_date` | string | `<Decision> Date` |

> **Default recommendation:** both columns — `scored_date` lets marketers see how fresh the recommendation is. Customers not in the scoring population have no value; audiences should treat that as "no recommendation".

---

## Example Audience Folder

**Folder name:** `<Decision> Examples` (e.g. `Next Best Offer Examples`)

Confirm this name with the user before creating any segments (per `../../shared/parent_segment_update.md` Step 3a).

---

## Example Segments

Present this full list to the user for approval before creating any YAMLs.

**STOP — before creating any segment YAMLs, load `tdx-skills:segment`.** That skill defines the exact YAML schema (`rule:` not `rules:`, flat `attribute:` string, `operator:` as an object) required by `tdx sg push`. The filter descriptions below are business-logic shorthand — always translate them through `tdx-skills:segment` to produce valid YAML. Never hand-craft segment YAMLs without it.

The default example set is exactly **4 segments**: one per recommended action, for the four actions with the most customers in the latest run. Do not create more unless the user explicitly asks. Name them in the customer's terms from `business-context.md` (e.g. "Free shipping offer", "Loyalty points offer").

| # | Segment name | Filter | Attribute | Operator |
|---|---|---|---|---|
| 1 | `[<Decision>] <action 1>` | recommended action = the largest action | `next_best_action` | `Equal` |
| 2 | `[<Decision>] <action 2>` | second largest | `next_best_action` | `Equal` |
| 3 | `[<Decision>] <action 3>` | third largest | `next_best_action` | `Equal` |
| 4 | `[<Decision>] <action 4>` | fourth largest — or, with fewer than four actions, every customer with a recommendation | `next_best_action` | `Equal` / `IsNotNull` |

Before presenting, query the source table for the values and sizes:

```sql
SELECT next_best_action, COUNT(*) AS cnt, MAX(scored_date) AS scored_date
FROM <sink_database>.<pred_output_table>
GROUP BY 1 ORDER BY 2 DESC;
```

> **Note:** use the exact action spellings from this query. Eligibility rules from the requirements (requirements question 7 — budget caps, regions, consent) are added as extra conditions on these segments, not in the model. Confirm segment counts with the customer before presenting them as production audiences.
