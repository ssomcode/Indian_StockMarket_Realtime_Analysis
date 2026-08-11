# E6 · AWS Deployment — Into Production 🏁 M5

**Goal:** Put the app on AWS so it's reachable on the internet, and learn AWS the way you wanted
— hands-on, incrementally. You're new to AWS/deploy, so this epic favors managed services and
free-tier-friendly choices, with cost guardrails up front. Go slow; every step teaches something.

**Target:** Oct 09 – Oct 29 (~3 weeks) · **Depends on:** E4, E5 · **Unlocks:** M5, E7
**Definition of done:** the frontend + API are reachable via a public URL, backed by managed
Postgres, deployed from a repeatable process — without a scary bill.

> **Cost first, always.** Set an AWS Budget + billing alert on day one. Prefer free-tier
> (RDS db.t3.micro, small Fargate tasks, S3). Tear down what you're not using.

---

### E6-T1 · AWS account, IAM, budget & billing alarm 🔴 (~3h)
- [ ] Create/secure the account: enable MFA on root, create an IAM admin user, stop using root.
- [ ] Set a **Budget** (e.g. $20/mo) with an email alert at 50/80/100%.
- [ ] Install & configure the AWS CLI.
- [ ] **AC:** you can `aws sts get-caller-identity` as your IAM user and a budget alert is armed.
- ⚠️ Do this before launching ANY resource. It's the guardrail that lets you experiment fearlessly.

### E6-T2 · Fix hardcoded credentials → Secrets Manager 🟡 (~3h)
- [ ] The DB creds are hardcoded everywhere (fine for local dev, unacceptable in cloud). Move them to AWS Secrets Manager (or SSM Parameter Store, cheaper).
- [ ] Have the API read secrets from the environment / secrets service at boot.
- [ ] **AC:** no plaintext DB password in any container image or repo file used in prod.

### E6-T3 · Managed Postgres on RDS 🔴 (~4h)
- [ ] Launch an RDS PostgreSQL (db.t3.micro, free tier). Enable pgvector if using E3 (`CREATE EXTENSION vector`).
- [ ] Run `sql/schema.sql` against it; load a data snapshot (or point ingestion at it).
- [ ] Lock down the security group (only your app + your IP).
- [ ] **AC:** you can connect to RDS and your tables exist.

### E6-T4 · Container registry (ECR) & push images 🟡 (~3h)
- [ ] Create ECR repos for `api` and `frontend`. Authenticate Docker to ECR.
- [ ] Build + tag + push the E4/E5 images.
- [ ] **AC:** both images are in ECR.

### E6-T5 · Run the containers (ECS Fargate or App Runner) 🔴 (~5h)
- [ ] Pick a runtime: **App Runner** (simplest — give it an ECR image, get a URL) or **ECS Fargate** (more control, more to learn). Recommend App Runner first.
- [ ] Deploy the API; wire its env/secrets to RDS + Secrets Manager.
- [ ] Deploy the frontend; point it at the API's public URL.
- [ ] **AC:** hitting the public API URL returns live signals; the frontend loads over the internet.
- 🧊 Kafka in the cloud is a big lift — for v1, skip the streaming producer/consumer in prod and serve from batch-loaded RDS data. Add MSK later if you want it.

### E6-T6 · CI/CD with GitHub Actions 🔴 (~4h)
- [ ] A workflow: on push to `main`, build images, push to ECR, trigger a new deployment.
- [ ] Store AWS creds as GitHub secrets (or OIDC role — the better, keyless way).
- [ ] **AC:** pushing to `main` ships to AWS automatically.
- ⭐ This is the "learn production" payoff — automated deploys are a core skill.

### E6-T7 · Logs, metrics & a teardown runbook 🟡 (~3h)
- [ ] Confirm app logs flow to CloudWatch; set an alarm on API errors/5xx.
- [ ] Write `docs/RUNBOOK.md`: how to deploy, roll back, and **tear everything down** to stop charges.
- [ ] **AC:** you can find logs in CloudWatch and you have a written kill-switch for costs.

---

**🏁 Milestone M5 — In Production.** It's live on AWS. You've touched IAM, RDS, ECR, a container
runtime, secrets, and CI/CD — the core of cloud engineering.

**Resources for this epic**
- ⭐ AWS free-tier overview + "how to set a budget alert"
- ⭐ AWS App Runner "deploy from ECR" tutorial (start here) · ECS Fargate workshop (if you go deeper)
- RDS PostgreSQL getting-started · Secrets Manager quickstart
- GitHub Actions → AWS via OIDC (keyless deploys) guide
- ⚠️ "AWS cost horror stories" — read one; it's why E6-T1 exists
