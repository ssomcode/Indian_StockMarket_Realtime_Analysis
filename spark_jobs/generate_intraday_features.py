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
        round(
            col("volume")
            /
            col("avg_volume_20"),
            4
        )
    )
)

# rolling high and low

df = (
    df

    .withColumn(
        "rolling_high_20",
        max("high_price")
        .over(window_20)
    )

    .withColumn(
        "rolling_low_20",
        min("low_price")
        .over(window_20)
    )
)

# breakout and breakdown - 20 candle

df = (
    df

    .withColumn(
        "breakout_above_high",
        when(
            col("close_price")
            >
            col("rolling_high_20"),
            True
        ).otherwise(False)
    )

    .withColumn(
        "breakdown_below_low",
        when(
            col("close_price")
            <
            col("rolling_low_20"),
            True
        ).otherwise(False)
    )
)