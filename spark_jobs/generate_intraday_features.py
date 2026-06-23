from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.types import *
from pyspark.sql.functions import *
import pandas as pd

# creating cursor
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="market_db",
    user="postgres",
    password="password"
)

cursor = conn.cursor()


# ----------------------------------
# Spark Session
# ----------------------------------

spark = (
    SparkSession.builder
    .appName("Daily Feature Generator")
    .getOrCreate()
)



# ----------------------------------
# Read PostgreSQL Table
# ----------------------------------

df = (
    spark.read
    .format("jdbc")
    .option(
        "url",
        "jdbc:postgresql://localhost:5432/market_db"
    )
    .option(
        "dbtable",
        "market_candles_5m"
    )
    .option(
        "user",
        "postgres"
    )
    .option(
        "password",
        "password"
    )
    .option(
        "driver",
        "org.postgresql.Driver"
    )
    .load()
)

print(f"Total Rows: {df.count()}")



# converting numericals to double
df = (
    df
    .withColumn(
        "open_price",
        col("open_price").cast("double")
    )
    .withColumn(
        "high_price",
        col("high_price").cast("double")
    )
    .withColumn(
        "low_price",
        col("low_price").cast("double")
    )
    .withColumn(
        "close_price",
        col("close_price").cast("double")
    )
    .withColumn(
        "volume",
        col("volume").cast("long")
    )
)


# creating windows
window_symbol = (
    Window.partitionBy("symbol")
    .orderBy("event_time")
)

window_9 = (
    Window.partitionBy("symbol")
    .orderBy("event_time")
    .rowsBetween(-8, 0)
)

window_20 = (
    Window.partitionBy("symbol")
    .orderBy("event_time")
    .rowsBetween(-19, 0)
)

window_50 = (
    Window.partitionBy("symbol")
    .orderBy("event_time")
    .rowsBetween(-49, 0)
)


# previous 20 window
window_20_previous = (
    Window.partitionBy("symbol")
    .orderBy("event_time")
    .rowsBetween(-20, -1)
)




# previous candle features
df = (
    df

    .withColumn(
        "previous_candle_close",
        lag("close_price", 1)
        .over(window_symbol)
    )

    .withColumn(
        "previous_candle_high",
        lag("high_price", 1)
        .over(window_symbol)
    )

    .withColumn(
        "previous_candle_low",
        lag("low_price", 1)
        .over(window_symbol)
    )
)

# momentum features
# candle return
df = df.withColumn(
    "candle_return_pct",
    round(
        (
            (
                col("close_price")
                -
                col("previous_candle_close")
            )
            /
            col("previous_candle_close")
        ) * 100,
        2
    )
)

# 3 candle return
df = df.withColumn(
    "close_3_candles_ago",
    lag("close_price", 3)
    .over(window_symbol)
)

df = df.withColumn(
    "return_3_candle_pct",
    round(
        (
            (
                col("close_price")
                -
                col("close_3_candles_ago")
            )
            /
            col("close_3_candles_ago")
        ) * 100,
        2
    )
)

#12 candle return
df = df.withColumn(
    "close_12_candles_ago",
    lag("close_price", 12)
    .over(window_symbol)
)

df = df.withColumn(
    "return_12_candle_pct",
    round(
        (
            (
                col("close_price")
                -
                col("close_12_candles_ago")
            )
            /
            col("close_12_candles_ago")
        ) * 100,
        2
    )
)


# volatility features

# range %
df = df.withColumn(
    "range_pct",
    round(
        (
            (
                col("high_price")
                -
                col("low_price")
            )
            /
            col("close_price")
        ) * 100,
        2
    )
)

# rolling volatility
df = df.withColumn(
    "rolling_volatility_20",
    round(
        stddev(
            "candle_return_pct"
        ).over(window_20),
        2
    )
)

# SMA
df = (
    df

    .withColumn(
        "sma_9",
        avg("close_price")
        .over(window_9)
    )

    .withColumn(
        "sma_20",
        avg("close_price")
        .over(window_20)
    )
)

# volume features

df = (
    df

    .withColumn(
        "avg_volume_20",
        avg("volume")
        .over(window_20)
    )

    .withColumn(
    "volume_ratio",
    when(
        col("avg_volume_20") != 0,
        round(
            col("volume")
            /
            col("avg_volume_20"),
            4
        )
    ).otherwise(None)
)
)

# ====================================
# Breakout Features
# ====================================

