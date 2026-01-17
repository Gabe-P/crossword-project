import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

SOLVE_TIMES_CSV = Path("data/derived/solve_times.csv")


def parse_bool(x: str | None) -> bool | None:
    if x is None:
        return None
    s = x.strip().lower()
    if s in ("true", "t", "1", "yes", "y"):
        return True
    if s in ("false", "f", "0", "no", "n"):
        return False
    if s == "":
        return None
    return None


def main() -> None:
    if not SOLVE_TIMES_CSV.exists():
        raise SystemExit(f"CSV not found: {SOLVE_TIMES_CSV}")

    db_url = os.environ["DATABASE_URL"]

    rows = []
    with open(SOLVE_TIMES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid_raw = (row.get("puzzle_id") or "").strip()
            date_str = (row.get("date") or "").strip()
            if pid_raw == "" or date_str == "":
                continue

            sec_raw = (row.get("seconds_spent_solving") or "").strip()
            seconds = int(sec_raw) if sec_raw != "" else None

            solved = parse_bool(row.get("solved"))

            pf_raw = (row.get("percent_filled") or "").strip()
            percent_filled = float(pf_raw) if pf_raw != "" else None

            rows.append(
                {
                    "puzzle_id": int(pid_raw),
                    "puzzle_date": date_str,
                    "seconds": seconds,
                    "solved": solved,
                    "percent_filled": percent_filled,
                }
            )

    if not rows:
        print("No valid rows found in CSV.")
        return

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO solve_times (
                  puzzle_id, puzzle_date,
                  seconds_spent_solving, solved, percent_filled
                )
                VALUES (
                  %(puzzle_id)s, %(puzzle_date)s::date,
                  %(seconds)s, %(solved)s, %(percent_filled)s
                )
                ON CONFLICT (puzzle_id) DO UPDATE SET
                  puzzle_date = EXCLUDED.puzzle_date,
                  seconds_spent_solving = EXCLUDED.seconds_spent_solving,
                  solved = EXCLUDED.solved,
                  percent_filled = EXCLUDED.percent_filled,
                  updated_at = now()
                """,
                rows,
            )
        conn.commit()

    print(f"Upserted solve times for {len(rows)} puzzles.")


if __name__ == "__main__":
    main()
