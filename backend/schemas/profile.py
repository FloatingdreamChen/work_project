from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    target_exam: str | None = None
    target_region: str | None = None
    education: str | None = None
    degree: str | None = None
    major: str | None = None
    graduation_year: int | None = None
    fresh_graduate_status: str | None = None
    political_status: str | None = None
    household_region: str | None = None
    grassroots_experience: str | None = None
    work_years: float | None = Field(default=None, ge=0, le=60)
    certificates: str | None = None


class ProfileUpsert(ProfileBase):
    pass


class ProfileOut(ProfileBase):
    id: str | None = None
    user_id: str
