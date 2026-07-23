"""Build lightweight knowledge chunks for gov exam documents.

This script intentionally has a no-model path. It writes data/knowledge_chunks.jsonl
so the application can retrieve local knowledge before Milvus/BGE are enabled.
When local models are enabled later, this script can be extended to upsert chunks
into Milvus using BGE-M3 embeddings.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import text

from backend.core.knowledge_base import KnowledgeBaseClient, generate_chunk_id
from backend.db.session import AsyncSessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build gov exam knowledge base.")
    parser.add_argument("input_dir", type=Path, help="Directory containing source documents.")
    parser.add_argument("--collection", default="gov_exam_knowledge")
    parser.add_argument("--output", type=Path, default=Path("data/knowledge_chunks.jsonl"))
    parser.add_argument("--write-db", action="store_true", help="Write document/chunk metadata to PostgreSQL.")
    parser.add_argument("--upsert-milvus", action="store_true", help="Embed and upsert chunks to Milvus.")
    return parser.parse_args()


def iter_text_files(input_dir: Path):
    for path in sorted(input_dir.rglob("*")):
        if path.suffix.lower() in {".md", ".txt"} and path.is_file():
            yield path, path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, size: int = 1200, overlap: int = 120) -> list[str]:
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    chunks = []
    start = 0
    while start < len(normalized):
        chunks.append(normalized[start : start + size])
        start += max(1, size - overlap)
    return chunks or [normalized]


async def write_db(records: list[dict]) -> None:
    docs: dict[str, list[dict]] = {}
    for record in records:
        docs.setdefault(record["metadata"]["path"], []).append(record)
    async with AsyncSessionLocal() as db:
        for source_path, chunks in docs.items():
            doc_result = await db.execute(
                text(
                    """
                    INSERT INTO knowledge_documents (source_name, source_path, source_type, metadata)
                    VALUES (:source_name, :source_path, 'local', CAST(:metadata AS JSONB))
                    RETURNING id
                    """
                ),
                {
                    "source_name": Path(source_path).name,
                    "source_path": source_path,
                    "metadata": json.dumps({"chunk_count": len(chunks)}, ensure_ascii=False),
                },
            )
            document_id = str(doc_result.scalar_one())
            for record in chunks:
                record["document_id"] = document_id
                record["id"] = generate_chunk_id(
                    record["content"],
                    document_id,
                    record["metadata"]["chunk_index"],
                )
                await db.execute(
                    text(
                        """
                        INSERT INTO knowledge_chunks (
                            id, document_id, chunk_index, content, source_name, token_count, metadata
                        )
                        VALUES (
                            :id, :document_id, :chunk_index, :content, :source_name, :token_count,
                            CAST(:metadata AS JSONB)
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata
                        """
                    ),
                    {
                        "id": record["id"],
                        "document_id": document_id,
                        "chunk_index": record["metadata"]["chunk_index"],
                        "content": record["content"],
                        "source_name": record["source_name"],
                        "token_count": len(record["content"]),
                        "metadata": json.dumps(record["metadata"], ensure_ascii=False),
                    },
                )
        await db.commit()


async def amain() -> None:
    args = parse_args()
    if not args.input_dir.exists():
        raise SystemExit(f"Input directory not found: {args.input_dir}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with args.output.open("w", encoding="utf-8") as fp:
        for path, text in iter_text_files(args.input_dir):
            for index, chunk in enumerate(chunk_text(text), start=1):
                record = {
                    "id": generate_chunk_id(chunk, str(path), index),
                    "document_id": str(path),
                    "content": chunk,
                    "source_name": f"{path.name}#{index}",
                    "metadata": {
                        "path": str(path),
                        "chunk_index": index,
                        "collection": args.collection,
                    },
                }
                fp.write(json.dumps(record, ensure_ascii=False) + "\n")
                records.append(record)
    if args.write_db:
        await write_db(records)
        print("PostgreSQL knowledge metadata written")
    if args.upsert_milvus:
        count = KnowledgeBaseClient().upsert_chunks(records)
        print(f"Milvus chunks upserted: {count}")
    print(f"Knowledge chunks written: {len(records)}")
    print(f"output={args.output}")


if __name__ == "__main__":
    asyncio.run(amain())
