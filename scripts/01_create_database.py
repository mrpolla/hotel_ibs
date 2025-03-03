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

conn.commit()

# Insert data into chains
for _, row in chain_info.iterrows():
    try:
        cursor.execute(
            "INSERT INTO chains (chain_id, chain_name) VALUES (%s, %s) ON CONFLICT (chain_id) DO NOTHING;",
            (row['chain_id'], row['chain_name'])
        )
    except psycopg2.IntegrityError:
        logging.info(f"Duplicate chain_id: {row['chain_id']}")
        conn.rollback()

# Insert data into hotels
for _, row in hotel_info.iterrows():
    # Generate availability and price per night for 30 days
    try:
        cursor.execute(
            "INSERT INTO hotels (hotel_id, hotel_name, chain_id, latitude, longitude) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (hotel_id) DO NOTHING;",
            (row['hotel_id'], row['hotel_name'], row['chain_id'], row['latitude'], row['longitude'])
        )
    except psycopg2.IntegrityError:
        logging.info(f"Duplicate hotel_id: {row['hotel_id']}")
        conn.rollback()

conn.commit()

# Function to find image path recursively
def find_image_path(base_path, image_id):
    for root, dirs, files in os.walk(base_path):
        if f"{image_id}.jpg" in files:
            return os.path.join(root, f"{image_id}.jpg")
    return None

# Insert data into images
missing_images = []
for index, row in train_set.iterrows():
    if index > 1000:
        break
    hotel_chain_map = hotel_info.set_index('hotel_id')['chain_id'].to_dict()
    chain_id = hotel_chain_map.get(row['hotel_id'], 'unknown')
    if chain_id > 5 or chain_id < 0:
        continue
    print(chain_id)
    print(str(row['hotel_id']))
    base_path = os.path.join(IMAGE_DIR, str(chain_id), str(row['hotel_id']))
    image_path = find_image_path(base_path, row['image_id'])
    
    if image_path:
        try:
            cursor.execute(
                "INSERT INTO images (image_id, hotel_id, image_url) VALUES (%s, %s, %s) ON CONFLICT (image_id) DO NOTHING;",
                (row['image_id'], row['hotel_id'], image_path)
            )
        except psycopg2.IntegrityError:
            conn.rollback()
    

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()

print("Data inserted successfully!")
