import os
import pandas as pd
import psycopg2
from psycopg2 import sql
import logging

# Setup logging
logging.basicConfig(filename='duplicates.log', level=logging.INFO, format='%(asctime)s - %(message)s')
logging.basicConfig(filename='missing_images.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Database connection details
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# File paths
DATASET_DIR = "./dataset"
IMAGE_DIR = "./images/train"

# Load datasets
train_set = pd.read_csv(os.path.join(DATASET_DIR, "train_set.csv"))
hotel_info = pd.read_csv(os.path.join(DATASET_DIR, "hotel_info.csv"))
chain_info = pd.read_csv(os.path.join(DATASET_DIR, "chain_info.csv"))

# Establish database connection
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cursor = conn.cursor()

# Create tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS chains (
        chain_id INT PRIMARY KEY,
        chain_name TEXT
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS hotels (
        hotel_id INT PRIMARY KEY,
        hotel_name TEXT,
        chain_id INT REFERENCES chains(chain_id),
        latitude FLOAT,
        longitude FLOAT
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS hotel_availability (
        hotel_id INT REFERENCES hotels(hotel_id) ON DELETE CASCADE,
        date DATE,
        is_available BOOLEAN,
        price_per_night FLOAT,
        PRIMARY KEY (hotel_id, date)
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS images (
        image_id TEXT PRIMARY KEY,
        hotel_id INT REFERENCES hotels(hotel_id),
        image_url TEXT
    );
""")

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()

print("Data inserted successfully!")
