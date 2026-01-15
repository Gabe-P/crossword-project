import csv
import json
import sys
from pathlib import Path

def load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    

def get_payload(puzzle_json: dict) -> dict:

    return puzzle_json['body'][0]

def get_plain_clue_text(clue_obj: dict) -> str:
    return clue_obj['text'][0]['plain']

def get_answer_display_for_clue(clue_obj: dict, grid_cells: list[dict]) -> str:
    letters = []
    for cell_idx in clue_obj['cells']:
        cell = grid_cells[cell_idx]
        letters.append(cell['answer'])
    return "".join(letters)

def canonical_cell_token(cell_obj: dict) -> tuple[str,bool]:
    '''Checking if a particular cell has a rebus answer and returns 
    the letters and a boolean saying it has multiple valid answers'''
    token = cell_obj.get("answer", "")
    is_rebus = False

    if "moreAnswers" in cell_obj and "valid" in cell_obj['moreAnswers']:
        is_rebus = True
        valid = cell_obj['moreAnswers']['valid']

        letters_only = [v for v in valid if v.isalpha()]
        if letters_only:
            token = letters_only[0]
        else:
            token = "".join(ch for ch in valid[0] if ch.isalpha())
    
    return token, is_rebus

def get_answer_canonical_for_clue(clue_obj: dict, grid_cells: list[dict]) -> tuple[str, bool]:

    tokens = []
    has_rebus = False

    for cell_idx in clue_obj['cells']:
        cell = grid_cells[cell_idx]
        token, is_rebus = canonical_cell_token(cell)
        tokens.append(token)
        has_rebus = has_rebus or is_rebus
    
    return "".join(tokens), has_rebus

def extract_clue_answer_rows(puzzle_json: dict, date_str: str) -> list[dict]:
    payload = get_payload(puzzle_json)
    cells = payload['cells']
    clues = payload['clues']

    rows = []

    for clue_id, clue in enumerate(clues):
        clue_text = get_plain_clue_text(clue)
        answer_display = get_answer_display_for_clue(clue, cells)
        answer_canonical, has_rebus = get_answer_canonical_for_clue(clue, cells)

        row = {
            "date": date_str,
            "puzzle_id": puzzle_json['id'],
            "clue_id": clue_id,
            "direction": clue['direction'],
            "label": clue['label'],
            "clue_text": clue_text,
            "answer_display":answer_display,
            "answer_canonical":answer_canonical,
            "answer_length": len(answer_canonical),
            "has_rebus": has_rebus,
        }
        rows.append(row)
    
    return rows

def write_rows_to_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "date",
        "puzzle_id",
        "clue_id",
        "direction",
        "label",
        "clue_text",
        "answer_display",
        "answer_canonical",
        "answer_length",
        "has_rebus",
    ]

    with open(out_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main(date_str: str) -> None:
    in_path = Path(f'data/raw/{date_str}.json')
    out_path = Path(f'data/private_text/clue_answer_pairs_{date_str}.csv')
    puzzle_json = load_json(in_path)
    rows = extract_clue_answer_rows(puzzle_json, date_str=date_str)
    write_rows_to_csv(rows, out_path)

    print(f'Read: {in_path}')
    print(f'Wrote: {out_path}')
    print(f'Rows: {len(rows)}')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/pipeline/extract_pairs_one_date.py YYYY-MM-DD")
        raise SystemExit(2)
    
    main(sys.argv[1])