# E5 · Frontend App — The Thing You Can Show People 🏁 M4

**Goal:** A clean dashboard that shows each ticker's live signal, confidence, a price chart, and
the news/sentiment rationale. You're a frontend beginner, so this epic is broken into small,
scaffolded steps with extra learning time. Don't aim for beautiful — aim for *working and clear*.

**Target:** Sep 18 – Oct 08 (~3 weeks) · **Depends on:** E4 · **Unlocks:** M4, E6
**Definition of done:** a local web app that calls your FastAPI backend and displays signals +
a chart + rationale for the 5 tickers.

> **Recommended stack (beginner-friendly, industry-standard):** React + Vite + TypeScript +
> Tailwind CSS, with `recharts` (simple) or `lightweight-charts` (finance-grade) for charts, and
> `axios`/`fetch` + TanStack Query for data. If React feels heavy, a single-page Streamlit app is
> a legitimate faster path — decide in E5-T1.

---

### E5-T1 · Choose stack & scaffold 🟡 (~3h)
- [ ] Decide: React+Vite (portfolio-grade, more to learn) vs. Streamlit (fastest to a working dashboard, less "app dev"). Write the choice + why in `dashboard/README.md`.
- [ ] Scaffold the project in `dashboard/` (`npm create vite@latest` or a Streamlit `app.py`).
- [ ] Get "hello world" rendering in the browser.
- [ ] **AC:** dev server runs, you can edit a file and see it hot-reload.

### E5-T2 · Connect to the backend 🟡 (~3h)
- [ ] Call `GET /signals` from the frontend; render the raw JSON on the page.
- [ ] Handle CORS (add `CORSMiddleware` in FastAPI for `localhost:5173`).
- [ ] **AC:** live data from your API appears in the browser.
- ⚠️ CORS errors are the classic first wall — expect it, it's a 3-line backend fix.

### E5-T3 · Ticker signal cards 🟡 (~4h)
- [ ] A card per ticker: symbol, direction (▲/▼ with color), confidence %, "as of" time.
- [ ] Loading + error states.
- [ ] **AC:** 5 cards render live signals with sensible styling.

### E5-T4 · Price chart component 🔴 (~5h · new territory)
- [ ] Add an endpoint (or reuse candle data) to feed recent candles to the chart.
- [ ] Render a candlestick or line chart per selected ticker with `recharts`/`lightweight-charts`.
- [ ] Overlay the signal (e.g. a marker where the model says "up").
- [ ] **AC:** a working, readable price chart for a selected ticker.
- ⭐ Charts are the steepest beginner curve here — budget extra time and copy from the library's examples.

### E5-T5 · News & rationale panel 🟡 (~4h)
- [ ] On selecting a ticker, call `/signal/{symbol}/explain`; show the rationale + linked source articles + sentiment.
- [ ] Show a spinner while the LLM call runs (it's slow).
- [ ] **AC:** clicking a ticker shows its explanation and cited news.

### E5-T6 · Layout, polish & responsiveness 🟡 (~4h)
- [ ] Arrange cards + chart + panel into a coherent dashboard grid (Tailwind).
- [ ] Make it usable on a laptop screen; a dark theme is a nice, easy win for a trading UI.
- [ ] Add a manual "refresh" and an auto-refresh interval.
- [ ] **AC:** it looks like a real (if simple) product, not a debug page.

### E5-T7 · Frontend Dockerfile 🟢 (~2h)
- [ ] Multi-stage build (build static assets → serve via nginx), or a Streamlit container.
- [ ] Add to `docker-compose.yml`.
- [ ] **AC:** `docker-compose up` serves the full stack (frontend + API + DB) locally.

---

**🏁 Milestone M4 — Live Locally.** The whole system runs end to end on your machine. Screenshot
it — this is the centerpiece of your portfolio.

**Resources for this epic**
- ⭐ react.dev "Quick Start" + Vite guide · or Streamlit "Get started"
- ⭐ Tailwind CSS docs (utility classes) · a free dashboard UI template for reference
- lightweight-charts (TradingView) or recharts examples
- TanStack Query "overview" (clean data-fetching)
- FastAPI CORS docs
