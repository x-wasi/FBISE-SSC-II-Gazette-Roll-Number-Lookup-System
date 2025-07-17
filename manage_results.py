"""
manage_results.py
-----------------
Utility to manage parsed Gazette data.
Usage:
    python manage_results.py --stats
    python manage_results.py --dedupe
"""

import argparse
import pandas as pd
from pathlib import Path

DATA_FILE = Path("data/results.csv")

def check_file():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"{DATA_FILE} not found. Parse the PDF first.")

def show_stats():
    check_file()
    df = pd.read_csv(DATA_FILE, dtype={"RollNo": str})
    print(f"Total rows: {len(df)}")
    print(df.head(10))

def dedupe():
    check_file()
    df = pd.read_csv(DATA_FILE, dtype={"RollNo": str})
    before = len(df)
    df.drop_duplicates(subset="RollNo", inplace=True)
    after = len(df)
    df.to_csv(DATA_FILE, index=False)
    print(f"Deduplicated: {before - after} removed. Final rows: {after}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true", help="Show data stats")
    parser.add_argument("--dedupe", action="store_true", help="Remove duplicate roll numbers")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.dedupe:
        dedupe()
    else:
        parser.print_help()
