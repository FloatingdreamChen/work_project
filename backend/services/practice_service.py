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
        module_name: str | None = None,
        question: str | None = None,
        accuracy: float | None = None,
        duration_minutes: float | None = None,
        question_count: int | None = None,
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
        if accuracy is not None or duration_minutes is not None or module_name:
            await db.execute(
                text(
                    """
                    INSERT INTO practice_metrics (
                        user_id, session_id, practice_type, module_name, accuracy,
                        duration_minutes, question_count
                    )
                    VALUES (
                        :user_id, :session_id, :practice_type, :module_name, :accuracy,
                        :duration_minutes, :question_count
                    )
                    """
                ),
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "practice_type": practice_type,
                    "module_name": module_name,
                    "accuracy": accuracy,
                    "duration_minutes": duration_minutes,
                    "question_count": question_count,
                },
            )
        if practice_type == "申论" and review.get("dimension_scores"):
            scores = review["dimension_scores"]
            await db.execute(
                text(
                    """
                    INSERT INTO essay_dimension_scores (
                        session_id, reading_score, structure_score, argument_score,
                        expression_score, policy_score
                    )
                    VALUES (
                        :session_id, :reading_score, :structure_score, :argument_score,
                        :expression_score, :policy_score
                    )
                    """
                ),
                {"session_id": session_id, **scores},
            )
        if self._should_create_wrong_question(review, accuracy):
            await db.execute(
                text(
                    """
                    INSERT INTO wrong_questions (
                        user_id, session_id, practice_type, module_name, topic, question,
                        user_answer, error_reason
                    )
                    VALUES (
                        :user_id, :session_id, :practice_type, :module_name, :topic, :question,
                        :user_answer, :error_reason
                    )
                    """
                ),
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "practice_type": practice_type,
                    "module_name": module_name,
                    "topic": topic,
                    "question": question,
                    "user_answer": user_answer,
                    "error_reason": "\n".join(review.get("problems", [])),
                },
            )
        await db.commit()
        return {"session_id": session_id, "review_id": str(review_result.scalar_one())}

    async def build_report(self, db: AsyncSession, user_id: str, days: int = 30) -> dict:
        result = await db.execute(
            text(
                """
                SELECT ps.practice_type, ps.topic, ps.created_at, pr.score, pr.problems, pr.next_steps,
                       pm.module_name, pm.accuracy, pm.duration_minutes
                FROM practice_sessions ps
                LEFT JOIN practice_reviews pr ON pr.session_id = ps.id
                LEFT JOIN practice_metrics pm ON pm.session_id = ps.id
                WHERE ps.user_id = :user_id
                  AND ps.created_at >= NOW() - (:days || ' days')::interval
                ORDER BY ps.created_at DESC
                """
            ),
            {"user_id": user_id, "days": days},
        )
        rows = [dict(row) for row in result.mappings().all()]
        by_type: dict[str, int] = {}
        by_module: dict[str, dict[str, float]] = {}
        scores: list[float] = []
        problem_keywords: dict[str, int] = {}
        for row in rows:
            practice_type = row.get("practice_type") or "未知"
            by_type[practice_type] = by_type.get(practice_type, 0) + 1
            if row.get("score") is not None:
                scores.append(float(row["score"]))
            module_name = row.get("module_name")
            if module_name:
                module = by_module.setdefault(module_name, {"count": 0, "accuracy_sum": 0.0, "duration_sum": 0.0})
                module["count"] += 1
                if row.get("accuracy") is not None:
                    module["accuracy_sum"] += float(row["accuracy"])
                if row.get("duration_minutes") is not None:
                    module["duration_sum"] += float(row["duration_minutes"])
            for text_value in (row.get("problems"), row.get("next_steps")):
                for keyword in self._extract_keywords(text_value or ""):
                    problem_keywords[keyword] = problem_keywords.get(keyword, 0) + 1

        average_score = round(sum(scores) / len(scores), 2) if scores else None
        top_problems = sorted(problem_keywords.items(), key=lambda item: item[1], reverse=True)[:6]
        return {
            "days": days,
            "practice_count": len(rows),
            "by_type": by_type,
            "by_module": {
                key: {
                    "count": int(value["count"]),
                    "avg_accuracy": round(value["accuracy_sum"] / value["count"], 2) if value["count"] else None,
                    "avg_duration_minutes": round(value["duration_sum"] / value["count"], 2) if value["count"] else None,
                }
                for key, value in by_module.items()
            },
            "average_score": average_score,
            "top_problem_keywords": [{"keyword": key, "count": count} for key, count in top_problems],
            "suggestions": self._build_suggestions(by_type, average_score, [key for key, _ in top_problems]),
            "recent": [
                {
                    "practice_type": row.get("practice_type"),
                    "topic": row.get("topic"),
                    "score": float(row["score"]) if row.get("score") is not None else None,
                    "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                }
                for row in rows[:10]
            ],
        }

    async def list_wrong_questions(
        self,
        db: AsyncSession,
        user_id: str,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        clauses = ["user_id = :user_id"]
        params = {"user_id": user_id, "limit": limit}
        if status:
            clauses.append("status = :status")
            params["status"] = status
        result = await db.execute(
            text(
                f"""
                SELECT id, practice_type, module_name, topic, question, error_reason, status, created_at
                FROM wrong_questions
                WHERE {' AND '.join(clauses)}
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            params,
        )
        rows = []
        for row in result.mappings().all():
            item = dict(row)
            item["id"] = str(item["id"])
            item["created_at"] = item["created_at"].isoformat() if item.get("created_at") else None
            rows.append(item)
        return rows

    def _should_create_wrong_question(self, review: dict, accuracy: float | None) -> bool:
        if accuracy is not None and accuracy < 60:
            return True
        score = review.get("score")
        if score is not None and float(score) < 70:
            return True
        return len(review.get("problems", [])) >= 2

    def _extract_keywords(self, text_value: str) -> list[str]:
        candidates = ["结构", "材料", "论证", "例证", "速度", "审题", "错因", "表达", "基层", "对策"]
        return [keyword for keyword in candidates if keyword in text_value]

    def _build_suggestions(
        self,
        by_type: dict[str, int],
        average_score: float | None,
        problem_keywords: list[str],
    ) -> list[str]:
        suggestions = []
        if not by_type:
            return ["近阶段暂无练习记录，建议先完成行测、申论各一次基线测试。"]
        if average_score is not None and average_score < 70:
            suggestions.append("近期均分低于70，先减少新内容输入，集中复盘高频错因。")
        if by_type.get("申论", 0) < 2:
            suggestions.append("申论练习偏少，建议每周至少完成2次材料阅读或小题输出。")
        if by_type.get("行测", 0) < 3:
            suggestions.append("行测训练样本不足，建议补充限时小组题并记录耗时。")
        if "结构" in problem_keywords:
            suggestions.append("多次出现结构问题，下一阶段优先训练总分总和分点表达。")
        if "审题" in problem_keywords:
            suggestions.append("审题问题反复出现，做题前先圈定问法、对象、限制条件。")
        return suggestions or ["练习节奏基本稳定，下一阶段提高套题限时比例并保留周复盘。"]
