# ─────────────────────────────────────────────────────────────────────────────
# predict_main.py — Lead Scoring Prediction Pipeline
# Entry point: py>: python.predict_main.main
#
# Responsibilities:
#   1. Load the trained model — XGBoost / CatBoost from td-model-store,
#      Logistic from coefficient + scaler tables
#   2. Pull threshold + training prediction-bin distribution from
#      lead_scoring_run_log + lead_probability_train_bins
#   3. Load + preprocess + align prediction features identically to
#      training (same Preprocessor class)
#   4. Score; bucket; flag predicted positives
#   5. Compute per-row SHAP (top-N positive + top-N negative drivers)
#   6. Write four artifacts to TD in parallel:
#        - lead_scoring_predictions               (one row per lead)
#        - lead_scoring_prediction_shap           (top-N drivers per lead)
#        - lead_scoring_prediction_bins           (score histogram)
#        - lead_scoring_prediction_run_log        (audit row)
#
# Digdag _env contract — additions vs. the original predictor:
#   model_type            ★ logistic | xgboost | catboost
#   model_store_table     ★ td-model-store table for tree models
#   model_name            ★ model name tag inside td-model-store
#   td_endpoint           ★ TD region endpoint
#   user_id_col           ★ source-table column carrying lead identity
#   columns_to_drop       ★ comma-separated drop list (mirrors training)
#   shap_topn_per_direction ★ 5 = top 5 positive + top 5 negative per lead
#   shap_max_rows         ★ 0 = compute SHAP for every lead; >0 caps it
#   write_concurrency     ★ parallel writer thread count
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import logging
import datetime
import gc

sys.path.append('/home/td-user/python')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('classify_pipeline.log'),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Package install — runs before heavy imports
# ─────────────────────────────────────────────────────────────────────────────
def install_packages():
    logger.info("Uninstalling existing NumPy...")
    os.system(f"{sys.executable} -m pip uninstall -y numpy")

    logger.info("Installing NumPy 1.22.4 to user location...")
    os.system(f"{sys.executable} -m pip install --user --force-reinstall 'numpy==1.22.4'")

    packages = [
        'scipy==1.10.1',
        'scikit-learn==1.2.2',
        'pandas==1.5.3',
        'pytd==1.4.0',
        'numba==0.57.0',
        'shap==0.42.1',
        'xgboost==1.7.6',
        'catboost==1.2.2',
        'td-model-store==0.1.5',
    ]
    for package in packages:
        logger.info(f"Installing {package}...")
        os.system(f"{sys.executable} -m pip install --user {package}")


logger.info("Installing required packages...")
install_packages()


import numpy as np
import pandas as pd

from data_handler     import DataHandler
from preprocessor     import Preprocessor
from parallel_writer  import ParallelWriter
from predictor        import LeadScoringPredictor


