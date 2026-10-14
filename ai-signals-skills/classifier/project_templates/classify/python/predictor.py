# ─────────────────────────────────────────────────────────────────────────────
# predictor.py  —  Lead Scoring Predictor (model-agnostic)
#
# Loads a trained model from Treasure Data and scores a held-out
# population.  Supports the same three model families as training:
#
#   logistic → reads coefficients + scaler_params tables, reconstructs
#              sklearn LogisticRegression.  Backwards-compatible with
#              the original predictor.
#   xgboost  → loads binary blob from td-model-store via
#              td_model_store.load_model()
#   catboost → same as xgboost
#
# Preprocessing is delegated to the SAME Preprocessor class used in
# training so the column-drop list, one-hot encoding, NaN handling, and
# float coercion are byte-identical between training and scoring.  This
# is the single most important alignment point — drift here silently
# corrupts predictions.
#
# SHAP at scoring time emits per-row top-N positive + top-N negative
# contributors so Sales can see WHY each lead got its score.
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import datetime
import logging
import gc

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression

import pytd.pandas_td as td

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# LeadScoringPredictor
# ─────────────────────────────────────────────────────────────────────────────
class LeadScoringPredictor:
    """
    Model-agnostic predictor.  Configure with a model_family
    ('logistic' | 'xgboost' | 'catboost') then call:

        load_model(train_session_id)
        load_training_metadata(train_session_id)
        load_prediction_data(prediction_table, pred_session_id)
        preprocess(df, preprocessor)
        align_features(X)
        predict_proba(X)
        compute_per_row_shap(X, ...)

    Each step has a tightly-scoped responsibility so the orchestrator
    (predict_main.py) reads top-to-bottom like a recipe.
    """

    SUPPORTED_FAMILIES = ('logistic', 'xgboost', 'catboost')

    def __init__(self, apikey, database, model_family,
                 endpoint='https://api.treasuredata.com',
                 table_prefix=''):
        if model_family not in self.SUPPORTED_FAMILIES:
            raise ValueError(
                f"Unknown model_family '{model_family}'. "
                f"Supported: {self.SUPPORTED_FAMILIES}"
            )

        from data_handler import DataHandler
        self.data_handler = DataHandler(apikey, database, endpoint)
        self.apikey       = apikey
        self.database     = database
        self.endpoint     = endpoint
        self.family       = model_family
        self.table_prefix = table_prefix

        # Model + metadata populated by load_*
        self.model           = None     # the actual estimator
        self.scaler          = None     # only for logistic
        self.feature_names   = None     # ordered list, training order
        self.best_threshold  = 0.5      # populated from run log
        self.train_pred_bins = None     # for PSI
        self.train_session_id = None    # for audit

    # ─────────────────────────────────────────────────────────────────────
    # Query helper
    # ─────────────────────────────────────────────────────────────────────
    def _read_query(self, query):
        try:
            con = td.connect(apikey=self.apikey, endpoint=self.endpoint)
            engine = td.create_engine(f"presto:{self.database}", con=con)
            return td.read_td_query(query, engine)
        except Exception as e:
            logger.error(f"Query failed: {e}\n{query}")
            raise

    # ─────────────────────────────────────────────────────────────────────
    # MODEL LOADING — dispatches on family
    # ─────────────────────────────────────────────────────────────────────
    def load_model(self, train_session_id, model_store_table=None,
                   model_name=None):
        """
        Family dispatch:
          logistic → load coefficients + scaler from TD tables
          xgboost / catboost → load binary blob via td_model_store

        Either model_name or train_session_id must identify the right
        record in td-model-store (the library accepts either one;
        session_id wins if both supplied).
        """
        self.train_session_id = int(train_session_id)
        logger.info(
            f"Loading model: family={self.family}, "
            f"train_session_id={train_session_id}"
        )

        if self.family == 'logistic':
            self._load_logistic(train_session_id)
        else:
            self._load_tree_model(train_session_id, model_store_table, model_name)

        if self.feature_names is None:
            raise RuntimeError(
                "feature_names not populated — model load did not establish "
                "the training feature ordering"
            )
        logger.info(f"Loaded model with {len(self.feature_names)} features")

    # ── Logistic (coefficients table path) ──────────────────────────────
    def _load_logistic(self, train_session_id):
        """Reconstruct sklearn LogisticRegression from saved coefficients
        + scaler tables.  Same approach as the original predictor."""
        from sklearn.preprocessing import StandardScaler

        # Coefficients
        coeff_df = self._read_query(f"""
            SELECT feature, coefficient
            FROM {self.table_prefix}coefficient
            WHERE session_id = {train_session_id}
        """)
        if coeff_df.empty:
            raise ValueError(
                f"No coefficients found for session_id {train_session_id}"
            )

        intercept_row = coeff_df[coeff_df['feature'].str.lower() == 'intercept']
        feature_rows  = coeff_df[coeff_df['feature'].str.lower() != 'intercept']
        if intercept_row.empty:
            raise ValueError("Intercept missing from coefficient table")

        intercept     = float(intercept_row.iloc[0]['coefficient'])
        feature_names = list(feature_rows['feature'])
        coefs         = np.array(feature_rows['coefficient'].astype(float).values)

        lr = LogisticRegression()
        lr.classes_         = np.array([0, 1])
        lr.coef_            = coefs.reshape(1, -1)
        lr.intercept_       = np.array([intercept])
        lr.n_features_in_   = len(feature_names)

        self.model         = lr
        self.feature_names = feature_names
        logger.info(
            f"Logistic reconstructed: intercept={intercept:.4f}, "
            f"n_features={len(feature_names)}"
        )

        # Scaler
        scaler_df = self._read_query(f"""
            SELECT feature, mean, scale
            FROM {self.table_prefix}scaler_params
            WHERE session_id = {train_session_id}
        """)
        if scaler_df.empty:
            raise ValueError(
                f"No scaler parameters for session_id {train_session_id}"
            )
        scaler_dict = dict(zip(
            scaler_df['feature'],
            zip(scaler_df['mean'].astype(float),
                scaler_df['scale'].astype(float))
        ))
        missing = [f for f in feature_names if f not in scaler_dict]
        if missing:
            raise ValueError(f"Scaler missing features: {missing}")

        means  = np.array([scaler_dict[f][0] for f in feature_names])
        scales = np.array([scaler_dict[f][1] for f in feature_names])

        scaler                 = StandardScaler()
        scaler.mean_           = means
        scaler.scale_          = scales
        scaler.var_            = scales ** 2
        scaler.n_features_in_  = len(feature_names)
        scaler.n_samples_seen_ = 1
        self.scaler            = scaler

    # ── Tree models (td-model-store path) ───────────────────────────────
    def _load_tree_model(self, train_session_id, model_store_table, model_name):
        """
        Load XGBoost / CatBoost binary blob via td_model_store.
        td_model_store accepts either a session_id (int) or a model_name
        (returns latest matching record).  We pass session_id when
        available so we always load the exact training run, not whatever
        was uploaded last.
        """
        try:
            from td_model_store import load_model
        except ImportError:
            os.system(f"{sys.executable} -m pip install --user td-model-store")
            from td_model_store import load_model

        store_table = model_store_table or f'{self.table_prefix}ml_model_store'

        # td-model-store's session_id column is INT.  Training writes the
        # Digdag session_id when it's int-coercible, otherwise a unix ts.
        # Try the int path first; fall back to model_name lookup.
        try:
            session_id_int = int(train_session_id)
            logger.info(
                f"td_model_store.load_model: db={self.database}, "
                f"table={store_table}, session_id={session_id_int}, "
                f"model_name={model_name}"
            )
            self.model = load_model(
                database   = self.database,
                table      = store_table,
                session_id = session_id_int,
                model_name = model_name,    # may be None — library treats
                                            # session_id as the strong filter
                apikey     = self.apikey,
                endpoint   = self.endpoint,
            )
        except (TypeError, ValueError):
            if not model_name:
                raise RuntimeError(
                    f"train_session_id '{train_session_id}' is not int-coercible "
                    "and no model_name was supplied — cannot identify the "
                    "model record in td-model-store"
                )
            logger.warning(
                f"session_id '{train_session_id}' not int-coercible — "
                f"falling back to latest model_name='{model_name}'"
            )
            self.model = load_model(
                database   = self.database,
                table      = store_table,
                model_name = model_name,
                apikey     = self.apikey,
                endpoint   = self.endpoint,
            )

        # ── Sanity check: declared family must match what was loaded ────
        # A common operational mistake is training as catboost but setting
        # model_type='xgboost' in the prediction Digdag (or vice-versa).
        # td-model-store happily reconstructs the right object regardless,
        # but the rest of the predictor (SHAP explainer, importance type)
        # is wired off self.family and would do the wrong thing silently.
        actual_family = self._infer_family_from_model(self.model)
        if actual_family and actual_family != self.family:
            raise RuntimeError(
                f"model_type mismatch: Digdag says '{self.family}' but the "
                f"model loaded from td-model-store is '{actual_family}'. "
                f"Update model_type in your prediction Digdag to '{actual_family}' "
                f"to match the trained model."
            )

        # ── Feature names: read from training-side artifact table ──────
        # We deliberately do NOT poke at model.feature_names_ /
        # booster.feature_names — those are unreliable across versions.
        # The training pipeline persists the authoritative ordering as
        # lead_scoring_feature_list{suffix}.
        self.feature_names = self._load_feature_list_from_table(int(train_session_id))
        if not self.feature_names:
            logger.warning(
                f"No rows in {self.table_prefix}feature_list for session_id="
                f"{train_session_id}.  Falling back to model-object "
                f"introspection — this is fragile and may produce wrong results."
            )
            self.feature_names = self._extract_feature_names_from_model()

        if not self.feature_names:
            raise RuntimeError(
                f"Could not recover feature names for {self.family} model "
                f"(train_session_id={train_session_id}).  Was the training "
                f"run done with this version of the pipeline?  Re-train to "
                f"populate {self.table_prefix}feature_list."
            )

    def _load_feature_list_from_table(self, train_session_id):
        """
        Look up the canonical feature ordering from
        {table_prefix}feature_list{suffix}.  Returns [] if not present
        (e.g. for runs that pre-date this table) so the caller can fall
        back to model-object introspection.
        """
        # Suffix-aware lookup.  The training pipeline writes to
        # {table_prefix}feature_list{suffix}; without knowing the suffix
        # at predict time we have to try both.
        candidates = [f'{self.table_prefix}feature_list']
        suffix = os.environ.get('unit', '').strip()
        if suffix:
            candidates.insert(0, f"{self.table_prefix}feature_list_{suffix}")

        for table in candidates:
            try:
                df = self._read_query(f"""
                    SELECT feature_index, feature_name
                    FROM {table}
                    WHERE session_id = {train_session_id}
                    ORDER BY feature_index
                """)
                if not df.empty:
                    logger.info(
                        f"Loaded {len(df)} feature names from {table}"
                    )
                    return list(df['feature_name'])
            except Exception as e:
                logger.debug(f"Lookup against {table} failed: {e}")
        return []

    @staticmethod
    def _infer_family_from_model(model):
        """Best-effort detection of model family from the loaded object."""
        cls_name = type(model).__name__
        if cls_name.startswith('XGB'):
            return 'xgboost'
        if cls_name.startswith('CatBoost'):
            return 'catboost'
        if 'LogisticRegression' in cls_name:
            return 'logistic'
        return None

    def _extract_feature_names_from_model(self):
        """
        Last-resort feature name recovery from the model object itself.
        Used only when feature_list table isn't available.
        """
        m = self.model

        # Both XGB and CatBoost may expose feature_names_ on the wrapper
        names = getattr(m, 'feature_names_', None)
        if names is not None and len(names) > 0:
            return list(names)

        # XGBoost: try the underlying booster
        if hasattr(m, 'get_booster'):
            try:
                booster_names = m.get_booster().feature_names
                if booster_names:
                    return list(booster_names)
            except Exception:
                pass

        # sklearn-style attribute
        names = getattr(m, 'feature_names_in_', None)
        if names is not None and len(names) > 0:
            return list(names)

        return []

    # ─────────────────────────────────────────────────────────────────────
    # TRAINING METADATA — threshold + score-bin distribution for PSI
    # ─────────────────────────────────────────────────────────────────────
    def load_training_metadata(self, train_session_id):
        # Threshold
        try:
            df = self._read_query(f"""
                SELECT best_threshold
                FROM {self.table_prefix}run_log
                WHERE session_id = {train_session_id}
                ORDER BY run_timestamp DESC
                LIMIT 1
            """)
            if not df.empty:
                self.best_threshold = float(df.iloc[0]['best_threshold'])
                logger.info(f"Loaded threshold: {self.best_threshold:.4f}")
            else:
                logger.warning(
                    f"No run_log row for session_id={train_session_id} — "
                    "defaulting threshold to 0.5"
                )
        except Exception as e:
            logger.warning(f"Threshold lookup failed: {e} — defaulting to 0.5")

        # Training prediction-bin distribution (for PSI)
        try:
            df = self._read_query(f"""
                SELECT bin_range, count, percentage
                FROM {self.table_prefix}probability_train_bins
                WHERE session_id = {train_session_id}
                ORDER BY bin_range
            """)
            self.train_pred_bins = df if not df.empty else None
            if df.empty:
                logger.warning("No training bin distribution — PSI will be skipped")
            else:
                logger.info(f"Loaded {len(df)} training prediction bins for PSI")
        except Exception as e:
            self.train_pred_bins = None
            logger.warning(f"Training bins lookup failed: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # DATA LOADING
    # ─────────────────────────────────────────────────────────────────────
    def load_prediction_data(self, prediction_table, pred_session_id):
        logger.info(
            f"Loading prediction data: table={prediction_table}, "
            f"pred_session_id={pred_session_id}"
        )
        df = self.data_handler.read_data(prediction_table, pred_session_id)
        if df.empty:
            raise ValueError(
                f"No prediction data for pred_session_id={pred_session_id}"
            )
        logger.info(f"Prediction data shape: {df.shape}")
        return df

    # ─────────────────────────────────────────────────────────────────────
    # PREPROCESS — delegated to the same Preprocessor used in training
    # so behaviour is byte-identical.  We pass impute_numerics based on
    # whether this model needs imputation (Logistic yes, trees no).
    # ─────────────────────────────────────────────────────────────────────
    def preprocess(self, df, preprocessor, columns_to_drop=None):
        impute = (self.family == 'logistic')
        logger.info(f"Preprocessing (family={self.family}, impute_numerics={impute})")
        # Caller passes is_training=False so the preprocessor doesn't
        # try to learn dummy columns — those came from training.
        # require_target=False because prediction feature tables don't
        # carry a label column.
        X, _ = preprocessor.preprocess(
            df, is_training=False,
            columns_to_drop=columns_to_drop,
            impute_numerics=impute,
            require_target=False,
        )
        return X

    # ─────────────────────────────────────────────────────────────────────
    # ALIGN PREDICTION FEATURES TO TRAINING FEATURE SET
    # ─────────────────────────────────────────────────────────────────────
    def align_features(self, X_pred):
        """
        Add zero-filled columns for training features missing from the
        prediction set; drop prediction-set features absent at training
        time; reorder to the exact training column order.
        """
        training = list(self.feature_names)
        present  = set(X_pred.columns)
        wanted   = set(training)

        missing = wanted - present
        extra   = present - wanted

        if missing:
            logger.warning(
                f"Adding {len(missing)} zero-filled columns missing in prediction data"
                + (f" — first 10: {sorted(missing)[:10]}"
                   if len(missing) > 10 else f": {sorted(missing)}")
            )
            for col in missing:
                X_pred[col] = 0
        if extra:
            logger.warning(
                f"Dropping {len(extra)} prediction-only columns"
                + (f" — first 10: {sorted(extra)[:10]}"
                   if len(extra) > 10 else f": {sorted(extra)}")
            )
            X_pred = X_pred.drop(columns=list(extra))

        X_pred = X_pred[training]
        logger.info(f"Aligned features: {X_pred.shape}")
        return X_pred

    # ─────────────────────────────────────────────────────────────────────
    # SCALING — only for logistic
    # ─────────────────────────────────────────────────────────────────────
    def maybe_scale(self, X):
        if self.family != 'logistic':
            return X
        if self.scaler is None:
            raise RuntimeError("Logistic scaler not loaded")
        arr = self.scaler.transform(X).astype(np.float32)
        return pd.DataFrame(arr, columns=X.columns, index=X.index)

    # ─────────────────────────────────────────────────────────────────────
    # PREDICT
    # ─────────────────────────────────────────────────────────────────────
    def predict_proba(self, X):
        proba = self.model.predict_proba(X)[:, 1]
        logger.info(
            f"Predictions: n={len(proba)}, "
            f"min={proba.min():.4f}, mean={proba.mean():.4f}, "
            f"max={proba.max():.4f}"
        )
        return np.asarray(proba)

    # ─────────────────────────────────────────────────────────────────────
    # PER-ROW SHAP — top-N positive + top-N negative contributors per lead
    # ─────────────────────────────────────────────────────────────────────
    def compute_per_row_shap(self, X, top_n_per_direction=5, max_rows=None):
        """
        For every row in X, identify the top N features that pushed the
        score UP (positive SHAP) and the top N that pushed it DOWN
        (negative SHAP).  Returns a long-format DataFrame with one row
        per (lead, top-feature) pair, ready to write to TD.

        Returns the long-format DF, the numpy SHAP matrix (for callers
        that want to compute their own aggregates), and the row-position
        index that was actually scored (so callers can join probabilities
        back to the right rows when max_rows truncates).

        Performance: uses batched computation (50K rows at a time) with
        GC between batches to control memory.  The long-format builder
        is fully vectorised (no Python loops).
        """
        import gc
        try:
            import shap
        except ImportError:
            os.system(f"{sys.executable} -m pip install --user shap")
            import shap

        # Sample if requested
        if max_rows and len(X) > max_rows:
            logger.info(
                f"SHAP: sampling {max_rows} of {len(X)} rows "
                "(set shap_max_rows=0 to score every lead)"
            )
            X_shap = X.sample(n=max_rows, random_state=24)
        else:
            X_shap = X
        sample_index_pos = np.array(
            [X.index.get_loc(ix) for ix in X_shap.index]
        )

        n_total = len(X_shap)
        logger.info(
            f"Computing SHAP on {n_total} rows "
            f"(top {top_n_per_direction} positive + top {top_n_per_direction} negative)"
        )

        # Build the right explainer
        if self.family == 'logistic':
            explainer = shap.LinearExplainer(self.model, X_shap)
        else:
            explainer = shap.TreeExplainer(self.model)

        # Batched SHAP: 50K rows at a time to control memory + show progress
        BATCH_SIZE = 50_000
        shap_chunks = []
        for start in range(0, n_total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, n_total)
            batch = X_shap.iloc[start:end]
            logger.info(f"SHAP batch {start:,}–{end:,} of {n_total:,}")
            sv = explainer.shap_values(batch)
            if isinstance(sv, list):
                sv = sv[1] if len(sv) > 1 else sv[0]
            shap_chunks.append(np.asarray(sv))
            del sv, batch
            gc.collect()

        shap_values = np.vstack(shap_chunks)
        del shap_chunks
        gc.collect()

        # Build long-format top-N DataFrame
        long_df = self._build_topn_long_df(
            X_shap, shap_values, top_n_per_direction
        )
        logger.info(f"Per-row SHAP long-format rows: {len(long_df)}")
        return long_df, shap_values, sample_index_pos

    def _build_topn_long_df(self, X, shap_values, top_n):
        """
        Vectorised construction of the long-format top-N table.

        For each row we take the top-N positive-SHAP and top-N
        negative-SHAP feature indices using np.argpartition (O(n)
        per row; meaningfully faster than argsort on wide feature sets).

        Output columns:
          row_id (positional), feature_name, feature_value,
          shap_value, direction ('positive'|'negative'),
          rank_within_direction (1..N)
        """
        n_rows, n_feats = shap_values.shape
        feat_arr        = np.asarray(self.feature_names)
        X_arr           = X.to_numpy()

        if top_n >= n_feats:
            logger.warning(
                f"top_n_per_direction ({top_n}) >= n_features ({n_feats}); "
                "reducing to n_features - 1"
            )
            top_n = max(1, n_feats - 1)

        # ── Top-N positive contributors (largest +SHAP values) ──────────
        # argpartition with -top_n puts the top_n largest at the end (unsorted)
        top_pos_unsorted = np.argpartition(shap_values, -top_n, axis=1)[:, -top_n:]
        # Then sort that small slice descending for ranking
        order = np.argsort(
            -np.take_along_axis(shap_values, top_pos_unsorted, axis=1),
            axis=1,
        )
        top_pos_idx = np.take_along_axis(top_pos_unsorted, order, axis=1)

        # ── Top-N negative contributors (most-negative SHAP) ────────────
        top_neg_unsorted = np.argpartition(shap_values, top_n, axis=1)[:, :top_n]
        order = np.argsort(
            np.take_along_axis(shap_values, top_neg_unsorted, axis=1),
            axis=1,
        )
        top_neg_idx = np.take_along_axis(top_neg_unsorted, order, axis=1)

        # Mask out non-positive entries from the "positive" side and
        # non-negative entries from the "negative" side — a row may have
        # fewer than N actually-positive (or actually-negative) SHAP values
        # if most contributions point one way.  Keeping spurious zeros in
        # would mislead Sales ("this 0.0001 feature pushed you up" is noise).
        rows_idx = np.arange(n_rows)[:, None]
        pos_shaps = shap_values[rows_idx, top_pos_idx]
        neg_shaps = shap_values[rows_idx, top_neg_idx]

        # Build the two halves separately then concat — fully vectorised
        pos_df = self._vectorised_topn_block(
            row_idx_block=top_pos_idx, shap_block=pos_shaps,
            X_arr=X_arr, feat_arr=feat_arr, direction='positive',
            keep_mask=pos_shaps > 0,
        )
        neg_df = self._vectorised_topn_block(
            row_idx_block=top_neg_idx, shap_block=neg_shaps,
            X_arr=X_arr, feat_arr=feat_arr, direction='negative',
            keep_mask=neg_shaps < 0,
        )

        long_df = pd.concat([pos_df, neg_df], ignore_index=True)
        if long_df.empty:
            return long_df
        long_df = long_df.sort_values(
            ['row_id', 'direction', 'rank_within_direction']
        ).reset_index(drop=True)
        return long_df

    @staticmethod
    def _vectorised_topn_block(row_idx_block, shap_block, X_arr,
                               feat_arr, direction, keep_mask):
        """
        Fully vectorised: no Python loops.  Builds the long-format
        DataFrame using numpy broadcasting + boolean indexing.
        ~100x faster than the per-row loop on 358K rows.
        """
        n_rows, top_n = row_idx_block.shape

        # Meshgrid for row_ids and ranks
        row_ids = np.repeat(np.arange(n_rows), top_n)
        ranks   = np.tile(np.arange(1, top_n + 1), n_rows)

        # Flatten feature indices and shap values
        f_idxs     = row_idx_block.ravel()
        shap_vals  = shap_block.ravel()
        mask_flat  = keep_mask.ravel()

        # Apply mask (only keep entries that actually point in the right direction)
        row_ids   = row_ids[mask_flat]
        ranks     = ranks[mask_flat]
        f_idxs    = f_idxs[mask_flat]
        shap_vals = shap_vals[mask_flat]

        if len(row_ids) == 0:
            return pd.DataFrame()

        # Vectorised feature name + value lookups
        feat_names  = feat_arr[f_idxs]
        feat_values = X_arr[row_ids, f_idxs]

        return pd.DataFrame({
            'row_id':                row_ids,
            'feature_name':          feat_names,
            'feature_value':         feat_values,
            'shap_value':            shap_vals,
            'direction':             direction,
            'rank_within_direction': ranks,
        })

    # ─────────────────────────────────────────────────────────────────────
    # PSI between training and current prediction distributions
    # ─────────────────────────────────────────────────────────────────────
    def calculate_psi(self, predictions):
        """
        PSI against the training prediction-bin distribution loaded
        in load_training_metadata().  Returns None if training bins
        weren't available.
        """
        if self.train_pred_bins is None:
            return None

        bin_edges  = np.arange(0.0, 1.1, 0.1)
        bin_labels = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5',
                      '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']

        actual_binned = pd.cut(predictions, bins=bin_edges,
                               labels=bin_labels, include_lowest=True)
        actual_pcts = (actual_binned.value_counts().sort_index() /
                       len(predictions)).reindex(bin_labels, fill_value=0).values

        expected_pcts = np.zeros(len(bin_labels))
        for i, lbl in enumerate(bin_labels):
            row = self.train_pred_bins[self.train_pred_bins['bin_range'] == lbl]
            if not row.empty:
                expected_pcts[i] = float(row.iloc[0]['percentage']) / 100.0

        eps = 1e-4
        expected_pcts = np.where(expected_pcts == 0, eps, expected_pcts)
        actual_pcts   = np.where(actual_pcts   == 0, eps, actual_pcts)
        psi = float(np.sum((actual_pcts - expected_pcts) *
                           np.log(actual_pcts / expected_pcts)))

        if psi < 0.10:
            logger.info(f"PSI = {psi:.4f} → no significant shift (<0.10)")
        elif psi < 0.25:
            logger.warning(f"PSI = {psi:.4f} → moderate shift (0.10–0.25)")
        else:
            logger.warning(f"PSI = {psi:.4f} → SIGNIFICANT shift (≥0.25), retrain")
        return round(psi, 4)