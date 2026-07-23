from __future__ import annotations

from typing import Any, TypedDict


class StudyPracticeState(TypedDict, total=False):
    """State passed between StudyPracticeAgent LangGraph nodes."""

    user_message: str
    conversation_id: str | None
    practice_type: str
    task_type: str
    topic: str | None
    question: str | None
    user_answer: str
    target_exam: str | None
    target_position: str | None
    province: str | None
    exam_date: str | None
    daily_hours: float
    weekly_days: int
    foundation_level: str
    weak_modules: list[str]
    strong_modules: list[str]
    preferred_modules: list[str]
    current_scores: dict[str, float]
    include_interview: bool
    notes: str | None
    weeks: int

    knowledge: list[dict[str, Any]]
    plan: dict[str, Any]
    review: dict[str, Any]
    answer: str
    sources: list[dict[str, str]]
    structured_output: dict[str, Any]
    fallback_used: bool
    fallback_level: str | None
    compliance_warnings: list[str]
    node_errors: list[dict[str, str]]
