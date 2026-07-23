from __future__ import annotations

from typing import Any, TypedDict


class PositionMatchState(TypedDict, total=False):
    """State passed between PositionMatchAgent LangGraph nodes."""

    user_message: str
    conversation_id: str | None
    profile: dict[str, Any]
    extracted_profile: dict[str, Any]
    missing_fields: list[str]
    needs_clarification: bool
    clarification_question: str

    exam_year: int | None
    exam_type: str | None
    province: str | None
    keyword: str | None
    needs_current_info: bool

    positions: list[dict[str, Any]]
    rule_result: dict[str, Any]
    match_summary: dict[str, Any]

    knowledge: list[dict[str, Any]]
    web_results: list[dict[str, Any]]
    sources: list[dict[str, str]]

    answer: str
    structured_output: dict[str, Any]
    fallback_used: bool
    fallback_level: str | None
    compliance_warnings: list[str]
    node_errors: list[dict[str, str]]
