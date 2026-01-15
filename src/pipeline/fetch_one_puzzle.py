import json
import requests
from pathlib import Path

PUZZLE_URL = "https://www.nytimes.com/svc/crosswords/v6/puzzle/daily/2026-01-11.json"
COOKIES_PATH = "nyt_cookies.json"
OUT_PATH = Path("data/raw/2026-01-11.json")

def load_cookies(path: str) -> dict:

    with open(path, 'r', encoding='utf-8') as f:
        cookies_list = json.load(f)
    
    cookies = {}

    for c in cookies_list:
        if "name" in c and "value" in c:
            cookies[c['name']] = c['value']
    
    return cookies

def fetch_puzzle_json() -> dict:
    cookies = load_cookies(COOKIES_PATH)

    resp = requests.get(PUZZLE_URL, cookies=cookies)

    resp.raise_for_status()

    return resp.json()

def save_raw_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__  == "__main__":
    puzzle_json = fetch_puzzle_json()
    print("Puzzle ID:", puzzle_json['id'])

    save_raw_json(puzzle_json, OUT_PATH)
    print(f'Saved raw puzzle JSON to {OUT_PATH}')

