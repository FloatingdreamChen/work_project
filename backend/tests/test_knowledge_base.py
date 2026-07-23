import asyncio

from backend.config import get_settings
from backend.core.knowledge_base import KnowledgeBaseClient, LocalKeywordKnowledgeStore
from backend.core.model_registry import LocalModelRegistry


def test_model_registry_reports_configured_models() -> None:
    statuses = LocalModelRegistry.status()

    assert "bge_m3" in statuses
    assert "reranker" in statuses
    assert statuses["bge_m3"].resolved_path.endswith("backend/models/embedding/bge-m3")


def test_local_keyword_store_searches_docs() -> None:
    store = LocalKeywordKnowledgeStore()

    docs = store.search("岗位 匹配", top_k=3)

    assert isinstance(docs, list)
    assert len(docs) <= 3


def test_knowledge_client_falls_back_when_vector_rag_not_ready() -> None:
    settings = get_settings()
    settings.enable_local_models = True
    settings.enable_milvus_rag = True

    results = asyncio.run(KnowledgeBaseClient().search("申论 备考", top_k=2))

    assert isinstance(results, list)
    assert len(results) <= 2
    for item in results:
        assert "content" in item
        assert item["is_high_confidence"] is False
