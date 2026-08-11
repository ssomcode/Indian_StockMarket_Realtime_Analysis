#!/usr/bin/env bash
#
# sync_github_board.sh — mirror PROJECT_BOARD.md to GitHub Issues/Milestones/Labels.
#
# WHAT IT DOES
#   • Creates one milestone per epic (E0..E7).
#   • Creates labels for difficulty (easy/stretch/new-territory), type, and each epic.
#   • Creates one issue per task, labeled + assigned to its epic milestone.
#
# SOURCE OF TRUTH is the markdown in docs/board/. This script just projects it onto GitHub.
# Re-running is safe-ish: labels/milestones are created only if missing. ISSUES are matched by
# title — an issue whose title starts with the same task ID (e.g. "E1-T3:") is skipped, so you
# can re-run without duplicating. Editing task text here does NOT edit an existing issue.
#
# PREREQUISITES
#   brew install gh && gh auth login        # authenticate to github.com/ssomcode
#   Run from the repo root:  bash scripts/sync_github_board.sh
#
# DRY RUN
#   DRY_RUN=1 bash scripts/sync_github_board.sh    # print actions, change nothing
#
set -euo pipefail

DRY="${DRY_RUN:-0}"
run() { if [[ "$DRY" == "1" ]]; then echo "DRY: $*"; else eval "$@"; fi; }

command -v gh >/dev/null || { echo "❌ gh CLI not found. Run: brew install gh && gh auth login"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "❌ Not authenticated. Run: gh auth login"; exit 1; }

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "📦 Repo: $REPO"

# ---- Labels -----------------------------------------------------------------
# name|color|description
LABELS=(
  "diff:easy|2ea44f|Comfortable given the user's skills"
  "diff:stretch|dbab09|A stretch; budget extra time"
  "diff:new-territory|d73a4a|New skill; expect learning time"
  "type:ml|5319e7|Machine learning work"
  "type:data|0e8a16|Data/pipeline work"
  "type:rag|1d76db|RAG / LLM / sentiment"
  "type:backend|006b75|API / services"
  "type:frontend|fbca04|UI / app"
  "type:infra|b60205|AWS / deploy / MLOps"
  "epic:E0|c5def5|Foundation & Reproducibility"
  "epic:E1|c5def5|ML Baseline"
  "epic:E2|c5def5|ML Iteration & Validation"
  "epic:E3|c5def5|RAG & Sentiment"
  "epic:E4|c5def5|Backend API"
  "epic:E5|c5def5|Frontend App"
  "epic:E6|c5def5|AWS Deployment"
  "epic:E7|c5def5|MLOps & Monitoring"
)
echo "🏷️  Ensuring labels..."
for l in "${LABELS[@]}"; do
  IFS='|' read -r name color desc <<< "$l"
  if gh label list --limit 200 | grep -q "^${name}\b"; then
    echo "   = $name"
  else
    run "gh label create '$name' --color '$color' --description '$desc'"
  fi
done

# ---- Milestones (one per epic) ---------------------------------------------
# gh has no first-class milestone command; use the REST API.
declare -A MILESTONES=(
  [E0]="E0 · Foundation & Reproducibility"
  [E1]="E1 · ML Baseline"
  [E2]="E2 · ML Iteration & Validation"
  [E3]="E3 · RAG & Sentiment Layer"
  [E4]="E4 · Backend API"
  [E5]="E5 · Frontend App"
  [E6]="E6 · AWS Deployment"
  [E7]="E7 · MLOps & Monitoring"
)
echo "🎯 Ensuring milestones..."
existing_ms="$(gh api "repos/$REPO/milestones?state=all&per_page=100" -q '.[].title' 2>/dev/null || true)"
for key in E0 E1 E2 E3 E4 E5 E6 E7; do
  title="${MILESTONES[$key]}"
  if grep -qxF "$title" <<< "$existing_ms"; then
    echo "   = $title"
  else
    run "gh api 'repos/$REPO/milestones' -f title='$title' >/dev/null"
  fi
done

# Map epic key -> milestone number (needed to attach issues).
ms_number() { gh api "repos/$REPO/milestones?state=all&per_page=100" -q ".[] | select(.title==\"${MILESTONES[$1]}\") | .number"; }

