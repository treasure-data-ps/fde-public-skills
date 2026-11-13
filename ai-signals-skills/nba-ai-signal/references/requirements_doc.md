# NBA AI Signal — Requirements Doc Body

Phase 2 body for `agent_outputs/<project_slug>/requirements.md` (title `<Project Name> Requirements`). Mechanics — writing, hand-off, reading it back — are in `../../shared/playbook.md` (Phase 2 and Phase 4).

Write the doc for the customer to fill in: one `> _Your answer:_` line under each question, Phase 1 findings (decision, actions, reward, sources) pre-filled and marked `[INFERRED — please confirm]`, open questions marked `[NEEDS YOUR INPUT]`. Do not include config parameter names in the customer-facing doc — the mapping table at the end of this file is for you.

> **How to ask (when the user answers in chat instead of the doc):** always use `AskUserQuestion`, never a plain-text list. Batches of up to 4 questions per call; 2–4 options per question with the recommended default marked `(Recommended)`; the implicit "Other" lets the user type their own answer.

Not asked here — confirmed in Phase 3: the output (sink) database and the workflow project name.

---

## Doc body

Title, one-line purpose ("These answers let us train a model that recommends the best <action type> for each customer"), a target return date, then these sections:

### 1. Decision and audience

1. Which decision should the model make for each customer — the best channel, the best time to send, the best campaign, or another choice (offer, treatment, content)? Pre-fill from Phase 1 in one sentence (e.g. "through which channel to reach each customer next").
2. How will the recommended action be used (campaign targeting, journey branch, sales script, website content), and through which channels?
3. Who will use the recommendations and the dashboard (CRM, marketing, analytics)?
4. Which Parent Segment should receive the recommendation as an attribute?

### 2. Actions

5. Confirm the list of actions found in Phase 1 (pre-filled table: action, how often it was used, its past success rate). Should any be merged, renamed or removed (retired campaigns, test variants, rare channels)?
5a. Channels only: confirm how website visits get their channel (pre-filled: the UTM values found and the channel each maps to, e.g. `cpc` + `google` → paid search). Are there tracking codes of your own (affiliate IDs, partner codes, internal campaign parameters) we should map?
5b. Time only: which time zone should times be read in, and which slots are useful — four dayparts, hours, or day of week × daypart?
6. Is there a "do nothing" / control option that was logged, and should the model be allowed to recommend it?
7. Are there rules on who may receive which action (eligibility, budget caps, minimum spend, regions)? The model doesn't apply them — they are applied when the audiences are built.
8. Were actions assigned at random or in rotation at any time (A/B tests, holdouts)? If the assignment probability was logged, where?

### 3. Success definition (reward)

9. Confirm what counts as success after an action (pre-fill: e.g. "an order within 14 days of the email"). Edge cases (refunds, orders without the offer, repeated actions)?
10. How long after an action should success count? (Recommended: the typical time from action to response.)
11. Should success be yes/no or a value (order value, margin)? If a value, should very large orders be capped?
11a. When a customer has several touches before converting, should the conversion count only for the last touch before it (Recommended when touches are frequent) or for every touch in the window?

### 4. Data sources and context

12. Confirm the sources combined into the customer timeline found in Phase 1 (pre-filled table: source — website, email, app, SMS, call center, orders —, what it records, the ID it uses, how its channel is set). Is any source missing (ad clicks, push, stores)?
12a. Which events count as a decision you make (sends, assignments) and which are customer engagement (opens, visits)? How long without activity ends a visit (Recommended: 30 minutes)?
13. Which customer signals do you believe change which action works (recent activity, spend level, tenure, channel preference, past response)?
14. Which columns must never be used (PII, sensitive attributes, anything recorded after the action)?
15. How much history should the model learn from (e.g. the last 3, 6 or 12 months of actions)? (Recommended: 6 months.) Did anything change in that period (new offers, pricing, tracking)?

### 5. Who gets a recommendation

16. Which customers should get a recommendation at each run (all active, opted in for the channel, not contacted recently)?
17. Which records must be excluded (test or internal accounts, employees, suppressed customers)?
18. Which ID identifies a customer across your tables (the one your Parent Segment joins on)? Pre-fill from Phase 1.

### 6. Schedule and notifications

19. **Retrain schedule** — how often should the model relearn? (Recommended: monthly, or when the action set changes.)
20. **Recommendation schedule** — how often should recommendations refresh? (Recommended: before each campaign, or weekly.)
21. Which email address should receive workflow failure alerts?

### 7. Business context

The questions still marked `[NEEDS YOUR INPUT]` in `business-context.md` that sections 1–6 don't already ask, grouped under that file's headings (playbook Phase 2 step 4). Omit the section if none are left.

Close with: "When done, save this file and send it back to the person who shared it with you."

---

## Answer → config mapping (for Phase 4)

Parameter meanings are in the template `README.md` (Configuration); choosing rules in `workflow-setup.md` and `ai-signals-guide.md` §5.

| Question | Sets |
|---|---|
| 4 | Parent Segment used in Phase 5 (`references/parent_segment.md`) |
| 1 | `nba_type` |
| 5, 6 | Action grouping: `min_action_share`; campaign themes / custom labels in `sql/touchpoints_union.sql` |
| 5a | Channel rules in `sql/touchpoints.sql`; UTM / traffic-source extraction in the web blocks of `sql/touchpoints_union.sql` |
| 5b | `local_timezone`, `time_grain` |
| 7 | Phase 5 example audiences and activation rules (not the model) |
| 8 | `propensity_column` + `propensity_type: true_propensity` in `train.dig` (Customization Points); rotations → caveat in the docs |
| 9 | Conversion blocks (`is_conversion`) in `sql/touchpoints_union.sql` |
| 11 | `reward_type`; cap in the orders block |
| 11a | `reward_attribution` |
| 10 | `reward_window_days` |
| 12 | Blocks of `sql/touchpoints_union.sql` |
| 12a | `action_sources` (and separate `src_name` for sends); `session_gap_minutes` |
| 13 | Context CTEs in `sql/input_features.sql` |
| 14 | Remove from the SQL; non-features into `exclude_columns` |
| 15 | `train_window_days`; `feature_lookback_days` |
| 16, 17 | `pred` branch of the `anchors` CTE in `sql/input_features.sql`; filters in the union blocks |
| 18 | `user_column` (and the join keys in the SQL) |
| 19, 20 | `schedule` in `nba_ais.dig`, or separate schedules in `train.dig` / `predict.dig` (`dataprep-guide.md` §6) |
| 21 | `_error` → `to:` in `nba_ais.dig` |

Questions 1–3, 5–9, 13, 14, 16, 17 and every section 7 answer also go into `business-context.md` (playbook Phase 4 Part B step 4); questions 1–3 feed the documentation set.

Before editing in Phase 4, show the user a summary of planned changes (decision type, union sources and channel rules, actions kept / merged / dropped, reward rule and window, context sources added or removed, excluded columns, training window, scoring population, tuning, policy type, schedules, alert email) and wait for approval.
