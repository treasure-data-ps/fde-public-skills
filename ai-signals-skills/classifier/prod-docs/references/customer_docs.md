# Classification Model — Customer-Facing Documentation

Template for customer-facing overview documentation. Replace placeholders with actual customer values.

---

## Overview

The Classification Model predicts the likelihood of [TARGET EVENT] for each [ENTITY TYPE] using machine learning. Every [ENTITY TYPE] receives a probability score (0.0–1.0) along with explanations showing which factors drove the prediction.

### What the Model Predicts

| Field | Value |
|-------|-------|
| **Prediction target** | [TARGET EVENT DESCRIPTION] (e.g., "whether a lead will submit an application within 90 days") |
| **Score interpretation** | Higher score = more likely to [TARGET EVENT]. A score of 0.75 means a 75% predicted probability. |
| **Classification threshold** | Scores above [THRESHOLD] are classified as "likely positive" |
| **Model type** | [MODEL TYPE] (XGBoost / CatBoost / Logistic Regression) |

### How to Use the Scores

| Score Range | Label | Recommended Action |
|-------------|-------|--------------------|
| 0.80 – 1.00 | Very High | [Customer-specific action for very high scores] |
| 0.60 – 0.80 | High | [Customer-specific action for high scores] |
| 0.40 – 0.60 | Medium | [Customer-specific action for medium scores] |
| 0.20 – 0.40 | Low | [Customer-specific action for low scores] |
| 0.00 – 0.20 | Very Low | [Customer-specific action for very low scores] |

### Key Output Tables

| Table | What It Contains | Who Uses It |
|-------|-----------------|-------------|
| `{tp}predictions` | One row per [ENTITY TYPE] with score, predicted label, and score bucket | Marketing, Sales, Analytics |
| `{tp}prediction_shap` | Per-record explanations — which features drive each score up/down | Analytics, Data Science |
| `{tp}feature_importance` | Global feature importance ranking | Data Science, Stakeholders |
| `{tp}run_log` | Model performance metrics per training run | Data Science |
| `{tp}prediction_run_log` | Prediction audit — records scored, drift check | Data Science, Ops |

### Model Performance Summary

| Metric | Value | What It Means |
|--------|-------|---------------|
| **Precision** | [VALUE] | Of all records predicted positive, [VALUE × 100]% actually are positive |
| **Recall** | [VALUE] | Of all actual positive records, the model catches [VALUE × 100]% |
| **AUC-ROC** | [VALUE] | Overall ranking quality (1.0 = perfect, 0.5 = random) |
| **F-beta** | [VALUE] | Combined precision/recall score |

### Feature Importance (Top 10)

| Rank | Feature | Direction | Business Meaning |
|------|---------|-----------|-----------------|
| 1 | [feature_name] | [Increases/Decreases score] | [Plain-language explanation] |
| 2 | [feature_name] | [Increases/Decreases score] | [Plain-language explanation] |
| ... | ... | ... | ... |

### Understanding Per-Record Explanations

Each scored record has a SHAP explanation showing the top features pushing the score up and down:

**Example:**
> **Lead: John Smith (Score: 0.82 — High)**
> - Visited pricing page 12 times (+0.15) — strong purchase intent signal
> - Downloaded product whitepaper (+0.08) — engaged with content
> - Enterprise company size (+0.06) — larger companies convert more often
> - No email opens in 30 days (-0.04) — recent email disengagement
> - Short average session duration (-0.03) — less time spent on site

### Refresh Schedule

| Component | Frequency | What Happens |
|-----------|-----------|--------------|
| Prediction scoring | [FREQUENCY] | New scores generated for all [ENTITY TYPES] |
| Model retraining | [FREQUENCY] | Model re-learns from latest data |
| Feature refresh | [FREQUENCY] | Feature tables rebuilt from source data |

### Data Sources

| Source | What It Provides | Refresh Cadence |
|--------|-----------------|-----------------|
| [Source 1] | [Description] | [Cadence] |
| [Source 2] | [Description] | [Cadence] |

### Support & Questions

For questions about the model, scores, or output tables, contact:
- **Solution owner**: [contact]
- **Model documentation**: the `docs/` folder shared with this document (architecture, runbook, eval results)
- **Run history and performance tracking**: See `{tp}run_log` table
