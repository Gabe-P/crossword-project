import json
import os
from pathlib import Path
import csv
from datetime import datetime

import psycopg
from dotenv import load_dotenv

from .ingest_one_date_to_db import main as ingest_one_date_main

load_dotenv()

RAW_DIR = Path('data/raw')
LOG_DIR = Path("data/private_text/logs")


def get_existing_puzzle_ids(conn) -> set[int]:
    with conn.cursor() as cur:
        cur.execute('SELECT puzzle_id FROM puzzles;')
        return {int(r[0]) for r in cur.fetchall()}

def extract_date_and_id_from_raw(path: Path) -> tuple[str, int]:

    date_str = path.stem
    with open(path, 'r', encoding='utf-8') as f:
        puzzle_json = json.load(f)

    puzzle_id = int(puzzle_json['id'])
    return date_str, puzzle_id

def _run_id() -> str:
    # e.g. 20260117_104522
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    db_url = os.environ['DATABASE_URL']

    raw_files = sorted(RAW_DIR.glob('*.json'))
    if not raw_files:
        print(f'No raw files found in {RAW_DIR}')
        return
    
    with psycopg.connect(db_url) as conn:
        existing_ids = get_existing_puzzle_ids(conn)
    
    print(f'Raw files found: {len(raw_files)}')
    print(f'Puzzles already in DB: {len(existing_ids)}')

    ingested = 0
    skipped = 0
    failed = 0
    run_id = _run_id()
    skipped_rows = []
    failed_rows = []
    ingested_rows = []


    for path in raw_files:
        try:
            date_str, puzzle_id = extract_date_and_id_from_raw(path)

            if puzzle_id in existing_ids:
                skipped += 1
                skipped_rows.append(
                    {"file": path.name, "date": date_str, "puzzle_id": puzzle_id, "reason": "puzzle_id already in DB"}
                )
                continue

            print(f'[{date_str}] ingesting (puzzle_id={puzzle_id})')
            ingest_one_date_main(date_str)
            ingested_rows.append({"file": path.name, "date": date_str, "puzzle_id": puzzle_id})
            ingested += 1
            existing_ids.add(puzzle_id)
        except Exception as e:
            failed += 1
            failed_rows.append(
                {"file": path.name, "date": path.stem, "error_type": type(e).__name__, "error_message": str(e)}
            )
            print(f'[{path.name}] ERROR: {type(e).__name__}: {e}')
            print('Continuing...')

    skipped_path = LOG_DIR / f"sync_skipped_{run_id}.csv"
    failed_path = LOG_DIR / f"sync_failed_{run_id}.csv"
    ingested_path = LOG_DIR / f"sync_ingested_{run_id}.csv"

    _write_rows(skipped_path, ["file", "date", "puzzle_id", "reason"], skipped_rows)
    _write_rows(failed_path, ["file", "date", "error_type", "error_message"], failed_rows)
    _write_rows(ingested_path, ["file", "date", "puzzle_id"], ingested_rows)

    print("Wrote logs:")
    print("  ", ingested_path)
    print("  ", skipped_path)
    print("  ", failed_path)

    print('\nDone.')
    print('Ingested:', ingested)
    print('Skipped:', skipped)
    print('Failed:', failed)

if __name__ == '__main__':
    main()