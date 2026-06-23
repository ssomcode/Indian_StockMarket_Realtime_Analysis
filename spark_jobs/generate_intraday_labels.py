from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

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

spark = (
    SparkSession.builder
    .appName("Intraday Label Generator")
    .getOrCreate()
)

df = (
    spark.read
    .format("jdbc")
    .option(
        "url",
        "jdbc:postgresql://localhost:5432/market_db"
    )
    .option(
        "dbtable",
        "intraday_market_features"
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


# future window

future_window = (
    Window
    .partitionBy("symbol")
    .orderBy("event_time")
    .rowsBetween(1,12)
)


# future prices

df = (

    df

    .withColumn("future_close_12",lead("close_price",12).over(Window.partitionBy("symbol").orderBy("event_time")))

    .withColumn(
        "future_high_12",
        max("high_price")
        .over(future_window)
    )

    .withColumn(
        "future_low_12",
        min("low_price")
        .over(future_window)
    )
)

# rounding up future prices
df = (
    df
    .withColumn(
        "future_close_12",
        round(col("future_close_12"),2)
    )
    .withColumn(
        "future_high_12",
        round(col("future_high_12"),2)
    )
    .withColumn(
        "future_low_12",
        round(col("future_low_12"),2)
    )
)

# Future returns

df = (

    df

    .withColumn(

        "future_return_1h_pct",

        round(

            (
                (
                    col("future_close_12")
                    -
                    col("close_price")
                )
                /
                col("close_price")
            ) * 100,

            4
        )
    )

    .withColumn(

        "future_high_return_1h_pct",

        round(

            (
                (
                    col("future_high_12")
                    -
                    col("close_price")
                )
                /
                col("close_price")
            ) * 100,

            4
        )
    )

    .withColumn(

        "future_low_return_1h_pct",

        round(

            (
                (
                    col("future_low_12")
                    -
                    col("close_price")
                )
                /
                col("close_price")
            ) * 100,

            4
        )
    )

)


# direction column

df = df.withColumn(

    "target_direction",

    when(col("future_return_1h_pct") > 0.1, 1) #considering 1 only if % > 0.1
    .otherwise(0)

)


# risk to reward ratio
df = df.withColumn(
    "reward_risk_ratio",
    when(
        col("future_low_return_1h_pct") != 0,
        round(
            abs(
                col("future_high_return_1h_pct")
                /
                col("future_low_return_1h_pct")
            ),
            4
        )
    ).otherwise(None)
)

# remove last 12 rows per column as they won't have future prices

df = df.filter(
    col("future_close_12").isNotNull()
)


# final dataset 
final_df = df.select(

    "symbol",
    "event_time",
    "close_price",
    "high_price",
    "low_price",

    "future_close_12",
    "future_high_12",
    "future_low_12",

    "future_return_1h_pct",
    "future_high_return_1h_pct",
    "future_low_return_1h_pct",

    "target_direction",
    "reward_risk_ratio"
)



final_df.select(

    "symbol",
    "event_time",
    "close_price",
    "high_price",
    "low_price",
    "future_close_12",
    "future_return_1h_pct",
    "future_high_return_1h_pct",
    "future_low_return_1h_pct",
    "target_direction",
    "reward_risk_ratio"

).show(
    20,
    False
)


# truncate the table before inserting
cursor.execute(
    "TRUNCATE TABLE intraday_training_dataset RESTART IDENTITY;"
)

conn.commit()
cursor.close()
conn.close()


# writting to dataset

print("Inserting to the table ..")
print(f"Rows to insert: {final_df.count()}")

final_df.write \
    .format("jdbc") \
    .option(
        "url",
        "jdbc:postgresql://localhost:5432/market_db"
    ) \
    .option(
        "dbtable",
        "intraday_training_dataset"
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



print("Insertion completed !")


spark.stop()