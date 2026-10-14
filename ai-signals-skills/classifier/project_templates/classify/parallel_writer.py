# ─────────────────────────────────────────────────────────────────────────────
# parallel_writer.py
#
# Thread-pool helper for writing many DataFrames to Treasure Data in parallel.
#
# Why this exists:
#   The training pipeline produces ~12 artifact tables per run (run logs, ROC,
#   bins, correlations, Optuna trials, SHAP, scaler, coefficients / importance,
#   model blob, …).  Writing them sequentially via save_data() is network-bound
#   and dominates wall-clock time on large runs.  Each write goes to a DISTINCT
#   table, so they parallelise trivially.
#
# Why threads (not processes):
#   - TD writes are I/O-bound (bulk import over HTTPS) → GIL is not a bottleneck
#   - Threads avoid pickling DataFrames and avoid Docker fork quirks on TD's
#     ECS workers
#
# Thread safety:
#   pytd.Client instances are not guaranteed thread-safe.  Each write therefore
#   constructs its own short-lived DataHandler (and therefore its own pytd
#   client) — one per thread-task.  This costs a handful of ms per write but
#   is the only pattern that is safely concurrent across pytd versions.
#
# Usage:
#   writer = ParallelWriter(apikey=..., database=..., endpoint=..., max_workers=6)
#   writer.submit(df1, 'table_a')
#   writer.submit(df2, 'table_b')
#   writer.submit_custom(lambda: my_blob_save_fn(), label='model_blob')
#   writer.flush()   # blocks until all done, raises aggregate error on failure
# ─────────────────────────────────────────────────────────────────────────────

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from data_handler import DataHandler

logger = logging.getLogger(__name__)


class ParallelWriter:
    """
    Buffer write jobs then execute them in a bounded thread pool.

    Two kinds of jobs:
      - submit(df, table, if_exists='append')  → vanilla save_data
      - submit_custom(fn, label)               → any callable (e.g. td-model-store)

    Both are executed when flush() is called.
    """

    def __init__(self, apikey, database, endpoint="https://api.treasuredata.com/", max_workers=6):
        self.apikey      = apikey
        self.database    = database
        self.endpoint    = endpoint
        self.max_workers = max(1, int(max_workers))
        self._jobs       = []   # list of (label, callable)

    # ─────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────
    def submit(self, df, table, if_exists='append'):
        """Queue a DataFrame → table write.  Empty / None DataFrames are skipped."""
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            logger.info(f"  [skip] {table} — DataFrame empty")
            return

        def _job(_df=df, _table=table, _if_exists=if_exists):
            return self._write_single(_df, _table, _if_exists)

        self._jobs.append((table, _job))
        logger.debug(f"  [queued] {table} ({df.shape})")

    def submit_custom(self, fn, label):
        """Queue an arbitrary callable (e.g. td-model-store save)."""
        self._jobs.append((label, fn))
        logger.debug(f"  [queued] {label} (custom)")

    def flush(self):
        """
        Execute all queued jobs in parallel.  Waits for completion.  If any
        job fails, logs every failure, then raises a single RuntimeError
        listing all of them so the Digdag task still fails loudly.
        """
        if not self._jobs:
            logger.info("ParallelWriter.flush() called with 0 queued jobs — nothing to do")
            return

        n        = len(self._jobs)
        workers  = min(self.max_workers, n)
        logger.info("=" * 60)
        logger.info(f"ParallelWriter: dispatching {n} write(s) on {workers} thread(s)")
        logger.info("=" * 60)

        t_start   = time.time()
        successes = []
        failures  = []  # list of (label, exception)

        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix='td-writer') as pool:
            future_to_label = {
                pool.submit(fn): label
                for (label, fn) in self._jobs
            }
            for fut in as_completed(future_to_label):
                label = future_to_label[fut]
                try:
                    fut.result()
                    successes.append(label)
                    logger.info(f"  ✓ {label}")
                except Exception as e:
                    failures.append((label, e))
                    logger.error(f"  ✗ {label} — {type(e).__name__}: {e}")

        elapsed = time.time() - t_start
        logger.info("-" * 60)
        logger.info(
            f"ParallelWriter: {len(successes)}/{n} succeeded, "
            f"{len(failures)} failed in {elapsed:.1f}s "
            f"(≈{elapsed / n:.2f}s/table avg)"
        )
        logger.info("=" * 60)

        # Reset queue — makes the writer reusable for a second batch if needed
        self._jobs = []

        if failures:
            msg_lines = [f"{lbl}: {type(exc).__name__}: {exc}" for lbl, exc in failures]
            raise RuntimeError(
                f"ParallelWriter: {len(failures)} write(s) failed:\n  - "
                + "\n  - ".join(msg_lines)
            )

    # ─────────────────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────────────────
    def _write_single(self, df, table, if_exists):
        """
        Build a DataHandler local to this thread (new pytd client) so we never
        share client state across threads.  Keeps things safe across all
        pytd versions.
        """
        local_handler = DataHandler(self.apikey, self.database, self.endpoint)
        local_handler.save_data(df, table, if_exists=if_exists)