from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.profile import ProfileUpsert


PROFILE_FIELDS = [
    "target_exam",
    "target_region",
    "education",
    "degree",
    "major",
    "graduation_year",
    "fresh_graduate_status",
    "political_status",
    "household_region",
    "grassroots_experience",
    "work_years",
    "certificates",
]


class ProfileService:
    async def get_profile(self, db: AsyncSession, user_id: str) -> dict | None:
        result = await db.execute(
            text("SELECT * FROM user_profiles WHERE user_id = :user_id LIMIT 1"),
            {"user_id": user_id},
        )
        row = result.mappings().first()
        return self._row_to_dict(row) if row else None

    async def upsert_profile(
        self,
        db: AsyncSession,
        user_id: str,
        payload: ProfileUpsert,
    ) -> dict:
        values = payload.model_dump()
        values["user_id"] = user_id
        columns = ", ".join(["user_id", *PROFILE_FIELDS])
        params = ", ".join([f":{field}" for field in ["user_id", *PROFILE_FIELDS]])
        update_clause = ", ".join([f"{field} = EXCLUDED.{field}" for field in PROFILE_FIELDS])

        result = await db.execute(
            text(
                f"""
                INSERT INTO user_profiles ({columns})
                VALUES ({params})
                ON CONFLICT (user_id) DO UPDATE SET
                    {update_clause},
                    updated_at = NOW()
                RETURNING *
                """
            ),
            values,
        )
        await db.commit()
        row = result.mappings().one()
        return self._row_to_dict(row)

    def _row_to_dict(self, row) -> dict:
        data = dict(row)
        for key in ("id", "user_id"):
            data[key] = str(data[key])
        return data
