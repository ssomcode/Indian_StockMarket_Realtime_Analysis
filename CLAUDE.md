# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A supervised ML **training-data pipeline** for intraday NSE stock price-direction
prediction. It tracks 5 blue-chip NSE tickers: `RELIANCE.NS`, `TCS.NS`, `INFY.NS`,
`HDFCBANK.NS`, `ICICIBANK.NS` (hardcoded as a `stocks` list in each ingestion script).

The README advertises a larger "Production-grade real-time analytics" vision (FastAPI,
sentiment, alerts, dashboard, AWS), but **only the data ingestion → feature → label
pipeline is actually built**. The `api/`, `dashboard/`, `sentiment/`, `ml_models/`,
`airflow/`, `ingestion/`, and `docker/` directories are empty placeholders.

## Architecture & data flow

```
yfinance (Yahoo Finance, unofficial)
  │
  ├─ historical_data/*.py ──────────────► PostgreSQL raw candle tables
  │   (one-shot backfill: 1D/5m/1m)        market_candles_daily
  │                                        market_candles_5m
  │                                        market_candles_1m
  │
  └─ kafka/producer/market_producer.py ──► Kafka topic: market_candles_1m
        (polls every 60s for new 1m candles)        │
                                                     ▼
                              kafka/consumer/market_consumer.py
                                  (UPSERT into market_candles_1m)

PostgreSQL raw tables
  │
  ├─ spark_jobs/generate_daily_features.py    ─► daily_market_features    (from _daily)
  ├─ spark_jobs/generate_intraday_features.py ─► intraday_market_features (from _5m)
  └─ spark_jobs/generate_intraday_labels.py   ─► intraday_training_dataset (from features)
       (adds 12-candle / ~1hr lookahead labels: target_direction, reward_risk_ratio)
```

The end product is the `intraday_training_dataset` table — the labeled dataset a future
ML training stage would consume. ML training/serving does not exist yet.

## Running things

There is no build, test runner, or lint setup. `tests/` and `scripts/test.py` are
stubs/scratch. Everything is run as standalone Python scripts against local infra.

**1. Start infrastructure** (Postgres, pgAdmin, Kafka, Zookeeper):
```bash
docker-compose up -d
```
Postgres → `localhost:5432` (db `market_db`, user `postgres`, pw `password`).
pgAdmin → `localhost:5050` (`admin@admin.com` / `admin`). Kafka → `localhost:9092`.

The raw candle tables and feature/label tables are **not** created by any script in the
repo — they must already exist in Postgres (created manually / in pgAdmin). Inserts
assume the schema and unique constraints (e.g. `ON CONFLICT (symbol, event_time)`) are
present. If a table is missing, create it before running the job that writes to it.

**2. Backfill historical candles** (run once; safe to re-run — they UPSERT):
```bash
python historical_data/historical_data_1D.py   # daily, multi-year
python historical_data/historical_data_5m.py    # 5-minute, ~60d
python historical_data/historical_data_1m.py     # 1-minute, ~8d
```

**3. Stream live 1m candles** (two long-running processes, separate terminals):
```bash
python kafka/consumer/market_consumer.py   # start consumer first
python kafka/producer/market_producer.py   # then producer (polls yfinance every 60s)
```

**4. Generate features & labels** (PySpark — require the bundled JDBC driver):
```bash
spark-submit --jars drivers/postgresql-42.7.11.jar spark_jobs/generate_daily_features.py
spark-submit --jars drivers/postgresql-42.7.11.jar spark_jobs/generate_intraday_features.py
spark-submit --jars drivers/postgresql-42.7.11.jar spark_jobs/generate_intraday_labels.py
```
The Postgres JDBC driver is committed at `drivers/postgresql-42.7.11.jar` and must be on
Spark's classpath (`--jars`). Run order matters: intraday **labels** read from
`intraday_market_features`, so run the intraday features job first.

Python deps: `pip install -r requirements.txt` (yfinance, kafka-python, pyspark via
spark-submit, psycopg2-binary, pandas, etc.).

## Conventions & gotchas specific to this codebase

- **Credentials are hardcoded** in every script (`host=localhost`, `database=market_db`,
  `user=postgres`, `password=password`). `config/settings.py` + `config/database.py` +
  `.env` exist but are **not wired up** — `.env` even names a different DB
  (`stockmarket_db`). Ignore `config/` and `.env`; the live value is `market_db`. If you
  add a script, follow the existing inline-psycopg2 pattern unless explicitly asked to
  refactor onto `config/`.

- **Spark feature jobs fully TRUNCATE then append.** Each `generate_*` job runs
  `TRUNCATE TABLE <target> RESTART IDENTITY` before writing `.mode("append")`. This is a
  deliberate dev-phase full-rebuild, not incremental. Do not assume idempotent merges.

- **Timezone handling is explicit and load-bearing.** yfinance returns tz-aware
  timestamps; ingestion converts to `Asia/Kolkata` and stores naive IST in
  `event_time`/`event_date`. The producer also localizes the DB's last `event_time` to
  IST before comparing. Preserve this when touching time logic.

- **The producer drops the last (forming) candle** (`df.iloc[:-1]`) and only publishes
  candles newer than `MAX(event_time)` already in `market_candles_1m`, to avoid emitting
  an incomplete bar and re-emitting history.

- **EMA & RSI are computed in pandas, not Spark SQL.** The feature jobs do windowed
  Spark aggregations (SMA, volatility, breakout, returns) but delegate EMA/RSI to a
  `groupBy("symbol").applyInPandas(...)` UDF with an explicit `result_schema`
  `StructType`. If you add a feature column, you must update both the select list **and**
  the `result_schema` (and the target table's columns), or the write will fail.

- **Two copies of `generate_daily_features.py` exist.** `spark_jobs/` is the **active
  PySpark version**. `feature_engineering/generate_daily_features.py` is an **older,
  superseded pandas-only version** (read-via-`pd.read_sql`, per-symbol loop, UPSERT). Edit
  the `spark_jobs/` one unless you have a specific reason not to.

- **Label definition** (`generate_intraday_labels.py`): lookahead is 12 candles of 5m
  data (~1 hour). `target_direction = 1` iff `future_return_1h_pct > 0.1` (0.1% threshold),
  else 0. Last 12 rows per symbol are dropped (no future). `reward_risk_ratio` =
  |future_high_return / future_low_return|.

## yfinance is intentional (for now)

yfinance is an unofficial Yahoo Finance scraper chosen deliberately for the dev/learning
phase; the documented plan is to swap to Upstox webhooks once the pipeline is solid. Don't
"fix" it to a paid/official API unless asked.