df = (

    df

    .withColumn(
        "rolling_high_20",
        max("high_price")
        .over(window_20_previous)
    )

    .withColumn(
        "rolling_low_20",
        min("low_price")
        .over(window_20_previous)
    )
)

# ====================================
# Breakout Strength
# ====================================

df = (

    df

    .withColumn(
        "breakout_strength_pct",

        round(

            (
                (
                    col("close_price")
                    -
                    col("rolling_high_20")
                )
                /
                col("rolling_high_20")
            ) * 100,

            4
        )
    )

    .withColumn(
        "breakdown_strength_pct",

        round(

            (
                (
                    col("rolling_low_20")
                    -
                    col("close_price")
                )
                /
                col("rolling_low_20")
            ) * 100,

            4
        )
    )
)

# ====================================
# Final Breakout Flags
# ====================================

df = (

    df

    .withColumn(
        "breakout_above_high",

        when(
            col("breakout_strength_pct")
            > 0.10,
            True
        ).otherwise(False)
    )

    .withColumn(
        "breakdown_below_low",

        when(
            col("breakdown_strength_pct")
            > 0.10,
            True
        ).otherwise(False)
    )
)


## pandas defined functions for EMA AND RSI

result_schema = StructType([

    StructField("id", LongType()),
    StructField("symbol", StringType()),
    StructField("open_price", DoubleType()),
    StructField("high_price", DoubleType()),
    StructField("low_price", DoubleType()),
    StructField("close_price", DoubleType()),
    StructField("volume", LongType()),
    StructField("event_time", TimestampType()),
    StructField("ingestion_time", TimestampType()),
    # Previous candle features

    StructField("previous_candle_close", DoubleType()),
    StructField("previous_candle_high", DoubleType()),
    StructField("previous_candle_low", DoubleType()),

    # Momentum

    StructField("candle_return_pct", DoubleType()),
    StructField("return_3_candle_pct", DoubleType()),
    StructField("return_12_candle_pct", DoubleType()),

    # Volatility

    StructField("range_pct", DoubleType()),
    StructField("rolling_volatility_20", DoubleType()),

    # Trend

    StructField("sma_9", DoubleType()),
    StructField("sma_20", DoubleType()),
    StructField("avg_volume_20", DoubleType()),
    StructField("volume_ratio", DoubleType()),
    StructField("rolling_high_20", DoubleType()),
    StructField("rolling_low_20", DoubleType()),
    StructField("breakout_strength_pct",DoubleType()),
    StructField("breakdown_strength_pct",DoubleType()),
    StructField("breakout_above_high", BooleanType()),
    StructField("breakdown_below_low", BooleanType()),

    # EMA Features

    StructField("ema_9", DoubleType()),
    StructField("ema_20", DoubleType()),
    StructField("ema_50", DoubleType()),
    StructField("ema_spread", DoubleType()),
    StructField("close_vs_ema9_pct", DoubleType()),
    StructField("close_vs_ema20_pct", DoubleType()),
    StructField("close_vs_ema50_pct", DoubleType()),

    # SMA Distance

    StructField("close_vs_sma9_pct", DoubleType()),
    StructField("close_vs_sma20_pct", DoubleType()),

    # RSI

    StructField("rsi_14", DoubleType())

])


# calculate EMA and RSI

