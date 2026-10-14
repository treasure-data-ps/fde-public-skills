# ─────────────────────────────────────────────────────────────────────────────
# models.py
#
# Model factory.  Each class encapsulates:
#   - Optuna search space (model-specific hyperparameters)
#   - fit() / predict_proba()
#   - Native feature importance
#   - Persistence artifacts to TD:
#       Logistic  → coefficient table + scaler_params table
#       XGBoost   → td-model-store (binary via pytd) + gain-based importance
#       CatBoost  → td-model-store + gain-based importance
#
# All three share the same evaluation path (see explainer.py), so the
# orchestrator (train.py) is mostly model-agnostic.
#
# ModelFactory.create(model_type, cfg) → BaseLeadScoringModel
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import datetime
import logging
import multiprocessing
from abc import ABC, abstractmethod
import gc
import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    make_scorer, fbeta_score, roc_auc_score,
    average_precision_score, precision_score, recall_score, log_loss,
)

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# OPTUNA CALLBACK (module-level → picklable across worker processes)
# ─────────────────────────────────────────────────────────────────────────────
def _make_optuna_callback():
    def cb(study, trial):
        if trial.state.name == 'COMPLETE':
            logger.info(
                f"Trial {trial.number:03d} | score={trial.value:.4f} | "
                f"params={trial.params} | best_so_far={study.best_value:.4f}"
            )
    return cb


def _make_scorer(metric='fbeta', beta=0.5):
    """Build a sklearn scorer and Optuna direction for the given metric name."""
    if metric == 'fbeta':
        return make_scorer(fbeta_score, beta=beta), 'maximize'
    elif metric == 'auc_roc':
        return make_scorer(roc_auc_score, needs_proba=True), 'maximize'
    elif metric == 'auc_pr':
        return make_scorer(average_precision_score, needs_proba=True), 'maximize'
    elif metric == 'precision':
        return make_scorer(precision_score, zero_division=0), 'maximize'
    elif metric == 'recall':
        return make_scorer(recall_score, zero_division=0), 'maximize'
    elif metric == 'log_loss':
        return make_scorer(log_loss, needs_proba=True, greater_is_better=False), 'maximize'
    else:
        logger.warning(f"Unknown optuna_metric '{metric}', falling back to fbeta")
        return make_scorer(fbeta_score, beta=beta), 'maximize'


def _n_jobs():
    return max(1, multiprocessing.cpu_count() - 1)


