import pandas as pd
import psycopg2
import numpy as np
import os
from dotenv import load_dotenv

# 🔹 Load environment variables from .env
load_dotenv()
# Database connection parameters
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# Create table function
def create_table():
    connection = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = connection.cursor()
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS availability_price (
        id SERIAL PRIMARY KEY,
        hotel_id INT REFERENCES hotels(hotel_id) ON DELETE CASCADE,
        date DATE NOT NULL,
        availability INT NOT NULL CHECK (availability >= 0),
        price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
        currency VARCHAR(10) NOT NULL,
        UNIQUE (hotel_id, date)
    );
    
    CREATE INDEX IF NOT EXISTS idx_availability_price_hotel_date
    ON availability_price (hotel_id, date);
    """
    
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()
    connection.close()

# Load CSV data
file_path = "./scripts/hotel_info.csv"
df = pd.read_csv(file_path)

# Generate availability and price data
hotel_ids = df['hotel_id'].unique().tolist()
dates = pd.date_range(start="2025-04-01", end="2025-04-30")

availability_price_data = []
for hotel_id in hotel_ids:
    base_price = np.random.uniform(50, 500)
    for date in dates:
        price = float(base_price * np.random.uniform(0.8, 1.2))
        availability = int(np.random.randint(0, 20))
        availability_price_data.append((hotel_id, date.date(), availability, round(price, 2), "EUR"))

# Insert data into PostgreSQL
def insert_data(data):
    connection = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = connection.cursor()
    
    insert_query = """
        INSERT INTO availability_price (hotel_id, date, availability, price, currency)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (hotel_id, date) DO NOTHING;
    """
    
    try:
        cursor.executemany(insert_query, data)
        rows_inserted = cursor.rowcount
        connection.commit()
        print(f"Successfully inserted {rows_inserted} records.")
    except Exception as e:
        print("Error inserting data:", e)
        connection.rollback()

# Execute the table creation and data insertion
# create_table()
insert_data(availability_price_data)
print("Table created and data inserted successfully.")
