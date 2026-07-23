from __future__ import annotations

import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.core.knowledge_base import KnowledgeBaseClient


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - only used before dependencies are installed
    FastMCP = None


class ResponseFormat(str, Enum):
    markdown = "markdown"
    json = "json"


class KnowledgeSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., min_length=1, max_length=500, description="考公政策、岗位、备考相关查询")
    top_k: int = Field(default=3, ge=1, le=10, description="返回结果数量")
    response_format: ResponseFormat = Field(default=ResponseFormat.json)


async def search_knowledge_base_impl(params: KnowledgeSearchInput) -> str:
    results = await KnowledgeBaseClient().search(params.query, top_k=params.top_k)
    if params.response_format == ResponseFormat.markdown:
        lines = [f"## 知识库检索：{params.query}"]
        for index, item in enumerate(results, start=1):
            lines.append(f"{index}. 来源：{item.get('source_name', '未知')}")
            lines.append(f"   摘要：{item.get('content', '')[:300]}")
        return "\n".join(lines)
    return json.dumps(results, ensure_ascii=False)


if FastMCP is not None:
    mcp = FastMCP(name="gov_exam_knowledge_mcp", stateless_http=True, json_response=True)

    @mcp.tool(
        name="gov_exam_search_knowledge",
        annotations={
            "title": "Search Gov Exam Knowledge",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def search_knowledge_base(params: KnowledgeSearchInput) -> str:
        """Search local civil-service exam knowledge and return cited snippets."""
        return await search_knowledge_base_impl(params)
else:
    mcp = None
