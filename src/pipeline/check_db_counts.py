import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(os.environ['DATABASE_URL']) as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM PUZZLES;')
        print('puzzles:', cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM clue_answers;")
        print("clue_answers:", cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM solve_times;")
        print("solve_times:", cur.fetchone()[0])