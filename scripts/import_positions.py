"""Import civil service position tables into PostgreSQL."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import gov exam positions.")
    parser.add_argument("file", type=Path, help="CSV or XLSX position table.")
    parser.add_argument("--exam-year", type=int, required=True)
    parser.add_argument("--exam-type", required=True, help="国考、省考、事业单位等")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.file.exists():
        raise SystemExit(f"File not found: {args.file}")
    print("Position import placeholder")
    print(f"file={args.file}")
    print(f"exam_year={args.exam_year}")
    print(f"exam_type={args.exam_type}")


if __name__ == "__main__":
    main()
