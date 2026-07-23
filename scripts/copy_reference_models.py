"""Copy optional local model directories from the read-only reference project.

This script writes only into the current project. Run it only when you really
want local BGE/Reranker/classifier assets because the full copy is about 4.3GB.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REFERENCE_MODELS = Path("/Users/chenshuaiwen/new_eduagent/backend/models")
TARGET_MODELS = Path("backend/models")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy optional reference models.")
    parser.add_argument(
        "--only",
        choices=["classifier", "embedding", "reranker", "all"],
        default="classifier",
        help="Copy classifier only by default; full embedding/reranker copy is large.",
    )
    return parser.parse_args()


def copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        raise SystemExit(f"Reference model path not found: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True)
    print(f"copied {source} -> {target}")


def main() -> None:
    args = parse_args()
    groups = ["classifier", "embedding", "reranker"] if args.only == "all" else [args.only]
    for group in groups:
        copy_tree(REFERENCE_MODELS / group, TARGET_MODELS / group)


if __name__ == "__main__":
    main()
