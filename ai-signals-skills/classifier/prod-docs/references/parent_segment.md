# Classification Model — Parent Segment Configuration

## Overview

After the classification model is trained and scoring predictions, the prediction scores and labels can be added as attributes to the customer's Parent Segment in Audience Studio. This enables marketers to create audience segments based on model predictions (e.g., "High-propensity leads" or "At-risk churners").

## Attributes to Add

Add these columns from the `{tp}predictions` table to the Parent Segment:

| Attribute Column | Source Table | Data Type | Description |
|-----------------|-------------|-----------|-------------|
| `predicted_proba` | `{tp}predictions` | double | Prediction probability (0.0–1.0) — rename to something meaningful for the use case (e.g., `churn_score`, `lead_score`, `response_score`) when adding to the Parent Segment |
| `predicted_label` | `{tp}predictions` | integer | Binary prediction (0 or 1) based on threshold |
| `score_bucket` | `{tp}predictions` | string | Human-readable bucket label (e.g., "0.80-1.00") |

## Join Key

The `user_id` column in `{tp}predictions` must match the Parent Segment's unique user identifier. Confirm the join key with the customer before adding attributes.

## Example Audience Segments

Create these example segments in Audience Studio after adding the prediction attributes:

### For Lead Scoring Use Cases

| Segment Name | Rule | Description |
|-------------|------|-------------|
| High-Propensity Leads | `predicted_proba >= 0.80` | Top-tier leads most likely to convert |
| Medium-Propensity Leads | `predicted_proba >= 0.50 AND predicted_proba < 0.80` | Leads worth nurturing |
| Low-Propensity Leads | `predicted_proba < 0.50` | Deprioritize for direct outreach |
| Predicted Converters | `predicted_label = 1` | All leads above the model's optimal threshold |

### For Churn Prediction Use Cases

| Segment Name | Rule | Description |
|-------------|------|-------------|
| High Churn Risk | `predicted_proba >= 0.70` | Customers most likely to churn — urgent retention |
| Moderate Churn Risk | `predicted_proba >= 0.40 AND predicted_proba < 0.70` | Monitor and proactive engagement |
| Low Churn Risk | `predicted_proba < 0.40` | Stable customers — standard engagement |
| Predicted Churners | `predicted_label = 1` | All customers above the churn threshold |

### For Campaign Response Use Cases

| Segment Name | Rule | Description |
|-------------|------|-------------|
| Likely Responders | `predicted_proba >= 0.60` | Target for the next campaign |
| Unlikely Responders | `predicted_proba < 0.30` | Exclude from campaign to save costs |

## Refresh Cadence

The prediction table should be refreshed on a regular schedule (matching the prediction workflow cadence). After each prediction run, the Parent Segment attributes automatically reflect the latest scores — no manual update needed as long as the `{tp}predictions` table is the source.

## Notes

- Only add prediction attributes from the **latest prediction run** (filter by `MAX(pred_session_id)`) or ensure the prediction table is replace-mode (not append)
- If the customer has multiple classification models in the same database, use `table_prefix` to namespace the output tables and add distinct attribute names to the Parent Segment
- The `score_bucket` attribute provides a pre-categorized version of the score for marketers who prefer dropdown-based segment rules over numeric thresholds
