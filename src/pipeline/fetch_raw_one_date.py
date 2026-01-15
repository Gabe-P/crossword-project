import json
import sys
from pathlib import Path

import requests

COOKIES_PATH = Path("nyt_cookies.json")

def load_cookies(path: Path) -> dict:
    """
    Load cookies from NYT website and convert them 
    into requests-compatible dict
    """

    with open(path, 'r', encoding='utf-8') as f:
        cookies_list = json.load(f)

    cookies = {}

    for c in cookies_list:
        if "name" in c and "value" in c:
            cookies[c["name"]] = c["value"]
    
    return cookies

def puzzle_url(date_str: str) -> str:
    return f'https://www.nytimes.com/svc/crosswords/v6/puzzle/daily/{date_str}.json'

def fetch_puzzle_json(date_str: str) -> dict:
    cookies = load_cookies(COOKIES_PATH)
    url = puzzle_url(date_str)

    resp = requests.get(url, cookies=cookies)
    resp.raise_for_status
    return resp.json()

def save_raw_json(data: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent = 2)

def main(date_str: str) -> None:
    out_path = Path(f'data/raw/{date_str}.json')

    data = fetch_puzzle_json(date_str)

    save_raw_json(data, out_path)

    print(f"Fetched: {puzzle_url(date_str)}")
    print(f"Saved:   {out_path}")
    print(f"Puzzle ID: {data.get('id')}")      

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python src/pipeline/fetch_raw_one_date.py YYYY-MM-DD")
        raise SystemExit(2)
    
    main(sys.argv[1])
    