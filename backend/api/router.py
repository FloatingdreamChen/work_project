from fastapi import APIRouter

from backend.api.v1 import auth, chat, knowledge, positions, practice, profiles


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["用户画像"])
api_router.include_router(positions.router, prefix="/positions", tags=["岗位"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI助手"])
api_router.include_router(practice.router, prefix="/practice", tags=["练习"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])
