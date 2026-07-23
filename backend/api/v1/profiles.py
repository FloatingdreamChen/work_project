from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.responses import ok
from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.schemas.profile import ProfileUpsert
from backend.services.profile_service import ProfileService


router = APIRouter()
service = ProfileService()


@router.get("/me")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await service.get_profile(db, current_user["id"])
    return ok(profile or {"user_id": current_user["id"]})


@router.put("/me")
async def update_my_profile(
    payload: ProfileUpsert,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await service.upsert_profile(db, current_user["id"], payload)
    return ok(profile, "画像已保存")
