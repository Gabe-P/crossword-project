import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

db_url = os.environ['DATABASE_URL']

with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        print("DB OK:", cur.fetchone()[0])