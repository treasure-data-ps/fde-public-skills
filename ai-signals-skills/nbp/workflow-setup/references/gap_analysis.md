# NBP Skill — Gap Analysis

Comparison of what the **`nbp_prod` repo** (Hive + automl) supports vs what the **ml-batch-api multi-algorithm approach** (from `ml-skills/solutions/nbp/`) supports. Only open items remain below.

## Features in ml-batch-api approach NOT in nbp_prod

- **Multi-algorithm parallel execution with priority merge**: Runs up to 3 algorithms (ALS, similar_to_latest, popular) in parallel and merges via `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY priority)`. `nbp_prod` runs one model type per execution. **Status: Future enhancement.** To add this to nbp_prod, the automl .dig would need to loop over multiple algorithms, write to separate tables, and merge with a priority SQL. This could be implemented as a new `nbp_model_train_automl_multi.dig`.
- **Atomic overwrite mode**: `output_mode: overwrite` uses tmp tables + atomic rename. `nbp_prod` overwrites via `create_table`. **Status: Low priority / deferred.** nbp_prod's `create_table:` is effectively atomic for `td>` steps. Only the automl `http>` call writes directly, but that table is intermediate and post-processed before final output.

## Features in nbp_prod NOT currently in the skill

- **Archive/historic scores**: Although not fully implemented in the current params, the structure supports `archive_results` and `store_historic_scores` patterns (from the RFM sibling). **Status: Future enhancement.** Can be added when run-over-run comparison is needed.
