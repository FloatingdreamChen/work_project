from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.position import PositionCreate, PositionQuery


POSITION_FIELDS = [
    "exam_year",
    "exam_type",
    "province",
    "city",
    "department",
    "bureau",
    "position_name",
    "position_code",
    "recruitment_count",
    "education_requirement",
    "degree_requirement",
    "major_requirement",
    "political_requirement",
    "grassroots_requirement",
    "work_years_requirement",
    "household_requirement",
    "remarks",
    "source_name",
    "source_url",
]


class PositionService:
    async def import_positions(
        self,
        db: AsyncSession,
        positions: list[PositionCreate],
    ) -> list[dict]:
        if not positions:
            return []

        inserted: list[dict] = []
        columns = ", ".join(POSITION_FIELDS)
        params = ", ".join([f":{field}" for field in POSITION_FIELDS])
        for position in positions:
            result = await db.execute(
                text(
                    f"""
                    INSERT INTO positions ({columns})
                    VALUES ({params})
                    RETURNING *
                    """
                ),
                position.model_dump(),
            )
            inserted.append(self._row_to_dict(result.mappings().one()))
        await db.commit()
        return inserted

    async def list_positions(
        self,
        db: AsyncSession,
        query: PositionQuery,
    ) -> list[dict]:
        clauses: list[str] = []
        params: dict = {"limit": query.limit}
        if query.exam_year:
            clauses.append("exam_year = :exam_year")
            params["exam_year"] = query.exam_year
        if query.exam_type:
            clauses.append("exam_type = :exam_type")
            params["exam_type"] = query.exam_type
        if query.province:
            clauses.append("province = :province")
            params["province"] = query.province
        if query.keyword:
            clauses.append(
                "(position_name ILIKE :keyword OR department ILIKE :keyword OR position_code ILIKE :keyword)"
            )
            params["keyword"] = f"%{query.keyword}%"
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        result = await db.execute(
            text(
                f"""
                SELECT * FROM positions
                {where}
                ORDER BY imported_at DESC
                LIMIT :limit
                """
            ),
            params,
        )
        return [self._row_to_dict(row) for row in result.mappings().all()]

    async def save_match_report(
        self,
        db: AsyncSession,
        user_id: str,
        profile_snapshot: dict,
        result: dict,
    ) -> str:
        response = await db.execute(
            text(
                """
                INSERT INTO position_match_reports (user_id, profile_snapshot, result)
                VALUES (:user_id, CAST(:profile_snapshot AS JSONB), CAST(:result AS JSONB))
                RETURNING id
                """
            ),
            {
                "user_id": user_id,
                "profile_snapshot": self._json(profile_snapshot),
                "result": self._json(result),
            },
        )
        await db.commit()
        return str(response.scalar_one())

    def _row_to_dict(self, row) -> dict:
        data = dict(row)
        data["id"] = str(data["id"])
        if data.get("imported_at"):
            data["imported_at"] = data["imported_at"].isoformat()
        return data

    def _json(self, payload: dict) -> str:
        import json

        return json.dumps(payload, ensure_ascii=False, default=str)
