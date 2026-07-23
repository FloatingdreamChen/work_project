from __future__ import annotations

import json
from typing import Any


async def call_mcp_tool(
    server_url: str,
    tool_name: str,
    arguments: dict[str, Any],
    timeout: float = 30.0,
) -> Any:
    """Call a stateless FastMCP HTTP tool."""
    import httpx

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
        response = await client.post(f"{server_url.rstrip('/')}/mcp", json=payload, headers=headers)
        response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise ValueError(data["error"].get("message", str(data["error"])))
    content = data.get("result", {}).get("content", [])
    if not content:
        return []
    parsed_items = []
    for item in content:
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = text
        if isinstance(parsed, list):
            return parsed
        parsed_items.append(parsed)
    return parsed_items


async def list_mcp_tools(server_url: str, timeout: float = 10.0) -> list[dict[str, Any]]:
    """List tools exposed by a stateless FastMCP HTTP server."""
    import httpx

    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
        response = await client.post(f"{server_url.rstrip('/')}/mcp", json=payload, headers=headers)
        response.raise_for_status()
    return response.json().get("result", {}).get("tools", [])
