from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.config import PROJECT_ROOT, get_settings
from backend.core.exceptions import MilvusConnectionError
from backend.core.logger import get_logger
from backend.core.model_registry import LocalModelRegistry


logger = get_logger(__name__)


@dataclass
class KnowledgeDocument:
    content: str
    source_name: str
    score: float = 0.0
    metadata: dict[str, Any] | None = None


class LocalKeywordKnowledgeStore:
    """Small no-model fallback retriever over local docs and project text files."""

    def __init__(self, docs_dir: Path | None = None) -> None:
        self.docs_dir = docs_dir or PROJECT_ROOT / "docs"
        self._documents: list[KnowledgeDocument] | None = None

    def search(self, query: str, top_k: int = 3) -> list[KnowledgeDocument]:
        docs = self._load()
        tokens = self._tokens(query)
        if not tokens:
            return docs[:top_k]

        scored: list[KnowledgeDocument] = []
        for doc in docs:
            content_lower = doc.content.lower()
            score = sum(content_lower.count(token) for token in tokens)
            if score:
                scored.append(
                    KnowledgeDocument(
                        content=doc.content,
                        source_name=doc.source_name,
                        score=float(score),
                        metadata=doc.metadata or {},
                    )
                )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def _load(self) -> list[KnowledgeDocument]:
        if self._documents is not None:
            return self._documents
        docs: list[KnowledgeDocument] = []
        kb_file = PROJECT_ROOT / "data" / "knowledge_chunks.jsonl"
        if kb_file.exists():
            import json

            for line in kb_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                docs.append(
                    KnowledgeDocument(
                        content=item.get("content", ""),
                        source_name=item.get("source_name", "knowledge_chunks.jsonl"),
                        metadata=item.get("metadata", {}),
                    )
                )
        for path in sorted(self.docs_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for index, chunk in enumerate(self._chunk(text)):
                docs.append(
                    KnowledgeDocument(
                        content=chunk,
                        source_name=f"{path.name}#{index + 1}",
                        metadata={"path": str(path), "retriever": "local_keyword"},
                    )
                )
        self._documents = docs
        return docs

    def _chunk(self, text: str, size: int = 1200) -> list[str]:
        normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        return [normalized[index : index + size] for index in range(0, len(normalized), size)] or [normalized]

    def _tokens(self, query: str) -> list[str]:
        raw = query.lower().replace("，", " ").replace("。", " ").replace("？", " ")
        tokens = [part.strip() for part in raw.split() if len(part.strip()) >= 2]
        if not tokens and query.strip():
            tokens = [query.strip().lower()]
        return tokens


class LocalSemanticKnowledgeStore:
    """BGE-M3 local dense retrieval fallback when Milvus is not available."""

    def __init__(self, keyword_store: LocalKeywordKnowledgeStore | None = None) -> None:
        self.keyword_store = keyword_store or LocalKeywordKnowledgeStore()
        self.cache_path = PROJECT_ROOT / "data" / "rag_embedding_cache.jsonl"

    def search(self, query: str, top_k: int = 3) -> list[KnowledgeDocument]:
        docs = self.keyword_store._load()
        if not docs:
            return []
        embeddings = self._load_or_build_embeddings(docs)
        query_dense, _ = BGEM3Embedder.get_instance().encode_query(query)
        scored: list[KnowledgeDocument] = []
        for index, doc in enumerate(docs):
            embedding = embeddings.get(self._doc_key(doc, index))
            if not embedding:
                continue
            score = self._cosine(query_dense, embedding)
            if score <= 0:
                continue
            metadata = {**(doc.metadata or {}), "retriever": "local_bge_m3_dense"}
            scored.append(
                KnowledgeDocument(
                    content=doc.content,
                    source_name=doc.source_name,
                    score=score,
                    metadata=metadata,
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        candidates = scored[: max(top_k * 4, top_k)]
        return self._rerank(query, candidates, top_k)

    def _load_or_build_embeddings(self, docs: list[KnowledgeDocument]) -> dict[str, list[float]]:
        cached = self._read_cache()
        missing = [
            (index, doc)
            for index, doc in enumerate(docs)
            if self._doc_key(doc, index) not in cached
        ]
        if missing:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            embedder = BGEM3Embedder.get_instance()
            dense_vecs, _ = embedder.encode([doc.content for _, doc in missing])
            with self.cache_path.open("a", encoding="utf-8") as fp:
                for (index, doc), embedding in zip(missing, dense_vecs, strict=False):
                    row = {
                        "key": self._doc_key(doc, index),
                        "source_name": doc.source_name,
                        "content_hash": hashlib.md5(doc.content.encode("utf-8")).hexdigest(),
                        "embedding": embedding,
                    }
                    fp.write(json.dumps(row, ensure_ascii=False) + "\n")
                    cached[row["key"]] = embedding
        return cached

    def _read_cache(self) -> dict[str, list[float]]:
        if not self.cache_path.exists():
            return {}
        cached: dict[str, list[float]] = {}
        for line in self.cache_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            embedding = row.get("embedding")
            if isinstance(embedding, list):
                cached[str(row.get("key"))] = [float(value) for value in embedding]
        return cached

    def _rerank(self, query: str, docs: list[KnowledgeDocument], top_k: int) -> list[KnowledgeDocument]:
        if not docs or not LocalModelRegistry.ready_for_vector_rag():
            return docs[:top_k]
        try:
            from backend.core.reranker import BGEReranker

            documents = [
                {"content": doc.content, "metadata": {"source_name": doc.source_name, **(doc.metadata or {})}}
                for doc in docs
            ]
            ranked, _ = BGEReranker.get_instance().rerank_with_confidence(query, documents, top_k=top_k)
            return [
                KnowledgeDocument(
                    content=item.content,
                    source_name=item.metadata.get("source_name", "知识库"),
                    score=item.score,
                    metadata={**item.metadata, "retriever": "local_bge_m3_dense_reranked"},
                )
                for item in ranked
            ]
        except Exception as exc:
            logger.warning("knowledge.local_rerank_failed | error=%s", exc)
            return docs[:top_k]

    def _doc_key(self, doc: KnowledgeDocument, index: int) -> str:
        digest = hashlib.md5(doc.content.encode("utf-8")).hexdigest()
        return f"{doc.source_name}:{index}:{digest}"

    def _cosine(self, left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)


class KnowledgeBaseClient:
    """Knowledge retrieval with optional local BGE/Milvus and keyword fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_store = LocalKeywordKnowledgeStore()
        self.semantic_store = LocalSemanticKnowledgeStore(self.local_store)

    async def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if self.settings.enable_local_models and self.settings.enable_milvus_rag:
            try:
                return await self._search_milvus(query, top_k)
            except Exception as exc:
                logger.warning("knowledge.milvus_failed | error=%s", exc)

        if self.settings.enable_local_models and self.settings.enable_local_semantic_rag:
            try:
                docs = await self._search_local_semantic(query, top_k)
                if docs:
                    return self._format_docs(docs, high_confidence_threshold=0.62)
            except Exception as exc:
                logger.warning("knowledge.local_semantic_failed | error=%s", exc)

        docs = self.local_store.search(query, top_k=top_k)
        return self._format_docs(docs, high_confidence_threshold=8.0, keyword_mode=True)

    def _format_docs(
        self,
        docs: list[KnowledgeDocument],
        *,
        high_confidence_threshold: float,
        keyword_mode: bool = False,
    ) -> list[dict[str, Any]]:
        return [
            {
                "content": doc.content,
                "source_name": doc.source_name,
                "score": doc.score,
                "confidence": self._confidence(doc.score, keyword_mode=keyword_mode),
                "is_high_confidence": doc.score >= high_confidence_threshold,
                "metadata": doc.metadata or {},
            }
            for doc in docs
        ]

    def _confidence(self, score: float, *, keyword_mode: bool) -> float:
        if keyword_mode:
            return min(0.74, score / 10) if score else 0.0
        return max(0.0, min(0.95, (score + 1) / 2))

    async def _search_milvus(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Optional heavy path. Requires local BGE/Reranker models and Milvus."""
        import asyncio

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._search_milvus_sync(query, top_k))

    async def _search_local_semantic(self, query: str, top_k: int) -> list[KnowledgeDocument]:
        import asyncio

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.semantic_store.search(query, top_k))

    def _search_milvus_sync(self, query: str, top_k: int) -> list[dict[str, Any]]:
        if not LocalModelRegistry.ready_for_vector_rag():
            raise MilvusConnectionError("BGE-M3 or reranker model files are not ready")
        from backend.core.reranker import retrieve

        ranked_docs, confidence = retrieve(query=query, top_k=top_k)
        return [
            {
                "content": doc.content,
                "source_name": doc.metadata.get("source_name", ""),
                "score": round(doc.score, 6),
                "confidence": round(confidence, 4),
                "is_high_confidence": confidence >= 0.75,
                "metadata": doc.metadata,
            }
            for doc in ranked_docs
        ]

    def ensure_collection(self) -> dict[str, Any]:
        """Create Milvus collection for BGE-M3 dense + sparse RAG if missing."""
        try:
            from pymilvus import DataType, MilvusClient
        except ImportError as exc:
            raise MilvusConnectionError("pymilvus is not installed") from exc

        client = MilvusClient(uri=f"http://{self.settings.milvus_host}:{self.settings.milvus_port}")
        if client.has_collection(self.settings.milvus_collection):
            return {"collection": self.settings.milvus_collection, "created": False}

        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
        schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=64)
        schema.add_field("content", DataType.VARCHAR, max_length=4096)
        schema.add_field("source_name", DataType.VARCHAR, max_length=512)
        schema.add_field("document_id", DataType.VARCHAR, max_length=64)
        schema.add_field("chunk_index", DataType.INT64)
        schema.add_field("metadata_json", DataType.VARCHAR, max_length=2048)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=self.settings.milvus_vector_dim)
        schema.add_field("sparse_embedding", DataType.SPARSE_FLOAT_VECTOR)

        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 200},
        )
        index_params.add_index(
            field_name="sparse_embedding",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="IP",
        )
        client.create_collection(
            collection_name=self.settings.milvus_collection,
            schema=schema,
            index_params=index_params,
        )
        return {"collection": self.settings.milvus_collection, "created": True}

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Embed and upsert chunks into Milvus. Requires local model assets."""
        if not chunks:
            return 0
        if not LocalModelRegistry.ready_for_vector_rag():
            raise MilvusConnectionError("Local BGE-M3/reranker models are not ready")
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise MilvusConnectionError("pymilvus is not installed") from exc

        self.ensure_collection()
        embedder = BGEM3Embedder.get_instance()
        dense_vecs, sparse_vecs = embedder.encode([chunk["content"] for chunk in chunks])
        rows = []
        for index, chunk in enumerate(chunks):
            rows.append(
                {
                    "id": chunk["id"],
                    "content": chunk["content"][:4096],
                    "source_name": chunk.get("source_name", ""),
                    "document_id": str(chunk.get("document_id", "")),
                    "chunk_index": int(chunk.get("chunk_index", index)),
                    "metadata_json": str(chunk.get("metadata", {}))[:2048],
                    "embedding": dense_vecs[index],
                    "sparse_embedding": sparse_vecs[index],
                }
            )
        client = MilvusClient(uri=f"http://{self.settings.milvus_host}:{self.settings.milvus_port}")
        client.upsert(collection_name=self.settings.milvus_collection, data=rows)
        return len(rows)


class BGEM3Embedder:
    """Lazy BGE-M3 wrapper. Imports FlagEmbedding only when vector RAG is enabled."""

    _instance: "BGEM3Embedder | None" = None

    def __init__(self) -> None:
        settings = get_settings()
        model_path = Path(settings.bge_m3_model_path)
        if not model_path.is_absolute():
            model_path = PROJECT_ROOT / model_path
        if not model_path.exists():
            raise FileNotFoundError(f"BGE-M3 model not found: {model_path}")
        from FlagEmbedding import BGEM3FlagModel

        self._model = BGEM3FlagModel(str(model_path), use_fp16=False)

    @classmethod
    def get_instance(cls) -> "BGEM3Embedder":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def encode(self, texts: list[str], batch_size: int = 8) -> tuple[list[list[float]], list[dict[int, float]]]:
        output = self._model.encode(
            texts,
            batch_size=batch_size,
            max_length=8192,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )
        dense = output["dense_vecs"].tolist()
        sparse = [{int(k): float(v) for k, v in item.items()} for item in output["lexical_weights"]]
        return dense, sparse

    def encode_query(self, text: str) -> tuple[list[float], dict[int, float]]:
        dense, sparse = self.encode([text], batch_size=1)
        return dense[0], sparse[0]


def generate_chunk_id(content: str, document_id: str, chunk_index: int) -> str:
    raw = f"{document_id}_{chunk_index}_{content[:80]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
