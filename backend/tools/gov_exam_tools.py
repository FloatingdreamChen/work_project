from __future__ import annotations

import asyncio
from typing import Any

from backend.config import get_settings
from backend.core.knowledge_base import KnowledgeBaseClient, LocalKeywordKnowledgeStore


async def search_knowledge(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Search policy/project knowledge with local keyword fallback."""
    settings = get_settings()
    try:
        return await asyncio.wait_for(
            KnowledgeBaseClient().search(query, top_k=top_k),
            timeout=settings.rag_timeout_seconds,
        )
    except Exception:
        docs = LocalKeywordKnowledgeStore().search(query, top_k=top_k)
        return [
            {
                "content": doc.content,
                "source_name": doc.source_name,
                "score": doc.score,
                "confidence": min(0.7, doc.score / 10) if doc.score else 0.0,
                "is_high_confidence": False,
                "metadata": {**(doc.metadata or {}), "retriever": "keyword_timeout_fallback"},
            }
            for doc in docs
        ]


async def search_positions(
    keyword: str | None = None,
    exam_year: int | None = None,
    province: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search imported positions from PostgreSQL for agent context."""
    clauses: list[str] = []
    params: dict[str, Any] = {"limit": max(1, min(limit, 20))}
    if keyword:
        clauses.append("(position_name ILIKE :keyword OR department ILIKE :keyword OR major_requirement ILIKE :keyword)")
        params["keyword"] = f"%{keyword}%"
    if exam_year:
        clauses.append("exam_year = :exam_year")
        params["exam_year"] = exam_year
    if province:
        clauses.append("province = :province")
        params["province"] = province
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    from sqlalchemy import text

    from backend.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                f"""
                SELECT id, exam_year, exam_type, province, city, department, position_name,
                       position_code, major_requirement, education_requirement, source_name, source_url
                FROM positions
                {where}
                ORDER BY imported_at DESC
                LIMIT :limit
                """
            ),
            params,
        )
        rows = []
        for row in result.mappings().all():
            item = dict(row)
            item["id"] = str(item["id"])
            rows.append(item)
        return rows


async def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search current public web information. Requires network and optional Tavily key."""
    from backend.mcp.web_search_server import web_search as mcp_web_search

    return await mcp_web_search(query=query, max_results=max_results)