def calculate_ema_rsi(pdf):

    pdf = pdf.sort_values(
        "event_time"
    )

    # ======================
    # EMA 9
    # ======================

    pdf["ema_9"] = (
        pdf["close_price"]
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
        .round(2)
    )

    # ======================
    # EMA 20
    # ======================

    pdf["ema_20"] = (
        pdf["close_price"]
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
        .round(2)
    )

    # ======================
    # EMA 50
    # ======================

    pdf["ema_50"] = (
        pdf["close_price"]
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
        .round(2)
    )

    # ======================
    # EMA Spread
    # ======================

    pdf["ema_spread"] = (
        pdf["ema_20"]
        -
        pdf["ema_50"]
    ).round(4)

    # ======================
    # Close vs EMA9
    # ======================

    pdf["close_vs_ema9_pct"] = (
        (
            (
                pdf["close_price"]
                -
                pdf["ema_9"]
            )
            /
            pdf["ema_9"]
        ) * 100
    ).round(2)

    # ======================
    # Close vs EMA20
    # ======================

    pdf["close_vs_ema20_pct"] = (
        (
            (
                pdf["close_price"]
                -
                pdf["ema_20"]
            )
            /
            pdf["ema_20"]
        ) * 100
    ).round(2)

    # ======================
    # Close vs EMA50
    # ======================

    pdf["close_vs_ema50_pct"] = (
        (
            (
                pdf["close_price"]
                -
                pdf["ema_50"]
            )
            /
            pdf["ema_50"]
        ) * 100
    ).round(2)

    # ======================
    # Close vs SMA9
    # ======================

    pdf["close_vs_sma9_pct"] = (
        (
            (
                pdf["close_price"]
                -
                pdf["sma_9"]
            )
            /
            pdf["sma_9"]
        ) * 100
    ).round(2)

    # ======================
    # Close vs SMA20
    # ======================

    pdf["close_vs_sma20_pct"] = (
        (
            (
                pdf["close_price"]
                -
                pdf["sma_20"]
            )
            /
            pdf["sma_20"]
        ) * 100
    ).round(2)

    # ======================
    # RSI 14
    # ======================

    delta = pdf["close_price"].diff()

    gain = delta.where(
        delta > 0,
        0
    )

    loss = -delta.where(
        delta < 0,
        0
    )

    avg_gain = (
        gain
        .rolling(14)
        .mean()
    )

    avg_loss = (
        loss
        .rolling(14)
        .mean()
    )

    rs = avg_gain / avg_loss

    pdf["rsi_14"] = (
        100
        -
        (
            100
            /
            (
                1 + rs
            )
        )
    ).round(2)

    return pdf


df = df.drop(
    "exchange",
    "close_3_candles_ago",
    "close_12_candles_ago"
)

feature_df = (
    df
    .groupBy("symbol")
    .applyInPandas(
        calculate_ema_rsi,
        schema=result_schema
    )
)

# final dataframe to load into table

final_df = feature_df.select(

    # Primary Keys

    "symbol",
    "event_time",

    # Price

    "close_price",
    "high_price",
    "low_price",

    # Previous Candle Features

    "previous_candle_close",
    "previous_candle_high",
    "previous_candle_low",

    # Momentum Features

    "candle_return_pct",
    "return_3_candle_pct",
    "return_12_candle_pct",

    # Volatility Features

    "range_pct",
    "rolling_volatility_20",

    # Trend Features

    "sma_9",
    "sma_20",

    "ema_9",
    "ema_20",
    "ema_50",

    "ema_spread",

    # Distance From Trend

    "close_vs_sma9_pct",
    "close_vs_sma20_pct",

    "close_vs_ema9_pct",
    "close_vs_ema20_pct",
    "close_vs_ema50_pct",

    # Volume Features

    "avg_volume_20",
    "volume_ratio",

    # Breakout Features

    "rolling_high_20",
    "rolling_low_20",
    "breakout_strength_pct",
    "breakdown_strength_pct",
    "breakout_above_high",
    "breakdown_below_low",

    # Oscillator

    "rsi_14"
)

# rounding up the numbers

final_df = (
    final_df

    .withColumn(
        "sma_9",
        round(col("sma_9"), 2)
    )

    .withColumn(
        "sma_20",
        round(col("sma_20"), 2)
    )

    .withColumn(
        "avg_volume_20",
        round(col("avg_volume_20"), 2)
    )

    .withColumn(
        "rolling_high_20",
        round(col("rolling_high_20"), 2)
    )

    .withColumn(
        "rolling_low_20",
        round(col("rolling_low_20"), 2)
    )

    .withColumn(
        "volume_ratio",
        round(col("volume_ratio"), 4)
    )

    .withColumn(
        "rolling_volatility_20",
        round(col("rolling_volatility_20"), 4)
    )

    .withColumn(
        "ema_spread",
        round(col("ema_spread"), 4)
    )
)



cursor.execute(
    "TRUNCATE TABLE intraday_market_features RESTART IDENTITY;"
)

conn.commit()
cursor.close()
conn.close()

final_df.write \
    .format("jdbc") \
    .option(
        "url",
        "jdbc:postgresql://localhost:5432/market_db"
    ) \
    .option(
        "dbtable",
        "intraday_market_features"
    ) \
    .option(
        "user",
        "postgres"
    ) \
    .option(
        "password",
        "password"
    ) \
    .option(
        "driver",
        "org.postgresql.Driver"
    ) \
    .mode("append") \
    .save()

print("Insertion into intraday feature table is complete..")
