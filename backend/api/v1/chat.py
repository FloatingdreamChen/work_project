from fastapi import APIRouter

from backend.core.orchestrator import AgentOrchestrator
from backend.core.responses import ok
from backend.schemas.chat import ChatRequest


router = APIRouter()
orchestrator = AgentOrchestrator()


@router.post("")
async def chat(payload: ChatRequest) -> dict:
    return ok(await orchestrator.chat(payload.message, payload.conversation_id, payload.category_hint))
