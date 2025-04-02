import psycopg2
import csv
import time
from datetime import datetime

PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "quartz",
    "user": "griffin",
    "password": "123456"
}

CSV_FILE = "data.csv"

def connect_postgres():
    """Connect to PostgreSQL."""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        print("Connected to PostgreSQL")
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def read_csv_batch(start_idx, batch_size=10):
    """Read a batch of rows from the CSV file."""
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)
        end_idx = min(start_idx + batch_size, len(data))
        rows = data[start_idx:end_idx]
    return rows

def insert_postgres_data(conn, rows):
    """Insert a batch of rows into PostgreSQL."""
    try:
        cur = conn.cursor()
        query = """
        INSERT INTO source (id, user_id, user_verified, username, url, published_on, text, image_count, video_count, has_audio)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
        for row in rows:
            data = (
                row["id"],
                row["user_id"],
                row["user_verified"].lower() == "true",
                row["username"],
                row["url"],
                row["published_on"],
                row["text"],
                int(row["image_count"]) if row["image_count"] else None,
		int(row["video_count"]) if row["video_count"] else None,
                row["has_audio"].lower() == "true" if row["has_audio"] else None
            )
            cur.execute(query, data)
        conn.commit()
        print(f"Inserted {len(rows)} rows into PostgreSQL")
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        cur.close()

def main():
    conn = connect_postgres()
    if not conn:
        return

    start_idx = 0
    batch_size = 10

    while True:
        rows = read_csv_batch(start_idx, batch_size)
        if not rows:
            print("No more data to insert. Exiting.")
            break

        insert_postgres_data(conn, rows)
        start_idx += batch_size
        time.sleep(10)

    conn.close()

if __name__ == "__main__":
    main()
