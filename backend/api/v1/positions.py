from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.position_match import PositionMatchAgent
from backend.core.responses import ok
from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.schemas.position import (
    PositionImportRequest,
    PositionMatchRequest,
    PositionQuery,
)
from backend.services.position_service import PositionService
from backend.services.profile_service import ProfileService


router = APIRouter()
position_service = PositionService()
profile_service = ProfileService()
agent = PositionMatchAgent()


@router.get("")
async def list_positions(
    exam_year: int | None = None,
    exam_type: str | None = None,
    province: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    positions = await position_service.list_positions(
        db,
        PositionQuery(
            exam_year=exam_year,
            exam_type=exam_type,
            province=province,
            keyword=keyword,
            limit=limit,
        ),
    )
    return ok(positions)


@router.post("/import")
async def import_positions(
    payload: PositionImportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    positions = await position_service.import_positions(db, payload.positions)
    return ok({"count": len(positions), "items": positions}, "岗位导入成功")


@router.post("/match")
async def match_positions(
    payload: PositionMatchRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = payload.profile.model_dump() if payload.profile else None
    if profile is None:
        profile = await profile_service.get_profile(db, current_user["id"]) or {}

    positions = await position_service.list_positions(
        db,
        PositionQuery(
            exam_year=payload.exam_year,
            exam_type=payload.exam_type,
            province=payload.province,
            limit=payload.limit,
        ),
    )
    result = agent.match(
        profile,
        positions,
        preferred_regions=payload.preferred_regions,
        risk_preference=payload.risk_preference,
    )
    report_id = await position_service.save_match_report(
        db,
        current_user["id"],
        profile,
        result,
    )
    result["report_id"] = report_id
    return ok(result)
