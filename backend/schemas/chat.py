from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None
    category_hint: str | None = None


class ChatResponse(BaseModel):
    answer: str
    agent: str
    sources: list[dict] = []
    fallback_used: bool = False
    fallback_level: str | None = None
    response_mode: str | None = None
    fallback_reason: str | None = None
    route: dict | None = None
    structured: dict | list | None = None
    conversation_id: str | None = None
