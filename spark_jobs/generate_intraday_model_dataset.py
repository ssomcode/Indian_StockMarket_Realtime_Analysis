from pyspark.sql import SparkSession
from pyspark.sql.functions import *

import psycopg2


# ----------------------------------
# PostgreSQL Connection
# ----------------------------------

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

spark = SparkSession.builder.appName('Intraday Model Dataset Generator').getOrCreate()

# ----------------------------------
# Read Feature Table
# ----------------------------------

feature_df = (
    spark.read.format("jdbc")
    .option("url","jdbc:postgresql://localhost:5432/market_db")
    .option("dbtable","intraday_market_features")
    .option("user","postgres")
    .option("password","password")
    .option( "driver","org.postgresql.Driver")
    .load()
)

label_df = (
    spark.read.format("jdbc")
    .option("url","jdbc:postgresql://localhost:5432/market_db")
    .option("dbtable","intraday_training_dataset")
    .option("user","postgres")
    .option("password","password")
    .option( "driver","org.postgresql.Driver")
    .load()
)

# ----------------------------------
# Join Features + Labels
# ----------------------------------


model_df = (
    feature_df.alias("f")
    .join(
        label_df.alias("l"),
          on = [ col("f.symbol") == col("l.symbol"),
                 col("f.event_time") == col("l.event_time") ],
                 how = "inner"
          )
)


# ----------------------------------
# Final Dataset
# ----------------------------------

final_df = model_df.select(

    # Keys
    col("f.symbol"),
    col("f.event_time"),

    # Current Prices
    col("f.close_price"),
    col("f.high_price"),
    col("f.low_price"),

    # Previous Candle
    col("f.previous_candle_close"),
    col("f.previous_candle_high"),
    col("f.previous_candle_low"),

    # Momentum
    col("f.candle_return_pct"),
    col("f.return_3_candle_pct"),
    col("f.return_12_candle_pct"),

    # Volatility
    col("f.range_pct"),
    col("f.rolling_volatility_20"),

    # Trend
    col("f.sma_9"),
    col("f.sma_20"),

    col("f.ema_9"),
    col("f.ema_20"),
    col("f.ema_50"),

    col("f.ema_spread"),

    # Distance
    col("f.close_vs_sma9_pct"),
    col("f.close_vs_sma20_pct"),

    col("f.close_vs_ema9_pct"),
    col("f.close_vs_ema20_pct"),
    col("f.close_vs_ema50_pct"),

    # Volume
    col("f.avg_volume_20"),
    col("f.volume_ratio"),

    # Breakout
    col("f.rolling_high_20"),
    col("f.rolling_low_20"),

    col("f.breakout_above_high"),
    col("f.breakdown_below_low"),

    # Oscillator
    col("f.rsi_14"),

    # ---------------- Labels ----------------

    col("l.future_close_12"),
    col("l.future_high_12"),
    col("l.future_low_12"),

    col("l.future_return_1h_pct"),
    col("l.future_high_return_1h_pct"),
    col("l.future_low_return_1h_pct"),

    col("l.reward_risk_ratio"),

    col("l.target_direction")

)


# ----------------------------------
# Validation
# ----------------------------------

print(f"Rows in final dataframe : {final_df.count()}")

final_df.show(20, truncate = False)

# ----------------------------------
# Truncate Target Table
# ----------------------------------

cursor.execute("TRUNCATE TABLE intraday_model_dataset RESTART IDENTITY;")
conn.commit()
cursor.close()
conn.commit()

# ----------------------------------
# Write to PostgreSQL
# ----------------------------------

print("Writing model dataset...")

(
    final_df.write
    .format("jdbc")
    .option(
        "url",
        "jdbc:postgresql://localhost:5432/market_db"
    )
    .option(
        "dbtable",
        "intraday_model_dataset"
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
    .mode("append")
    .save()
)

print("Model dataset created successfully!")

print("Feature Rows :", feature_df.count())
print("Label Rows   :", label_df.count())
print("Model Rows   :", final_df.count())

spark.stop()
