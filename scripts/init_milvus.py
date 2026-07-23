"""Initialize the Milvus collection used by GovExamAgent RAG."""

from __future__ import annotations

import argparse

from backend.core.knowledge_base import KnowledgeBaseClient
from backend.core.model_registry import LocalModelRegistry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize Milvus collection.")
    parser.add_argument("--check-models", action="store_true", help="Also print local model readiness.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check_models:
        for name, status in LocalModelRegistry.status().items():
            print(
                f"{name}: exists={status.exists} path={status.resolved_path} "
                f"missing={status.missing_files} size_mb={status.size_mb}"
            )
    result = KnowledgeBaseClient().ensure_collection()
    print(f"Milvus collection ready: {result}")


if __name__ == "__main__":
    main()
