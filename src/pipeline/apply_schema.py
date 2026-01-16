import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

SCHEMA_PATH = Path('src/pipeline/schema.sql')

def main() -> None:
    db_url = os.environ['DATABASE_URL']
    sql = SCHEMA_PATH.read_text(encoding='utf-8')

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

    print("Schema applied.")


if __name__ == "__main__":
    main()