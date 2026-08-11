# 📊 Project Board — Indian Stock Market ML Analysis

> Your single source of truth. Open this file first every day.
> Detailed tasks live in [`docs/board/`](docs/board/). GitHub mirror: see [Syncing to GitHub](#-syncing-to-github).

**Vision:** An ML + RAG powered tool that predicts intraday price direction / signals for NSE
stocks, served through a full-stack app, deployed on AWS.

**Where you are today (2026-07-07):** the data pipeline (ingestion → features → labels) is
built. The labeled table `intraday_training_dataset` exists and is the launch pad for ML.
Everything from ML onward is greenfield.

**Your working profile (drives every estimate below):**
- ⏱️ ~2–3 hrs/day → ~12–18 hrs/week
- 💪 Backend: strong · 🧠 ML: new · ☁️ Deploy/AWS: new · 🎨 Frontend: beginner

---

## 🗂️ Kanban (update this by hand as you go)

Move an epic's row as its status changes. Task-level tracking lives in each epic file.

| Epic | Status | Progress | File |
|------|--------|----------|------|
| E0 · Foundation & Reproducibility | 🔜 Todo | 0/6 | [00-foundation.md](docs/board/00-foundation.md) |
| E1 · ML Baseline | 🔜 Todo | 0/7 | [01-ml-baseline.md](docs/board/01-ml-baseline.md) |
| E2 · ML Iteration & Validation | 📥 Backlog | 0/7 | [02-ml-improve.md](docs/board/02-ml-improve.md) |
| E3 · RAG & Sentiment Layer | 📥 Backlog | 0/6 | [03-rag-sentiment.md](docs/board/03-rag-sentiment.md) |
| E4 · Backend API (FastAPI) | 📥 Backlog | 0/6 | [04-backend-api.md](docs/board/04-backend-api.md) |
| E5 · Frontend App | 📥 Backlog | 0/7 | [05-frontend-app.md](docs/board/05-frontend-app.md) |
| E6 · AWS Deployment | 📥 Backlog | 0/7 | [06-aws-deploy.md](docs/board/06-aws-deploy.md) |
| E7 · MLOps & Monitoring | 📥 Backlog | 0/5 | [07-mlops-monitoring.md](docs/board/07-mlops-monitoring.md) |

**Status legend:** 📥 Backlog · 🔜 Todo · 🏗️ In Progress · 🔎 Review/Verify · ✅ Done · 🧊 Blocked

---

## 🗺️ Roadmap (target dates @ ~2–3 hrs/day)

Dates are targets, not deadlines. Slipping is fine — just drag the whole tail right. The
**order matters**: each epic unlocks the next. E7 runs in parallel once E1 lands.

```
2026
Jul  ├─ E0 Foundation ........... Jul 07 – Jul 13  (1 wk)
     ├─ E1 ML Baseline .......... Jul 14 – Jul 27  (2 wk)   ← first real prediction
Aug  ├─ E2 ML Iteration ......... Jul 28 – Aug 17  (3 wk)   ← make it actually good
     ├─ E3 RAG & Sentiment ...... Aug 18 – Sep 07  (3 wk)   ← accuracy boost + explanations
Sep  ├─ E4 Backend API .......... Sep 08 – Sep 17  (1.5 wk) ← serve predictions
     ├─ E5 Frontend App ......... Sep 18 – Oct 08  (3 wk)   ← the app you can show people
Oct  ├─ E6 AWS Deployment ....... Oct 09 – Oct 29  (3 wk)   ← production on AWS
     └─ E7 MLOps & Monitoring ... parallel from Aug, hardens through Nov
```

**Milestones to celebrate:**
- 🏁 **M1 — First Signal** (end E1): a saved model predicts up/down on held-out data with honest metrics.
- 🏁 **M2 — Trustworthy Model** (end E2): walk-forward validated, backtested, no leakage.
- 🏁 **M3 — Context-Aware** (end E3): predictions augmented with news/sentiment + a plain-English rationale.
- 🏁 **M4 — Live Locally** (end E5): full stack running on your machine end to end.
- 🏁 **M5 — In Production** (end E6): reachable on AWS.

---

## 🔁 The discipline ritual (this is the whole point)

**Every working session (5 min to start):**
1. Open this file → look at the current 🏗️ epic.
2. Open that epic file → pick the first unchecked `[ ]` subtask.
3. Set it in progress, do it, check it `[x]`.
4. Before you close: write one line in the [Daily Log](#-daily-log) — what you did + next step.

**Every Sunday (15 min review):**
- Update the Kanban progress counts + statuses above.
- Re-baseline the roadmap tail if you slipped.
- Run `scripts/sync_github_board.sh` if you want the GitHub board refreshed.
- Write a one-line weekly retro in the log.

**Rules that keep you sane:**
- One epic 🏗️ In Progress at a time. Resist jumping ahead to the fun frontend stuff.
- A task too big to finish in one sitting is too big — split it in the epic file.
- "Learning" counts as work. Log the resource you read.

---

## 📓 Daily Log

> Newest at top. Format: `YYYY-MM-DD — did X · next: Y`. One line. Keep it honest.

- 2026-07-07 — Set up the project board & task system · next: start E0-T1 (schema DDL capture)

<!-- Weekly retro example:
### Week of 2026-07-07 (retro)
- Shipped: E0 T1–T3. Learned Spark write modes the hard way.
- Slipped: none. Felt good.
-->

---

## 🏷️ Conventions

- **Task IDs:** `E<epic>-T<task>` (e.g. `E1-T3`). Referenced in commits: `E1-T3: add time-series split`.
- **Difficulty (calibrated to _your_ profile):** 🟢 comfortable · 🟡 stretch · 🔴 new territory, budget learning time.
- **Estimates** are focused-hours. Double them mentally for anything 🔴 the first time.
- **Resources** in each epic are curated — read the ⭐ ones, skim the rest.

---

## 🔗 Syncing to GitHub

You chose **markdown-as-source-of-truth + GitHub Issues mirror**. Markdown here is authoritative;
GitHub gives you the drag-and-drop kanban.

**One-time setup (when you're ready):**
```bash
brew install gh          # install GitHub CLI
gh auth login            # authenticate to github.com/ssomcode
```

**Generate the board on GitHub:**
```bash
bash scripts/sync_github_board.sh
```
This creates one **milestone per epic**, the **labels** (difficulty, epic, type), and one
**issue per task**. Then open your repo → Projects → new board → add the issues. See the script
header for details and idempotency notes.

> Prefer to stay in markdown only? You never have to run the script. The checkboxes in
> `docs/board/*.md` are a complete tracker on their own.
