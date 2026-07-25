import asyncio

import backend.tools.gov_exam_tools as tools


def test_search_knowledge_timeout_falls_back_to_keyword(monkeypatch) -> None:
    async def slow_search(self, query: str, top_k: int = 3):
        await asyncio.sleep(0.05)
        return []

    settings = tools.get_settings()
    old_timeout = settings.rag_timeout_seconds
    settings.rag_timeout_seconds = 0.001
    monkeypatch.setattr(tools.KnowledgeBaseClient, "search", slow_search)

    try:
        results = asyncio.run(tools.search_knowledge("岗位 匹配", top_k=2))
    finally:
        settings.rag_timeout_seconds = old_timeout

    assert isinstance(results, list)
    assert len(results) <= 2
    for item in results:
        assert item["metadata"]["retriever"] == "keyword_timeout_fallback"
