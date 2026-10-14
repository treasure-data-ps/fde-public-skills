# ─────────────────────────────────────────────────────────────────────────────
# explainer.py
#
# Model-agnostic evaluation + explainability layer.
#
# Responsibilities:
#   - Precision-optimal threshold selection via PR curve
#   - Full evaluation metrics (baseline @ 0.5 + tuned threshold)
#   - SHAP values via the appropriate explainer per model family
#   - Result DataFrames for TD (ROC curve, prediction bins, SHAP)
#
# All functions accept plain numpy / pandas inputs and either:
#   (a) probabilities (for metric / threshold functions), or
#   (b) a fitted model + background data (for SHAP).
#
# No model-specific hyperparameters live here.
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import datetime
import logging
import numpy as np
import pandas as pd

from sklearn.metrics import (
    confusion_matrix, accuracy_score, precision_score,
    recall_score, f1_score, roc_curve, roc_auc_score,
    precision_recall_curve, average_precision_score, fbeta_score,
)

try:
    import shap
except ImportError:
    os.system(f"{sys.executable} -m pip install --user shap")
    import shap

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# THRESHOLD SELECTION
# ─────────────────────────────────────────────────────────────────────────────
def find_precision_optimal_threshold(y_true, y_proba, min_recall=0.10):
    """
    Pick the threshold that maximises precision subject to a minimum
    recall floor.  Identical semantics to the original LR pipeline so
    behaviour is preserved for existing runs.
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)

    best_threshold = 0.5
    best_precision = 0.0

    for p, r, t in zip(precisions, recalls, thresholds):
        if r >= min_recall and p > best_precision:
            best_precision = p
            best_threshold = t

    logger.info(
        f"Precision-optimal threshold: {best_threshold:.4f} → "
        f"precision={best_precision:.4f} (min_recall floor={min_recall})"
    )
    return float(best_threshold)


def find_f1_optimal_threshold(y_true, y_proba):
    """Pick the threshold that maximises the F1 score."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-15)
    best_idx = np.argmax(f1_scores[:-1])
    best_threshold = float(thresholds[best_idx])
    logger.info(
        f"F1-optimal threshold: {best_threshold:.4f} → "
        f"F1={f1_scores[best_idx]:.4f}"
    )
    return best_threshold


def find_recall_optimal_threshold(y_true, y_proba, min_precision=0.10):
    """Pick the threshold that maximises recall subject to a minimum precision floor."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    best_threshold = 0.5
    best_recall = 0.0
    for p, r, t in zip(precisions, recalls, thresholds):
        if p >= min_precision and r > best_recall:
            best_recall = r
            best_threshold = t
    logger.info(
        f"Recall-optimal threshold: {best_threshold:.4f} → "
        f"recall={best_recall:.4f} (min_precision floor={min_precision})"
    )
    return float(best_threshold)


def find_youden_j_threshold(y_true, y_proba):
    """Pick the threshold that maximises Youden's J statistic (TPR - FPR)."""
    fpr_arr, tpr_arr, thresholds = roc_curve(y_true, y_proba)
    j_scores = tpr_arr - fpr_arr
    best_idx = np.argmax(j_scores)
    best_threshold = float(thresholds[best_idx])
    logger.info(
        f"Youden-J threshold: {best_threshold:.4f} → "
        f"J={j_scores[best_idx]:.4f} (TPR={tpr_arr[best_idx]:.4f}, FPR={fpr_arr[best_idx]:.4f})"
    )
    return best_threshold


