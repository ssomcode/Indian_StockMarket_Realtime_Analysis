# E7 · MLOps & Monitoring — Keep It Alive & Honest

**Goal:** A model that trained once and never retrains slowly rots as the market changes. This
epic automates the pipeline, schedules retraining, and watches for the model going stale. It runs
**in parallel** — start pieces of it as soon as E1 gives you a model, and harden it through E6.

**Target:** parallel from Aug, hardens through Nov · **Depends on:** E1+ · **Enhances:** everything
**Definition of done:** the feature/label pipeline runs on a schedule, the model retrains
periodically, and you get alerted when performance or data drifts.

---

### E7-T1 · Orchestrate the pipeline (Airflow) 🔴 (~5h)
The `airflow/` dir is an empty placeholder. Turn the manual `spark-submit` chain into a DAG.
- [ ] A DAG that runs, in order: daily features → intraday features → intraday labels → snapshot export (respecting the run-order dependency from CLAUDE.md).
- [ ] Schedule it (e.g. after market close, IST-aware).
- [ ] **AC:** the whole feature/label pipeline runs on a schedule with visible task status.
- 📌 If Airflow feels heavy, a cron + a Python runner is a legitimate v1. Upgrade later.

### E7-T2 · Scheduled retraining 🟡 (~4h)
- [ ] A job that periodically retrains on fresh data, logs to MLflow, and promotes the new model only if it beats the current champion on walk-forward metrics (a "challenger beats champion" gate).
- [ ] **AC:** retraining is automated and safe (a worse model can't auto-deploy).

### E7-T3 · Data drift monitoring 🟡 (~3h)
- [ ] Track feature distributions over time (e.g. mean/std, or a library like `evidently`). Alert if a feature drifts far from the training distribution.
- [ ] **AC:** you'd get notified if incoming data stops resembling training data.

### E7-T4 · Prediction/performance monitoring 🔴 (~4h)
- [ ] Once you have live signals, log predictions and later join to realized outcomes (the `future_*` truth becomes known ~1hr later).
- [ ] Track rolling live accuracy / precision-at-threshold vs. the backtest expectation.
- [ ] **AC:** a dashboard/metric showing whether the live model still performs like it did in testing.
- ⭐ This closes the loop — it's how you learn the model degraded *before* it costs you.

### E7-T5 · Alerting 🟢 (~2h)
- [ ] Wire drift/performance alerts to email or Slack.
- [ ] **AC:** a real alert fires when you deliberately feed bad/stale data.

---

**Resources for this epic**
- ⭐ Airflow "core concepts" + a "first DAG" tutorial
- MLflow Model Registry (champion/challenger promotion)
- `evidently` (open-source data & ML drift monitoring) docs
- "ML monitoring / drift" primers; Google's "Rules of ML" (classic, worth reading once)
