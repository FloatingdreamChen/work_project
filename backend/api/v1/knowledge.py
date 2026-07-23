from fastapi import APIRouter, Depends

from backend.core.knowledge_base import KnowledgeBaseClient
from backend.core.model_registry import LocalModelRegistry
from backend.core.responses import ok
from backend.dependencies import get_current_user
from backend.schemas.knowledge import KnowledgeSearchRequest


router = APIRouter()


@router.get("/status")
async def knowledge_status(current_user: dict = Depends(get_current_user)) -> dict:
    statuses = LocalModelRegistry.status()
    return ok(
        {
            "models": {
                name: {
                    "exists": status.exists,
                    "path": status.resolved_path,
                    "missing_files": status.missing_files,
                    "size_mb": status.size_mb,
                }
                for name, status in statuses.items()
            },
            "vector_rag_ready": LocalModelRegistry.ready_for_vector_rag(),
        }
    )


@router.post("/search")
async def knowledge_search(
    payload: KnowledgeSearchRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return ok(await KnowledgeBaseClient().search(payload.query, top_k=payload.top_k))


@router.post("/init-milvus")
async def init_milvus(current_user: dict = Depends(get_current_user)) -> dict:
    return ok(KnowledgeBaseClient().ensure_collection())