# ---- Tasks ------------------------------------------------------------------
# id | epic | difficulty-label | type-label | title
TASKS=(
  "E0-T1|E0|diff:easy|type:data|Capture table schemas as SQL DDL"
  "E0-T2|E0|diff:easy|type:ml|Add ML/eval Python dependencies"
  "E0-T3|E0|diff:stretch|type:data|Freeze a versioned training snapshot (parquet)"
  "E0-T4|E0|diff:stretch|type:data|Data-quality sanity checks (nulls, dupes, class balance)"
  "E0-T5|E0|diff:new-territory|type:ml|Verify no future leakage in features (feature contract)"
  "E0-T6|E0|diff:easy|type:ml|Scaffold ml/ project structure"

  "E1-T1|E1|diff:stretch|type:ml|EDA notebook"
  "E1-T2|E1|diff:easy|type:ml|Define feature contract (X, y) in code"
  "E1-T3|E1|diff:new-territory|type:ml|Time-based train/test split (not random)"
  "E1-T4|E1|diff:easy|type:ml|Establish naive baselines"
  "E1-T5|E1|diff:stretch|type:ml|Train baseline models (LogReg + XGB/LGBM)"
  "E1-T6|E1|diff:new-territory|type:ml|Evaluate with the right metrics (PR-AUC, confusion)"
  "E1-T7|E1|diff:easy|type:ml|Save model + metrics artifact + model card"

  "E2-T1|E2|diff:new-territory|type:ml|Walk-forward / expanding-window CV"
  "E2-T2|E2|diff:stretch|type:ml|Feature importance & pruning with SHAP"
  "E2-T3|E2|diff:stretch|type:ml|Feature engineering round 2"
  "E2-T4|E2|diff:new-territory|type:ml|Class imbalance & decision-threshold tuning"
  "E2-T5|E2|diff:stretch|type:ml|Hyperparameter tuning with Optuna"
  "E2-T6|E2|diff:new-territory|type:ml|Signal backtest simulation (P&L, drawdown)"
  "E2-T7|E2|diff:stretch|type:ml|Experiment tracking with MLflow"

  "E3-T1|E3|diff:stretch|type:rag|News ingestion for the 5 tickers"
  "E3-T2|E3|diff:new-territory|type:rag|Enable pgvector & embeddings"
  "E3-T3|E3|diff:stretch|type:rag|Sentiment scoring (FinBERT or Claude Haiku)"
  "E3-T4|E3|diff:new-territory|type:rag|RAG pipeline (retrieve -> Claude explanation)"
  "E3-T5|E3|diff:stretch|type:ml|Feed sentiment into model & measure lift"
  "E3-T6|E3|diff:stretch|type:rag|LLM guardrails & cost controls"

  "E4-T1|E4|diff:easy|type:backend|FastAPI skeleton & config (wire .env)"
  "E4-T2|E4|diff:easy|type:backend|Model loader service"
  "E4-T3|E4|diff:stretch|type:backend|Feature-fetch service"
  "E4-T4|E4|diff:easy|type:backend|Core endpoints (/health, /signal, /signals)"
  "E4-T5|E4|diff:stretch|type:backend|RAG explanation endpoint"
  "E4-T6|E4|diff:stretch|type:backend|Dockerize the API"

  "E5-T1|E5|diff:stretch|type:frontend|Choose stack & scaffold"
  "E5-T2|E5|diff:stretch|type:frontend|Connect to backend (CORS)"
  "E5-T3|E5|diff:stretch|type:frontend|Ticker signal cards"
  "E5-T4|E5|diff:new-territory|type:frontend|Price chart component"
  "E5-T5|E5|diff:stretch|type:frontend|News & rationale panel"
  "E5-T6|E5|diff:stretch|type:frontend|Layout, polish & responsiveness"
  "E5-T7|E5|diff:easy|type:frontend|Frontend Dockerfile"

  "E6-T1|E6|diff:new-territory|type:infra|AWS account, IAM, budget & billing alarm"
  "E6-T2|E6|diff:stretch|type:infra|Fix hardcoded creds -> Secrets Manager"
  "E6-T3|E6|diff:new-territory|type:infra|Managed Postgres on RDS"
  "E6-T4|E6|diff:stretch|type:infra|Container registry (ECR) & push images"
  "E6-T5|E6|diff:new-territory|type:infra|Run containers (App Runner / ECS Fargate)"
  "E6-T6|E6|diff:new-territory|type:infra|CI/CD with GitHub Actions"
  "E6-T7|E6|diff:stretch|type:infra|Logs, metrics & teardown runbook"

  "E7-T1|E7|diff:new-territory|type:infra|Orchestrate pipeline (Airflow DAG)"
  "E7-T2|E7|diff:stretch|type:ml|Scheduled retraining (champion/challenger)"
  "E7-T3|E7|diff:stretch|type:ml|Data drift monitoring"
  "E7-T4|E7|diff:new-territory|type:ml|Prediction/performance monitoring"
  "E7-T5|E7|diff:easy|type:infra|Alerting (email/Slack)"
)

echo "📝 Ensuring issues..."
existing_titles="$(gh issue list --state all --limit 400 --json title -q '.[].title' 2>/dev/null || true)"
for t in "${TASKS[@]}"; do
  IFS='|' read -r id epic diff typ title <<< "$t"
  full="${id}: ${title}"
  if grep -qF "$id:" <<< "$existing_titles"; then
    echo "   = $full"
    continue
  fi
  msnum="$(ms_number "$epic")"
  body="Task **${id}** — see docs/board/ for full subtasks, acceptance criteria, and resources. Source of truth: PROJECT_BOARD.md."
  run "gh issue create --title '$full' --body '$body' --label '${diff}' --label '${typ}' --label 'epic:${epic}' ${msnum:+--milestone '${MILESTONES[$epic]}'}"
done

echo "✅ Done. Now create a Project board in GitHub and add these issues for a drag-and-drop kanban."
echo "   Repo issues: https://github.com/$REPO/issues"
