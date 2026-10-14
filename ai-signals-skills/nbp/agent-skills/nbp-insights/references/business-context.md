# NBP — Business Context

Use this document to interpret NBP recommendations, coverage metrics, and dashboard data in the context of how the workflow actually works. For table schemas, see `data-dictionary.md`.

---

## What the NBP Workflow Produces

For every unique user in the customer's transaction data, the workflow writes a row of ranked product recommendations into `{user_master_attr_table}` (default: `nbp_user_master`). Each workflow run is identified by a `session_id` tracked in `{prefix}global_session_filter`.

The NBP outputs span two groups:

- **Ranked recommendations** — per-rank product name, SKU, and category columns (`nbp_1`, `nbp_1_sku`, `nb_category_1`, ...) written to the user master attribute table for Parent Segment ingestion.
- **Dashboard aggregations** — run-level stats, item popularity, category breakdowns, recommendation distributions, and (optionally) test set evaluation results.

---

## Recommendation Engines

### `hive` Engine — Hivemall DIMSUM Collaborative Filtering

**Question it answers:** "Based on what this user has bought, what similar items should we recommend?"

**How it works:**
1. Builds item-item cosine similarity via DIMSUM on the full user-item interaction matrix
2. For each user, seeds from their `N` most recent purchases (controlled by `recent_items`)
3. Finds the top-K similar items for each seed (controlled by `topk_similar_items`)
4. Aggregates across seeds and explodes into per-rank recommendation columns
5. Already-purchased items are automatically excluded via `NOT EXISTS` SQL

**When to use:** No external API dependency required; full algorithm control; best for customers with clear purchase patterns and a catalog large enough to produce meaningful similarities.

**Cold-start behavior:** Users with zero purchase history receive no recommendations. There is no fallback algorithm.

**Tuning knobs visible in `dash_model_param_stats_agg.model_params`:**
- `topk_similar_items` — how many similar items are retained per seed item (default: 3)
- `recent_items` — how many of the user's recent purchases seed the recommendation
- `max_recommended_items` — final output rank depth (default: 5)
- `min_cooccurence_filter` — minimum purchase count per item to be included in training
- `dimsum_similarity_threshold` — cosine similarity cutoff (lower = more diverse, higher = more precise)

---

### `automl` Engine — ml-batch-api (PrecisionML)

**Question it answers:** "Using a PrecisionML model, what should we recommend to this user?"

**Three algorithms:**

| Algorithm | How it works | Best for |
|-----------|-------------|----------|
| `als` | Alternating Least Squares matrix factorization — learns latent user and item factors from interaction history | Strong personalization; best when ≥50K users with sufficient purchase history |
| `similar_to_latest` | Recommends items most similar to the user's most recent purchase | Lighter than ALS; good when recency is the primary signal |
| `popular` | Recommends the globally most-ordered items; identical output for all users | Cold-start fallback; ensures 100% user coverage |

**Cold-start behavior:** `popular` covers all users including those with zero purchase history. `als` and `similar_to_latest` may leave cold-start users without recommendations, depending on the model's minimum interaction threshold.

**`filter_viewed` toggle:** When `true`, already-purchased items are excluded from the recommendation output. The hive engine does this automatically; for automl it must be explicitly enabled.

---

## Key Metrics and What They Mean

### Coverage Rate

`users_with_recs / distinct_users_transactions_table`

The share of source-data users who received at least one recommendation. Healthy coverage is **≥ 80%**. Below 80%, investigate:
- Is the `popular` algorithm available as a fallback?
- Are exclusion filters removing too many items, leaving users without scorable products?
- Is the `orders_lookback` so short that most users' history was excluded?

### Recommendation Concentration

The share of users receiving the same top-1 recommendation. High concentration (>30% of users getting the same `nbp_1`) suggests the model has low differentiation — it's behaving more like a popularity ranker than a personalized recommender. This is expected for `popular` algorithm but is a signal worth flagging for `als` or `hive`.

### Item Coverage Breadth

`distinct_items_recommended / total_items_in_catalog`

How much of the product catalog appears in the recommendation output. Low breadth means the long tail is being ignored — either by `min_cooccurence_filter` removing rare items or because training data is sparse across categories.

### Test Set Metrics (when `run_model_test_set: yes`)

| Metric | What it measures | Healthy threshold |
|--------|-----------------|-------------------|
| Product match rate vs. `random_item_rate` | Exact product recommendation quality | > 2× random |
| Category match rate vs. `random_category_rate` | Category-level preference capture | > 3× random |

Good category match with poor product match is expected for diverse catalogs — the model captures what kind of thing the user wants, even if the exact item is hard to predict.

---

## How Run Config Drives What You See

The `dash_model_param_stats_agg.model_params` column captures the engine and algorithm used per run. The most consequential config knobs for interpreting dashboard data:

| Config knob | What changes if you tune it |
|-------------|----------------------------|
| `model_type` + `automl_model_type` | Entire recommendation strategy changes |
| `orders_lookback` | Shorter window → fresher signal but fewer users qualify; longer → more stable but potentially stale |
| `min_cooccurence_filter` (hive) | Higher threshold → fewer items in training → lower catalog breadth |
| `dimsum_similarity_threshold` (hive) | Higher → more precise pairs but fewer recommendations generated |
| `als_sample_rate` / `als_max_users` (automl ALS) | Sampling reduces training data for large datasets — may lower precision |
| `filter_viewed` (automl) | Toggling changes which users receive recs and what rank-1 looks like |
| Exclusion filters | Wide exclusions reduce catalog diversity and may drop high-volume items |

**Practical rule:** When a coverage or distribution metric changes run-over-run, ALWAYS pull `model_params` and `exclusion_filters` from both runs before attributing the change to real user behavior or catalog changes.

---

## What This Workflow Does NOT Do

Be explicit when the user asks something the dashboard tables can't answer:

- **No revenue forecasting** — the dashboard tracks recommendation coverage and item distributions, not predicted uplift from acting on recommendations. Never project ROI.
- **No per-user recommendation lookup** — the dashboard tables are aggregated. To see what a specific user was recommended, query `{user_master_attr_table}` directly, not the dash tables.
- **No real-time scoring** — recommendations come from the most recent batch run. `nbp_user_master` is only as fresh as the last `nbp_launch.dig` execution.
- **No affinity scores** — NBP outputs ranked items, not engagement probability scores. For engagement channel/time scoring, route to NBA.
- **No channel attribution** — NBP tells you what to recommend, not which channel drove the behavior. For attribution, route to MTA.
- **No similarity for automl** — `dash_similarity_stats_agg` is only populated by the `hive` engine. Automl does not expose item-item similarity in the dashboard.

If a question requires any of the above, say what the table can show vs. what's actually being asked, and recommend the alternative skill or analysis path.
