# E2 · ML Iteration & Validation — Make It Actually Good 🏁 M2

**Goal:** Turn the mediocre baseline into a model you'd trust enough to paper-trade. The theme is
**rigorous validation** (does it hold up over time?) and **honest improvement** (feature work,
tuning, threshold selection, backtesting) — not chasing a shiny accuracy number.

**Target:** Jul 28 – Aug 17 (~3 weeks) · **Depends on:** E1 · **Unlocks:** E3, E4
**Definition of done:** a walk-forward-validated model, a simple backtest of its signals, and an
experiment log — with no leakage and clear-eyed conclusions about whether it's usable.

---

### E2-T1 · Walk-forward / expanding-window cross-validation 🔴 (~4h)
A single holdout can be lucky. Validate across multiple time windows.
- [ ] Use `TimeSeriesSplit` (or a manual expanding window): train on months 1–2 → test month 3; train 1–3 → test 4; etc.
- [ ] Report mean ± std of your key metric across folds.
- [ ] **AC:** you know whether performance is stable across time or wildly variable.
- ⭐ Instability across folds is a red flag worth more than a high average.

### E2-T2 · Feature importance & pruning with SHAP 🟡 (~3h)
- [ ] Compute SHAP values on the tree model; plot the summary.
- [ ] Identify low-signal features (from E1-T1 suspicions + SHAP) and try dropping them.
- [ ] **AC:** a ranked feature list + a decision on which to keep.

### E2-T3 · Feature engineering round 2 🟡 (~4h)
- [ ] Add a few candidate features grounded in the existing pipeline: e.g. RSI regime buckets, EMA-cross flags, volatility-adjusted returns, time-of-day (open/mid/close session), day-of-week.
- [ ] Remember: update BOTH the Spark feature job's select list AND `result_schema` if you add them upstream (see CLAUDE.md), OR compute them in pandas at train time for fast iteration.
- [ ] Re-run E2-T1 to see if they help.
- [ ] **AC:** you kept only features that improved (or held) walk-forward metrics.

### E2-T4 · Handle class imbalance & tune the decision threshold 🔴 (~3h)
- [ ] Try `class_weight`/`scale_pos_weight`, and compare to leaving it default.
- [ ] Don't default to a 0.5 probability cutoff — pick the threshold that maximizes your trading-relevant metric (e.g. precision at a target recall) using the PR curve.
- [ ] **AC:** a chosen probability threshold with a documented reason.

### E2-T5 · Hyperparameter tuning with Optuna 🟡 (~3h)
- [ ] Wrap the model in an Optuna study; tune within a walk-forward CV (never tune on the final test window).
- [ ] Cap trials (e.g. 50) so it finishes in a session.
- [ ] **AC:** best params saved; verified they don't overfit the validation folds.
- ⚠️ Tuning on data you also evaluate on = leakage. Keep a final untouched test period.

### E2-T6 · Signal backtest simulation 🔴 (~5h · the fun one)
Convert probabilities → trades → a P&L curve. This is where "is it real?" gets answered.
- [ ] For each test candle: if `P(up) > threshold`, simulate entering; use the existing `future_*` columns (return over the ~1hr lookahead) and `reward_risk_ratio` as ground-truth outcome.
- [ ] Track cumulative return, win rate, avg win/loss, max drawdown. Include a simple cost assumption (e.g. 0.05% per trade).
- [ ] Compare to buy-and-hold over the same window.
- [ ] **AC:** an equity curve + a one-paragraph verdict: does the signal add value after costs?
- ⭐ A backtest that beats naive after costs is your real success metric — not accuracy.

### E2-T7 · Experiment tracking with MLflow 🟡 (~3h)
- [ ] Wrap training runs in `mlflow.start_run()`; log params, metrics, and the model artifact.
- [ ] Run `mlflow ui` and browse your runs.
- [ ] **AC:** every future model experiment is logged and comparable — no more "which version was that?"

---

**🏁 Milestone M2 — Trustworthy Model.** You can now say, with evidence, whether your signal is
worth serving. Save the champion model + its MLflow run ID — E4 will load it.

**Resources for this epic**
- ⭐ SHAP docs + "Interpreting a model" tutorial
- ⭐ Optuna quickstart
- MLflow tracking quickstart
- "Advances in Financial ML" — combinatorial purged CV & backtest overfitting (skim for awareness)
- Blog searches: "backtesting pitfalls", "why your backtest lies"
