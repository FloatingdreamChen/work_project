from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from backend.core.logger import get_logger


logger = get_logger(__name__)


def safe_node(
    name: str,
    func: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    fallback: dict[str, Any] | None = None,
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    """Wrap a graph node so node-level failures become state, not crashes."""

    async def wrapper(state: dict[str, Any]) -> dict[str, Any]:
        try:
            return await func(state)
        except Exception as exc:
            logger.error("graph.node_failed | node=%s error=%s", name, exc)
            errors = list(state.get("node_errors", []))
            errors.append({"node": name, "error": str(exc)})
            return {
                "node_errors": errors,
                "fallback_used": True,
                "fallback_level": f"node:{name}",
                **(fallback or {}),
            }

    return wrapper
