from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *
import pandas as pd
from pyspark.sql.types import *

# creating cursor to execture queries on table
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

# Close vs sma20%
df = df.withColumn(
    "close_vs_sma20_pct",
    round(
        (
            (col("close_price") - col("sma_20"))
            /
            col("sma_20")
        ) * 100,
        2
    )
)

#close vs sma50
df = df.withColumn(
    "close_vs_sma50_pct",
    round(
        (
            (col("close_price") - col("sma_50"))
            /
            col("sma_50")
        ) * 100,
        2
    )
)

#==========================
# metrics of 5 day ago

df = df.withColumn(
    "close_5d_ago",
    lag("close_price", 5)
    .over(window_symbol)
)

df = df.withColumn(
    "return_5d_pct",
    round(
        (
            (
                col("close_price")
                -
                col("close_5d_ago")
            )
            /
            col("close_5d_ago")
        ) * 100,
        2
    )
)

#=========================
# 20 day ago metrics

df = df.withColumn(
    "close_20d_ago",
    lag("close_price", 20)
    .over(window_symbol)
)

df = df.withColumn(
    "return_20d_pct",
    round(
        (
            (
                col("close_price")
                -
                col("close_20d_ago")
            )
            /
            col("close_20d_ago")
        ) * 100,
        2
    )
)

#=========================
# Rolling volatility

# first calculate daily return number
df = df.withColumn(
    "daily_return_raw",
    (
        (
            col("close_price")
            -
            col("previous_day_close")
        )
        /
        col("previous_day_close")
    )
)

# 20 day rolling volatility
df = df.withColumn(
    "rolling_volatility_20",
    round(
        stddev(
            "daily_return_raw"
        ).over(window_20) * 100,
        2
    )
)

df = df.drop(
    "close_20d_ago",
    "close_5d_ago",
    "daily_return_raw"
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
    StructField("close_vs_sma20_pct", DoubleType()),
    StructField("close_vs_sma50_pct", DoubleType()),
    StructField("return_5d_pct", DoubleType()),
    StructField("return_20d_pct", DoubleType()),
    StructField("rolling_volatility_20", DoubleType()),
    StructField("ema_20", DoubleType()),
    StructField("ema_50", DoubleType()),
    StructField("ema_spread", DoubleType()),
    StructField("close_vs_ema20_pct", DoubleType()),
    StructField("close_vs_ema50_pct", DoubleType())
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
        .round(2)
    )

    pdf["ema_50"] = (
        pdf["close_price"]
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
        .round(2)
    )

    pdf["ema_spread"] = (
        pdf["ema_20"]
        -
        pdf["ema_50"]
    ).round(2)

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

    return pdf


feature_df = (
    df
    .groupBy("symbol")
    .applyInPandas(
        calculate_ema,
        schema=result_schema
    )
)

feature_df = (
    feature_df

    .withColumn(
        "sma_20",
        round(col("sma_20"), 2)
    )

    .withColumn(
        "sma_50",
        round(col("sma_50"), 2)
    )

    .withColumn(
        "avg_volume_20",
        round(col("avg_volume_20"), 2)
    )

    .withColumn(
        "volume_ratio",
        round(col("volume_ratio"), 4)
    )
)


final_df = feature_df.select(
    "symbol",
    "event_date",
    "close_price",
    "previous_day_high",
    "previous_day_low",
    "previous_day_close",
    "gap_pct",
    "daily_return_pct",
    "return_5d_pct",
    "return_20d_pct",
    "range_pct",
    "rolling_volatility_20",
    "sma_20",
    "sma_50",
    "ema_20",
    "ema_50",
    "ema_spread",
    "close_vs_sma20_pct",
    "close_vs_sma50_pct",
    "close_vs_ema20_pct",
    "close_vs_ema50_pct",
    "avg_volume_20",
    "volume_ratio"
)



# truncate the table before inserting the data
cursor.execute("TRUNCATE TABLE daily_market_features RESTART IDENTITY;;")

conn.commit()
cursor.close()
conn.close()


print("Rows to load:", final_df.count())
final_df.show(5,False)

## inserting the data into table "daily_market_features"
final_df.write \
    .format("jdbc") \
    .option(
        "url",
        "jdbc:postgresql://localhost:5432/market_db"
    ) \
    .option(
        "dbtable",
        "daily_market_features"
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

#
print("Daily Features Loaded Successfully.")

# ----------------------------------
# Stop Spark
# ----------------------------------

spark.stop()