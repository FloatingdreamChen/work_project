"""Build the Milvus knowledge base for gov exam documents."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build gov exam knowledge base.")
    parser.add_argument("input_dir", type=Path, help="Directory containing source documents.")
    parser.add_argument("--collection", default="gov_exam_knowledge")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input_dir.exists():
        raise SystemExit(f"Input directory not found: {args.input_dir}")
    print("Knowledge base build placeholder")
    print(f"input_dir={args.input_dir}")
    print(f"collection={args.collection}")


if __name__ == "__main__":
    main()
