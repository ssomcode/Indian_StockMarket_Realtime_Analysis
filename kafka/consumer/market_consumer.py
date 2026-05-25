from kafka import KafkaConsumer
import json
import psycopg2

consumer = KafkaConsumer(
    'market_ticks',

    bootstrap_servers='localhost:9092',

    auto_offset_reset='earliest',

    enable_auto_commit=False,

    group_id='market-db-consumer-v2',

    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

connection = psycopg2.connect(
    host='localhost',
    port=5432,
    database='market_db',
    user='postgres',
    password='password'
)

cursor = connection.cursor()

print("DB Consumer started...\n")

for message in consumer:

    data = message.value

    insert_query = """
        INSERT INTO market_ticks
        (
            symbol,
            price,
            volume,
            exchange,
            event_time
        )

        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(
        insert_query,
        (
            data['symbol'],
            data['price'],
            data['volume'],
            data['exchange'],
            data['event_time']
        )
    )

    connection.commit()

    print(f"Inserted into DB: {data}")