# ═════════════════════════════════════════════════════════════════════════════
# ABSTRACT BASE
# ═════════════════════════════════════════════════════════════════════════════
class BaseLeadScoringModel(ABC):
    """
    Abstract base.  Concrete subclasses override:
      - family             (class attr: 'logistic' | 'xgboost' | 'catboost')
      - requires_scaling   (class attr: bool)
      - requires_imputation (class attr: bool)
          Logistic cannot consume NaN → must impute.
          XGBoost / CatBoost handle NaN natively via learned default
          split directions → should NOT impute (imputation destroys the
          missingness signal and routes missing rows toward the centre
          of the distribution, where they often don't belong).
      - _build_estimator(params)        → untrained estimator
      - _suggest_params(trial)          → Optuna suggestion dict
      - _fit_final(estimator, X, y)     → fits in place
      - save_artifacts(data_handler, session_id, cfg, env_vars)
      - build_feature_importance_df(session_id)
    """

    family              = 'base'
    requires_scaling    = False
    requires_imputation = True   # safe default: subclasses opt out
    requires_corr_drop   = True

    def __init__(self, cfg):
        self.cfg           = cfg
        self.model         = None
        self.scaler        = StandardScaler() if self.requires_scaling else None
        self.feature_names = None
        self.best_params   = None
        self.optuna_trials_df = pd.DataFrame()

    # ── Public fit API ──────────────────────────────────────────────────
    def fit(self, X_train, y_train):
        """
        Tune via Optuna (if n_trials > 0), then fit the final estimator on
        the full training set.  Returns self.
        """
        if self.cfg.get('n_trials', 0) > 0:
            self._tune_optuna(X_train, y_train)
        else:
            logger.info("n_trials <= 0 → skipping Optuna, using default params")
            self.best_params = self._default_params()

        logger.info(f"Fitting final {self.family} model with params: {self.best_params}")
        self.model = self._build_estimator(self.best_params)
        self._fit_final(self.model, X_train, y_train)
        self.feature_names = list(X_train.columns)
        return self

    def predict_proba(self, X):
        """Return positive-class probabilities."""
        return self.model.predict_proba(X)[:, 1]

    # ── Scaling (delegated to preprocessor.py isn't a fit — LR owns its own
    #    scaler).  Tree models override these to be no-ops.
    def scale_fit_transform(self, X):
        if not self.requires_scaling:
            return X
        logger.info(f"Fitting StandardScaler on {X.shape[1]} features")
        arr = self.scaler.fit_transform(X)
        return pd.DataFrame(arr, columns=X.columns, index=X.index)

    def scale_transform(self, X):
        if not self.requires_scaling:
            return X
        arr = self.scaler.transform(X)
        return pd.DataFrame(arr, columns=X.columns, index=X.index)

    def subset_scaler(self, kept_cols, original_cols):
        """After correlation drop, trim scaler params so we avoid double-scaling."""
        if not self.requires_scaling:
            return
        kept_mask = np.array([c in kept_cols for c in original_cols])
        self.scaler.mean_          = self.scaler.mean_[kept_mask]
        self.scaler.scale_         = self.scaler.scale_[kept_mask]
        self.scaler.var_           = self.scaler.var_[kept_mask]
        self.scaler.n_features_in_ = len(kept_cols)
        logger.info(
            f"Scaler subset: {kept_mask.sum()} of {len(original_cols)} features retained"
        )

    # ── Optuna orchestration ────────────────────────────────────────────
    def _tune_optuna(self, X_train, y_train):
        if not OPTUNA_AVAILABLE:
            logger.warning("Optuna not available — using default params")
            self.best_params = self._default_params()
            return

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        optuna_metric = self.cfg.get('optuna_metric', 'fbeta')
        scorer, direction = _make_scorer(
            optuna_metric, beta=self.cfg.get('fbeta_beta', 0.5),
        )
        cv = StratifiedKFold(
            n_splits=int(self.cfg.get('cv_folds', 3)),
            shuffle=True, random_state=24,
        )
        n_trials   = int(self.cfg.get('n_trials', 3))
        n_startup  = min(10, max(2, n_trials // 3))

        logger.info(
            f"Optuna TPE search | family={self.family} | n_trials={n_trials} | "
            f"metric={optuna_metric} | cv_folds={cv.n_splits}"
        )

        def objective(trial):
            params = self._suggest_params(trial)
            est = self._build_estimator(params)

            fold_scores = []
            for fold_idx, (tr_idx, val_idx) in enumerate(cv.split(X_train, y_train)):
                X_tr,  y_tr  = X_train.iloc[tr_idx],  y_train.iloc[tr_idx]
                X_val, y_val = X_train.iloc[val_idx], y_train.iloc[val_idx]

                if len(np.unique(y_tr)) < 2:
                    raise optuna.exceptions.TrialPruned()

                self._fit_final(est, X_tr, y_tr, eval_set=[(X_val, y_val)])
                score = scorer(est, X_val, y_val)
                fold_scores.append(score)

                trial.report(np.mean(fold_scores), step=fold_idx)
                if trial.should_prune():
                  del est, X_tr, y_tr, X_val, y_val
                  gc.collect()
                  raise optuna.exceptions.TrialPruned()

            del est
            gc.collect()
            return float(np.mean(fold_scores))

        sampler = optuna.samplers.TPESampler(
            seed=24, n_startup_trials=n_startup, multivariate=True
        )
        pruner = optuna.pruners.MedianPruner(
            n_startup_trials=n_startup, n_warmup_steps=1
        )
        study = optuna.create_study(
            direction=direction,
            sampler=sampler,
            pruner=pruner,
            study_name=f'classify_{self.family}',
        )

        # Tree models' internal n_jobs already saturate cores → run Optuna
        # trials serially for them. LR uses 1 internal thread so we can
        # parallelise trials safely.
        optuna_n_jobs = _n_jobs() if self.family == 'logistic' else 1

        study.optimize(
            objective,
            n_trials=n_trials,
            n_jobs=optuna_n_jobs,
            # timeout=cfg.get('optuna_timeout_sec'),  # optional, e.g. 1800 = 30 min
            show_progress_bar=False,
            callbacks=[_make_optuna_callback()],
        )

        completed = [t for t in study.trials
                     if t.state == optuna.trial.TrialState.COMPLETE]
        if not completed:
            logger.warning("All Optuna trials pruned/failed — using defaults")
            self.best_params = self._default_params()
            return

        self.best_params = self._resolve_params_from_trial(study.best_trial)
        logger.info(f"Best trial score: {study.best_trial.value:.4f}")
        logger.info(f"Best params: {self.best_params}")

        try:
            importances = optuna.importance.get_param_importances(study)
            logger.info(f"Param importances: {importances}")
        except Exception:
            pass

        self.optuna_trials_df = study.trials_dataframe()

    # ── Abstract hooks ──────────────────────────────────────────────────
    @abstractmethod
    def _build_estimator(self, params): ...
    @abstractmethod
    def _suggest_params(self, trial):   ...
    @abstractmethod
    def _default_params(self):          ...
    @abstractmethod
    def _fit_final(self, estimator, X, y, eval_set=None): ...

    def _resolve_params_from_trial(self, trial):
        """Default: best_trial.params == what _build_estimator expects.
        Subclasses (e.g. Logistic with class_weight_idx) override."""
        return dict(trial.params)

    # ── Persistence hooks — each model family has its own story ─────────
    @abstractmethod
    def save_artifacts(self, writer, session_id, cfg, env_vars):
        """
        Queue model-specific artifacts on the supplied ParallelWriter.
        Does NOT flush — the orchestrator owns flushing so that
        model-specific + shared writes all dispatch in one parallel burst.

        Logistic → coefficients + scaler_params
        XGBoost / CatBoost → td-model-store blob + gain importance
        """
        ...

    @abstractmethod
    def build_feature_importance_df(self, session_id):
        """Return a DataFrame with at least columns:
           feature_name, importance, rank
        Used as a complement to SHAP for tree models; LR returns empty."""
        ...


# ═════════════════════════════════════════════════════════════════════════════
# LOGISTIC REGRESSION
# ═════════════════════════════════════════════════════════════════════════════
class LogisticModel(BaseLeadScoringModel):
    """
    Precision-focused logistic regression (saga + l1/l2).

    Persistence:
      - coefficients → {trgt_table}
      - scaler_params → {table_prefix}scaler_params{suffix}
    """
    family              = 'logistic'
    requires_scaling    = True
    requires_imputation = True   # LR cannot consume NaN

    def __init__(self, cfg):
        super().__init__(cfg)
        self._class_weight_candidates = None  # built lazily from y_train

    # ── Class-weight candidates (precision-biased grid) ─────────────────
    def _build_class_weight_candidates(self, y_train):
        if self.cfg.get('class_balance_strategy', 'balanced') == 'none':
            return [None]
        neg = (y_train == 0).sum()
        pos = (y_train == 1).sum()
        natural_ratio = neg / max(pos, 1)
        logger.info(f"Class dist — neg={neg}, pos={pos}, ratio={natural_ratio:.2f}")
        multipliers = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
        candidates  = ['balanced']
        for m in multipliers:
          candidates.append({0: max(round(natural_ratio * m, 2), 0.01), 1: 1})
        return candidates

    def fit(self, X_train, y_train):
        # class_weight grid depends on y_train → build it before Optuna runs
        self._class_weight_candidates = self._build_class_weight_candidates(y_train)
        return super().fit(X_train, y_train)

    def _suggest_params(self, trial):
        C        = trial.suggest_float('C', 1e-3, 1e2, log=True)
        penalty  = trial.suggest_categorical('penalty', ['l1', 'l2'])
        cw_idx   = trial.suggest_categorical(
            'class_weight_idx',
            list(range(len(self._class_weight_candidates)))
        )
        return {
            'C':            C,
            'penalty':      penalty,
            'class_weight': self._class_weight_candidates[cw_idx],
        }

    def _resolve_params_from_trial(self, trial):
        # Map the idx back to the actual class_weight dict/string
        p = dict(trial.params)
        p['class_weight'] = self._class_weight_candidates[p.pop('class_weight_idx')]
        return p

    def _default_params(self):
        cw = 'balanced' if self.cfg.get('class_balance_strategy', 'balanced') == 'balanced' else None
        return {'C': 1.0, 'penalty': 'l2', 'class_weight': cw}

    def _build_estimator(self, params):
        return LogisticRegression(
            C=params['C'],
            penalty=params['penalty'],
            class_weight=params['class_weight'],
            solver='saga',
            max_iter=self.cfg.get('max_iter', 1000),
            tol=1e-3,
            random_state=24,
            n_jobs=1,  # parallelism lives in Optuna layer
        )

    def _fit_final(self, estimator, X, y, eval_set=None):
        estimator.fit(X, y)

    # ── Artifact DataFrames ─────────────────────────────────────────────
    def build_coefficients_df(self, session_id):
        coefs     = self.model.coef_[0]
        intercept = self.model.intercept_[0]
        n         = len(self.feature_names) + 1
        return pd.DataFrame({
            'session_id':      [session_id] * n,
            'feature':         ['Intercept'] + list(self.feature_names),
            'coefficient':     [intercept]   + list(coefs),
            'abs_coefficient': [abs(intercept)] + [abs(c) for c in coefs],
            'created_at':      [datetime.datetime.now()] * n,
        })

    def build_scaler_df(self, session_id):
        assert len(self.scaler.mean_) == len(self.feature_names), (
            f"Scaler mean_ ({len(self.scaler.mean_)}) != "
            f"feature_names ({len(self.feature_names)}). Check subset step."
        )
        n = len(self.feature_names)
        return pd.DataFrame({
            'session_id': [session_id] * n,
            'feature':    list(self.feature_names),
            'mean':       self.scaler.mean_,
            'scale':      self.scaler.scale_,
            'created_at': [datetime.datetime.now()] * n,
        })

    def build_feature_importance_df(self, session_id):
        """LR uses SHAP for importance — return empty so the generic
        importance-write path is skipped."""
        return pd.DataFrame()

    def save_artifacts(self, writer, session_id, cfg, env_vars):
        suffix = f"_{env_vars.get('unit', '').strip()}" if env_vars.get('unit') else ""
        tp     = cfg.get('table_prefix', '')

        writer.submit(
            self.build_coefficients_df(session_id),
            env_vars['trgt_table'],
        )
        writer.submit(
            self.build_scaler_df(session_id),
            f"{tp}scaler_params{suffix}",
        )


# ═════════════════════════════════════════════════════════════════════════════
# XGBOOST
# ═════════════════════════════════════════════════════════════════════════════
class XGBoostModel(BaseLeadScoringModel):
    """
    Precision-focused XGBoost classifier.

    Null handling: XGBoost's `tree_method='hist'` learns a default split
    direction for missing values at each node.  We deliberately do NOT
    impute upstream so this native handling kicks in — imputation would
    throw away the "missingness as signal" information and push missing
    rows toward the distribution centre, which is rarely where they
    actually belong.

    Persistence:
      - full binary model → td-model-store (plazma chunked VARCHAR)
      - native gain importance → {table_prefix}xgb_gain_importance{suffix}
    """
    family              = 'xgboost'
    requires_scaling    = False
    requires_imputation = False  # XGBoost handles NaN natively
    requires_corr_drop  = False   # ← new

    def _lazy_import_xgb(self):
        try:
            import xgboost as xgb
        except ImportError:
            os.system(f"{sys.executable} -m pip install --user xgboost")
            import xgboost as xgb
        return xgb

    def _scale_pos_weight(self, y):
        pos = max(int((y == 1).sum()), 1)
        neg = int((y == 0).sum())
        return neg / pos

    def _suggest_params(self, trial):
        cfg = self.cfg
        return {
            'n_estimators':     trial.suggest_int(
                'n_estimators',
                cfg.get('n_estimators_min', 100),
                cfg.get('n_estimators_max', 800),
            ),
            'max_depth':        trial.suggest_int(
                'max_depth',
                cfg.get('max_depth_min', 3),
                cfg.get('max_depth_max', 10),
            ),
            'learning_rate':    trial.suggest_float(
                'learning_rate',
                cfg.get('learning_rate_min', 0.01),
                cfg.get('learning_rate_max', 0.3),
                log=True,
            ),
            'subsample':        trial.suggest_float('subsample',        0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_int(  'min_child_weight', 1, 50),
            'reg_alpha':  trial.suggest_float('reg_alpha',  1e-3, 10.0, log=True),
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-3, 10.0, log=True),
            'gamma':            trial.suggest_float('gamma',      0.0, 10.0),
        }

    def _default_params(self):
        return {
            'n_estimators':     300,
            'max_depth':        6,
            'learning_rate':    0.1,
            'subsample':        0.9,
            'colsample_bytree': 0.9,
            'min_child_weight': 1,
            'reg_alpha':        1e-4,
            'reg_lambda':       1.0,
            'gamma':            0.0,
        }

    def _build_estimator(self, params):
        xgb = self._lazy_import_xgb()
        return xgb.XGBClassifier(
            **params,
            objective='binary:logistic',
            eval_metric=self.cfg.get('xgb_eval_metric', 'aucpr'),
            tree_method='hist',
            # scale_pos_weight=self._current_spw,  # set per-fit (see _fit_final)
            random_state=24,
            n_jobs=_n_jobs(),
            # use_label_encoder=False,
            verbosity=0,
        )

    def _fit_final(self, estimator, X, y, eval_set=None):
        if self.cfg.get('class_balance_strategy', 'balanced') == 'balanced':
            spw = self._scale_pos_weight(y)
            estimator.set_params(scale_pos_weight=spw)
        else:
            estimator.set_params(scale_pos_weight=1)

        fit_kwargs = {}
        es_rounds = int(self.cfg.get('early_stopping_rounds', 0))
        if eval_set is not None and es_rounds > 0:
            fit_kwargs['eval_set'] = eval_set
            fit_kwargs['early_stopping_rounds'] = es_rounds
            fit_kwargs['verbose'] = False
        estimator.fit(X, y, **fit_kwargs)

    def fit(self, X_train, y_train):
        # Seed scale_pos_weight with full-train ratio so _build_estimator
        # works even before the first _fit_final call during Optuna objective.
        # self._current_spw = self._scale_pos_weight(y_train)
        return super().fit(X_train, y_train)

    # ── Importance ──────────────────────────────────────────────────────
    def build_feature_importance_df(self, session_id):
        try:
            booster = self.model.get_booster()
            gain    = booster.get_score(importance_type='gain')
            # xgboost may use f0..fN if column names were stripped; map back
            items = []
            for k, v in gain.items():
                feat = k if k in self.feature_names else \
                       (self.feature_names[int(k[1:])] if k.startswith('f') and k[1:].isdigit()
                        and int(k[1:]) < len(self.feature_names) else k)
                items.append((feat, v))
            imp_df = pd.DataFrame(items, columns=['feature_name', 'importance'])
            # Fill missing features with 0
            missing = set(self.feature_names) - set(imp_df['feature_name'])
            if missing:
                imp_df = pd.concat([
                    imp_df,
                    pd.DataFrame({'feature_name': list(missing), 'importance': 0.0})
                ], ignore_index=True)
            imp_df = imp_df.sort_values('importance', ascending=False).reset_index(drop=True)
            imp_df['rank']       = imp_df.index + 1
            imp_df['session_id'] = session_id
            imp_df['created_at'] = datetime.datetime.now()
            return imp_df
        except Exception as e:
            logger.warning(f"XGB gain importance failed: {e}")
            return pd.DataFrame()

    def save_artifacts(self, writer, session_id, cfg, env_vars):
        suffix = f"_{env_vars.get('unit', '').strip()}" if env_vars.get('unit') else ""
        tp     = cfg.get('table_prefix', '')

        # 1) Binary model blob via td-model-store (runs in thread pool too)
        writer.submit_custom(
            lambda: _save_to_model_store(
                model        = self.model,
                model_family = self.family,
                session_id   = session_id,
                env_vars     = env_vars,
                cfg          = cfg,
            ),
            label=f"td_model_store[{self.family}]",
        )

        # 2) Native gain importance table
        writer.submit(
            self.build_feature_importance_df(session_id),
            f"{tp}xgb_gain_importance{suffix}",
        )


# ═════════════════════════════════════════════════════════════════════════════
# CATBOOST
# ═════════════════════════════════════════════════════════════════════════════
class CatBoostModel(BaseLeadScoringModel):
    """
    Precision-focused CatBoost classifier.

    Null handling: CatBoost treats NaN as a special value via
    nan_mode='Min' (default), learning splits against it.  We do NOT
    impute upstream so this native handling kicks in.

    Persistence:
      - full .cbm binary → td-model-store
      - native gain importance → {table_prefix}cb_gain_importance{suffix}
    """
    family              = 'catboost'
    requires_scaling    = False
    requires_imputation = False  # CatBoost handles NaN natively
    requires_corr_drop  = False   # ← new

    def _lazy_import_cb(self):
        try:
            from catboost import CatBoostClassifier
        except ImportError:
            os.system(f"{sys.executable} -m pip install --user catboost")
            from catboost import CatBoostClassifier
        return CatBoostClassifier

    def _cb_eval_metric(self):
        """Map xgb_eval_metric config to CatBoost eval_metric names."""
        mapping = {
            'aucpr':   'PRAUC',
            'auc':     'AUC',
            'logloss': 'Logloss',
            'error':   'Accuracy',
        }
        return mapping.get(self.cfg.get('xgb_eval_metric', 'aucpr'), 'PRAUC')

    def _suggest_params(self, trial):
        cfg = self.cfg
        return {
            'iterations':        trial.suggest_int(
                'iterations',
                cfg.get('n_estimators_min', 200),
                cfg.get('n_estimators_max', 1500),
            ),
            'depth':             trial.suggest_int(
                'depth',
                cfg.get('max_depth_min', 4),
                cfg.get('max_depth_max', 10),
            ),
            'learning_rate':     trial.suggest_float(
                'learning_rate',
                cfg.get('learning_rate_min', 0.01),
                cfg.get('learning_rate_max', 0.3),
                log=True,
            ),
            'l2_leaf_reg':       trial.suggest_float('l2_leaf_reg', 1.0, 10.0, log=True),
            'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0),
            'random_strength':   trial.suggest_float('random_strength', 1e-8, 10.0, log=True),
            'border_count':      trial.suggest_int('border_count', 32, 255),
        }

    def _default_params(self):
        return {
            'iterations':          500,
            'depth':               6,
            'learning_rate':       0.1,
            'l2_leaf_reg':         3.0,
            'bagging_temperature': 0.5,
            'random_strength':     1.0,
            'border_count':        128,
        }

    def _build_estimator(self, params):
        CatBoostClassifier = self._lazy_import_cb()
        kwargs = dict(
            **params,
            loss_function='Logloss',
            eval_metric=self._cb_eval_metric(),
            random_state=24,
            thread_count=_n_jobs(),
            verbose=False,
            allow_writing_files=False,
        )
        if self.cfg.get('class_balance_strategy', 'balanced') == 'balanced':
            kwargs['auto_class_weights'] = 'Balanced'
        return CatBoostClassifier(**kwargs)

    def _fit_final(self, estimator, X, y, eval_set=None):
        fit_kwargs = {}
        es_rounds = int(self.cfg.get('early_stopping_rounds', 0))
        if eval_set is not None and es_rounds > 0:
            from catboost import Pool
            eval_X, eval_y = eval_set[0]
            fit_kwargs['eval_set'] = Pool(eval_X, eval_y)
            fit_kwargs['early_stopping_rounds'] = es_rounds
        estimator.fit(X, y, **fit_kwargs)

    def build_feature_importance_df(self, session_id):
        try:
            importances = self.model.get_feature_importance()
            imp_df = pd.DataFrame({
                'feature_name': self.feature_names,
                'importance':   importances,
            }).sort_values('importance', ascending=False).reset_index(drop=True)
            imp_df['rank']       = imp_df.index + 1
            imp_df['session_id'] = session_id
            imp_df['created_at'] = datetime.datetime.now()
            return imp_df
        except Exception as e:
            logger.warning(f"CatBoost importance failed: {e}")
            return pd.DataFrame()

    def save_artifacts(self, writer, session_id, cfg, env_vars):
        suffix = f"_{env_vars.get('unit', '').strip()}" if env_vars.get('unit') else ""
        tp     = cfg.get('table_prefix', '')

        writer.submit_custom(
            lambda: _save_to_model_store(
                model        = self.model,
                model_family = self.family,
                session_id   = session_id,
                env_vars     = env_vars,
                cfg          = cfg,
            ),
            label=f"td_model_store[{self.family}]",
        )

        writer.submit(
            self.build_feature_importance_df(session_id),
            f"{tp}cb_gain_importance{suffix}",
        )


# ═════════════════════════════════════════════════════════════════════════════
# td-model-store helper (shared by XGBoost + CatBoost)
# ═════════════════════════════════════════════════════════════════════════════
def _save_to_model_store(model, model_family, session_id, env_vars, cfg):
    """
    Persist a tree model's binary blob via td-model-store.  Chunks into
    Plazma VARCHAR automatically.  Kept in this module so model-family
    knowledge stays co-located with the class that uses it.
    """
    try:
        from td_model_store import save_model
    except ImportError:
        os.system(f"{sys.executable} -m pip install --user td-model-store")
        from td_model_store import save_model

    tp                = cfg.get('table_prefix', '')
    model_store_table = cfg.get('model_store_table') or env_vars.get('model_store_table') \
                        or f'{tp}ml_model_store'
    model_name        = cfg.get('model_name')        or env_vars.get('model_name') \
                        or f"{tp}{model_family}"
    endpoint          = cfg.get('td_endpoint')       or env_vars.get('td_endpoint') \
                        or 'https://api.treasuredata.com'

    logger.info(
        f"Saving {model_family} model to td-model-store: "
        f"db={env_vars['database']}, table={model_store_table}, "
        f"name={model_name}, session_id={session_id}"
    )

    try:
        # td-model-store expects an int session_id.  Digdag session_ids are
        # strings but commonly numeric; fall back to unix-timestamp otherwise.
        try:
            session_id_int = int(session_id)
        except (TypeError, ValueError):
            session_id_int = int(datetime.datetime.now().timestamp())
            logger.warning(
                f"session_id '{session_id}' not int-coercible — using unix ts "
                f"{session_id_int} for td-model-store only"
            )

        metadata = save_model(
            model      = model,
            database   = env_vars['database'],
            table      = model_store_table,
            model_name = model_name,
            session_id = session_id_int,
            apikey     = env_vars['apikey'],
            endpoint   = endpoint,
        )
        logger.info(
            f"✓ Model stored: chunks={metadata['num_chunks']}, "
            f"size={metadata['size_bytes']} bytes, format={metadata['model_format']}"
        )
    except Exception as e:
        logger.error(f"td-model-store save FAILED: {e}")
        raise


# ═════════════════════════════════════════════════════════════════════════════
# FACTORY
# ═════════════════════════════════════════════════════════════════════════════
class ModelFactory:
    _REGISTRY = {
        'logistic': LogisticModel,
        'xgboost':  XGBoostModel,
        'catboost': CatBoostModel,
    }

    @classmethod
    def create(cls, model_type, cfg):
        key = (model_type or 'logistic').strip().lower()
        if key not in cls._REGISTRY:
            raise ValueError(
                f"Unknown model_type '{model_type}'. "
                f"Supported: {list(cls._REGISTRY.keys())}"
            )
        logger.info(f"ModelFactory: creating {key} model")
        return cls._REGISTRY[key](cfg)