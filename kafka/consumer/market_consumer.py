from kafka import KafkaConsumer
import psycopg2
import json

consumer = KafkaConsumer(
    "market_candles_1m",

    bootstrap_servers="localhost:9092",

    group_id="market-db-consumer-v1",

    auto_offset_reset="latest",

    value_deserializer=lambda x: json.loads(
        x.decode("utf-8")
    )
)

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="market_db",
    user="postgres",
    password="password"
)

cursor = conn.cursor()

print("DB Consumer Started...")

for message in consumer:

    data = message.value

    insert_query = """
    INSERT INTO market_candles_1m
    (
        symbol,
        exchange,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        event_time,
        ingestion_time
    )
    VALUES
    (
        %s,%s,%s,%s,%s,%s,%s,%s,%s
    )


    ON CONFLICT (symbol, event_time)

    DO UPDATE SET

    exchange = EXCLUDED.exchange,
    open_price = EXCLUDED.open_price,
    high_price = EXCLUDED.high_price,
    low_price = EXCLUDED.low_price,
    close_price = EXCLUDED.close_price,
    volume = EXCLUDED.volume,
    ingestion_time = CURRENT_TIMESTAMP;   
    """

    cursor.execute(
        insert_query,
        (
            data["symbol"],
            data["exchange"],
            data["open_price"],
            data["high_price"],
            data["low_price"],
            data["close_price"],
            data["volume"],
            data["event_time"],
            data["ingestion_time"]
        )
    )

    conn.commit()

    print(
        f"Inserted {data['symbol']} into DB"
    )