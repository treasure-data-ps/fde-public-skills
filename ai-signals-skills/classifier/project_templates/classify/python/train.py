# ─────────────────────────────────────────────────────────────────────────────
# train.py
# Entry point: py>: python.train.main
#
# Digdag _env contract (additions to the original pipeline marked ★):
#
#   ── Identity / IO ─────────────────────────────────────────────────────
#   apikey                → TD API key (secret)
#   database              → TD database name
#   session_id            → Digdag session ID (used as run id everywhere)
#   unit                  → business unit identifier (suffix on output tables)
#   train_table           → source feature table
#   trgt_table            → logistic coefficient output table
#   start_date, end_date  → training window
#   target_variable       → binary target column
#
#   ── Model selection ★ ──────────────────────────────────────────────────
#   model_type            → 'logistic' | 'xgboost' | 'catboost'  (default: logistic)
#
#   ── td-model-store (xgb/catboost only) ★ ───────────────────────────────
#   model_store_table     → table to write binary blob to  (default: lead_ml_model_store)
#   model_name            → name tag for the stored model  (default: lead_scoring_{family})
#   td_endpoint           → TD API endpoint                (default: US)
#
#   ── Shared tuning ─────────────────────────────────────────────────────
#   columns_to_drop, test_size, fbeta_beta, n_trials,
#   corr_threshold, min_metric_floor
#
#   ── Logistic-only (ignored for tree models) ───────────────────────────
#   max_iter              → LR solver max iterations
#
#   ── Tree-model tuning ★ (ignored for logistic) ─────────────────────────
#   n_estimators_min, n_estimators_max   → Optuna range for n_trees
#   max_depth_min,    max_depth_max      → Optuna range for depth
#   learning_rate_min, learning_rate_max → Optuna range for LR (loguniform)
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import logging
import datetime

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
# PACKAGE INSTALL — runs before any third-party imports
# ─────────────────────────────────────────────────────────────────────────────
def install_packages():
    """Install required packages (Python 3.9-compatible pins)."""
    logger.info("Uninstalling existing NumPy...")
    os.system(f"{sys.executable} -m pip uninstall -y numpy")

    logger.info("Installing NumPy 1.22.4 to user location...")
    os.system(f"{sys.executable} -m pip install --user --force-reinstall 'numpy==1.22.4'")

    packages = [
        'scipy==1.10.1',
        'scikit-learn==1.2.2',
        'imbalanced-learn==0.10.1',
        'matplotlib==3.7.1',
        'plotly==5.14.1',
        'pandas==1.5.3',
        'pytd==1.4.0',
        'numba==0.57.0',
        'shap==0.42.1',
        'statsmodels==0.14.6',
        'optuna==3.5.0',
        'optuna-integration==3.5.0',
        # Tree models — installed unconditionally so model_type can switch
        # at runtime without pipeline edits
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
from sklearn.model_selection import train_test_split
import gc
from data_handler     import DataHandler
from preprocessor     import Preprocessor
from parallel_writer  import ParallelWriter
from models           import ModelFactory
import explainer


# ─────────────────────────────────────────────────────────────────────────────
# ENV PARSING
# ─────────────────────────────────────────────────────────────────────────────
def validate_training_environment():
    required = [
        'apikey', 'database', 'session_id', 'train_table',
        'trgt_table', 'start_date', 'end_date', 'target_variable',
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    env = {v: os.environ.get(v) for v in required}
    # Optional passthroughs for model store + unit suffix
    for v in ['unit', 'model_store_table', 'model_name', 'td_endpoint']:
        env[v] = os.environ.get(v, '')
    return env


def parse_env_config():
    """
    Read all tuning params from Digdag env with sensible fallbacks.
    New (vs. original pipeline): model_type, tree-model hyperparam ranges,
    td-model-store params.
    """
    raw_cols = os.environ.get('columns_to_drop', '').strip()
    columns_to_drop = [c.strip() for c in raw_cols.split(',') if c.strip()] or None

    cfg = {
        # Shared
        'model_type':       os.environ.get('model_type', 'logistic').strip().lower(),
        'columns_to_drop':  columns_to_drop,
        'test_size':        float(os.environ.get('test_size',        '0.2')),
        'fbeta_beta':       float(os.environ.get('fbeta_beta',       '0.5')),
        'n_trials':         int(os.environ.get('n_trials',           '3')),
        'corr_threshold':   float(os.environ.get('corr_threshold',   '0.80')),
        'min_metric_floor': float(os.environ.get('min_metric_floor', '0.10')),

        # Tuning strategy
        'optuna_metric':          os.environ.get('optuna_metric', 'fbeta').strip().lower(),
        'threshold_strategy':     os.environ.get('threshold_strategy', 'precision_optimal').strip().lower(),
        'fixed_threshold':        float(os.environ.get('fixed_threshold', '0.5')),
        'cv_folds':               int(os.environ.get('cv_folds', '3')),
        'early_stopping_rounds':  int(os.environ.get('early_stopping_rounds', '0')),
        'class_balance_strategy': os.environ.get('class_balance_strategy', 'balanced').strip().lower(),
        'xgb_eval_metric':       os.environ.get('xgb_eval_metric', 'aucpr').strip().lower(),
        'description':               os.environ.get('description', '').strip(),

        # Logistic-only
        'max_iter':         int(os.environ.get('max_iter',           '1000')),

        # Tree models — Optuna ranges
        'n_estimators_min': int(  os.environ.get('n_estimators_min',  '100')),
        'n_estimators_max': int(  os.environ.get('n_estimators_max',  '800')),
        'max_depth_min':    int(  os.environ.get('max_depth_min',     '3')),
        'max_depth_max':    int(  os.environ.get('max_depth_max',     '10')),
        'learning_rate_min': float(os.environ.get('learning_rate_min', '0.01')),
        'learning_rate_max': float(os.environ.get('learning_rate_max', '0.3')),

        # td-model-store
        'model_store_table': os.environ.get('model_store_table', 'ml_model_store'),
        'model_name':        os.environ.get('model_name', ''),
        'td_endpoint':       os.environ.get('td_endpoint', 'https://api.treasuredata.com'),

        # Parallel TD writes — number of concurrent threads flushing tables
        'write_concurrency': int(os.environ.get('write_concurrency', '6')),

        # Output table prefix — if set (e.g. 'lead_scoring_'), all output
        # tables use this prefix; if empty, generic names are used.
        'table_prefix': os.environ.get('table_prefix', ''),

        # ─── SHAP explainability artifacts ────────────────────────────
        # Sample size ceiling for SHAP computation. TreeExplainer scales
        # linearly; LinearExplainer is essentially free.  1000 is usually
        # plenty for stable aggregate statistics.
        'shap_max_samples':          int(os.environ.get('shap_max_samples',          '1000')),

        # Interaction SHAP — off by default; O(n_features^2) cost.
        # Supports XGBoost directly; CatBoost best-effort.
        'shap_interactions_enabled': os.environ.get('shap_interactions_enabled', 'false').lower() == 'true',
        'shap_interactions_samples': int(os.environ.get('shap_interactions_samples', '200')),
        'shap_interactions_top_k':   int(os.environ.get('shap_interactions_top_k',   '50')),

        # ─── Test predictions ──────────────────────────────────────────
        # Column in the raw training table that uniquely identifies a lead
        # (e.g. ucp_id, lead_id).  If set, the test-set predictions are
        # written to lead_scoring_test_predictions{suffix} so Sales /
        # downstream systems can attribute probabilities back to users.
        # Leave blank to skip the test-prediction write.
        'user_id_col':               os.environ.get('user_id_col', '').strip(),
        
    }
    return cfg


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def run_training():
    logger.info("=" * 80)
    logger.info("STARTING TRAINING MODE")
    logger.info("=" * 80)

    start_time = datetime.datetime.now()

    try:
        env_vars = validate_training_environment()
        cfg      = parse_env_config()

        # Safety: if user_id_col is set, make sure it's in columns_to_drop so
        # it can't accidentally be used as a feature.  We do this silently
        # if already present, or with a warning if we had to add it.
        if cfg['user_id_col']:
            uid = cfg['user_id_col']
            drop_list = list(cfg['columns_to_drop'] or [])
            if uid not in drop_list:
                logger.warning(
                    f"user_id_col='{uid}' was not in columns_to_drop — "
                    f"appending it defensively so it cannot leak as a feature. "
                    f"Please add it to your Digdag columns_to_drop list too."
                )
                drop_list.append(uid)
                cfg['columns_to_drop'] = drop_list

        logger.info(f"Model type:     {cfg['model_type']}")
        logger.info(f"Database:       {env_vars['database']}")
        logger.info(f"Training Table: {env_vars['train_table']}")
        logger.info(f"Session ID:     {env_vars['session_id']}")
        logger.info(f"Training Period: {env_vars['start_date']} → {env_vars['end_date']}")
        logger.info(f"Run config:     {cfg}")

        data_handler = DataHandler(env_vars['apikey'], env_vars['database'], cfg['td_endpoint'])
        preprocessor = Preprocessor()
        model        = ModelFactory.create(cfg['model_type'], cfg)

        # ── STEP 1: Load data ─────────────────────────────────────────
        logger.info("-" * 60)
        logger.info("STEP 1: Loading data from Treasure Data")
        logger.info("-" * 60)
        train_data = data_handler.read_data(env_vars['train_table'], env_vars['session_id'])

        if train_data.empty:
            logger.error("No data loaded. Aborting.")
            return

        target = env_vars['target_variable']
        logger.info(f"Shape: {train_data.shape}")
        logger.info(f"Target distribution:\n{train_data[target].value_counts()}")

        if train_data[target].nunique() < 2:
            raise RuntimeError(
                f"Training data contains only one class: {train_data[target].unique()}. "
                "Check lead_generation.sql — ensure non-won customers are included."
            )

        # ── STEP 2: Stratified train/test split ───────────────────────
        logger.info("-" * 60)
        logger.info(f"STEP 2: Stratified split — test_size={cfg['test_size']}")
        logger.info("-" * 60)

        df_train, df_test = train_test_split(
            train_data,
            test_size=cfg['test_size'],
            stratify=train_data[target],
            random_state=24,
        )
        del train_data
        gc.collect()
        logger.info(f"Train: {df_train.shape} | Test: {df_test.shape}")

        # Capture test-set identity BEFORE preprocessing drops the id column.
        # We key by df_test.index (pandas index is preserved through
        # preprocessing because nothing calls reset_index), so we can join
        # predictions back on the original rows at the end.
        test_ids = None
        if cfg['user_id_col']:
            uid = cfg['user_id_col']
            if uid in df_test.columns:
                test_ids = df_test[uid].copy()  # indexed by df_test.index
                logger.info(
                    f"Captured {len(test_ids)} test-set ids from '{uid}' "
                    f"for test_predictions"
                )
            else:
                logger.warning(
                    f"user_id_col='{uid}' not found in source table columns "
                    f"{list(df_test.columns)} — test predictions will use "
                    f"positional index as id fallback"
                )

        # ── STEP 3: Preprocess ────────────────────────────────────────
        logger.info("-" * 60)
        logger.info(
            f"STEP 3: Preprocessing "
            f"(impute_numerics={model.requires_imputation}, "
            f"family={model.family})"
        )
        logger.info("-" * 60)

        X_train, y_train = preprocessor.preprocess(
            df_train, is_training=True,
            columns_to_drop=cfg['columns_to_drop'],
            impute_numerics=model.requires_imputation,
        )
        X_test,  y_test  = preprocessor.preprocess(
            df_test,  is_training=False,
            columns_to_drop=cfg['columns_to_drop'],
            impute_numerics=model.requires_imputation,
        )
        X_test = preprocessor.align_columns(X_train, X_test)
        del df_train, df_test
        gc.collect()
        logger.info(f"Train features: {X_train.shape} | Test features: {X_test.shape}")

        data_info = {
            'train_shape':       X_train.shape,
            'test_shape':        X_test.shape,
            'train_target_dist': y_train.value_counts().to_dict(),
            'test_target_dist':  y_test.value_counts().to_dict(),
            'start_date':        env_vars['start_date'],
            'end_date':          env_vars['end_date'],
            'test_start_date':   None,
            'test_end_date':     None,
        }

        # ── STEP 4: (LR only) scale  then  drop correlated features ──
        # Logistic: scale → drop → subset scaler (avoids double-scaling bug)
        # Trees   : drop only (no scaling needed)
        logger.info("-" * 60)
        logger.info(f"STEP 4: Feature selection (corr > {cfg['corr_threshold']})")
        logger.info("-" * 60)

        if model.requires_scaling:
            logger.info("A. StandardScaler fit on full training features")
            X_train_proc = model.scale_fit_transform(X_train)
            X_test_proc  = model.scale_transform(X_test)

            full_cols = list(X_train_proc.columns)
            logger.info("B. Dropping highly correlated features (post-scale)")
            X_train_proc, dropped, corr_drop_report = preprocessor.drop_highly_correlated(
                X_train_proc, threshold=cfg['corr_threshold']
            )
            X_test_proc = X_test_proc.drop(
                columns=[c for c in dropped if c in X_test_proc.columns],
                errors='ignore',
            )

            logger.info("C. Subsetting scaler params to kept features (NO refit)")
            model.subset_scaler(list(X_train_proc.columns), full_cols)
        else:
            logger.info("Tree model — skipping scaling")
            X_train_proc, dropped, corr_drop_report = preprocessor.drop_highly_correlated(
                X_train, threshold=cfg['corr_threshold']
            )
            X_test_proc = X_test.drop(
                columns=[c for c in dropped if c in X_test.columns],
                errors='ignore',
            )
            del X_train, X_test
            gc.collect()

        logger.info(f"After corr drop — Train: {X_train_proc.shape}, Test: {X_test_proc.shape}")

        # ── STEP 5: Correlation reports + VIF ─────────────────────────
        logger.info("-" * 60)
        logger.info("STEP 5: Correlation reports + VIF")
        logger.info("-" * 60)

        feature_corr_df, target_corr_df = preprocessor.compute_correlations(
            X_train_proc, target=y_train
        )
        vif_df = preprocessor.compute_vif(X_train_proc)

        # ── STEP 6: Fit (Optuna → final model) ────────────────────────
        logger.info("-" * 60)
        logger.info(f"STEP 6: Model training — {cfg['model_type']} + Optuna TPE")
        logger.info("-" * 60)

        model.fit(X_train_proc, y_train)

        # ── STEP 7: Threshold selection (precision-optimal via PR curve) ─
        logger.info("-" * 60)
        logger.info(f"STEP 7: Threshold selection (strategy={cfg['threshold_strategy']}, "
                    f"min_metric_floor={cfg['min_metric_floor']}, fbeta_beta={cfg['fbeta_beta']})")
        logger.info("-" * 60)

        train_proba = model.predict_proba(X_train_proc)
        best_threshold = explainer.find_threshold(
            y_true=y_train,
            y_proba=train_proba,
            strategy=cfg['threshold_strategy'],
            min_metric_floor=cfg['min_metric_floor'],
            fbeta_beta=cfg['fbeta_beta'],
            fixed_threshold=cfg['fixed_threshold'],
        )
        del X_train_proc
        gc.collect()

        # ── STEP 8: Evaluate ──────────────────────────────────────────
        logger.info("-" * 60)
        logger.info("STEP 8: Evaluation")
        logger.info("-" * 60)

        test_proba = model.predict_proba(X_test_proc)

        test_metrics  = explainer.evaluate(y_test,  test_proba,  best_threshold,
                                           fbeta_beta=cfg['fbeta_beta'])
        train_metrics = explainer.evaluate(y_train, train_proba, best_threshold,
                                           fbeta_beta=cfg['fbeta_beta'])

        # PSI between train & test score distributions
        psi = preprocessor.compute_psi(train_proba, test_proba)
        test_metrics['psi'] = round(psi, 4)
        logger.info(f"PSI (train vs test): {psi:.4f}")
        del train_proba
        gc.collect()

        # ── STEP 9: SHAP — importance, directional (up/down), optional interactions
        logger.info("-" * 60)
        logger.info("STEP 9: SHAP explainability")
        logger.info("-" * 60)

        shap_df, shap_values, X_shap_sample, shap_explainer_obj = explainer.compute_shap(
            model        = model.model,
            X            = X_test_proc,
            model_family = model.family,
            feature_names= model.feature_names,
            max_samples  = cfg['shap_max_samples'],
        )

        # ── STEP 10: Save everything (PARALLEL) ───────────────────────
        # All artifact writes go to distinct tables, so they parallelise
        # cleanly.  We queue every write into a ParallelWriter then flush()
        # once — any individual failure raises a single aggregate error at
        # the end rather than leaving writes half-done silently.
        logger.info("-" * 60)
        logger.info(
            f"STEP 10: Writing artifacts to Treasure Data "
            f"(concurrency={cfg['write_concurrency']})"
        )
        logger.info("-" * 60)

        session_id = env_vars['session_id']
        suffix     = f"_{env_vars['unit'].strip()}" if env_vars.get('unit') else ""
        tp         = cfg['table_prefix']

        writer = ParallelWriter(
            apikey      = env_vars['apikey'],
            database    = env_vars['database'],
            endpoint    = cfg['td_endpoint'],
            max_workers = cfg['write_concurrency'],
        )

        # ── Shared artifacts (all model types) ────────────────────────
        # VIF
        writer.submit(
            explainer.stamp_session(vif_df, session_id),
            f"{tp}vif_scores",
        )

        # Run logs (test + train)
        run_log = explainer.build_run_log(
            test_metrics, session_id, data_info,
            feature_count = len(model.feature_names),
            best_params   = model.best_params,
            cfg           = cfg,
            model_type    = cfg['model_type'],
           
        )
        writer.submit(run_log, f"{tp}run_log{suffix}")

        train_run_log = explainer.build_run_log(
            train_metrics, session_id, data_info,
            feature_count = len(model.feature_names),
            best_params   = model.best_params,
            cfg           = cfg,
            model_type    = cfg['model_type'],
            
        )
        writer.submit(train_run_log, f"{tp}train_run_log{suffix}")

        # Row-level test-set predictions (if user_id_col configured).
        # y_test, test_proba, and test_ids are all indexed/ordered the same
        # way because nothing in the pipeline ever called reset_index on
        # the test split.  We align test_ids → y_test via its pandas index.
        if cfg['user_id_col']:
            if test_ids is not None:
                aligned_ids = test_ids.loc[y_test.index].values
            else:
                # Fallback — user_id_col was configured but column wasn't in
                # the source table (warning was already logged above).  Use
                # positional index so Sales can at least see row-level results.
                aligned_ids = np.arange(len(y_test))

            test_preds_df = explainer.build_test_predictions_df(
                y_true     = y_test.values,
                y_proba    = test_proba,
                threshold  = best_threshold,
                session_id = session_id,
                user_ids   = aligned_ids,
            )
            writer.submit(test_preds_df, f"{tp}test_predictions{suffix}")
        else:
            logger.info(
                "  [skip] test predictions — user_id_col not set in Digdag. "
                "Set user_id_col: 'ucp_id' (or similar) to emit "
                "test_predictions."
            )

        feature_list_df = pd.DataFrame({
            'session_id':    [session_id] * len(model.feature_names),
            'feature_name':  list(model.feature_names),
            'feature_index': list(range(len(model.feature_names))),
            'created_at':    [datetime.datetime.now()] * len(model.feature_names),
        })
        writer.submit(feature_list_df, f"{tp}feature_list{suffix}")
        
        # SHAP importance (magnitude — "which features matter")
        writer.submit(
            explainer.stamp_session(shap_df, session_id),
            f"{tp}feature_importance{suffix}",
        )

        # SHAP directional ("do they push scores UP or DOWN, and how consistently")
        directional_df = explainer.build_shap_directional_df(
            shap_values   = shap_values,
            X_sample      = X_shap_sample,
            feature_names = model.feature_names,
            session_id    = session_id,
            model_family  = model.family,
        )
        writer.submit(directional_df, f"{tp}shap_directional{suffix}")

        # SHAP pairwise interactions (opt-in — O(n_features^2), XGBoost-native)
        if cfg['shap_interactions_enabled']:
            interactions_df = explainer.build_shap_interactions_df(
                explainer_obj           = shap_explainer_obj,
                X_sample                = X_shap_sample,
                feature_names           = model.feature_names,
                session_id              = session_id,
                model_family            = model.family,
                max_interaction_samples = cfg['shap_interactions_samples'],
                top_k_pairs             = cfg['shap_interactions_top_k'],
            )
            writer.submit(interactions_df, f"{tp}shap_interactions{suffix}")
        else:
            logger.info("  [skip] shap_interactions disabled (set shap_interactions_enabled='true' to emit)")

        # ROC curve + prediction bins
        roc_df  = explainer.build_roc_curve_df(test_metrics, session_id)
        bins_df = explainer.build_prediction_bins_df(test_metrics, session_id)
        writer.submit(roc_df,  f"{tp}roc_curve{suffix}")
        writer.submit(bins_df, f"{tp}prediction_bins{suffix}")
        writer.submit(bins_df, f"{tp}probability_train_bins")

        # Correlation reports
        writer.submit(
            explainer.stamp_session(feature_corr_df, session_id),
            f"{tp}feature_correlations{suffix}",
        )
        writer.submit(
            explainer.stamp_session(target_corr_df, session_id),
            f"{tp}target_correlations{suffix}",
        )
        writer.submit(
            explainer.stamp_session(corr_drop_report, session_id),
            f"{tp}corr_drop_report{suffix}",
        )

        # Optuna trials
        writer.submit(
            explainer.stamp_session(model.optuna_trials_df, session_id),
            f"{tp}optuna_trials{suffix}",
        )

        # ── Model-specific artifacts (coefficients / scaler / blob / gain) ─
        # save_artifacts queues its own jobs onto the same writer so
        # everything flushes together in one parallel burst.
        model.save_artifacts(writer, session_id, cfg, env_vars)

        # ── Dispatch all writes concurrently ──────────────────────────
        writer.flush()

        # ── Final summary ─────────────────────────────────────────────
        end_time       = datetime.datetime.now()
        execution_time = end_time - start_time

        logger.info("=" * 80)
        logger.info("TRAINING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"Model type:     {cfg['model_type']}")
        logger.info(f"Execution time: {execution_time}")
        logger.info(f"Session ID:     {session_id}")
        logger.info(f"Features dropped (corr > {cfg['corr_threshold']}): {len(corr_drop_report)}")
        logger.info(f"Final feature count: {len(model.feature_names)}")
        logger.info(f"Best params (Optuna): {model.best_params}")
        logger.info(f"Threshold: {best_threshold:.4f}  (precision-optimal, PR curve)")
        logger.info("")
        logger.info("TRAIN metrics:")
        _log_metrics(train_metrics)
        logger.info("")
        logger.info("TEST metrics:")
        _log_metrics(test_metrics)
        logger.info("")
        _log_threshold_delta(test_metrics)

    except Exception as e:
        end_time = datetime.datetime.now()
        logger.error("=" * 80)
        logger.error("TRAINING FAILED!")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Execution time before failure: {end_time - start_time}")
        import traceback
        logger.error(traceback.format_exc())
        raise


# ─────────────────────────────────────────────────────────────────────────────
# LOG HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _log_metrics(m):
    logger.info(f"  Precision:     {m.get('precision', 0):.4f}  ← primary metric")
    logger.info(f"  Recall:        {m.get('recall', 0):.4f}")
    logger.info(f"  F_beta:        {m.get('fbeta', 0):.4f}")
    logger.info(f"  F1-Score:      {m.get('f1', 0) / 100:.4f}")
    logger.info(f"  Accuracy:      {m.get('test_accuracy', 0):.4f}")
    if m.get('auc_roc') is not None:
        logger.info(f"  AUC-ROC:       {m.get('auc_roc', 0) / 100:.4f}")
    if m.get('aucpr') is not None:
        logger.info(f"  AUC-PR:        {m.get('aucpr', 0) / 100:.4f}")
    logger.info(f"  Threshold:     {m.get('best_threshold', 0.5):.4f}")
    logger.info(f"  TN={m.get('true_negatives',0):,}  FP={m.get('false_positives',0):,}  "
                f"FN={m.get('false_negatives',0):,}  TP={m.get('true_positives',0):,}")
    if m.get('psi') is not None:
        logger.info(f"  PSI:           {m.get('psi', 0):.4f}")


def _log_threshold_delta(m):
    thr  = m.get('best_threshold', 0.5)
    prec = m.get('precision', 0)
    rec  = m.get('recall', 0)
    logger.info(f"  Applied threshold : {thr:.4f}")
    logger.info(f"  Precision @ thr   : {prec:.4f}")
    logger.info(f"  Recall    @ thr   : {rec:.4f}")
    if rec > 0:
        logger.info(f"  Precision/Recall  : {prec/rec:.2f}x  (>1 = precision-dominant ✓)")


def main():
    run_training()


# if __name__ == "__main__":
#     main()