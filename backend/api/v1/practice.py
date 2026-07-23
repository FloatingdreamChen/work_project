from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.study_practice import StudyPracticeAgent
from backend.core.responses import ok
from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.schemas.practice import PracticeReviewRequest
from backend.services.practice_service import PracticeService


router = APIRouter()
agent = StudyPracticeAgent()
service = PracticeService()


@router.post("/review")
async def review_practice(
    payload: PracticeReviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = agent.review_answer(
        payload.practice_type,
        payload.user_answer,
        payload.topic,
        payload.question,
    )
    saved = await service.save_review(
        db,
        current_user["id"],
        payload.practice_type,
        payload.topic,
        payload.user_answer,
        result,
    )
    result.update(saved)
    return ok(result)
