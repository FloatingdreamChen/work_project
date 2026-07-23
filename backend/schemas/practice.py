from pydantic import BaseModel, Field


class PracticeReviewRequest(BaseModel):
    practice_type: str = Field(..., description="行测、申论、面试")
    topic: str | None = None
    question: str | None = None
    user_answer: str = Field(..., min_length=1)


class PracticeReviewResult(BaseModel):
    agent: str = "StudyPracticeAgent"
    score: float | None = None
    strengths: list[str]
    problems: list[str]
    improved_answer: str
    next_steps: list[str]
    disclaimer: str
