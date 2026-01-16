import argparse
import random
import time
from datetime import date, timedelta
from pathlib import Path

import requests

from .fetch_raw_one_date import main as fetch_main
from .extract_pairs_one_date import main as extract_main
from .fetch_solve_time_one_date import main as solve_time_main

RAW_DIR = Path('data/raw')
PAIRS_DIR = Path('data/private_text')
SOLVE_CSV = Path('data/derived/solve_times.csv')

def parse_yyyy_mm_dd(s: str) -> date:

    y, m, d = s.split('-')

    return date(int(y),int(m),int(d))

def iter_dates(start: date, end: date):
    cur = start

    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def load_existing_solve_keys(path: Path) -> set[tuple[str, int]]:
    '''
    Read solve_times.csv to skip known dates
    '''
    if not path.exists():
        return set()
    
    keys: set[tuple[str, int]] = set()

    with open(path, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')

        date_idx = header.index('date')
        pid_idx = header.index('puzzle_id')

        for line in f:
            parts = line.strip().split(',')
            if len(parts) <= max(date_idx, pid_idx):
                continue
            try:
                keys.add((parts[date_idx], int(parts[pid_idx])))
            except ValueError:
                continue
    return keys

def polite_sleep(base_seconds: float, jitter_seconds: float) -> None:
    time.sleep(base_seconds + random.uniform(0, jitter_seconds))

def call_with_backoff(fn, *args, max_retries: int=6, base_backoff: float = 10.0) -> None:

    attempt = 0
    while True:
        try:
            fn(*args)
            return
        except requests.HTTPError as e:
            resp = getattr(e, 'response', None)
            status = resp.status_code if resp is not None else None

            if status in (429, 503) and attempt < max_retries:
                sleep_s = base_backoff * (2 ** attempt) + random.uniform(0, 3)
                print(f'Got {status}. Backing off {sleep_s:.1f}s (attempt {attempt+1}/{max_retries})')
                time.sleep(sleep_s)
                attempt += 1
                continue

            raise

def run_one_date(
    date_str: str,
    solve_keys: set[tuple[str, int]],
    base_sleep_seconds: float,
    jitter_seconds: float,
) -> None:
    raw_path = RAW_DIR / f'{date_str}.json'
    pairs_path = PAIRS_DIR / f'clue_answer_pairs_{date_str}.csv'

    if raw_path.exists():
        print(f'[{date_str}] raw exists -> skip fetch')
    else:
        print(f'[{date_str}] fetching raw...')
        call_with_backoff(fetch_main, date_str)
        polite_sleep(base_sleep_seconds, jitter_seconds)
    
    if pairs_path.exists():
        print(f'[{date_str}] pairs exists -> skip extract')
    else:
        print(f'[{date_str}] extracting pairs...')
        extract_main(date_str)

    import json
    with open(raw_path, 'r', encoding='utf-8') as f:
        puzzle_id = int(json.load(f)['id'])

    if (date_str, puzzle_id) in solve_keys:
        print(f'[{date_str}] solve time exists -> skip')
    else:
        print(f'[{date_str}] fetching solve time...')
        call_with_backoff(solve_time_main, date_str)
        solve_keys.add((date_str, puzzle_id))
        polite_sleep(base_sleep_seconds, jitter_seconds)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True, help='YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='YYYY-MM-DD')
    parser.add_argument('--sleep',type=float,default=3.0,help='Base sleep between network calls (seconds)')
    parser.add_argument('--jitter', type=float, default=2.0, help='Random jitter added to sleep(seconds)')
    args = parser.parse_args()

    start = parse_yyyy_mm_dd(args.start)
    end = parse_yyyy_mm_dd(args.end)
    if end < start:
        raise SystemExit('end must be >= start')
    
    solve_keys = load_existing_solve_keys(SOLVE_CSV)

    print(f"Running range {start.isoformat()} -> {end.isoformat()}")
    print(f"Rate limit: sleep={args.sleep}s + jitter up to {args.jitter}s")
    print(f"Existing solve keys loaded: {len(solve_keys)}")

    for d in iter_dates(start, end):
        date_str = d.isoformat()
        try:
            run_one_date(date_str, solve_keys, args.sleep, args.jitter)
        except Exception as e:
            print(f'[{date_str}] ERROR: {type(e).__name__}: {e}')
            print('Continuing to next date')

            polite_sleep(args.sleep, args.jitter)

if __name__ == '__main__':
    main()