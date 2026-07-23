from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.config import get_settings
from backend.core.exceptions import LLMAPIError
from backend.core.logger import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


class LLMFactory:
    """OpenAI-compatible LLM access with provider fallback.

    The factory first tries LangChain when installed, then falls back to a direct
    OpenAI-compatible HTTP call. If no API key is configured, callers should
    catch LLMAPIError and use the project fallback path.
    """

    @classmethod
    async def ainvoke(
        cls,
        messages: list[dict[str, str]] | list[LLMMessage],
        agent_type: str,
        temperature: float = 0.2,
        system_prompt: str | None = None,
    ) -> str:
        normalized = cls._normalize_messages(messages, system_prompt)
        settings = get_settings()
        if not settings.openai_api_key or settings.openai_api_key.startswith("replace-"):
            raise LLMAPIError("OPENAI_API_KEY is not configured", agent_type=agent_type)

        try:
            return await cls._ainvoke_langchain(normalized, temperature)
        except ImportError:
            return await cls._ainvoke_http(normalized, temperature)
        except Exception as exc:
            logger.warning("llm.langchain_failed | agent=%s error=%s", agent_type, exc)
            try:
                return await cls._ainvoke_http(normalized, temperature)
            except Exception as http_exc:
                raise LLMAPIError(str(http_exc), agent_type=agent_type) from http_exc

    @classmethod
    async def _ainvoke_langchain(
        cls,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> str:
        try:
            from langchain.chat_models import init_chat_model
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        except ImportError:
            raise

        settings = get_settings()
        lc_messages = []
        for message in messages:
            if message["role"] == "system":
                lc_messages.append(SystemMessage(content=message["content"]))
            elif message["role"] == "assistant":
                lc_messages.append(AIMessage(content=message["content"]))
            else:
                lc_messages.append(HumanMessage(content=message["content"]))

        llm = init_chat_model(
            model=settings.openai_model,
            model_provider="openai",
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=temperature,
            max_retries=0,
        )
        response = await llm.ainvoke(lc_messages)
        return response.content if hasattr(response, "content") else str(response)

    @classmethod
    async def _ainvoke_http(
        cls,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> str:
        import httpx

        settings = get_settings()
        payload = {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds, trust_env=False) as client:
            response = await client.post(
                f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    @classmethod
    def _normalize_messages(
        cls,
        messages: list[dict[str, str]] | list[LLMMessage],
        system_prompt: str | None,
    ) -> list[dict[str, str]]:
        normalized = [
            message if isinstance(message, dict) else {"role": message.role, "content": message.content}
            for message in messages
        ]
        if system_prompt:
            normalized = [{"role": "system", "content": system_prompt}, *normalized]
        return normalized
