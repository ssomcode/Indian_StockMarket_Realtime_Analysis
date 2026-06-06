from kafka import KafkaProducer
import yfinance as yf
import psycopg2
import pandas as pd
import json
import time
from datetime import datetime

# --------------------------------
# Kafka
# --------------------------------

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# --------------------------------
# PostgreSQL
# --------------------------------

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="market_db",
    user="postgres",
    password="password"
)

cursor = conn.cursor()

# --------------------------------
# Stocks
# --------------------------------

stocks = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS"
]

print("Producer Started...")

# --------------------------------
# Main Loop
# --------------------------------

while True:

    for stock in stocks:

        try:

            # --------------------------------
            # Get latest processed candle
            # --------------------------------

            cursor.execute(
                """
                SELECT MAX(event_time)
                FROM market_candles_1m
                WHERE symbol = %s
                """,
                (stock,)
            )

            last_event_time = cursor.fetchone()[0]

            # --------------------------------
            # Download today's 1-minute candles
            # --------------------------------

            ticker = yf.Ticker(stock)

            df = ticker.history(
                period="1d",
                interval="1m"
            )

            if df.empty:
                print(f"No data available for {stock}")
                continue

            df = df.reset_index()

            # --------------------------------
            # Remove currently forming candle
            # --------------------------------

            if len(df) <= 1:
                continue

            df = df.iloc[:-1]

            # --------------------------------
            # Only fetch missing candles
            # --------------------------------

            if last_event_time is not None:

                last_event_time = (
                    pd.Timestamp(last_event_time)
                    .tz_localize("Asia/Kolkata")
                    )
                

                df = df[
                    df["Datetime"] >
                    last_event_time
                ]

            if df.empty:
                continue

            # --------------------------------
            # Publish all missing candles
            # --------------------------------

            for _, row in df.iterrows():

                candle_data = {

                    "symbol": stock,

                    "exchange": "NSE",

                    "open_price": round(
                        float(row["Open"]), 2
                    ),

                    "high_price": round(
                        float(row["High"]), 2
                    ),

                    "low_price": round(
                        float(row["Low"]), 2
                    ),

                    "close_price": round(
                        float(row["Close"]), 2
                    ),

                    "volume": int(
                        row["Volume"]
                    ),

                    "event_time":
                    row["Datetime"].isoformat(),

                    "ingestion_time":
                    datetime.now().isoformat()
                }

                producer.send(
                    "market_candles_1m",
                    value=candle_data
                )

                print(
                    f"Produced: "
                    f"{stock} | "
                    f"{row['Datetime']}"
                )

            producer.flush()

        except Exception as e:

            print(
                f"Error for {stock}: {e}"
            )

        # print(f"Produced :  {candle_data}")

    time.sleep(60)