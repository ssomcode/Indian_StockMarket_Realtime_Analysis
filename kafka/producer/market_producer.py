from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

stocks = [
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK"
]

while True:

    stock_data = {
        "symbol": random.choice(stocks),

        "price": round(random.uniform(1000, 3000), 2),

        "volume": random.randint(1000, 100000),

        "exchange": "NSE",

        "event_time": datetime.now().isoformat()
    }

    producer.send(
        "market_ticks",
        value=stock_data
    )

    print(f"Produced: {stock_data}")

    time.sleep(2)