# E0 · Foundation & Reproducibility Hardening

**Goal:** Make the data layer trustworthy and reproducible *before* pouring ML on top. Garbage
or silently-changing data is the #1 reason ML projects fail. You're backend-strong, so this
epic is mostly lean plumbing — do it once, benefit forever.

**Target:** Jul 07 – Jul 13 (~1 week) · **Unlocks:** E1
**Definition of done:** you can rebuild every table from scripts, you have a frozen, versioned
copy of the training data, and you've eyeballed its quality.

---

### E0-T1 · Capture the table schemas as SQL DDL 🟢 (~2h)
Right now tables are created by hand in pgAdmin — that's a reproducibility hole.
- [ ] From pgAdmin (or `pg_dump --schema-only`), export DDL for: `market_candles_daily`, `market_candles_5m`, `market_candles_1m`, `daily_market_features`, `intraday_market_features`, `intraday_training_dataset`.
- [ ] Save as `sql/schema.sql` with the `CREATE TABLE` + unique constraints (e.g. `UNIQUE(symbol, event_time)`).
- [ ] Add a one-liner to the README: "run `psql -f sql/schema.sql` to create all tables."
- [ ] **AC:** dropping and recreating a table from `sql/schema.sql` lets a feature job run without error.
- 📌 `pg_dump --schema-only --no-owner -d market_db > sql/schema.sql`

### E0-T2 · Add ML/eval Python dependencies 🟢 (~1h)
- [ ] Add to `requirements.txt`: `scikit-learn`, `xgboost`, `lightgbm`, `matplotlib`, `seaborn`, `jupyter`, `shap`, `optuna`, `mlflow`, `joblib`.
- [ ] `pip install -r requirements.txt` in your venv; confirm imports work.
- [ ] **AC:** `python -c "import sklearn, xgboost, lightgbm, shap, optuna, mlflow"` runs clean.

### E0-T3 · Freeze a versioned training snapshot 🟡 (~2h)
ML needs a *stable* dataset — the Spark jobs TRUNCATE+rebuild, so the table is a moving target.
- [ ] Write `ml/data/export_snapshot.py`: read `intraday_training_dataset` via pandas, write to `ml/data/snapshots/intraday_YYYYMMDD.parquet`.
- [ ] Record row count + date range + class balance to a small `.json` sidecar.
- [ ] **AC:** you have a parquet file you can re-load identically tomorrow regardless of pipeline reruns.
- 📌 Parquet (not CSV) preserves dtypes and is fast. `df.to_parquet(path, index=False)`.

### E0-T4 · Data-quality sanity checks 🟡 (~3h)
- [ ] Write `ml/data/quality_report.py` that prints, per symbol: row count, null counts per column, min/max `event_time`, duplicate `(symbol, event_time)` count, and `target_direction` class balance.
- [ ] Eyeball it. Flag anything weird (all-null columns, huge gaps, 99% one class).
- [ ] **AC:** you can state, in one sentence, how balanced your labels are and whether any feature is mostly null.
- ⚠️ Class balance matters enormously for E1 — if it's 85/15, plain accuracy will lie to you.

### E0-T5 · Verify no future leakage in features 🔴 (~3h · load-bearing)
The single most important check in the whole project. A feature computed with future info makes
your model look brilliant and fail in real life.
- [ ] For each column in `intraday_market_features`, ask: "could I compute this at candle time T using only data ≤ T?" Windows like `rowsBetween(-19, 0)` are safe; anything using `lead()` is not.
- [ ] Confirm the label columns (`future_*`, `target_direction`, `reward_risk_ratio`) are the ONLY forward-looking fields, and that E1 will **exclude them from X**.
- [ ] Write your conclusion as a comment block in `ml/README.md` (a "feature contract").
- [ ] **AC:** a written list of which columns are safe inputs (X) vs. which are labels/leakage (never in X).
- ⭐ Read: "Data Leakage in Machine Learning" — search Kaggle's leakage guide.

### E0-T6 · Scaffold the `ml/` project structure 🟢 (~1h)
- [ ] Create `ml/` with subdirs: `data/`, `notebooks/`, `models/` (gitignored artifacts), `src/`.
- [ ] Add `ml/models/.gitkeep` and a line in `.gitignore` for `ml/models/*.pkl`, `ml/data/snapshots/*.parquet`, `mlruns/`.
- [ ] Add a stub `ml/README.md` describing the folder layout.
- [ ] **AC:** a clean, conventional ML project skeleton exists.

---

**Resources for this epic**
- ⭐ scikit-learn "Getting Started" — https://scikit-learn.org/stable/getting_started.html
- pandas `to_parquet` / `read_parquet` docs
- Kaggle: "Data Leakage" micro-course lesson (free)