def find_threshold(y_true, y_proba, strategy='precision_optimal',
                   min_metric_floor=0.10, fbeta_beta=0.5, fixed_threshold=0.5):
    """
    Dispatcher: select a classification threshold using the named strategy.

    min_metric_floor is a safety net whose meaning is determined by fbeta_beta:
      - beta < 1 (precision-biased) → floor applies to recall (min_recall)
      - beta >= 1 (recall-biased)   → floor applies to precision (min_precision)

    For strategies that don't use a floor (f1_optimal, youden_j, fixed),
    the parameter is ignored.
    Falls back to precision_optimal for unknown strategy values.
    """
    is_precision_biased = fbeta_beta < 1.0
    floor_target = 'recall' if is_precision_biased else 'precision'
    logger.info(f"Threshold strategy: {strategy} | fbeta_beta={fbeta_beta} | "
                f"min_metric_floor={min_metric_floor} (applied as min_{floor_target})")

    if strategy == 'precision_optimal':
        return find_precision_optimal_threshold(y_true, y_proba, min_recall=min_metric_floor)
    elif strategy == 'f1_optimal':
        return find_f1_optimal_threshold(y_true, y_proba)
    elif strategy == 'recall_optimal':
        return find_recall_optimal_threshold(y_true, y_proba, min_precision=min_metric_floor)
    elif strategy == 'youden_j':
        return find_youden_j_threshold(y_true, y_proba)
    elif strategy == 'fixed':
        logger.info(f"Using fixed threshold: {fixed_threshold:.4f}")
        return float(fixed_threshold)
    else:
        logger.warning(f"Unknown threshold_strategy '{strategy}', falling back to precision_optimal")
        return find_precision_optimal_threshold(y_true, y_proba, min_recall=min_metric_floor)


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
def evaluate(y_true, y_proba, best_threshold, fbeta_beta=0.5):
    """
    Full evaluation at both the baseline (0.5) and tuned thresholds.
    Returns a dict that matches the schema previously produced by
    LeadScoringModel._evaluate_model so run_log columns stay identical.
    """
    logger.info("=" * 60)
    logger.info("MODEL EVALUATION")
    logger.info(f"Threshold: {best_threshold:.4f} (precision-optimal)")
    logger.info("=" * 60)

    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba)

    # ── Baseline @ 0.5 ──
    y_pred_baseline    = (y_proba >= 0.5).astype(int)
    baseline_precision = precision_score(y_true, y_pred_baseline, zero_division=0)
    baseline_recall    = recall_score(y_true,    y_pred_baseline, zero_division=0)
    baseline_f1        = f1_score(y_true,        y_pred_baseline, zero_division=0)
    baseline_fbeta     = fbeta_score(y_true,     y_pred_baseline, beta=fbeta_beta, zero_division=0)
    cm_baseline        = confusion_matrix(y_true, y_pred_baseline)
    tn_b, fp_b, fn_b, tp_b = cm_baseline.ravel() if cm_baseline.size == 4 else (0, 0, 0, 0)

    logger.info("── Baseline @ threshold=0.50 ──────────────────────────")
    logger.info(f"  Precision : {baseline_precision:.4f}")
    logger.info(f"  Recall    : {baseline_recall:.4f}")
    logger.info(f"  F1        : {baseline_f1:.4f}")
    logger.info(f"  F_beta({fbeta_beta}) : {baseline_fbeta:.4f}")
    logger.info(f"  TN={tn_b}, FP={fp_b}, FN={fn_b}, TP={tp_b}")

    # ── Tuned threshold ──
    y_pred = (y_proba >= best_threshold).astype(int)

    epsilon  = 1e-15
    ll_model = round(np.sum(
        y_true * np.log(y_proba + epsilon) +
        (1 - y_true) * np.log(1 - y_proba + epsilon)
    ), 2)
    p_null   = np.mean(y_true)
    ll_null  = round(np.sum(
        y_true * np.log(p_null + epsilon) +
        (1 - y_true) * np.log(1 - p_null + epsilon)
    ), 2)
    chi_square   = round(-2 * (ll_null - ll_model), 2)
    mcfadden_r2  = 1 - (ll_model / ll_null) if ll_null != 0 else 0
    n            = len(y_true)
    cox_snell_r2 = 1 - np.exp((2 / n) * (ll_null - ll_model)) if n > 0 else 0

    logger.info(f"McFadden R²: {mcfadden_r2:.4f} | Cox & Snell R²: {cox_snell_r2:.4f}")

    cm = confusion_matrix(y_true, y_pred)
    logger.info(f"Confusion Matrix:\n{cm}")
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    test_accuracy = accuracy_score(y_true, y_pred)
    precision     = precision_score(y_true, y_pred, zero_division=0)
    recall        = recall_score(y_true,    y_pred, zero_division=0)
    f1            = f1_score(y_true,        y_pred, zero_division=0)
    fbeta         = fbeta_score(y_true,     y_pred, beta=fbeta_beta, zero_division=0)

    auc_roc, fpr_arr, tpr_arr, roc_thresholds = None, None, None, None
    try:
        auc_roc                         = roc_auc_score(y_true, y_proba)
        fpr_arr, tpr_arr, roc_thresholds = roc_curve(y_true, y_proba)
        logger.info(f"AUC-ROC: {auc_roc:.4f}")
    except Exception as e:
        logger.warning(f"AUC-ROC failed: {str(e)}")

    aucpr = None
    try:
        aucpr = average_precision_score(y_true, y_proba)
        logger.info(f"AUC-PR (avg precision): {aucpr:.4f}")
    except Exception as e:
        logger.warning(f"AUC-PR failed: {str(e)}")

    # PR curve logging
    pr_precisions, pr_recalls, pr_thresholds = precision_recall_curve(y_true, y_proba)
    pr_df = pd.DataFrame({
        'threshold': np.append(pr_thresholds, 1.0),
        'precision': pr_precisions,
        'recall':    pr_recalls,
    })
    for target_recall in [0.10, 0.20, 0.30, 0.50]:
        subset = pr_df[pr_df['recall'] >= target_recall]
        if not subset.empty:
            best_row = subset.loc[subset['precision'].idxmax()]
            logger.info(
                f"  PR @ recall≥{target_recall:.0%}: "
                f"precision={best_row['precision']:.4f}, "
                f"threshold={best_row['threshold']:.4f}"
            )

    # Probability bins
    bins       = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    bin_labels = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5',
                  '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
    pred_binned = pd.cut(y_proba, bins=bins, labels=bin_labels, include_lowest=True)
    bin_counts  = pred_binned.value_counts().sort_index()

    logger.info("Prediction Probability Distribution:")
    for bl, cnt in bin_counts.items():
        logger.info(f"  {bl}: {cnt} ({cnt / len(y_proba) * 100:.1f}%)")

    # Delta summary
    logger.info("=" * 60)
    logger.info(
        f"{'METRIC':<20} {'@ 0.50 (baseline)':>20} "
        f"{'@ ' + f'{best_threshold:.4f}' + ' (optimal)':>22}  DELTA"
    )
    logger.info("-" * 70)
    logger.info(f"{'Precision':<20} {baseline_precision:>20.4f} {precision:>22.4f}  {precision - baseline_precision:+.4f}  ← primary")
    logger.info(f"{'Recall':<20} {baseline_recall:>20.4f} {recall:>22.4f}  {recall - baseline_recall:+.4f}")
    logger.info(f"{'F1':<20} {baseline_f1:>20.4f} {f1:>22.4f}  {f1 - baseline_f1:+.4f}")
    logger.info(f"{'F_beta(' + str(fbeta_beta) + ')':<20} {baseline_fbeta:>20.4f} {fbeta:>22.4f}  {fbeta - baseline_fbeta:+.4f}")
    logger.info(f"{'FP (false alarms)':<20} {fp_b:>20d} {fp:>22d}  {fp - fp_b:+d}")
    logger.info(f"{'TP (correct hits)':<20} {tp_b:>20d} {tp:>22d}  {tp - tp_b:+d}")
    logger.info("-" * 70)
    logger.info(f"Accuracy : {test_accuracy:.4f}")
    logger.info(f"AUC-ROC  : {auc_roc:.4f}" if auc_roc else "AUC-ROC: N/A")
    logger.info(f"AUC-PR   : {aucpr:.4f}"   if aucpr   else "AUC-PR: N/A")
    logger.info("=" * 60)

    return {
        'test_accuracy':         round(test_accuracy, 2),
        'precision':             round(precision, 2),
        'recall':                round(recall, 2),
        'f1':                    round(f1 * 100, 2),
        'fbeta':                 round(fbeta, 4),
        'fbeta_beta':            fbeta_beta,
        'auc_roc':               round(auc_roc * 100, 2) if auc_roc else None,
        'aucpr':                 round(aucpr  * 100, 2) if aucpr   else None,
        'best_threshold':        round(best_threshold, 4),
        'confusion_matrix':      cm.tolist(),
        'true_negatives':        int(tn),
        'true_negatives_pct':    round((tn / len(y_true)) * 100, 2),
        'false_positives':       int(fp),
        'false_positives_pct':   round((fp / len(y_true)) * 100, 2),
        'false_negatives':       int(fn),
        'false_negatives_pct':   round((fn / len(y_true)) * 100, 2),
        'true_positives':        int(tp),
        'true_positives_pct':    round((tp / len(y_true)) * 100, 2),
        'test_samples':          len(y_true),
        'test_pred_proba':       [round(p, 2) for p in y_proba.tolist()],
        'bin_counts':            bin_counts.to_dict(),
        'fpr':                   [round(x, 2) for x in (fpr_arr * 100).tolist()] if fpr_arr is not None else None,
        'tpr':                   [round(x, 2) for x in (tpr_arr * 100).tolist()] if tpr_arr is not None else None,
        'thresholds':            [round(x, 2) for x in roc_thresholds.tolist()]  if roc_thresholds is not None else None,
        'log_likelihood_model':  round(ll_model, 2),
        'log_likelihood_null':   round(ll_null, 2),
        'chi_square':            round(chi_square, 2),
        'mcfadden_r2':           round(mcfadden_r2, 4),
        'cox_snell_r2':          round(cox_snell_r2, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SHAP — explainer factory dispatches on model family
# ─────────────────────────────────────────────────────────────────────────────
def compute_shap(model, X, model_family, feature_names, max_samples=1000):
    """
    Calculate SHAP values for any supported model family.

    model_family ∈ {'logistic', 'xgboost', 'catboost'}
      logistic → shap.LinearExplainer  (needs scaled X)
      xgboost  → shap.TreeExplainer
      catboost → shap.TreeExplainer

    Returns:
      importance_df : DataFrame with feature_name, mean_abs_shap_value, rank
      shap_values   : np.ndarray (n_samples, n_features) — positive-class
                      SHAP contributions.  Used by downstream artifacts
                      (directional, dependence, per-row, interactions).
      X_sample      : DataFrame — the exact rows used for SHAP, aligned to
                      shap_values row-for-row.  Caller should join on this
                      (not the original X) when emitting row-level tables.
      explainer_obj : the fitted shap.Explainer (kept for interaction values)

    Failure path returns (empty DF, None, None, None) so callers can skip
    downstream SHAP artifacts gracefully.
    """
    logger.info(f"Calculating SHAP values (family={model_family})")
    try:
        X_sample = X.head(max_samples).copy() if len(X) > max_samples else X.copy()

        if model_family == 'logistic':
            explainer_obj = shap.LinearExplainer(model, X_sample)
            shap_values   = explainer_obj.shap_values(X_sample)
        elif model_family in ('xgboost', 'catboost'):
            explainer_obj = shap.TreeExplainer(model)
            shap_values   = explainer_obj.shap_values(X_sample)
            # Tree explainers sometimes return [class0, class1] for binary tasks
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            raise ValueError(f"Unsupported model_family: {model_family}")

        shap_values = np.asarray(shap_values)

        shap_importance = np.abs(shap_values).mean(axis=0)
        importance_df = pd.DataFrame({
            'feature_name':        feature_names,
            'mean_abs_shap_value': shap_importance,
            'rank':                range(1, len(shap_importance) + 1),
        }).sort_values('mean_abs_shap_value', ascending=False).reset_index(drop=True)
        importance_df['rank'] = importance_df.index + 1
        logger.info(f"SHAP top 10:\n{importance_df.head(10)}")
        return importance_df, shap_values, X_sample, explainer_obj

    except Exception as e:
        logger.warning(f"SHAP failed: {str(e)}")
        return (pd.DataFrame(columns=['feature_name', 'mean_abs_shap_value', 'rank']),
                None, None, None)


# ─────────────────────────────────────────────────────────────────────────────
# DIRECTIONAL SHAP — "does this feature push scores up or down?"
# ─────────────────────────────────────────────────────────────────────────────
def build_shap_directional_df(shap_values, X_sample, feature_names, session_id,
                              model_family='xgboost'):
    """
    Executive-summary table: one row per feature answering
    "does this feature push predictions up or down, and by how much?"

    Columns:
      feature_name           — the feature
      mean_shap              — signed avg SHAP across the sample.
                               CAVEAT: can be misleading — SHAP values are
                               contributions relative to the sample's
                               expected prediction, so mean(SHAP) depends on
                               the baseline, not only the true effect
                               direction.  Use pearson_value_vs_shap as the
                               primary directional signal.
      mean_abs_shap          — magnitude (same as the importance table)
      median_shap            — robust centre of SHAP distribution
      shap_std               — spread of the SHAP effect
      pct_pushing_up         — % of rows where this feature raised the score
      pct_pushing_down       — % of rows where it lowered the score
      direction_confidence   — max(pct_up, pct_down) / 100; how consistently
                               the feature points in its dominant direction.
                               1.0 = always same direction; 0.5 = coin flip
      pearson_value_vs_shap  — corr(feature_value, SHAP).  This is the
                               correct directional signal.
                                 > 0  : monotonic up (higher value → higher score)
                                 < 0  : monotonic down (higher value → lower score)
                                 ≈ 0  : non-monotonic (tree models) OR constant
                               For linear models the magnitude is ±1.0 by
                               construction — only the SIGN carries info.
                               For tree models the magnitude also indicates
                               how monotonic the effect is.
      direction              — human label
      rank                   — by mean_abs_shap

    model_family ∈ {'logistic', 'xgboost', 'catboost'}
    """
    if shap_values is None or X_sample is None or len(shap_values) == 0:
        logger.info("  [skip] shap_directional — no SHAP values available")
        return pd.DataFrame()

    logger.info(f"Building SHAP directional table (family={model_family})")

    X_arr = X_sample[feature_names].to_numpy(dtype=float)

    mean_shap     = shap_values.mean(axis=0)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    median_shap   = np.median(shap_values, axis=0)
    std_shap      = shap_values.std(axis=0)
    pct_up        = (shap_values > 0).mean(axis=0) * 100
    pct_down      = (shap_values < 0).mean(axis=0) * 100
    direction_confidence = np.maximum(pct_up, pct_down) / 100.0

    # Pearson corr between feature value and SHAP — the correct directional
    # signal for ALL model families.  For linear models the magnitude is ±1
    # by construction (only sign informs); for tree models the magnitude
    # also tells us how monotonic the effect is.
    pearson = np.zeros(len(feature_names))
    for i in range(len(feature_names)):
        fv = X_arr[:, i]
        sv = shap_values[:, i]
        if np.std(fv) == 0 or np.std(sv) == 0:
            pearson[i] = 0.0
        else:
            pearson[i] = np.corrcoef(fv, sv)[0, 1]
    pearson = np.nan_to_num(pearson, nan=0.0)

    # Thresholds for direction label depend on whether the magnitude of
    # Pearson is informative.  For linear models it's always ~1.0 so we
    # only care about the sign.  For trees we want a moderate threshold
    # (|corr| > 0.3) to distinguish strongly-monotonic from mixed.
    is_linear = (model_family == 'logistic')
    monotonic_threshold = 0.05 if is_linear else 0.3

    def _label(mean_abs, corr, conf):
        if mean_abs < 1e-6:
            return 'neutral'
        if corr >  monotonic_threshold:
            return 'increases score'
        if corr < -monotonic_threshold:
            return 'decreases score'
        # Weak Pearson + low confidence → truly non-monotonic / noisy
        if conf < 0.7:
            return 'mixed / non-monotonic'
        # Weak Pearson but consistent sign → rare but possible on trees
        # with rare feature values; mark clearly
        return 'weakly directional'

    directions = [
        _label(mean_abs_shap[i], pearson[i], direction_confidence[i])
        for i in range(len(feature_names))
    ]

    df = pd.DataFrame({
        'feature_name':          feature_names,
        'mean_shap':             mean_shap,
        'mean_abs_shap':         mean_abs_shap,
        'median_shap':           median_shap,
        'shap_std':              std_shap,
        'pct_pushing_up':        pct_up,
        'pct_pushing_down':      pct_down,
        'direction_confidence':  direction_confidence,
        'pearson_value_vs_shap': pearson,
        'direction':             directions,
    })
    df = df.sort_values('mean_abs_shap', ascending=False).reset_index(drop=True)
    df['rank']       = df.index + 1
    df['session_id'] = session_id
    df['created_at'] = datetime.datetime.now()

    log_cols = ['feature_name', 'pearson_value_vs_shap',
                'direction_confidence', 'direction']
    logger.info(f"SHAP directional top 10:\n{df.head(10)[log_cols].to_string()}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# DEPENDENCE — feature value → mean SHAP at each decile of the feature
# ─────────────────────────────────────────────────────────────────────────────
def build_shap_dependence_df(shap_values, X_sample, feature_names, session_id,
                             n_bins=10, top_k=None):
    """
    For each feature, bucket its observed values into `n_bins` deciles and
    report the mean SHAP within each bucket.  Lets you draw the partial-
    dependence shape ("is the effect U-shaped? thresholded? linear?") in
    a dashboard without streaming raw SHAP values.

    Columns:
      feature_name, bin_index, bin_min, bin_max, bin_center,
      n_samples, mean_shap, median_shap, mean_feature_value,
      session_id, created_at

    top_k: if set, only emit bins for the top-K features by |mean SHAP|.
           Use to keep table size bounded on wide models.
    """
    if shap_values is None or X_sample is None:
        logger.info("  [skip] shap_dependence — no SHAP values available")
        return pd.DataFrame()

    logger.info(f"Building SHAP dependence table (n_bins={n_bins}, top_k={top_k})")

    importances = np.abs(shap_values).mean(axis=0)
    feature_order = np.argsort(-importances)  # descending by |SHAP|
    if top_k is not None:
        feature_order = feature_order[:top_k]

    rows = []
    for f_idx in feature_order:
        feat  = feature_names[f_idx]
        fv    = X_sample[feat].to_numpy(dtype=float)
        sv    = shap_values[:, f_idx]

        # Binary/ohe features have only 2 unique values → use them as bins.
        unique_vals = np.unique(fv)
        if len(unique_vals) <= n_bins:
            edges = np.concatenate([unique_vals, [unique_vals[-1] + 1e-9]])
            bin_ids = np.searchsorted(unique_vals, fv, side='right') - 1
            bin_ids = np.clip(bin_ids, 0, len(unique_vals) - 1)
            actual_bins = len(unique_vals)
        else:
            # qcut handles skew better than cut; duplicates='drop' avoids
            # edge collisions on heavy-tailed features.
            try:
                bin_ids = pd.qcut(fv, q=n_bins, labels=False, duplicates='drop')
                bin_ids = np.asarray(bin_ids)
                actual_bins = int(np.nanmax(bin_ids)) + 1 if not np.all(np.isnan(bin_ids)) else 1
                # Reconstruct edges for reporting
                edges = np.quantile(fv, np.linspace(0, 1, actual_bins + 1))
            except Exception:
                # Fallback to equal-width bins
                edges   = np.linspace(fv.min(), fv.max(), n_bins + 1)
                bin_ids = np.clip(np.digitize(fv, edges) - 1, 0, n_bins - 1)
                actual_bins = n_bins

        for b in range(actual_bins):
            mask = (bin_ids == b)
            if mask.sum() == 0:
                continue
            rows.append({
                'feature_name':       feat,
                'bin_index':          int(b),
                'bin_min':            float(edges[b])   if b   < len(edges) else float('nan'),
                'bin_max':            float(edges[b+1]) if b+1 < len(edges) else float('nan'),
                'bin_center':         float((edges[b] + edges[b+1]) / 2) if b+1 < len(edges) else float(edges[b]),
                'n_samples':          int(mask.sum()),
                'mean_shap':          float(sv[mask].mean()),
                'median_shap':        float(np.median(sv[mask])),
                'mean_feature_value': float(fv[mask].mean()),
            })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df['session_id'] = session_id
    df['created_at'] = datetime.datetime.now()
    logger.info(f"SHAP dependence rows: {len(df)} ({df['feature_name'].nunique()} features)")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PER-ROW SHAP — long-format "why did row X score Y?"
# ─────────────────────────────────────────────────────────────────────────────
def build_shap_per_row_df(shap_values, X_sample, y_proba_sample, feature_names,
                          session_id, row_ids=None, top_k_per_row=None):
    """
    Emit one row per (sample, feature) pair so Sales can answer
    "why did lead 12345 score 0.87?".

    Columns:
      session_id, row_id, predicted_proba, feature_name,
      feature_value, shap_value, abs_shap, contribution_rank,
      created_at

    row_ids: optional array-like of length n_samples.  If None, uses the
             positional index of X_sample (0..n-1).  IMPORTANT: pass the
             actual lead / ucp_id so the table is joinable downstream.

    top_k_per_row: if set, keep only the top-K contributing features per
                   row (by |SHAP|).  Cuts table size roughly n_features/K×.
                   Default None = full fidelity.
    """
    if shap_values is None or X_sample is None:
        logger.info("  [skip] shap_per_row — no SHAP values available")
        return pd.DataFrame()

    n_rows, n_feats = shap_values.shape
    logger.info(
        f"Building per-row SHAP table: {n_rows} rows × {n_feats} features "
        f"= {n_rows * n_feats} entries (top_k_per_row={top_k_per_row})"
    )

    if row_ids is None:
        row_ids = np.arange(n_rows)
    else:
        row_ids = np.asarray(row_ids)
        if len(row_ids) != n_rows:
            raise ValueError(
                f"row_ids length ({len(row_ids)}) != shap_values rows ({n_rows}). "
                "Pass the id column sliced to the same rows used for SHAP."
            )

    # Build wide matrices then melt to long — significantly faster than
    # looping in Python on 1000 × 80.
    shap_df = pd.DataFrame(shap_values, columns=feature_names)
    shap_df.insert(0, 'row_id', row_ids)
    shap_df.insert(1, 'predicted_proba',
                   y_proba_sample if y_proba_sample is not None else np.nan)

    val_df = X_sample[feature_names].reset_index(drop=True).copy()
    val_df.columns = [f"__VAL__{c}" for c in feature_names]

    wide = pd.concat([shap_df.reset_index(drop=True), val_df], axis=1)

    # Long format
    shap_long = wide.melt(
        id_vars=['row_id', 'predicted_proba'],
        value_vars=feature_names,
        var_name='feature_name',
        value_name='shap_value',
    )
    val_long = wide.melt(
        id_vars=['row_id'],
        value_vars=[f"__VAL__{c}" for c in feature_names],
        var_name='feature_name',
        value_name='feature_value',
    )
    val_long['feature_name'] = val_long['feature_name'].str.replace(
        '__VAL__', '', regex=False
    )

    long_df = shap_long.merge(val_long, on=['row_id', 'feature_name'])
    long_df['abs_shap'] = long_df['shap_value'].abs()

    # Rank within each row
    long_df['contribution_rank'] = (
        long_df.groupby('row_id')['abs_shap']
               .rank(ascending=False, method='first').astype(int)
    )

    if top_k_per_row is not None:
        before = len(long_df)
        long_df = long_df[long_df['contribution_rank'] <= int(top_k_per_row)]
        logger.info(f"  Trimmed to top_k_per_row={top_k_per_row}: "
                    f"{before} → {len(long_df)} rows")

    long_df = long_df.sort_values(['row_id', 'contribution_rank']).reset_index(drop=True)
    long_df['session_id'] = session_id
    long_df['created_at'] = datetime.datetime.now()

    # Reorder columns for readability
    long_df = long_df[[
        'session_id', 'row_id', 'predicted_proba',
        'feature_name', 'feature_value',
        'shap_value', 'abs_shap', 'contribution_rank',
        'created_at',
    ]]
    logger.info(f"Per-row SHAP table shape: {long_df.shape}")
    return long_df


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTION SHAP — top feature pairs (XGBoost only; expensive)
# ─────────────────────────────────────────────────────────────────────────────
def build_shap_interactions_df(explainer_obj, X_sample, feature_names,
                               session_id, model_family,
                               max_interaction_samples=200, top_k_pairs=50):
    """
    Compute SHAP interaction values and emit the top-K most important
    feature pairs (by mean absolute interaction contribution).

    Currently supports XGBoost via shap.TreeExplainer.shap_interaction_values.
    CatBoost has its own get_feature_importance(type='Interaction') API
    with a very different shape; we handle that lazily if the family is
    catboost, but it's best-effort.  Logistic returns empty (no higher-
    order terms in a linear model).

    Columns:
      session_id, feature_a, feature_b,
      mean_abs_interaction, mean_signed_interaction,
      rank, created_at

    Performance note: shap_interaction_values is O(n_features² × n_samples)
    in memory and ~10× slower than shap_values.  We cap the sample size
    via max_interaction_samples (default 200) and only return the top-K
    pairs to keep this bounded.
    """
    if explainer_obj is None or X_sample is None:
        logger.info("  [skip] shap_interactions — no explainer available")
        return pd.DataFrame()

    if model_family == 'logistic':
        logger.info("  [skip] shap_interactions — linear model, no interactions")
        return pd.DataFrame()

    logger.info(
        f"Building SHAP interaction table "
        f"(max_samples={max_interaction_samples}, top_k={top_k_pairs})"
    )

    X_int = X_sample.head(max_interaction_samples).copy() \
            if len(X_sample) > max_interaction_samples else X_sample.copy()

    try:
        if model_family == 'xgboost':
            iv = explainer_obj.shap_interaction_values(X_int)
        elif model_family == 'catboost':
            # CatBoost has a direct API for pairwise interaction strength;
            # it returns a DataFrame with columns [Feature1, Feature2, Interaction].
            # If shap doesn't support it for this catboost version we skip.
            try:
                iv = explainer_obj.shap_interaction_values(X_int)
            except Exception as e:
                logger.warning(
                    f"shap.TreeExplainer.shap_interaction_values not supported "
                    f"for this CatBoost version: {e}. Skipping."
                )
                return pd.DataFrame()
        else:
            return pd.DataFrame()

        iv = np.asarray(iv)
        if isinstance(iv, list):
            iv = iv[1] if len(iv) > 1 else iv[0]
            iv = np.asarray(iv)

        if iv.ndim != 3:
            logger.warning(f"Unexpected interaction value shape: {iv.shape}")
            return pd.DataFrame()

        # Mean |SHAP interaction| across samples → (n_feats, n_feats) matrix
        mean_abs   = np.abs(iv).mean(axis=0)
        mean_signed = iv.mean(axis=0)
        n = len(feature_names)

        # Extract upper triangle (i < j) + diagonal separately.
        # Off-diagonal entries are double-counted (i,j) + (j,i), so we
        # sum them for total pairwise interaction.
        rows = []
        for i in range(n):
            for j in range(i + 1, n):
                rows.append({
                    'feature_a':              feature_names[i],
                    'feature_b':              feature_names[j],
                    'mean_abs_interaction':   float(mean_abs[i, j] + mean_abs[j, i]),
                    'mean_signed_interaction': float(mean_signed[i, j] + mean_signed[j, i]),
                })

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df = df.sort_values('mean_abs_interaction', ascending=False).reset_index(drop=True)
        df = df.head(top_k_pairs).reset_index(drop=True)
        df['rank']       = df.index + 1
        df['session_id'] = session_id
        df['created_at'] = datetime.datetime.now()

        logger.info(f"Top 10 interactions:\n{df.head(10)[['feature_a','feature_b','mean_abs_interaction']].to_string()}")
        return df

    except Exception as e:
        logger.warning(f"Interaction SHAP failed: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# TEST PREDICTIONS — row-level results for the held-out test set
# ─────────────────────────────────────────────────────────────────────────────
def build_test_predictions_df(y_true, y_proba, threshold, session_id,
                              user_ids=None):
    """
    Emit one row per held-out test sample with probability, predicted
    label at the precision-optimal threshold, true label, and the
    TP/TN/FP/FN outcome class.  Lets Sales answer "which of our scored
    leads did the model get right / wrong?" without rerunning inference.

    Columns:
      session_id        — ties back to the run log
      user_id           — caller-supplied (user_id_col); positional idx if None
      predicted_proba   — raw model probability (positive class)
      predicted_label   — 0/1 at the applied threshold
      actual_label      — the true target
      threshold_used    — the threshold applied (audit trail)
      is_correct        — predicted_label == actual_label
      outcome_class     — 'TP' / 'TN' / 'FP' / 'FN'
      score_bucket      — one of 10 decile labels matching prediction_bins
      created_at

    Parameters:
      y_true    : array-like of 0/1 labels
      y_proba   : array-like of positive-class probabilities
      threshold : the precision-optimal threshold to apply
      user_ids  : optional array-like of ids aligned to y_true/y_proba;
                  if None, positional indices are used
    """
    y_true  = np.asarray(y_true)
    y_proba = np.asarray(y_proba)

    if len(y_true) != len(y_proba):
        raise ValueError(
            f"Length mismatch: y_true={len(y_true)} vs y_proba={len(y_proba)}"
        )

    if user_ids is None:
        user_ids = np.arange(len(y_true))
    else:
        user_ids = np.asarray(user_ids)
        if len(user_ids) != len(y_true):
            raise ValueError(
                f"user_ids length ({len(user_ids)}) != y_true ({len(y_true)}). "
                "Ensure test_ids is sliced to the same rows used for evaluation."
            )

    y_pred = (y_proba >= threshold).astype(int)

    # Outcome class — vectorised TP/TN/FP/FN mapping
    outcome = np.empty(len(y_true), dtype=object)
    outcome[(y_true == 1) & (y_pred == 1)] = 'TP'
    outcome[(y_true == 0) & (y_pred == 0)] = 'TN'
    outcome[(y_true == 0) & (y_pred == 1)] = 'FP'
    outcome[(y_true == 1) & (y_pred == 0)] = 'FN'

    # Score buckets matching build_prediction_bins_df labels
    bins       = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    bin_labels = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5',
                  '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
    score_bucket = pd.cut(y_proba, bins=bins, labels=bin_labels,
                          include_lowest=True).astype(str)

    df = pd.DataFrame({
        'session_id':       session_id,
        'user_id':          user_ids,
        'predicted_proba':  np.round(y_proba, 6),
        'predicted_label':  y_pred.astype(int),
        'actual_label':     y_true.astype(int),
        'threshold_used':   round(float(threshold), 4),
        'is_correct':       (y_pred == y_true).astype(int),
        'outcome_class':    outcome.astype(str),
        'score_bucket':     score_bucket,
        'created_at':       datetime.datetime.now(),
    })

    # Log summary (echoes what's in run log, useful for sanity check at write time)
    logger.info(
        f"Test predictions: {len(df)} rows | "
        f"TP={ (df['outcome_class']=='TP').sum() } "
        f"TN={ (df['outcome_class']=='TN').sum() } "
        f"FP={ (df['outcome_class']=='FP').sum() } "
        f"FN={ (df['outcome_class']=='FN').sum() } "
        f"accuracy={df['is_correct'].mean():.4f}"
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# RESULT-DATAFRAME BUILDERS
# ─────────────────────────────────────────────────────────────────────────────
def build_run_log(metrics, session_id, data_info, feature_count,
                  best_params, cfg, model_type):
    """Build run log row.  Same schema as before, plus model_type."""
    return pd.DataFrame({
        'session_id':            [session_id],
        'description':           [cfg.get('description')], 
        'model_type':            [model_type],
        'train_start_date':      [data_info.get('start_date')],
        'train_end_date':        [data_info.get('end_date')],
        'test_start_date':       [data_info.get('test_start_date')],
        'test_end_date':         [data_info.get('test_end_date')],
        'test_accuracy':         [metrics['test_accuracy']],
        'precision':             [metrics['precision']],
        'recall':                [metrics['recall']],
        'f1_score':              [metrics['f1']],
        'fbeta':                 [metrics.get('fbeta')],
        'fbeta_beta':            [metrics.get('fbeta_beta', cfg.get('fbeta_beta'))],
        'auc_roc':               [metrics.get('auc_roc')],
        'aucpr':                 [metrics.get('aucpr')],
        'best_threshold':        [metrics.get('best_threshold', 0.5)],
        'true_negatives':        [metrics.get('true_negatives', 0)],
        'false_positives':       [metrics.get('false_positives', 0)],
        'false_negatives':       [metrics.get('false_negatives', 0)],
        'true_positives':        [metrics.get('true_positives', 0)],
        'confusion_matrix':      [str(metrics.get('confusion_matrix', []))],
        'test_samples':          [metrics['test_samples']],
        'total_features':        [feature_count],
        'train_shape':           [str(data_info.get('train_shape', 'Unknown'))],
        'test_shape':            [str(data_info.get('test_shape', 'Unknown'))],
        'train_target_dist':     [str(data_info.get('train_target_dist', {}))],
        'test_target_dist':      [str(data_info.get('test_target_dist', {}))],
        'best_params':           [str(best_params) if best_params else None],
        'corr_threshold':        [cfg.get('corr_threshold')],
        'min_metric_floor':      [cfg.get('min_metric_floor')],
        'max_iter':              [cfg.get('max_iter')],
        'optuna_metric':         [cfg.get('optuna_metric')],
        'threshold_strategy':    [cfg.get('threshold_strategy')],
        'fixed_threshold':       [cfg.get('fixed_threshold')],
        'cv_folds':              [cfg.get('cv_folds')],
        'early_stopping_rounds': [cfg.get('early_stopping_rounds')],
        'class_balance_strategy':[cfg.get('class_balance_strategy')],
        'xgb_eval_metric':       [cfg.get('xgb_eval_metric')],
        'log_likelihood_model':  [metrics.get('log_likelihood_model', 0)],
        'log_likelihood_null':   [metrics.get('log_likelihood_null', 0)],
        'chi_square':            [metrics.get('chi_square', 0)],
        'mcfadden_r2':           [metrics.get('mcfadden_r2', 0)],
        'cox_snell_r2':          [metrics.get('cox_snell_r2', 0)],
        'psi':                   [metrics.get('psi', None)],
        'evaluation_note':       [f"{cfg.get('threshold_strategy', 'precision_optimal')} threshold applied"],
    })


def build_roc_curve_df(metrics, session_id):
    fpr        = metrics.get('fpr')
    tpr        = metrics.get('tpr')
    thresholds = metrics.get('thresholds')
    if fpr is None or tpr is None or thresholds is None:
        return pd.DataFrame()
    n = len(fpr)
    return pd.DataFrame({
        'session_id':  [session_id] * n,
        'fpr':         fpr,
        'tpr':         tpr,
        'threshold':   thresholds,
        'created_at':  [datetime.datetime.now()] * n,
    })


def build_prediction_bins_df(metrics, session_id):
    bin_counts = metrics.get('bin_counts', {})
    if not bin_counts:
        return pd.DataFrame()
    total = sum(bin_counts.values())
    rows = []
    for bl, cnt in sorted(bin_counts.items()):
        rows.append({
            'session_id':  session_id,
            'bin_range':   bl,
            'count':       cnt,
            'percentage':  (cnt / total) * 100 if total > 0 else 0,
            'created_at':  datetime.datetime.now(),
        })
    return pd.DataFrame(rows)


def stamp_session(df, session_id):
    """Add session_id + created_at to an arbitrary result DataFrame."""
    if df is None or df.empty:
        return df
    df = df.copy()
    df['session_id'] = session_id
    df['created_at'] = datetime.datetime.now()
    return df