import psycopg2
import pandas as pd

# ----------------------------
# DB Connection
# ----------------------------

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="market_db",
    user="postgres",
    password="password"
)

# ----------------------------
# Read Daily Data
# ----------------------------

query = """
SELECT
    symbol,
    event_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM market_candles_daily
ORDER BY symbol,event_date
"""

df = pd.read_sql(query, conn)

print(f"Rows fetched: {len(df)}")

# ----------------------------
# Feature Engineering
# ----------------------------

feature_dfs = []

for symbol in df["symbol"].unique():
# storing whole symbol's data into temp for the loop
    temp = (
        df[df["symbol"] == symbol]
        .copy()
        .sort_values("event_date")
    )

    # Previous Day Values

    temp["previous_day_high"] = (
        temp["high_price"].shift(1)
    )

    temp["previous_day_low"] = (
        temp["low_price"].shift(1)
    )

    temp["previous_day_close"] = (
        temp["close_price"].shift(1)
    )

    # Gap % = (open - PDC) / PDC

    temp["gap_pct"] = (
        (
            temp["open_price"]
            -
            temp["previous_day_close"]
        )
        /
        temp["previous_day_close"]
    ) * 100

    # Daily Return % (Close - PDC) / PDC

    temp["daily_return_pct"] = (
        (
            temp["close_price"]
            -
            temp["previous_day_close"]
        )
        /
        temp["previous_day_close"]
    ) * 100

    # Range % (high - low) / close

    temp["range_pct"] = (
        (
            temp["high_price"]
            -
            temp["low_price"]
        )
        /
        temp["close_price"]
    ) * 100

    # Moving Averages

    temp["sma_20"] = (
        temp["close_price"]
        .rolling(20)
        .mean()
    )

    temp["sma_50"] = (
        temp["close_price"]
        .rolling(50)
        .mean()
    )

    temp["ema_20"] = (
        temp["close_price"]
        .ewm(span=20)
        .mean()
    )

    temp["ema_50"] = (
        temp["close_price"]
        .ewm(span=50)
        .mean()
    )

    temp["ema_spread"] = (
        temp["ema_20"]
        -
        temp["ema_50"]
    )

    # Volume

    temp["avg_volume_20"] = (
        temp["volume"]
        .rolling(20)
        .mean()
    )

    temp["volume_ratio"] = (
        temp["volume"]
        /
        temp["avg_volume_20"]
    )

    feature_dfs.append(temp)

feature_df = pd.concat(feature_dfs)

print(
    f"Features Generated: "
    f"{len(feature_df)}"
)

# ----------------------------
# Load to Feature Store
# ----------------------------

cursor = conn.cursor()

insert_query = """
INSERT INTO daily_market_features
(
    symbol,
    event_date,
    close_price,

    previous_day_high,
    previous_day_low,
    previous_day_close,

    gap_pct,
    daily_return_pct,
    range_pct,

    sma_20,
    sma_50,

    ema_20,
    ema_50,
    ema_spread,

    avg_volume_20,
    volume_ratio
)
VALUES
(
    %s,%s,%s,
    %s,%s,%s,
    %s,%s,%s,
    %s,%s,
    %s,%s,%s,
    %s,%s
)

ON CONFLICT(symbol,event_date)

DO UPDATE SET

close_price = EXCLUDED.close_price,

previous_day_high = EXCLUDED.previous_day_high,
previous_day_low = EXCLUDED.previous_day_low,
previous_day_close = EXCLUDED.previous_day_close,

gap_pct = EXCLUDED.gap_pct,
daily_return_pct = EXCLUDED.daily_return_pct,
range_pct = EXCLUDED.range_pct,

sma_20 = EXCLUDED.sma_20,
sma_50 = EXCLUDED.sma_50,

ema_20 = EXCLUDED.ema_20,
ema_50 = EXCLUDED.ema_50,
ema_spread = EXCLUDED.ema_spread,

avg_volume_20 = EXCLUDED.avg_volume_20,
volume_ratio = EXCLUDED.volume_ratio;
"""

for _, row in feature_df.iterrows():

    cursor.execute(
        insert_query,
        (
            row["symbol"],
            row["event_date"],
            row["close_price"],

            row["previous_day_high"],
            row["previous_day_low"],
            row["previous_day_close"],

            row["gap_pct"],
            row["daily_return_pct"],
            row["range_pct"],

            row["sma_20"],
            row["sma_50"],

            row["ema_20"],
            row["ema_50"],
            row["ema_spread"],

            row["avg_volume_20"],
            row["volume_ratio"]
        )
    )

conn.commit()

cursor.close()
conn.close()

print("Daily Features Loaded Successfully.")