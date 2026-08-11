# E1 · ML Baseline — First Real Prediction 🏁 M1

**Goal:** Get a *correct* first classifier predicting `target_direction` (up vs. not-up) on
held-out data, with metrics you can trust. "Correct" > "accurate" here — the point is a
leak-free, time-aware baseline you'll improve in E2. You're new to ML, so this epic is
deliberately explained; take the learning time.

**Target:** Jul 14 – Jul 27 (~2 weeks) · **Depends on:** E0 · **Unlocks:** E2
**Definition of done:** a saved model file + a metrics report on a time-based holdout, with a
written interpretation of whether it beats a naive baseline.

---

### E1-T1 · Exploratory Data Analysis (EDA) notebook 🟡 (~3h)
- [ ] `ml/notebooks/01_eda.ipynb`: load the E0 snapshot parquet.
- [ ] Plot: class balance, distribution of each feature, feature-vs-feature correlation heatmap, `target_direction` vs a few features (do RSI/breakout actually relate to the label?).
- [ ] Note any features that are constant, redundant, or heavily null.
- [ ] **AC:** you can name 3 features that look predictive and 2 that look useless.
- ⭐ This is where ML intuition is built. Spend real time looking at the data.

### E1-T2 · Define the feature contract (X, y) in code 🟢 (~2h)
- [ ] `ml/src/dataset.py`: a function returning `X` (safe input columns from E0-T5) and `y` (`target_direction`).
- [ ] Explicitly DROP: `future_*`, `reward_risk_ratio`, `event_time` (keep for splitting, not as a feature), `symbol` (or one-hot it — decide and comment why).
- [ ] Handle NaNs (early candles have null rolling features) — drop or impute, and write down which.
- [ ] **AC:** `X, y = load_dataset()` returns aligned arrays with zero leakage columns.
- ⚠️ Cross-check against your E0-T5 list. This is where leakage sneaks back in.

### E1-T3 · Time-based train/test split (NOT random) 🔴 (~2h · concept-heavy)
- [ ] Split by `event_time`, not `train_test_split(shuffle=True)`. Train on the earlier ~80%, test on the most recent ~20%.
- [ ] Do it per symbol OR globally by timestamp — decide and document.
- [ ] **AC:** every test-set timestamp is strictly later than every train-set timestamp.
- ⭐ Why: shuffling leaks the future into training for time series. This is the #1 beginner mistake in trading ML. Read scikit-learn `TimeSeriesSplit` docs.

### E1-T4 · Establish naive baselines 🟢 (~1h)
Before any model, know the number to beat.
- [ ] Compute: accuracy of "always predict majority class", and of "predict up if last candle was up".
- [ ] Record these. Your model must beat them to mean anything.
- [ ] **AC:** two baseline accuracy numbers written in the notebook.

### E1-T5 · Train baseline models 🟡 (~3h)
- [ ] Model A: `LogisticRegression` (scale features first with `StandardScaler` in a `Pipeline`).
- [ ] Model B: `XGBoostClassifier` or `LGBMClassifier` (trees don't need scaling; handle imbalance with `scale_pos_weight` / `class_weight`).
- [ ] Fit on train, predict on the time-holdout.
- [ ] **AC:** both models train and produce predictions on the holdout without leakage.

### E1-T6 · Evaluate with the right metrics 🔴 (~3h · concept-heavy)
Accuracy alone is misleading on imbalanced trading data.
- [ ] Report: accuracy, precision, recall, F1, ROC-AUC, PR-AUC, and a confusion matrix.
- [ ] Add a **trading-flavored** read: of the candles the model predicted "up" with high confidence, what fraction actually went up? (precision at high confidence)
- [ ] Compare against the E1-T4 baselines.
- [ ] **AC:** a short written verdict: "does this beat naive, and by how much, on which metric?"
- ⭐ Read: precision/recall + ROC vs PR curves for imbalanced data.

### E1-T7 · Save the model + metrics artifact 🟢 (~2h)
- [ ] `joblib.dump()` the winning pipeline to `ml/models/baseline_YYYYMMDD.pkl`.
- [ ] Save the metrics dict + the feature list used to `ml/models/baseline_YYYYMMDD.json`.
- [ ] Write a 5-line "model card" in `ml/README.md`: what it predicts, on what features, its holdout metrics, known limitations.
- [ ] **AC:** you can reload the model and reproduce a prediction from the saved artifact.

---

**🏁 Milestone M1 — First Signal.** You now have an honest, leak-free predictor. It's probably
mediocre — that's expected and fine. E2 makes it good.

**Resources for this epic**
- ⭐ scikit-learn Pipeline + TimeSeriesSplit user guide
- ⭐ "Advances in Financial Machine Learning" (López de Prado) — ch. on labeling & CV (skim; it's advanced but shapes the right instincts)
- XGBoost / LightGBM "first model" quickstarts
- StatQuest (YouTube): ROC/AUC, precision-recall, gradient boosting — excellent for beginners
