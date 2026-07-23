from __future__ import annotations

import asyncio
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.config import get_settings
from backend.core.web_search_quality import enrich_search_results


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None


class ResponseFormat(str, Enum):
    markdown = "markdown"
    json = "json"


class WebSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., min_length=2, max_length=300, description="联网搜索关键词")
    max_results: int = Field(default=5, ge=1, le=10)
    response_format: ResponseFormat = Field(default=ResponseFormat.json)


async def _search_tavily(query: str, max_results: int, api_key: str) -> list[dict]:
    import httpx

    async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
        )
        response.raise_for_status()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", "")[:500],
            "content": item.get("content", ""),
            "published_at": item.get("published_date"),
        }
        for item in response.json().get("results", [])
    ]


async def _search_duckduckgo(query: str, max_results: int) -> list[dict]:
    def run() -> list[dict]:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("href", ""),
                        "snippet": item.get("body", "")[:500],
                        "content": item.get("body", ""),
                    }
                )
        return results

    return await asyncio.to_thread(run)


async def web_search_impl(params: WebSearchInput) -> str:
    settings = get_settings()
    results: list[dict] = []
    provider = "none"
    if settings.tavily_api_key:
        try:
            results = await _search_tavily(params.query, params.max_results, settings.tavily_api_key)
            provider = "tavily"
        except Exception:
            results = []
    if not results and settings.enable_web_search:
        try:
            results = await _search_duckduckgo(params.query, params.max_results)
            provider = "duckduckgo"
        except Exception:
            results = []
            provider = "unavailable"

    results = enrich_search_results(results, provider=provider, query=params.query)

    if params.response_format == ResponseFormat.markdown:
        lines = [f"## 联网搜索：{params.query}"]
        for index, item in enumerate(results, start=1):
            lines.append(f"{index}. [{item.get('title', '无标题')}]({item.get('url', '')})")
            lines.append(f"   {item.get('snippet', '')}")
        return "\n".join(lines)
    return json.dumps(results, ensure_ascii=False)


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    raw = await web_search_impl(WebSearchInput(query=query, max_results=max_results))
    return json.loads(raw)


if FastMCP is not None:
    mcp = FastMCP(name="gov_exam_web_search_mcp", stateless_http=True, json_response=True)

    @mcp.tool(
        name="gov_exam_web_search",
        annotations={
            "title": "Search Current Web",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def mcp_web_search(params: WebSearchInput) -> str:
        """Search the public web for current policy, announcement, or exam information."""
        return await web_search_impl(params)
else:
    mcp = None
