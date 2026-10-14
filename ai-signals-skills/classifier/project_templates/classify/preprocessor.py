# ─────────────────────────────────────────────────────────────────────────────
# preprocessor.py
#
# Model-agnostic data preprocessing & feature-selection utilities.
#
# Responsibilities:
#   - Drop ID / target / user-blacklisted columns
#   - Numeric coercion + mean imputation (numeric)
#   - "missing" fill + one-hot encoding (categorical)
#   - Pairwise-correlation based feature drop
#   - Feature-feature and feature-target correlation matrices
#   - VIF (on a sample)
#   - PSI (train vs test score drift)
#
# This module contains NO model-specific logic.  The same Preprocessor
# instance is used regardless of which estimator (logistic / xgboost /
# catboost) is selected downstream.
# ─────────────────────────────────────────────────────────────────────────────

import os
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Preprocessor:
    """
    Generic preprocessing pipeline shared by all model types.

    Note on scaling:
      Logistic regression requires StandardScaler (for coefficient
      interpretability and saga solver convergence).  Tree-based models
      (XGBoost, CatBoost) do NOT need scaling.  Scaling is therefore
      handled INSIDE the model classes (models.py), not here.
    """

    # Fallback drop list when no columns_to_drop is passed from Digdag
    _DEFAULT_DROP_COLS = ['session_id']

    # Columns that are commonly stored as strings but are actually numeric
    # Extend this list as new pipelines encounter fresh cases.
    _FORCE_NUMERIC_COLS = [
        'median_income_per_capita',
        'median_household_income',
        'hh_65_plus',
    ]

    def __init__(self):
        self.training_dummy_columns = []
        self.feature_corr_df        = pd.DataFrame()
        self.target_corr_df         = pd.DataFrame()
        self.corr_drop_report       = pd.DataFrame()

    # ─────────────────────────────────────────────────────────────────────
    # PREPROCESS
    # ─────────────────────────────────────────────────────────────────────
    def preprocess(self, df, is_training=True, columns_to_drop=None,
                   impute_numerics=True, require_target=None):
        """
        Clean + one-hot encode.  Returns (X, y).

        columns_to_drop: list from Digdag env (via train.py) or None to
                         fall back to _DEFAULT_DROP_COLS.  The target
                         column is always appended regardless of source
                         when present in df.

        impute_numerics: if True (default), fill NaN in numeric columns
                         with the column mean (required for logistic
                         regression, which cannot consume NaN).  If
                         False, leave numeric NaNs untouched so XGBoost
                         / CatBoost can use their native missing-value
                         handling — each learns a default split direction
                         for NaN at every node rather than imputing.

                         Categorical imputation (→ "missing" string) always
                         runs, because one-hot encoding can't produce a
                         dummy column from NaN.  This is harmless — it
                         preserves the missingness signal via a
                         {col}_missing dummy.

                         ±inf is always replaced with NaN (then possibly
                         imputed or left for the model, depending on the
                         flag).

        require_target:  whether the target column must exist in df.
                         None (default) → derives from is_training:
                           training (True) requires target,
                           prediction (False) doesn't.
                         Override explicitly when needed.

                         At predict time, source feature tables have no
                         label column and we just return (X, None).
        """
        # If require_target wasn't specified, default to is_training.
        # This preserves the training contract while making prediction
        # not blow up on missing labels.
        if require_target is None:
            require_target = is_training

        logger.info(
            f"Preprocessing (is_training={is_training}, "
            f"impute_numerics={impute_numerics}, "
            f"require_target={require_target})"
        )

        target = os.environ.get('target_variable', 'won')

        drop_list = list(columns_to_drop) if columns_to_drop is not None \
                    else list(self._DEFAULT_DROP_COLS)

        # Always include target in the drop list when it's present in df.
        # Prevents accidental leakage at training; harmless at predict time
        # since the column simply isn't there to drop.
        if target not in drop_list:
            drop_list.append(target)

        existing_cols_to_drop = [c for c in drop_list if c in df.columns]
        missing_cols          = [c for c in drop_list if c not in df.columns]

        logger.info(f"Columns to drop (found):   {existing_cols_to_drop}")
        if missing_cols:
            logger.warning(f"Columns to drop (missing): {missing_cols}")

        # Target handling: hard-fail for training (no labels = nothing to
        # learn from), warn-and-continue for prediction.
        if target in df.columns:
            y = df[target]
            logger.info(f"Target column '{target}' found in df")
            logger.info(f"Target distribution:\n{y.value_counts()}")
        else:
            if require_target:
                raise ValueError(
                    f"Target variable '{target}' not found in DataFrame "
                    f"(required because require_target=True). "
                    f"If this is a prediction run, pass require_target=False "
                    f"or call from a context where is_training=False."
                )
            y = None
            logger.info(
                f"Target column '{target}' not in df — proceeding without "
                "labels (prediction mode)"
            )

        X = df.drop(existing_cols_to_drop, axis=1, errors='ignore')

        logger.info(f"Features shape: {X.shape}")

        # Coerce known stringy-numeric columns — this may introduce NaNs
        # that didn't exist before (strings that couldn't parse).
        for col in [c for c in self._FORCE_NUMERIC_COLS if c in X.columns]:
            X[col] = pd.to_numeric(X[col], errors='coerce')

        num_cols = X.select_dtypes(include=['number']).columns
        n_nulls_before = int(X[num_cols].isna().sum().sum()) if len(num_cols) else 0

        if impute_numerics:
            # Logistic regression path: mean-impute so LR sees no NaN
            X[num_cols] = X[num_cols].fillna(X[num_cols].mean())
            logger.info(
                f"Numeric imputation: filled {n_nulls_before} NaN(s) "
                f"across {len(num_cols)} numeric columns with column means"
            )
        else:
            # Tree-model path: leave NaN in place so XGBoost / CatBoost
            # can use their native missing-value handling.  Log the null
            # profile so we have a record of what the model will see.
            if n_nulls_before > 0:
                nulls_per_col = X[num_cols].isna().sum()
                top_nulls = nulls_per_col[nulls_per_col > 0].sort_values(ascending=False)
                logger.info(
                    f"Numeric imputation: SKIPPED (impute_numerics=False). "
                    f"{n_nulls_before} NaN(s) passing to model natively. "
                    f"Top null columns:\n{top_nulls.head(10).to_string()}"
                )
            else:
                logger.info("Numeric imputation: SKIPPED (no NaNs to handle)")

        # Categorical imputation ALWAYS runs.  One-hot encoding turns NaN
        # into all-zero rows silently (losing the missingness signal), so
        # we fill with literal "missing" first and let it become an
        # explicit {col}_missing dummy.
        cat_cols = [c for c in X.columns if c not in num_cols]
        logger.info(f"Categorical columns found: {list(cat_cols)}")
        X[cat_cols] = X[cat_cols].fillna("missing")

        if cat_cols:
            logger.info(f"One-hot encoding {len(cat_cols)} categorical columns")
            X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
            if is_training:
                self.training_dummy_columns = list(X.columns)
                logger.info(
                    f"Stored {len(self.training_dummy_columns)} training "
                    f"dummy columns for predictor alignment"
                )

        # ±inf handling: always replace with NaN so downstream doesn't
        # choke.  What happens next depends on impute_numerics:
        #   - If True:  previous .fillna(mean) already ran but infs slipped
        #               through → fall through to fillna(0) safety net.
        #   - If False: we want to KEEP NaN so the tree model sees it.
        X.replace([np.inf, -np.inf], np.nan, inplace=True)

        if impute_numerics:
            # Safety net: zero-fill any NaN created by the inf replacement
            # above, or any dummy columns that somehow ended up NaN.
            X = X.fillna(0)
        else:
            # Tree path: leave numeric NaNs alone, but fill NaNs in dummy
            # columns with 0 (a dummy column should never be NaN; if it is,
            # something's wrong upstream and 0 is the correct default).
            dummy_cols = [c for c in X.columns if c not in num_cols]
            if dummy_cols:
                X[dummy_cols] = X[dummy_cols].fillna(0)

        # Ensure dummy columns are int (get_dummies may emit bool)
        bool_cols = X.select_dtypes(include=['bool']).columns
        if len(bool_cols) > 0:
            X[bool_cols] = X[bool_cols].astype(int)

        n_nulls_final = int(X.isna().sum().sum())
        logger.info(
            f"Final preprocessed shape: {X.shape}  "
            f"(NaNs remaining: {n_nulls_final})"
        )
        return X, y

        # # Coerce known stringy-numeric columns — this may introduce NaNs
        # # that didn't exist before (strings that couldn't parse).
        # for col in [c for c in self._FORCE_NUMERIC_COLS if c in X.columns]:
        #     X[col] = pd.to_numeric(X[col], errors='coerce')

        # num_cols = X.select_dtypes(include=['number']).columns
        # n_nulls_before = int(X[num_cols].isna().sum().sum()) if len(num_cols) else 0

        # if impute_numerics:
        #     # Logistic regression path: mean-impute so LR sees no NaN
        #     X[num_cols] = X[num_cols].fillna(X[num_cols].mean())
        #     logger.info(
        #         f"Numeric imputation: filled {n_nulls_before} NaN(s) "
        #         f"across {len(num_cols)} numeric columns with column means"
        #     )
        # else:
        #     # Tree-model path: leave NaN in place so XGBoost / CatBoost
        #     # can use their native missing-value handling.  Log the null
        #     # profile so we have a record of what the model will see.
        #     if n_nulls_before > 0:
        #         nulls_per_col = X[num_cols].isna().sum()
        #         top_nulls = nulls_per_col[nulls_per_col > 0].sort_values(ascending=False)
        #         logger.info(
        #             f"Numeric imputation: SKIPPED (impute_numerics=False). "
        #             f"{n_nulls_before} NaN(s) passing to model natively. "
        #             f"Top null columns:\n{top_nulls.head(10).to_string()}"
        #         )
        #     else:
        #         logger.info("Numeric imputation: SKIPPED (no NaNs to handle)")

        # # Categorical imputation ALWAYS runs.  One-hot encoding turns NaN
        # # into all-zero rows silently (losing the missingness signal), so
        # # we fill with literal "missing" first and let it become an
        # # explicit {col}_missing dummy.
        # cat_cols = [c for c in X.columns if c not in num_cols]
        # logger.info(f"Categorical columns found: {list(cat_cols)}")
        # X[cat_cols] = X[cat_cols].fillna("missing")

        # if cat_cols:
        #     logger.info(f"One-hot encoding {len(cat_cols)} categorical columns")
        #     X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
        #     if is_training:
        #         self.training_dummy_columns = list(X.columns)
        #         logger.info(
        #             f"Stored {len(self.training_dummy_columns)} training "
        #             f"dummy columns for predictor alignment"
        #         )

        # # ±inf handling: always replace with NaN so downstream doesn't
        # # choke.  What happens next depends on impute_numerics:
        # #   - If True:  previous .fillna(mean) already ran but infs slipped
        # #               through → fall through to fillna(0) safety net.
        # #   - If False: we want to KEEP NaN so the tree model sees it.
        # X.replace([np.inf, -np.inf], np.nan, inplace=True)

        # if impute_numerics:
        #     # Safety net: zero-fill any NaN created by the inf replacement
        #     # above, or any dummy columns that somehow ended up NaN.
        #     X = X.fillna(0)
        # else:
        #     # Tree path: leave numeric NaNs alone, but fill NaNs in dummy
        #     # columns with 0 (a dummy column should never be NaN; if it is,
        #     # something's wrong upstream and 0 is the correct default).
        #     dummy_cols = [c for c in X.columns if c not in num_cols]
        #     if dummy_cols:
        #         X[dummy_cols] = X[dummy_cols].fillna(0)

        # # Ensure dummy columns are int (get_dummies may emit bool)
        # bool_cols = X.select_dtypes(include=['bool']).columns
        # if len(bool_cols) > 0:
        #     X[bool_cols] = X[bool_cols].astype(int)

        # n_nulls_final = int(X.isna().sum().sum())
        # logger.info(
        #     f"Final preprocessed shape: {X.shape}  "
        #     f"(NaNs remaining: {n_nulls_final})"
        # )
        # return X, y

    # ─────────────────────────────────────────────────────────────────────
    # ALIGN TEST COLUMNS TO TRAIN
    # ─────────────────────────────────────────────────────────────────────
    @staticmethod
    def align_columns(X_train, X_test):
        """
        Make X_test have exactly the same columns (and order) as X_train.
        Missing dummies → filled with 0; extra dummies → dropped.
        """
        missing_in_test = [c for c in X_train.columns if c not in X_test.columns]
        extra_in_test   = [c for c in X_test.columns  if c not in X_train.columns]

        if missing_in_test:
            logger.warning(f"Adding {len(missing_in_test)} zero-filled cols to X_test: {missing_in_test}")
            for col in missing_in_test:
                X_test[col] = 0
        if extra_in_test:
            logger.warning(f"Dropping {len(extra_in_test)} unseen cols from X_test: {extra_in_test}")
            X_test = X_test.drop(columns=extra_in_test)

        return X_test[X_train.columns]

    # ─────────────────────────────────────────────────────────────────────
    # CORRELATION-BASED FEATURE DROP
    # ─────────────────────────────────────────────────────────────────────
    def drop_highly_correlated(self, X, threshold=0.80):
        """
        Note on NaN: pandas .corr() handles NaN via pairwise-complete
        observations.  Zero-variance or all-NaN columns produce NaN in
        the correlation matrix, and `NaN > threshold` evaluates False,
        so those columns are silently skipped (not dropped).  This is
        the right behaviour for tree-model paths where we deliberately
        leave NaNs in place.
        """
        logger.info(f"Dropping features with pairwise correlation > {threshold}")

        corr_matrix = X.corr(method='pearson').abs()

        # Diagnostic: log any columns that have all-NaN correlations, so
        # we know why they weren't considered in the drop logic.
        all_nan_cols = corr_matrix.columns[corr_matrix.isna().all()].tolist()
        if all_nan_cols:
            logger.warning(
                f"{len(all_nan_cols)} column(s) have all-NaN correlations "
                f"(likely zero-variance or all-null): {all_nan_cols[:10]}"
                + (" ..." if len(all_nan_cols) > 10 else "")
            )

        upper_tri   = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        to_drop     = set()
        drop_report = []

        for col in upper_tri.columns:
            high_corr_partners = upper_tri.index[upper_tri[col] > threshold].tolist()
            for partner in high_corr_partners:
                if col not in to_drop and partner not in to_drop:
                    corr_val = corr_matrix.loc[partner, col]
                    to_drop.add(col)
                    drop_report.append({
                        'kept_feature':    partner,
                        'dropped_feature': col,
                        'correlation':     round(corr_val, 4),
                    })
                    logger.info(f"  Dropping '{col}' (corr={corr_val:.4f} with '{partner}')")

        drop_report_df = pd.DataFrame(drop_report)
        X_reduced      = X.drop(columns=list(to_drop), errors='ignore')

        logger.info(
            f"Features before: {X.shape[1]}, after: {X_reduced.shape[1]}, "
            f"dropped: {len(to_drop)}"
        )

        self.corr_drop_report = drop_report_df
        return X_reduced, list(to_drop), drop_report_df

    # ─────────────────────────────────────────────────────────────────────
    # CORRELATION MATRICES (reporting only)
    # ─────────────────────────────────────────────────────────────────────
    def compute_correlations(self, X, target=None):
        logger.info("Calculating feature correlation matrices")

        corr_matrix = X.corr(method='pearson')
        corr_long = (
            corr_matrix
            .reset_index()
            .melt(id_vars='index', var_name='feature_b', value_name='correlation')
            .rename(columns={'index': 'feature_a'})
        )
        corr_long = corr_long[corr_long['feature_a'] < corr_long['feature_b']]
        corr_long['abs_correlation'] = corr_long['correlation'].abs()
        corr_long = corr_long.sort_values('abs_correlation', ascending=False).reset_index(drop=True)

        target_corr_df = pd.DataFrame()
        if target is not None:
            tc = X.corrwith(target.astype(float), method='pearson')
            target_corr_df = pd.DataFrame({
                'feature':                tc.index,
                'target_correlation':     tc.values,
                'abs_target_correlation': tc.abs().values,
            }).sort_values('abs_target_correlation', ascending=False).reset_index(drop=True)
            target_corr_df['rank'] = target_corr_df.index + 1
            logger.info(
                f"Top 10 by target corr:\n"
                f"{target_corr_df.head(10)[['feature','target_correlation']].to_string()}"
            )

        self.feature_corr_df = corr_long
        self.target_corr_df  = target_corr_df
        return corr_long, target_corr_df

    # ─────────────────────────────────────────────────────────────────────
    # VIF
    # ─────────────────────────────────────────────────────────────────────
    @staticmethod
    def compute_vif(X, max_sample=100_000):
        """
        Multicollinearity report.  Note: VIF is a reporting diagnostic only
        — tree models don't use it.  statsmodels' variance_inflation_factor
        does not accept NaN, so we drop rows with any NaN from the sampled
        copy before computing.  This affects ONLY the VIF output, not the
        training data.
        """
        from statsmodels.stats.outliers_influence import variance_inflation_factor

        sample_size = min(max_sample, len(X))
        X_sample    = X.sample(n=sample_size, random_state=42) if sample_size < len(X) else X

        # Drop any rows containing NaN (tree-model path leaves them in)
        X_clean = X_sample.dropna()
        n_dropped = len(X_sample) - len(X_clean)
        if n_dropped > 0:
            logger.info(
                f"VIF: dropping {n_dropped} / {len(X_sample)} rows with NaN "
                f"before computation (report-only, doesn't affect model)"
            )

        if len(X_clean) < max(len(X_clean.columns) + 1, 10):
            logger.warning(
                f"VIF: too few complete rows ({len(X_clean)}) for "
                f"{X_clean.shape[1]} features — returning empty VIF"
            )
            return pd.DataFrame(columns=['feature', 'VIF'])

        vif_df = pd.DataFrame()
        vif_df['feature'] = X_clean.columns
        vif_df['VIF']     = [
            variance_inflation_factor(X_clean.values, i)
            for i in range(X_clean.shape[1])
        ]
        logger.info(f"VIF completed:\n{vif_df.sort_values('VIF', ascending=False).head(10)}")
        return vif_df

    # ─────────────────────────────────────────────────────────────────────
    # PSI — Population Stability Index between train & test score dists
    # ─────────────────────────────────────────────────────────────────────
    @staticmethod
    def compute_psi(expected, actual, bins=10):
        expected = np.array(expected)
        actual   = np.array(actual)
        breakpoints    = np.percentile(expected, np.arange(0, 101, 100 / bins))
        expected_bins  = np.histogram(expected, bins=breakpoints)[0] / len(expected)
        actual_bins    = np.histogram(actual,   bins=breakpoints)[0] / len(actual)
        expected_bins  = np.where(expected_bins == 0, 0.0001, expected_bins)
        actual_bins    = np.where(actual_bins   == 0, 0.0001, actual_bins)
        return float(np.sum((actual_bins - expected_bins) * np.log(actual_bins / expected_bins)))