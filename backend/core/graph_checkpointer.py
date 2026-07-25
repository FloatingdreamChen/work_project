from __future__ import annotations

from backend.config import get_settings
from backend.core.logger import get_logger


logger = get_logger(__name__)


def get_langgraph_checkpointer():
    """Return an optional LangGraph checkpointer.

    The project keeps ConversationStateStore as the stable long-term memory layer.
    This checkpointer is an additional LangGraph-native checkpoint hook and is
    enabled only when ENABLE_LANGGRAPH_CHECKPOINTS=true.
    """
    settings = get_settings()
    if not settings.enable_langgraph_checkpoints:
        return None
    backend = settings.graph_memory_backend.lower()
    if backend == "memory":
        try:
            from langgraph.checkpoint.memory import InMemorySaver

            return InMemorySaver()
        except Exception:
            try:
                from langgraph.checkpoint.memory import MemorySaver

                return MemorySaver()
            except Exception as exc:
                logger.warning("langgraph.memory_checkpointer_unavailable | error=%s", exc)
                return None
    if backend == "postgres":
        logger.warning("langgraph.postgres_checkpointer_requires_runtime_setup")
        return None
    if backend == "redis":
        logger.warning("langgraph.redis_checkpointer_requires_runtime_setup")
        return None
    return None
