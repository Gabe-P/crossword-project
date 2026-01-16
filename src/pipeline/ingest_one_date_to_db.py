import os
import json
import sys
from pathlib import Path
import csv

import psycopg

from dotenv import load_dotenv

from .extract_pairs_one_date import extract_clue_answer_rows  # reuse your working logic

load_dotenv()

COOKIES_PATH = Path("nyt_cookies.json")
SOLVE_TIMES_CSV = Path("data/derived/solve_times.csv")

def load_raw_puzzle(date_str: str) -> dict:
    path = Path(f'data/raw/{date_str}.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def puzzle_features(puzzle_json: dict) -> tuple[int, int, int, int]:
    payload = puzzle_json['body'][0]
    dims = payload.get('dimensions', {})
    width = int(dims.get('width'))
    height = int(dims.get('height'))
    cells = payload['cells']
    cell_count = len(cells)
    black_count = sum(1 for c in cells if not c or "answer" not in c)
    return width, height, cell_count, black_count

def upsert_puzzle(cur, puzzle_id: int, date_str: str, width: int, height: int, cell_count: int, black_count: int):
    cur.execute(
        '''
        INSERT INTO puzzles (puzzle_id, puzzle_date, width, height, cell_count, black_count)\
        VALUES (%s, %s::date, %s, %s, %s, %s)
        ON CONFLICT (puzzle_id) DO UPDATE SET
            puzzle_date = EXCLUDED.puzzle_date,
            width = EXCLUDED.width,
            height = EXCLUDED.height,
            cell_count = EXCLUDED.cell_count,
            black_count = EXCLUDED.black_count
        ''',
        (puzzle_id, date_str, width, height, cell_count, black_count),
    )

def upsert_clue_answers(cur, rows: list[dict]):
    cur.executemany(
        """
        INSERT INTO clue_answers (
            puzzle_id, clue_id, direction, label, clue_text,
            answer_display, answer_canonical, answer_length, has_rebus
        )
        VALUES (
            %(puzzle_id)s, %(clue_id)s, %(direction)s, %(label)s, %(clue_text)s,
            %(answer_display)s, %(answer_canonical)s, %(answer_length)s, %(has_rebus)s
        )
        ON CONFLICT (puzzle_id, clue_id) DO UPDATE SET
            direction = EXCLUDED.direction,
            label = EXCLUDED.label,
            clue_text = EXCLUDED.clue_text,
            answer_display = EXCLUDED.answer_display,
            answer_canonical = EXCLUDED.answer_canonical,
            answer_length = EXCLUDED.answer_length,
            has_rebus = EXCLUDED.has_rebus
        """,
        rows, 
    )

def upsert_solve_time(cur, puzzle_id:int, date_str: str, seconds: int | None, solved: bool | None, percent_filled: float | None):
    cur.execute(
        """
        INSERT INTO solve_times (puzzle_id, puzzle_date, seconds_spent_solving, solved, percent_filled)
        VALUES (%s, %s::date, %s, %s, %s)
        ON CONFLICT (puzzle_id) DO UPDATE SET
            puzzle_date = EXCLUDED.puzzle_date,
            seconds_spent_solving = EXCLUDED.seconds_spent_solving,
            solved = EXCLUDED.solved,
            percent_filled = EXCLUDED.percent_filled,
            updated_at = now()
        """,
        (puzzle_id, date_str, seconds, solved, percent_filled),
    )

def parse_bool(x: str | None) -> bool | None:
    if x is None:
        return None
    s = x.strip().lower()

    if s in ('true', 't', '1', 'yes','y'):
        return True
    if s in ('false','f','0','no','n'):
        return False
    if s == '':
        return None
    return None

def load_solve_time_from_csv(date_str: str, puzzle_id: int) -> tuple[int | None, bool | None, float | None]:
    if not SOLVE_TIMES_CSV.exists():
        return None, None, None
    
    with open(SOLVE_TIMES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('date') == date_str and row.get('puzzle_id') and int(row['puzzle_id']) == puzzle_id:
                sec_raw = (row.get('seconds_spent_solving') or '').strip()
                seconds = int(sec_raw) if sec_raw != '' else None

                solved = parse_bool(row.get('solved'))

                pf_raw = (row.get('percent_filled') or "").strip()
                percent_filled = float(pf_raw) if pf_raw != "" else None

                return seconds, solved, percent_filled
    return None, None, None


def main(date_str: str) -> None:
    db_url = os.environ['DATABASE_URL']

    puzzle_json = load_raw_puzzle(date_str)
    puzzle_id = int(puzzle_json['id'])

    width, height, cell_count, black_count = puzzle_features(puzzle_json)

    rows = extract_clue_answer_rows(puzzle_json,date_str=date_str)

    seconds, solved, percent_filled = load_solve_time_from_csv(date_str, puzzle_id)


    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            upsert_puzzle(cur, puzzle_id, date_str, width, height, cell_count, black_count)
            upsert_clue_answers(cur, rows)
            upsert_solve_time(cur, puzzle_id, date_str, seconds, solved, percent_filled)
        conn.commit()

    print("Ingested date:", date_str)
    print("Puzzle ID:", puzzle_id)
    print("Clue rows:", len(rows))
    print("seconds_spent_solving:", seconds)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.pipeline.ingest_one_date_to_db YYYY-MM-DD")
        raise SystemExit(2)

    main(sys.argv[1])