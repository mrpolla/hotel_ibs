import psycopg2
import pandas as pd
import json
import os
from dotenv import load_dotenv

# 🔹 Load environment variables from .env
load_dotenv()

# 🔹 PostgreSQL Connection Details (Modify with your actual credentials)
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# 🔹 CSV File Path (Change this to the actual path on your system)
CSV_PATH = os.getenv("CSV_PATH")

# ✅ Function to Connect to PostgreSQL
def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )

# ✅ Create the `image_tags` Table If It Doesn't Exist
def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS image_tags (
        image_id INT,
        tag_name TEXT,
        confidence_score FLOAT,
        PRIMARY KEY (image_id, tag_name)
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()

# ✅ Function to Insert Tags into Database
def insert_tags_into_db():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Load CSV File
    df = pd.read_csv(CSV_PATH)

    for _, row in df.iterrows():
        image_id = row["image_id"]
        
        # Convert tags from string to dictionary
        tags = json.loads(row["tags"].replace("'", "\""))  # Fix single quotes

        for tag, score in tags.items():
            cursor.execute("""
                INSERT INTO image_tags (image_id, tag_name, confidence_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (image_id, tag_name) DO NOTHING;
            """, (image_id, tag, score))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tags successfully inserted into the database.")

# ✅ Function to Fetch and Print Data for Verification
def fetch_data():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM image_tags LIMIT 10;")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

# 🔹 Main Execution
if __name__ == "__main__":
    create_table()  # Ensure table exists
    insert_tags_into_db()  # Insert data
    print("✅ First 10 Rows from the Database:")
    print(fetch_data())  # Verify inserted data
