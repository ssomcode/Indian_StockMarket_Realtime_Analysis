import psycopg2

connection = psycopg2.connect(
    host = "localhost",
    port = 5432,
    database = "market_db",
    user = "postgres",
    password = "password"
)

cursor = connection.cursor()
