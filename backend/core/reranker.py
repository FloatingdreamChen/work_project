from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.config import PROJECT_ROOT, get_settings


@dataclass
class RankedDocument:
    content: str
    score: float
    original_index: int
    metadata: dict[str, Any]


class BGEReranker:
    """Optional BGE reranker wrapper loaded only when explicitly enabled."""

    _instance: "BGEReranker | None" = None

    def __init__(self) -> None:
        settings = get_settings()
        model_path = Path(settings.reranker_model_path)
        if not model_path.is_absolute():
            model_path = PROJECT_ROOT / model_path
        if not model_path.exists():
            raise FileNotFoundError(f"Reranker model not found: {model_path}")

        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(str(model_path), max_length=512)

    @classmethod
    def get_instance(cls) -> "BGEReranker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def rerank_with_confidence(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int = 3,
    ) -> tuple[list[RankedDocument], float]:
        if not documents:
            return [], 0.0
        pairs = [(query, (doc.get("content") or "")[:1200]) for doc in documents]
        raw_scores = self._model.predict(pairs)
        scores = raw_scores.tolist() if hasattr(raw_scores, "tolist") else list(raw_scores)
        ranked = sorted(
            [
                RankedDocument(
                    content=documents[index].get("content", ""),
                    score=float(scores[index]),
                    original_index=index,
                    metadata=documents[index].get("metadata", {}),
                )
                for index in range(len(documents))
            ],
            key=lambda item: item.score,
            reverse=True,
        )
        top = ranked[:top_k]
        return top, top[0].score if top else 0.0


def retrieve(query: str, top_k: int = 3) -> tuple[list[RankedDocument], float]:
    """Local-model retrieval entry. Heavy dependencies are imported lazily."""
    from pymilvus import AnnSearchRequest, MilvusClient, WeightedRanker
    from backend.core.knowledge_base import BGEM3Embedder

    settings = get_settings()
    client = MilvusClient(uri=f"http://{settings.milvus_host}:{settings.milvus_port}")
    dense_vec, sparse_vec = BGEM3Embedder.get_instance().encode_query(query)
    dense_req = AnnSearchRequest(
        data=[dense_vec],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 64}},
        limit=max(top_k * 4, 10),
    )
    sparse_req = AnnSearchRequest(
        data=[sparse_vec],
        anns_field="sparse_embedding",
        param={"metric_type": "IP"},
        limit=max(top_k * 4, 10),
    )
    search_results = client.hybrid_search(
        collection_name=settings.milvus_collection,
        reqs=[dense_req, sparse_req],
        ranker=WeightedRanker(0.7, 0.3),
        limit=max(top_k * 4, 10),
        output_fields=["content", "source_name", "document_id", "chunk_index"],
    )
    hits = search_results[0] if search_results else []
    documents = [
        {
            "content": hit.get("entity", {}).get("content", ""),
            "metadata": {
                "source_name": hit.get("entity", {}).get("source_name", ""),
                "document_id": hit.get("entity", {}).get("document_id", ""),
                "chunk_index": hit.get("entity", {}).get("chunk_index", 0),
                "hybrid_score": hit.get("distance", 0.0),
            },
        }
        for hit in hits
    ]
    return BGEReranker.get_instance().rerank_with_confidence(query, documents, top_k=top_k)
