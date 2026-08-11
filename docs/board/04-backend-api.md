# E4 · Backend API (FastAPI) — Serve the Predictions

**Goal:** Wrap the champion model + RAG layer behind a clean HTTP API. This is your home turf
(backend-strong), so it's a fast, satisfying epic. `fastapi` and `uvicorn` are already in
`requirements.txt` and the `api/` dir is an empty placeholder waiting for you.

**Target:** Sep 08 – Sep 17 (~1.5 weeks) · **Depends on:** E2 (model), E3 (RAG, optional) · **Unlocks:** E5, E6
**Definition of done:** a running FastAPI service that returns a live signal + confidence (+
optional rationale) for a ticker, with `/docs` working and a Dockerfile.

---

### E4-T1 · FastAPI skeleton & config 🟢 (~2h)
- [ ] Scaffold `api/`: `main.py`, `routers/`, `schemas.py`, `services/`.
- [ ] Now is the right time to *actually wire* `config/settings.py` + `.env` (DB creds) instead of the inline-psycopg2 pattern — this is a real service. Fix the `.env` DB name mismatch (`market_db`, not `stockmarket_db`) noted in CLAUDE.md.
- [ ] **AC:** `uvicorn api.main:app --reload` serves and `/docs` (Swagger) loads.

### E4-T2 · Model loader service 🟢 (~2h)
- [ ] `services/model.py`: load the E2 `.pkl` (or fetch from MLflow) once at startup; expose `predict(features) -> {direction, probability}`.
- [ ] Load the exact feature list saved alongside the model (E1-T7) so input columns match.
- [ ] **AC:** the model loads at boot and predicts from an in-memory features dict.

### E4-T3 · Feature-fetch service 🟡 (~3h)
- [ ] `services/features.py`: given a symbol, fetch the latest row from `intraday_market_features` and shape it into model input.
- [ ] Handle "symbol not found / no recent candle" cleanly.
- [ ] **AC:** for a valid symbol, returns a ready-to-predict feature vector.

### E4-T4 · Core endpoints 🟢 (~3h)
- [ ] `GET /health` → status + model version loaded.
- [ ] `GET /signal/{symbol}` → `{symbol, as_of, direction, probability, threshold}` using E4-T2+T3.
- [ ] `GET /signals` → all 5 tracked tickers at once.
- [ ] Pydantic response models for each (typed, self-documenting).
- [ ] **AC:** all three return correct JSON; visible and testable in `/docs`.

### E4-T5 · RAG explanation endpoint 🟡 (~3h)
- [ ] `GET /signal/{symbol}/explain` → calls the E3 RAG pipeline, returns rationale + cited article URLs.
- [ ] Make it async and cache results (LLM calls are slow/costly). Return the numeric signal immediately and the explanation on this separate call so the UI stays snappy.
- [ ] **AC:** endpoint returns a cited explanation, cached on repeat calls.
- 🧊 If E3 slipped, ship E4 without this and add it later — don't block the API on RAG.

### E4-T6 · Dockerize the API 🟡 (~2h)
- [ ] Write `docker/api.Dockerfile`; add the api service to `docker-compose.yml` alongside Postgres/Kafka.
- [ ] Confirm it talks to Postgres over the compose network (not `localhost`).
- [ ] **AC:** `docker-compose up` brings the API up and `/signals` works from the container.
- 📌 This container becomes the E6 AWS deployment unit — build it clean now.

---

**Resources for this epic**
- ⭐ FastAPI official tutorial (it's excellent and fast to read)
- Pydantic v2 models · `python-dotenv` for config
- FastAPI `BackgroundTasks` / async for the RAG endpoint
- "Dockerizing FastAPI" guides