# ─────────────────────────────────────────────────────────────────────────────
# Env parsing
# ─────────────────────────────────────────────────────────────────────────────
def validate_prediction_environment():
    required = [
        'apikey', 'database', 'prediction_table',
        'train_session_id', 'pred_session_id', 'trgt_table',
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise ValueError(f"Missing required env vars: {missing}")
    env = {v: os.environ.get(v) for v in required}

    # Optional passthroughs
    for v in ['unit', 'model_store_table', 'model_name', 'td_endpoint',
              'user_id_col', 'columns_to_drop']:
        env[v] = os.environ.get(v, '').strip()
    return env


def parse_pred_config():
    """
    Per-run knobs.  We deliberately re-parse here (rather than reuse
    train.parse_env_config) because prediction has a smaller surface and
    coupling the two pipelines on a single config helper would create
    a needless dependency.
    """
    raw_drop = os.environ.get('columns_to_drop', '').strip()
    columns_to_drop = [c.strip() for c in raw_drop.split(',') if c.strip()] or None

    return {
        'model_type':             os.environ.get('model_type', 'logistic').strip().lower(),
        'columns_to_drop':        columns_to_drop,
        'user_id_col':            os.environ.get('user_id_col', '').strip(),

        'shap_topn_per_direction': int(os.environ.get('shap_topn_per_direction', '5')),
        # 0 means "score every lead"; positive ints cap the SHAP sample size
        'shap_max_rows':          int(os.environ.get('shap_max_rows', '0')),
          
        'write_concurrency':      int(os.environ.get('write_concurrency', '6')),
        'table_prefix':           os.environ.get('table_prefix', ''),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def run_prediction():
    logger.info("=" * 80)
    logger.info("STARTING PREDICTION MODE")
    logger.info("=" * 80)
    start_time = datetime.datetime.now()

    try:
        env_vars = validate_prediction_environment()
        cfg      = parse_pred_config()

        # Defensive: append user_id_col to columns_to_drop so it can never
        # leak into the model as a feature.  Same protection as training.
        if cfg['user_id_col']:
            uid = cfg['user_id_col']
            drop_list = list(cfg['columns_to_drop'] or [])
            if uid not in drop_list:
                logger.warning(
                    f"user_id_col='{uid}' was not in columns_to_drop — "
                    "appending defensively"
                )
                drop_list.append(uid)
                cfg['columns_to_drop'] = drop_list

        logger.info(f"Model type:        {cfg['model_type']}")
        logger.info(f"Database:          {env_vars['database']}")
        logger.info(f"Prediction Table:  {env_vars['prediction_table']}")
        logger.info(f"Target Table:      {env_vars['trgt_table']}")
        logger.info(f"Train session id:  {env_vars['train_session_id']}")
        logger.info(f"Pred  session id:  {env_vars['pred_session_id']}")
        logger.info(f"Run config:        {cfg}")

        train_session_id = env_vars['train_session_id']
        pred_session_id  = env_vars['pred_session_id']
        suffix           = f"_{env_vars['unit']}" if env_vars.get('unit') else ""
        tp               = cfg['table_prefix']

        predictor = LeadScoringPredictor(
            apikey       = env_vars['apikey'],
            database     = env_vars['database'],
            model_family = cfg['model_type'],
            endpoint     = env_vars.get('td_endpoint') or 'https://api.treasuredata.com',
            table_prefix = tp,
        )
        preprocessor = Preprocessor()

        # ── STEP 1: Load model ────────────────────────────────────────
        logger.info("-" * 60)
        logger.info(f"STEP 1: Loading {cfg['model_type']} model")
        logger.info("-" * 60)
        predictor.load_model(
            train_session_id  = train_session_id,
            model_store_table = env_vars.get('model_store_table') or None,
            model_name        = env_vars.get('model_name') or None,
        )

        # ── STEP 2: Threshold + training-bin distribution ─────────────
        logger.info("-" * 60)
        logger.info("STEP 2: Loading training metadata (threshold + PSI bins)")
        logger.info("-" * 60)
        predictor.load_training_metadata(train_session_id)

        # ── STEP 3: Load prediction data ──────────────────────────────
        logger.info("-" * 60)
        logger.info("STEP 3: Loading prediction data")
        logger.info("-" * 60)
        pred_df = predictor.load_prediction_data(
            env_vars['prediction_table'], pred_session_id
        )

        # Capture user_ids BEFORE preprocessing drops them.  Indexed by
        # pred_df.index — the preprocessor preserves the pandas index so
        # we can join back at the end.
        user_ids_full = None
        if cfg['user_id_col']:
            uid = cfg['user_id_col']
            if uid in pred_df.columns:
                user_ids_full = pred_df[uid].copy()
                logger.info(
                    f"Captured {len(user_ids_full)} user_ids from '{uid}'"
                )
            else:
                logger.warning(
                    f"user_id_col '{uid}' not in prediction table columns — "
                    "writing predictions with positional ids"
                )

        # ── STEP 4: Preprocess + align ────────────────────────────────
        logger.info("-" * 60)
        logger.info("STEP 4: Preprocess + align to training feature set")
        logger.info("-" * 60)
        X_pred = predictor.preprocess(
            pred_df, preprocessor,
            columns_to_drop=cfg['columns_to_drop'],
        )
        X_pred = predictor.align_features(X_pred)

        # ── STEP 5: Scale (logistic only) ─────────────────────────────
        X_for_score = predictor.maybe_scale(X_pred)

        # ── STEP 6: Predict ───────────────────────────────────────────
        logger.info("-" * 60)
        logger.info("STEP 6: Scoring")
        logger.info("-" * 60)
        predictions = predictor.predict_proba(X_for_score)

        # ── STEP 7: Per-row SHAP ──────────────────────────────────────
        # Only compute SHAP for predicted-positive leads (saves ~80% time).
        # Sales only needs explanations for leads they'll act on.
        logger.info("-" * 60)
        logger.info(
            f"STEP 7: Per-row SHAP — top {cfg['shap_topn_per_direction']} "
            f"positive + top {cfg['shap_topn_per_direction']} negative"
        )
        logger.info("-" * 60)

        predicted_positive_mask = predictions >= predictor.best_threshold
        n_positive = int(predicted_positive_mask.sum())
        logger.info(
            f"Predicted positives: {n_positive:,} of {len(predictions):,} "
            f"({n_positive/len(predictions)*100:.1f}%) — computing SHAP only for these"
        )

        if n_positive > 0:
            X_for_shap = X_for_score[predicted_positive_mask]
            shap_max = cfg['shap_max_rows'] if cfg['shap_max_rows'] > 0 else None
            shap_long_df, _, shap_row_pos = predictor.compute_per_row_shap(
                X               = X_for_shap,
                top_n_per_direction = cfg['shap_topn_per_direction'],
                max_rows        = shap_max,
            )
            del X_for_shap
            gc.collect()
        else:
            logger.warning("No predicted positives — skipping SHAP")
            shap_long_df = pd.DataFrame()
            shap_row_pos = np.array([], dtype=int)

        # ── STEP 8: Build output DataFrames ───────────────────────────
        logger.info("-" * 60)
        logger.info("STEP 8: Building output DataFrames")
        logger.info("-" * 60)
        predictions_df  = build_predictions_df(
            pred_df            = pred_df,
            X_pred             = X_for_score,    # for feature-count audit
            predictions        = predictions,
            threshold          = predictor.best_threshold,
            user_ids_full      = user_ids_full,
            train_session_id   = train_session_id,
            pred_session_id    = pred_session_id,
            model_type         = cfg['model_type'],
            model_session_id   = train_session_id,
        )

        # For SHAP stamping, we need the positive-only subset references
        X_positive = X_for_score[predicted_positive_mask] if n_positive > 0 else X_for_score.iloc[:0]
        predictions_positive = predictions[predicted_positive_mask] if n_positive > 0 else predictions[:0]

        shap_out_df = stamp_shap_long(
            shap_long_df     = shap_long_df,
            X_for_score      = X_positive,
            predictions      = predictions_positive,
            user_ids_full    = user_ids_full,
            shap_row_pos     = shap_row_pos,
            train_session_id = train_session_id,
            pred_session_id  = pred_session_id,
            model_type       = cfg['model_type'],
            top_n_per_direction = cfg['shap_topn_per_direction'],
        )
        del X_positive, predictions_positive
        gc.collect()

        bins_df = build_prediction_bins_df(
            predictions     = predictions,
            pred_session_id = pred_session_id,
            train_session_id= train_session_id,
        )

        # PSI uses the bins we already loaded
        psi = predictor.calculate_psi(predictions)

        run_log_df = build_pred_run_log(
            predictions      = predictions,
            threshold        = predictor.best_threshold,
            train_session_id = train_session_id,
            pred_session_id  = pred_session_id,
            data_shape       = pred_df.shape,
            n_features       = len(predictor.feature_names),
            model_type       = cfg['model_type'],
            psi              = psi,
        )

        # Free memory before parallel TD writes
        del X_pred, X_for_score, pred_df
        gc.collect()

        # ── STEP 9: Parallel write ────────────────────────────────────
        logger.info("-" * 60)
        logger.info(
            f"STEP 9: Writing artifacts to TD "
            f"(concurrency={cfg['write_concurrency']})"
        )
        logger.info("-" * 60)

        writer = ParallelWriter(
            apikey      = env_vars['apikey'],
            database    = env_vars['database'],
            endpoint    = env_vars.get('td_endpoint') or 'https://api.treasuredata.com',
            max_workers = cfg['write_concurrency'],
        )

        writer.submit(predictions_df, env_vars['trgt_table'])
        writer.submit(shap_out_df,    f"{tp}prediction_shap{suffix}")
        writer.submit(bins_df,        f"{tp}prediction_bins{suffix}")
        writer.submit(run_log_df,     f"{tp}prediction_run_log{suffix}")
        writer.flush()

        # ── Final summary ─────────────────────────────────────────────
        end_time       = datetime.datetime.now()
        execution_time = end_time - start_time

        logger.info("=" * 80)
        logger.info("PREDICTION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"Execution time:    {execution_time}")
        logger.info(f"Model:             {cfg['model_type']} (train_session={train_session_id})")
        logger.info(f"Records scored:    {len(predictions):,}")
        logger.info(f"Threshold applied: {predictor.best_threshold:.4f}")
        n_pos = int((predictions >= predictor.best_threshold).sum())
        logger.info(
            f"Predicted positive: {n_pos:,} / {len(predictions):,} "
            f"({n_pos/len(predictions)*100:.2f}%)"
        )
        if psi is not None:
            logger.info(f"PSI vs train:      {psi:.4f}")
        logger.info(f"SHAP rows written: {len(shap_out_df):,}")

    except Exception as e:
        end_time = datetime.datetime.now()
        logger.error("=" * 80)
        logger.error("PREDICTION FAILED!")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.error(f"Execution time before failure: {end_time - start_time}")
        import traceback
        logger.error(traceback.format_exc())
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Output DataFrame builders
# ─────────────────────────────────────────────────────────────────────────────
def build_predictions_df(pred_df, X_pred, predictions, threshold,
                         user_ids_full, train_session_id, pred_session_id,
                         model_type, model_session_id):
    """
    One row per lead — main output for downstream Sales / activation.
    """
    bin_edges  = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    bin_labels = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5',
                  '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
    score_bucket = pd.cut(predictions, bins=bin_edges,
                          labels=bin_labels, include_lowest=True).astype(str)

    if user_ids_full is not None:
        # X_pred shares the pandas index with pred_df → align user_ids by index
        user_ids = user_ids_full.loc[X_pred.index].values
    else:
        user_ids = np.arange(len(predictions))

    return pd.DataFrame({
        'pred_session_id':       pred_session_id,
        'train_session_id':      train_session_id,
        'model_type':            model_type,
        'model_session_id':      model_session_id,
        'user_id':               user_ids,
        'lead_score':            np.round(predictions, 6),
        'predicted_label':       (predictions >= threshold).astype(int),
        'threshold_applied':     round(float(threshold), 4),
        'score_bucket':          score_bucket,
        'prediction_timestamp':  datetime.datetime.now(),
    })


def stamp_shap_long(shap_long_df, X_for_score, predictions, user_ids_full,
                    shap_row_pos, train_session_id, pred_session_id,
                    model_type, top_n_per_direction):
    """
    Promote the predictor's positional `row_id` to the real `user_id`,
    add denormalised lead_score for fast dashboards, attach run-level ids.
    """
    if shap_long_df.empty:
        logger.warning("SHAP long DataFrame empty — nothing to stamp")
        return shap_long_df

    # Map SHAP positional row_id → real user_id and lead_score
    if user_ids_full is not None:
        scored_index = X_for_score.index[shap_row_pos]
        scored_uids  = user_ids_full.loc[scored_index].values
    else:
        scored_uids  = shap_row_pos
    scored_proba = predictions[shap_row_pos]

    df = shap_long_df.copy()
    df['user_id']        = df['row_id'].map(
        dict(zip(range(len(scored_uids)), scored_uids))
    )
    df['lead_score']     = df['row_id'].map(
        dict(zip(range(len(scored_proba)), np.round(scored_proba, 6)))
    )
    df['pred_session_id']      = pred_session_id
    df['train_session_id']     = train_session_id
    df['model_type']           = model_type
    df['top_n_per_direction']  = top_n_per_direction
    df['created_at']           = datetime.datetime.now()

    # Drop the positional row_id; keep user_id as the join key
    df = df.drop(columns=['row_id'])
    # Reorder columns for readability
    df = df[[
        'pred_session_id', 'train_session_id', 'model_type',
        'user_id', 'lead_score',
        'feature_name', 'feature_value', 'shap_value',
        'direction', 'rank_within_direction', 'top_n_per_direction',
        'created_at',
    ]]
    return df


def build_prediction_bins_df(predictions, pred_session_id, train_session_id):
    bins   = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    labels = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5',
              '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
    binned = pd.cut(predictions, bins=bins, labels=labels, include_lowest=True)
    counts = binned.value_counts().sort_index()
    total  = len(predictions)
    rows = []
    now  = datetime.datetime.now()
    for label, count in counts.items():
        rows.append({
            'pred_session_id':  pred_session_id,
            'train_session_id': train_session_id,
            'bin_range':        str(label),
            'count':            int(count),
            'percentage':       round((count / total) * 100, 2) if total else 0,
            'source':           'prediction',
            'created_at':       now,
        })
    return pd.DataFrame(rows)


def build_pred_run_log(predictions, threshold, train_session_id, pred_session_id,
                       data_shape, n_features, model_type, psi):
    return pd.DataFrame({
        'pred_session_id':    [pred_session_id],
        'train_session_id':   [train_session_id],
        'model_type':         [model_type],
        'run_timestamp':      [datetime.datetime.now()],
        'records_scored':     [len(predictions)],
        'data_shape':         [str(data_shape)],
        'score_min':          [round(float(predictions.min()),    6)],
        'score_max':          [round(float(predictions.max()),    6)],
        'score_mean':         [round(float(predictions.mean()),   6)],
        'score_median':       [round(float(np.median(predictions)), 6)],
        'score_std':          [round(float(predictions.std()),    6)],
        'threshold_applied':  [round(float(threshold),            4)],
        'predicted_positive': [int((predictions >= threshold).sum())],
        'predicted_negative': [int((predictions <  threshold).sum())],
        'psi':                [psi],
        'total_features':     [n_features],
    })


def main():
    run_prediction()