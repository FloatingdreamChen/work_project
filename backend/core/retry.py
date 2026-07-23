from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from backend.config import get_settings
from backend.core.exceptions import (
    AuthenticationError,
    InvalidInputError,
    LLMAPIError,
    MilvusConnectionError,
    ToolExecutionError,
)
from backend.core.logger import get_logger


logger = get_logger(__name__)

RETRYABLE_ERRORS = (LLMAPIError, MilvusConnectionError, ToolExecutionError, TimeoutError, ConnectionError)
NON_RETRYABLE_ERRORS = (InvalidInputError, AuthenticationError)


def with_retry(agent_type: str = ""):
    """Three-layer protection: retry, agent fallback, system fallback."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            settings = get_settings()
            max_retries = max(0, settings.llm_max_retries)
            last_error: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=settings.llm_timeout_seconds,
                    )
                except NON_RETRYABLE_ERRORS:
                    raise
                except RETRYABLE_ERRORS as exc:
                    last_error = exc
                    if attempt < max_retries:
                        delay = min(1.0 + attempt * 1.5, 5.0)
                        logger.warning(
                            "retry.attempt_failed | agent=%s attempt=%s error=%s",
                            agent_type,
                            attempt + 1,
                            exc,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error("retry.exhausted | agent=%s error=%s", agent_type, exc)
                except Exception as exc:
                    last_error = exc
                    logger.error("retry.unexpected | agent=%s error=%s", agent_type, exc)
                    break

            try:
                return await AgentFallbackHandler.handle(agent_type, last_error, *args, **kwargs)
            except Exception as fallback_error:
                logger.error(
                    "retry.agent_fallback_failed | agent=%s original=%s fallback=%s",
                    agent_type,
                    last_error,
                    fallback_error,
                )
                return system_fallback_response(agent_type, last_error)

        return wrapper

    return decorator


class AgentFallbackHandler:
    """Agent-specific degraded behavior when model/tool calls fail."""

    @classmethod
    async def handle(cls, agent_type: str, error: Exception | None, *args, **kwargs) -> dict:
        if agent_type == "position_match":
            return {
                "answer": (
                    "岗位匹配 AI 分析暂时不可用，已降级为规则匹配。请在岗位匹配页面查看"
                    "硬性条件、资格风险和人工核验项；最终以招录机关审核为准。"
                ),
                "agent": "PositionMatchAgent",
                "fallback_used": True,
                "fallback_level": "agent",
                "sources": [],
            }
        if agent_type == "study_practice":
            return {
                "answer": (
                    "AI 深度批改暂时不可用，已降级为结构化备考建议：先完成基础诊断，"
                    "再按行测专项、申论材料、面试表达分别训练，并每周复盘错题。"
                ),
                "agent": "StudyPracticeAgent",
                "fallback_used": True,
                "fallback_level": "agent",
                "sources": [],
            }
        if error:
            raise error
        raise ToolExecutionError("No fallback handler available", agent_type=agent_type)


def system_fallback_response(agent_type: str, error: Exception | None = None) -> dict:
    agent_name = "PositionMatchAgent" if agent_type == "position_match" else "StudyPracticeAgent"
    return {
        "answer": "服务暂时不可用，请稍后再试。若涉及岗位资格，请以官方公告和人工审核为准。",
        "agent": agent_name,
        "fallback_used": True,
        "fallback_level": "system",
        "error": str(error) if error else None,
        "sources": [],
    }
