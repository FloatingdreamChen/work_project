from datetime import date

from pydantic import BaseModel, Field


class PracticeReviewRequest(BaseModel):
    practice_type: str = Field(..., description="行测、申论、面试")
    module_name: str | None = Field(default=None, description="具体模块，如 行测-资料分析")
    topic: str | None = None
    question: str | None = None
    user_answer: str = Field(..., min_length=1)
    accuracy: float | None = Field(default=None, ge=0, le=100)
    duration_minutes: float | None = Field(default=None, ge=0)
    question_count: int | None = Field(default=None, ge=1)


class PracticeReviewResult(BaseModel):
    agent: str = "StudyPracticeAgent"
    score: float | None = None
    strengths: list[str]
    problems: list[str]
    improved_answer: str
    next_steps: list[str]
    disclaimer: str


class StudyPlanRequest(BaseModel):
    target_exam: str = Field(default="公务员考试")
    exam_date: date | None = Field(default=None, description="目标考试日期")
    target_position: str | None = None
    province: str | None = None
    daily_hours: float = Field(default=2.0, ge=0.5, le=12)
    weekly_days: int = Field(default=6, ge=1, le=7)
    foundation_level: str = Field(default="零基础", description="零基础、一般、较好")
    weak_modules: list[str] = Field(default_factory=list)
    strong_modules: list[str] = Field(default_factory=list)
    preferred_modules: list[str] = Field(default_factory=list)
    current_scores: dict[str, float] = Field(default_factory=dict)
    include_interview: bool = True
    notes: str | None = None


class StudyPlanResult(BaseModel):
    agent: str = "StudyPracticeAgent"
    target_exam: str
    exam_date: str | None
    days_until_exam: int | None
    planned_days: int
    planned_weeks: int
    min_cycle_enforced: bool
    warning: str | None
    weekly_hours: float
    module_weights: dict[str, float]
    phases: list[dict]
    weekly_plan: list[dict]
    daily_template: list[dict]
    milestones: list[dict]
    adjustment_rules: list[str]
    disclaimer: str


class StudyReportRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=365)


class WrongQuestionQuery(BaseModel):
    status: str | None = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)
