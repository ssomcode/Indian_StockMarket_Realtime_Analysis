from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'market_ticks',

    bootstrap_servers='localhost:9092',

    auto_offset_reset='earliest',

    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Consumer started...\n")

for message in consumer:

    data = message.value

    print(f"Consumed: {data}")