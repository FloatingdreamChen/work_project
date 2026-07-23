from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text


class SourceAuditService:
    async def save_web_sources(self, results: list[dict[str, Any]]) -> int:
        if not results:
            return 0

        from backend.db.session import AsyncSessionLocal

        count = 0
        async with AsyncSessionLocal() as db:
            for item in results:
                await db.execute(
                    text(
                        """
                        INSERT INTO current_information_sources (
                            source_type, provider, query, title, url, domain, published_at,
                            imported_at, credibility, credibility_score, credibility_reason, metadata
                        )
                        VALUES (
                            'web', :provider, :query, :title, :url, :domain, :published_at,
                            :imported_at, :credibility, :credibility_score, :credibility_reason,
                            CAST(:metadata AS JSONB)
                        )
                        """
                    ),
                    {
                        "provider": item.get("provider"),
                        "query": item.get("query"),
                        "title": item.get("title"),
                        "url": item.get("url") or "",
                        "domain": item.get("domain"),
                        "published_at": item.get("published_at"),
                        "imported_at": item.get("imported_at"),
                        "credibility": item.get("credibility"),
                        "credibility_score": item.get("credibility_score"),
                        "credibility_reason": item.get("credibility_reason"),
                        "metadata": json.dumps(item, ensure_ascii=False, default=str),
                    },
                )
                count += 1
            await db.commit()
        return count
