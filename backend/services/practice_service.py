from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PracticeService:
    async def save_review(
        self,
        db: AsyncSession,
        user_id: str,
        practice_type: str,
        topic: str | None,
        user_answer: str,
        review: dict,
    ) -> dict:
        session_result = await db.execute(
            text(
                """
                INSERT INTO practice_sessions (user_id, practice_type, topic, user_answer)
                VALUES (:user_id, :practice_type, :topic, :user_answer)
                RETURNING id
                """
            ),
            {
                "user_id": user_id,
                "practice_type": practice_type,
                "topic": topic,
                "user_answer": user_answer,
            },
        )
        session_id = str(session_result.scalar_one())
        review_result = await db.execute(
            text(
                """
                INSERT INTO practice_reviews (
                    session_id, score, strengths, problems, improved_answer, next_steps
                )
                VALUES (
                    :session_id, :score, :strengths, :problems, :improved_answer, :next_steps
                )
                RETURNING id
                """
            ),
            {
                "session_id": session_id,
                "score": review.get("score"),
                "strengths": "\n".join(review.get("strengths", [])),
                "problems": "\n".join(review.get("problems", [])),
                "improved_answer": review.get("improved_answer"),
                "next_steps": "\n".join(review.get("next_steps", [])),
            },
        )
        await db.commit()
        return {"session_id": session_id, "review_id": str(review_result.scalar_one())}
