import csv
import json
import sys
from pathlib import Path
import requests

COOKIES_PATH = Path('nyt_cookies.json')
OUT_PATH = Path('data/derived/solve_times.csv')

def load_cookies(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        cookies_list = json.load(f)

    cookies = {}

    for c in cookies_list:
        if "name" in c and "value" in c:
            cookies[c['name']] = c['value']

    return cookies

def load_puzzle_id(date_str: str) -> int:
    in_path = Path(f'data/raw/{date_str}.json')
    with open(in_path, 'r', encoding='utf-8') as f:
        puzzle_json = json.load(f)
    return int(puzzle_json['id'])

def puzzle_stats_url(puzzle_id: int) -> str:
    return f'https://www.nytimes.com/svc/crosswords/v6/game/{puzzle_id}.json'

def fetch_puzzle_stats_json(puzzle_id: int) -> dict:
    cookies = load_cookies(COOKIES_PATH)
    url = puzzle_stats_url(puzzle_id)

    resp = requests.get(url, cookies=cookies)
    resp.raise_for_status
    return resp.json()

def extract_seconds_spent_solving(puzzle_stats_json: dict) -> int | None:
    '''
    Puzzle completion depends on if 'secondsSpentSolving' is present in the json
    '''

    calcs = puzzle_stats_json.get('calcs',{})

    seconds = calcs.get('secondsSpentSolving')

    if seconds is None:
        return None

    return int(seconds)

def extract_optional_calcs(puzzle_stats_json: dict) -> tuple[bool | None, float | None]:

    calcs = puzzle_stats_json.get('calcs',{})

    solved = calcs.get('solved')

    percent_filled = calcs.get('percentFilled')

    return solved, percent_filled

def append_row(out_path: Path, row: dict) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['date', 'puzzle_id', 'seconds_spent_solving', 'solved', 'percent_filled']

    file_exists = out_path.exists()

    with open(out_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def load_existing_keys(path: Path) -> set[tuple[str, int]]:
    if not path.exists():
        return set()
    
    keys = set()

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keys.add((row['date']))

def main(date_str: str) -> None:
    puzzle_id = load_puzzle_id(date_str)
    puzzle_stats_json = fetch_puzzle_stats_json(puzzle_id)

    seconds = extract_seconds_spent_solving(puzzle_stats_json)

    solved, percent_filled = extract_optional_calcs(puzzle_stats_json)
    
    append_row(
        OUT_PATH,
        {
            'date':date_str,
            'puzzle_id':puzzle_id,
            'seconds_spent_solving':seconds,
            'solved':solved,
            'percent_filled':percent_filled,
        }
    )

    print('Date:', date_str)
    print('Puzzle ID:', puzzle_id)
    print('Seconds Spent Solving:', seconds)
    print('Wrote/updated:', OUT_PATH)

if __name__  == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python -m src.pipeline.fetch_solve_time_one_date YYYY-MM-DD")
        raise SystemExit(2)
    
    main(sys.argv[1])