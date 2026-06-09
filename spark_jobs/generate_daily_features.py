from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *
import pandas as pd
from pyspark.sql.types import *


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
        "market_candles_daily"
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


## converting numeric to decimal

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
        "previous_day_close",
        lit(None).cast("double")
    )
)

# create window
window_symbol = (
    Window.partitionBy('symbol').orderBy('event_date')
)

window_20 = (
    Window.partitionBy('symbol').orderBy('event_date').rowsBetween(-19,0)
)

window_50 = (
    Window.partitionBy('symbol').orderBy('event_date').rowsBetween(-49,0)
)


#Previous day features
df = (
    df
    .withColumn('previous_day_close',lag("close_price",1).over(window_symbol))
    .withColumn('previous_day_high',lag('high_price',1).over(window_symbol))
    .withColumn('previous_day_low',lag('low_price',1).over(window_symbol))
    )

# Gap
df = df.withColumn('gap_pct',round(
                  (col('open_price') - col('previous_day_close')) 
                   / 
                   (col('previous_day_close')) * 100
                   ,2))

# daily return
df = df.withColumn('daily_return_pct',round(
                  (col('close_price') - col('previous_day_close')) 
                   / 
                   (col('previous_day_close')) * 100
                   ,2))

# range_pct
df = df.withColumn('range_pct',round(
                  (col('high_price') - col('low_price')) 
                   / 
                   (col('close_price')) * 100
                   ,2))

# SMA
df = (
    df
    .withColumn('sma_20',avg('close_price').over(window_20))
    .withColumn('sma_50',avg('close_price').over(window_50))
)

# volume and volume ratio
df = (

    df
    .withColumn(
        "avg_volume_20",
        avg("volume")
        .over(window_20)
    )
    .withColumn(
        "volume_ratio",
        col("volume")
        /
        col("avg_volume_20")
    )
)

## Pandas defined function to calculate EMA's

result_schema = StructType([
    StructField("id", LongType()),
    StructField("symbol", StringType()),
    StructField("open_price", DoubleType()),
    StructField("high_price", DoubleType()),
    StructField("low_price", DoubleType()),
    StructField("close_price", DoubleType()),
    StructField("volume", LongType()),
    StructField("event_date", DateType()),
    StructField("ingestion_time", TimestampType()),
    StructField("previous_day_close", DoubleType()),
    StructField("previous_day_high", DoubleType()),
    StructField("previous_day_low", DoubleType()),
    StructField("gap_pct", DoubleType()),
    StructField("daily_return_pct", DoubleType()),
    StructField("range_pct", DoubleType()),
    StructField("sma_20", DoubleType()),
    StructField("sma_50", DoubleType()),
    StructField("avg_volume_20", DoubleType()),
    StructField("volume_ratio", DoubleType()),
    StructField("ema_20", DoubleType()),
    StructField("ema_50", DoubleType()),
    StructField("ema_spread", DoubleType())
])

# function to calulate ema

def calculate_ema(pdf):

    pdf = pdf.sort_values(
        "event_date"
    )

    pdf["ema_20"] = (
        pdf["close_price"]
        .ewm(
            span=20,
            adjust=False
        )
        .mean()
    )

    pdf["ema_50"] = (
        pdf["close_price"]
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
    )

    pdf["ema_spread"] = (
        pdf["ema_20"]
        -
        pdf["ema_50"]
    )

    return pdf


feature_df = (
    df
    .groupBy("symbol")
    .applyInPandas(
        calculate_ema,
        schema=result_schema
    )
)

feature_df.select(
    "symbol",
    "event_date",
    "close_price",
    "sma_20",
    "sma_50",
    "ema_20",
    "ema_50",
    "ema_spread",
    "volume_ratio"
).show(
    20,
    False
)

# ----------------------------------
# Stop Spark
# ----------------------------------

spark.stop()