# E3 · RAG & Sentiment Layer — Context-Aware Signals 🏁 M3

**Goal:** Numbers alone miss *why* a stock moves. Add a news/sentiment layer and a Retrieval-
Augmented Generation (RAG) pipeline so each signal comes with relevant recent news + a
plain-English rationale — and optionally a sentiment feature that feeds back into the model.
This is LLM-shaped work; you'll use **Claude** (see model notes below).

**Target:** Aug 18 – Sep 07 (~3 weeks) · **Depends on:** E2 · **Unlocks:** richer E4 endpoints
**Definition of done:** given a ticker + time, you can retrieve the most relevant news and get a
Claude-generated, cited explanation of the current signal — and you've measured whether a
sentiment feature improves the model.

> **Store vectors in Postgres with `pgvector`.** You already run Postgres — don't add a new DB.
> `CREATE EXTENSION vector;` then a `news_embeddings` table with a `vector(N)` column.

---

### E3-T1 · News ingestion for the 5 tickers 🟡 (~4h)
- [ ] Pull headlines/articles for RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK. Options: RSS feeds (Economic Times, Moneycontrol, Livemint), a free-tier News API, or Yahoo Finance news via `yfinance`'s `.news`.
- [ ] Store in a `news_articles` table: `symbol, published_at (IST), title, body, url, source`. Mirror the pipeline's tz handling (naive IST).
- [ ] **AC:** a table with recent news rows per ticker, deduped by URL.
- ⚠️ Respect each source's ToS / rate limits — mirror the "yfinance is a dev-phase choice" pragmatism from CLAUDE.md.

### E3-T2 · Enable pgvector & embeddings 🔴 (~4h)
- [ ] `CREATE EXTENSION IF NOT EXISTS vector;` add `sql/schema.sql` entry for `news_embeddings(article_id, embedding vector(N), model, created_at)`.
- [ ] Pick an embedding model (a sentence-transformers model like `all-MiniLM-L6-v2` runs locally and free; N=384). Embed each article's title+body.
- [ ] Add an ANN index (`ivfflat`/`hnsw`) for fast similarity search.
- [ ] **AC:** a cosine-similarity query returns the top-k most similar articles to a text query.
- ⭐ Read: pgvector README (indexing + `<=>` operator).

### E3-T3 · Sentiment scoring 🟡 (~4h)
- [ ] Score each article's sentiment. Two paths: (a) a finance-tuned model (FinBERT via HuggingFace), or (b) **Claude Haiku 4.5** for cheap, fast batch classification (`claude-haiku-4-5`, $1/$5 per 1M tok) — good when you want nuance + reasoning.
- [ ] Store `sentiment_score` (−1..1) + `sentiment_label` on the article.
- [ ] Aggregate to a per-symbol, per-time-bucket sentiment feature (e.g. mean sentiment over trailing 24h).
- [ ] **AC:** a `symbol_sentiment` time series you can join to features.

### E3-T4 · The RAG pipeline (retrieve → generate) 🔴 (~5h)
- [ ] Build `rag/explain_signal.py`: given `(symbol, timestamp, model_signal)`, retrieve top-k relevant recent articles via pgvector, then ask Claude to explain the signal grounded in those articles.
- [ ] Use the official Anthropic Python SDK (`pip install anthropic`). Default model **`claude-opus-4-8`** for the best reasoning (or `claude-sonnet-5` to cut cost on volume). Use adaptive thinking: `thinking={"type": "adaptive"}`.
- [ ] Feed retrieved articles as context; instruct Claude to cite which article supports each point and to say "no relevant news" when retrieval is weak (avoid hallucinated rationales).
- [ ] **AC:** a function returning a short, cited, plain-English rationale for a given signal.
- 📌 Auth: set `ANTHROPIC_API_KEY` (or `ant auth login`). Don't hardcode the key — use an env var, unlike the DB creds pattern.

### E3-T5 · Feed sentiment back into the model & measure lift 🟡 (~4h)
- [ ] Add the E3-T3 sentiment feature to the E2 feature set; re-run walk-forward CV + backtest.
- [ ] Compare metrics with vs. without sentiment. Keep it only if it genuinely helps.
- [ ] **AC:** a documented before/after — sentiment either earns its place or gets cut.
- ⚠️ Watch leakage again: only use sentiment from news published *before* candle time T.

### E3-T6 · Guardrails & cost controls for the LLM 🟡 (~2h)
- [ ] Cache RAG explanations (don't re-generate identical requests). Consider the Anthropic Batch API (50% cheaper) for bulk sentiment scoring.
- [ ] Add a token/cost log per call; set a sane `max_tokens`.
- [ ] Handle refusals/errors: check `response.stop_reason` and catch `RateLimitError`.
- [ ] **AC:** predictable, bounded LLM spend + graceful failure.

---

**🏁 Milestone M3 — Context-Aware.** Signals now carry a "why". This is a genuine differentiator
and a great portfolio story.

**Resources for this epic**
- ⭐ Anthropic docs: Messages API, tool use, prompt caching (platform.claude.com/docs)
- ⭐ pgvector GitHub README
- sentence-transformers docs (local embeddings) · FinBERT model card (HuggingFace)
- "What is RAG" primers; Anthropic's "contextual retrieval" blog post
- Model IDs (current): `claude-opus-4-8` (best reasoning), `claude-sonnet-5` (balanced), `claude-haiku-4-5` (cheap/fast classification)
