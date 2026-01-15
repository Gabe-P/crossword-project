import sys

from .fetch_raw_one_date import main as fetch_main
from .extract_pairs_one_date import main as extract_main
from .fetch_solve_time_one_date import main as solve_time_main

def main(date_str: str) -> None:
    fetch_main(date_str)
    extract_main(date_str)
    solve_time_main(date_str)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python src/pipeline/run_one_date.py YYYY-MM-DD")
        raise SystemExit(2)
    
    main(sys.argv[1])

    