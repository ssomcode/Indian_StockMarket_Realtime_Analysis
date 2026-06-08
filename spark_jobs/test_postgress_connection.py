from pyspark.sql import SparkSession

# ----------------------------------
# Spark Session
# ----------------------------------

spark = (
    SparkSession.builder
    .appName("Postgres Test")
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

df.show(10, truncate=False)

# ----------------------------------
# Stop Spark
# ----------------------------------

spark.stop()