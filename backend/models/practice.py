from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    practice_type: Mapped[str] = mapped_column(String(80), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255))
    user_answer: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class WrongQuestion(Base):
    __tablename__ = "wrong_questions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("practice_sessions.id", ondelete="CASCADE"))
    practice_type: Mapped[str] = mapped_column(String(80), nullable=False)
    module_name: Mapped[str | None] = mapped_column(String(120))
    question: Mapped[str | None] = mapped_column(Text)
    user_answer: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="open")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PracticeMetric(Base):
    __tablename__ = "practice_metrics"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("practice_sessions.id", ondelete="CASCADE"))
    practice_type: Mapped[str] = mapped_column(String(80), nullable=False)
    module_name: Mapped[str | None] = mapped_column(String(120))
    accuracy: Mapped[float | None] = mapped_column(Numeric(5, 2))
    duration_minutes: Mapped[float | None] = mapped_column(Numeric(6, 2))
    question_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EssayDimensionScore(Base):
    __tablename__ = "essay_dimension_scores"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False)
    reading_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    structure_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    argument_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    expression_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    policy_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_position: Mapped[str | None] = mapped_column(String(255))
    stage: Mapped[str] = mapped_column(String(80), nullable=False, server_default="warmup")
    turns: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
