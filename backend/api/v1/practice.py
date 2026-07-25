from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.study_practice import StudyPracticeAgent
from backend.agents.study_practice.graph import build_study_practice_graph
from backend.core.responses import ok
from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.schemas.practice import (
    InterviewStartRequest,
    InterviewTurnRequest,
    PracticeReviewRequest,
    StudyPlanRequest,
    StudyReportRequest,
    WrongQuestionQuery,
)
from backend.services.practice_service import PracticeService


router = APIRouter()
agent = StudyPracticeAgent()
service = PracticeService()
study_graph = build_study_practice_graph()


@router.post("/review")
async def review_practice(
    payload: PracticeReviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        state = await study_graph.ainvoke(
            {
                "user_message": payload.question or payload.topic or payload.user_answer,
                "practice_type": payload.practice_type,
                "topic": payload.topic,
                "question": payload.question,
                "user_answer": payload.user_answer,
            }
        )
        result = state.get("review") or {}
        result["ai_review"] = state.get("answer", "")
        result["fallback_used"] = state.get("fallback_used", False)
        result["sources"] = state.get("sources", [])
    except Exception:
        result = agent.review_answer(
            payload.practice_type,
            payload.user_answer,
            payload.topic,
            payload.question,
        )
        result["fallback_used"] = True
    saved = await service.save_review(
        db,
        current_user["id"],
        payload.practice_type,
        payload.topic,
        payload.user_answer,
        result,
        module_name=payload.module_name,
        question=payload.question,
        accuracy=payload.accuracy,
        duration_minutes=payload.duration_minutes,
        question_count=payload.question_count,
    )
    result.update(saved)
    return ok(result)


@router.post("/interview/start")
async def start_interview(
    payload: InterviewStartRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return ok(
        await service.start_interview_session(
            db,
            current_user["id"],
            payload.target_position,
            payload.topic,
        )
    )


@router.post("/interview/turn")
async def interview_turn(
    payload: InterviewTurnRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    review = agent.review_answer("面试", payload.user_answer, topic="面试追问", question=payload.question)
    try:
        result = await service.add_interview_turn(
            db,
            current_user["id"],
            payload.session_id,
            payload.user_answer,
            payload.question,
            review,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ok(result)


@router.post("/plan")
async def build_study_plan(
    payload: StudyPlanRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    state = await study_graph.ainvoke(
        {
            "user_message": payload.notes or "生成个性化备考计划",
            "task_type": "plan",
            "target_exam": payload.target_exam,
            "target_position": payload.target_position,
            "province": payload.province,
            "exam_date": payload.exam_date.isoformat() if payload.exam_date else None,
            "daily_hours": payload.daily_hours,
            "weekly_days": payload.weekly_days,
            "foundation_level": payload.foundation_level,
            "weak_modules": payload.weak_modules,
            "strong_modules": payload.strong_modules,
            "preferred_modules": payload.preferred_modules,
            "current_scores": payload.current_scores,
            "include_interview": payload.include_interview,
            "notes": payload.notes,
        }
    )
    return ok(
        {
            "plan": state.get("plan"),
            "answer": state.get("answer"),
            "sources": state.get("sources", []),
            "structured": state.get("structured_output", {}),
        }
    )


@router.post("/report")
async def study_report(
    payload: StudyReportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        report = await service.build_report(db, current_user["id"], days=payload.days)
    except Exception:
        report = service.empty_report(payload.days)
    return ok(report)


@router.post("/wrong-questions")
async def wrong_questions(
    payload: WrongQuestionQuery,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return ok(await service.list_wrong_questions(db, current_user["id"], payload.status, payload.limit))
