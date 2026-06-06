import psycopg2
import yfinance as yf
from datetime import datetime
# ----------------------------
# PostgreSQL Connection
# ----------------------------

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="market_db",
    user="postgres",
    password="password"
)

cursor = conn.cursor()

stocks = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS"
]

for stock in stocks:

    print(f"\nLoading {stock}...")

    try:

        df = yf.download(
            tickers=stock,
            period="60d",
            interval="5m",
            progress=False,
            auto_adjust=False
        )

        if df.empty:
            print(f"No data found for {stock}")
            continue

        if hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)
            

        for timestamp, row in df.iterrows():

            insert_query = """
            INSERT INTO market_candles_5m
            (
                symbol,
                exchange,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                event_time
            )
            VALUES
            (
                %s,%s,%s,%s,%s,%s,%s,%s
            )

            ON CONFLICT (symbol, event_time)

            DO UPDATE SET

                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume;
            """

            cursor.execute(
                insert_query,
                (
                    stock,
                    "NSE",
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    int(row["Volume"]),
                    timestamp.to_pydatetime()
                )
            )

        conn.commit()

        print(
            f"{stock} loaded successfully."
        )

    except Exception as e:

        conn.rollback()

        print(
            f"Error loading {stock}: {e}"
        )

cursor.close()
conn.close()

print("\5 min historical backfill completed.")