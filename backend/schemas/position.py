from pydantic import BaseModel, Field

from backend.schemas.profile import ProfileBase


class PositionCreate(BaseModel):
    exam_year: int
    exam_type: str
    province: str | None = None
    city: str | None = None
    department: str | None = None
    bureau: str | None = None
    position_name: str
    position_code: str | None = None
    recruitment_count: int | None = None
    applicant_count: int | None = None
    competition_ratio: float | None = None
    previous_min_score: float | None = None
    education_requirement: str | None = None
    degree_requirement: str | None = None
    major_requirement: str | None = None
    political_requirement: str | None = None
    grassroots_requirement: str | None = None
    work_years_requirement: str | None = None
    household_requirement: str | None = None
    remarks: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    source_published_at: str | None = None


class PositionOut(PositionCreate):
    id: str
    imported_at: str | None = None


class PositionQuery(BaseModel):
    exam_year: int | None = None
    exam_type: str | None = None
    province: str | None = None
    keyword: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class PositionImportRequest(BaseModel):
    positions: list[PositionCreate]


class PositionMatchRequest(BaseModel):
    profile: ProfileBase | None = None
    exam_year: int | None = None
    exam_type: str | None = None
    province: str | None = None
    preferred_regions: list[str] = []
    risk_preference: str = Field(default="balanced", description="conservative/balanced/aggressive")
    limit: int = Field(default=20, ge=1, le=100)


class MatchItem(BaseModel):
    position: PositionOut | dict
    tier: str
    score: int
    matched: list[str]
    risks: list[str]
    verification: list[str]
    policy_basis: dict | None = None
    rationale: str


class PositionMatchResult(BaseModel):
    agent: str = "PositionMatchAgent"
    disclaimer: str
    items: list[MatchItem]
    sources: list[dict] = []
