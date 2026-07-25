from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from backend.config import get_settings
from backend.core.compliance import redact_sensitive


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
        snapshot = cls._snapshot(state)
        existing = cls._states.get(conversation_id, {})
        snapshot = cls._merge_snapshot(existing, snapshot)
        cls._states[conversation_id] = snapshot

    @classmethod
    async def load_async(cls, conversation_id: str | None) -> dict[str, Any]:
        if not conversation_id:
            return {}
        backend = get_settings().graph_memory_backend.lower()
        if backend == "postgres":
            return await cls._load_postgres(conversation_id)
        if backend == "redis":
            return await cls._load_redis(conversation_id)
        return cls.load(conversation_id)

    @classmethod
    async def save_async(
        cls,
        conversation_id: str | None,
        state: dict[str, Any],
        *,
        user_message: str | None = None,
        assistant_answer: str | None = None,
    ) -> None:
        if not conversation_id:
            return
        backend = get_settings().graph_memory_backend.lower()
        snapshot = cls._snapshot(state)
        if user_message or assistant_answer:
            snapshot["recent_turns"] = cls._append_turns(
                state.get("recent_turns", []),
                user_message=user_message,
                assistant_answer=assistant_answer,
            )
            snapshot = redact_sensitive(snapshot)
        if backend == "postgres":
            await cls._save_postgres(conversation_id, snapshot)
            return
        if backend == "redis":
            await cls._save_redis(conversation_id, snapshot)
            return
        cls.save(conversation_id, snapshot)

    @classmethod
    def _snapshot(cls, state: dict[str, Any]) -> dict[str, Any]:
        return redact_sensitive(
            {
            "profile": state.get("profile", {}),
            "extracted_profile": state.get("extracted_profile", {}),
            "missing_fields": state.get("missing_fields", []),
            "task_type": state.get("task_type"),
            "practice_type": state.get("practice_type"),
            "weak_modules": state.get("weak_modules", []),
            "current_scores": state.get("current_scores", {}),
            "recent_turns": state.get("recent_turns", [])[-8:],
            "long_term_memory": cls._long_term_memory(state),
        }
        )

    @classmethod
    def _merge_snapshot(cls, existing: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
        merged_profile = {**existing.get("profile", {}), **snapshot.get("profile", {})}
        snapshot["profile"] = merged_profile
        existing_turns = existing.get("recent_turns", [])
        incoming_turns = snapshot.get("recent_turns", [])
        snapshot["recent_turns"] = (existing_turns + incoming_turns)[-8:]
        snapshot["long_term_memory"] = {
            **existing.get("long_term_memory", {}),
            **snapshot.get("long_term_memory", {}),
        }
        return snapshot

    @classmethod
    def _append_turns(
        cls,
        turns: list[dict[str, str]],
        *,
        user_message: str | None,
        assistant_answer: str | None,
    ) -> list[dict[str, str]]:
        timestamp = datetime.now(UTC).isoformat()
        updated = list(turns or [])
        if user_message:
            updated.append({"role": "user", "content": user_message[:1200], "created_at": timestamp})
        if assistant_answer:
            updated.append({"role": "assistant", "content": assistant_answer[:1600], "created_at": timestamp})
        return updated[-8:]

    @classmethod
    def _long_term_memory(cls, state: dict[str, Any]) -> dict[str, Any]:
        memory = dict(state.get("long_term_memory", {}) or {})
        profile = state.get("profile") or {}
        if profile:
            memory["profile"] = {**memory.get("profile", {}), **profile}
        if state.get("weak_modules"):
            memory["weak_modules"] = state.get("weak_modules")
        if state.get("current_scores"):
            memory["current_scores"] = state.get("current_scores")
        return memory

    @classmethod
    async def _load_postgres(cls, conversation_id: str) -> dict[str, Any]:
        from backend.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text(
                    """
                    SELECT state FROM conversation_memories
                    WHERE conversation_id = :conversation_id
                    LIMIT 1
                    """
                ),
                {"conversation_id": conversation_id},
            )
            row = result.mappings().first()
        return deepcopy(row["state"]) if row else {}

    @classmethod
    async def _save_postgres(cls, conversation_id: str, state: dict[str, Any]) -> None:
        from backend.db.session import AsyncSessionLocal

        existing = await cls._load_postgres(conversation_id)
        snapshot = cls._merge_snapshot(existing, state)
        async with AsyncSessionLocal() as db:
            await db.execute(
                text(
                    """
                    INSERT INTO conversation_memories (conversation_id, state)
                    VALUES (:conversation_id, CAST(:state AS JSONB))
                    ON CONFLICT (conversation_id) DO UPDATE SET
                        state = EXCLUDED.state,
                        updated_at = NOW()
                    """
                ),
                {"conversation_id": conversation_id, "state": json.dumps(snapshot, ensure_ascii=False, default=str)},
            )
            await db.commit()

    @classmethod
    async def _load_redis(cls, conversation_id: str) -> dict[str, Any]:
        try:
            import redis.asyncio as redis
        except ImportError:
            return cls.load(conversation_id)
        client = redis.from_url(get_settings().redis_url, decode_responses=True)
        raw = await client.get(f"gov_exam:conversation:{conversation_id}")
        await client.aclose()
        return json.loads(raw) if raw else {}

    @classmethod
    async def _save_redis(cls, conversation_id: str, state: dict[str, Any]) -> None:
        try:
            import redis.asyncio as redis
        except ImportError:
            cls.save(conversation_id, state)
            return
        existing = await cls._load_redis(conversation_id)
        snapshot = cls._merge_snapshot(existing, state)
        client = redis.from_url(get_settings().redis_url, decode_responses=True)
        await client.set(f"gov_exam:conversation:{conversation_id}", json.dumps(snapshot, ensure_ascii=False, default=str))
        await client.aclose()

    @classmethod
    def clear(cls) -> None:
        cls._states.clear()
