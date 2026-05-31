from kafka import KafkaProducer
import yfinance as yf
import json
import time
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

stocks = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS"
]

while True:

    for stock in stocks:

        try:

            ticker = yf.Ticker(stock)

            df = ticker.history(
                period="1d",
                interval="1m"
            )

            if df.empty:
                print(f"No data available for {stock}")
                continue

            latest = df.iloc[-1]

            candle_time = latest.name

            candle_data = {

                "symbol": stock,

                "exchange": "NSE",

                "open_price": round(float(latest["Open"]), 2),

                "high_price": round(float(latest["High"]), 2),

                "low_price": round(float(latest["Low"]), 2),

                "close_price": round(float(latest["Close"]), 2),

                "volume": int(latest["Volume"]),

                "event_time": candle_time.isoformat(),

                "ingestion_time" : datetime.now().isoformat()

            }

            producer.send(
                "market_ticks",
                value=candle_data
            )

            producer.flush()

            # print(
            #     f"Produced: {stock} | "
            #     f"Close={candle_data['close_price']} | "
            #     f"Time={candle_data['event_time']} | "
            #     f"Ingestion Tume {candle_data['ingestion_time']}"
            # )
            print(candle_data)
        except Exception as e:

            print(f"Error for {stock}: {e}")

    time.sleep(60)