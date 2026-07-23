from __future__ import annotations

from copy import deepcopy
from typing import Any


class ConversationStateStore:
    """Small in-process state store for graph continuity during local MVP.

    It is intentionally simple and replaceable. Production should swap this for
    a LangGraph checkpointer backed by PostgreSQL or Redis.
    """

    _states: dict[str, dict[str, Any]] = {}

    @classmethod
    def load(cls, conversation_id: str | None) -> dict[str, Any]:
        if not conversation_id:
            return {}
        return deepcopy(cls._states.get(conversation_id, {}))

    @classmethod
    def save(cls, conversation_id: str | None, state: dict[str, Any]) -> None:
        if not conversation_id:
            return
        snapshot = {
            "profile": state.get("profile", {}),
            "extracted_profile": state.get("extracted_profile", {}),
            "missing_fields": state.get("missing_fields", []),
            "task_type": state.get("task_type"),
            "practice_type": state.get("practice_type"),
            "weak_modules": state.get("weak_modules", []),
            "current_scores": state.get("current_scores", {}),
        }
        existing = cls._states.get(conversation_id, {})
        merged_profile = {**existing.get("profile", {}), **snapshot.get("profile", {})}
        snapshot["profile"] = merged_profile
        cls._states[conversation_id] = snapshot

    @classmethod
    def clear(cls) -> None:
        cls._states.clear()
