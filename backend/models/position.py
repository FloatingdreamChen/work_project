from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    exam_year: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_type: Mapped[str] = mapped_column(String(80), nullable=False)
    province: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    department: Mapped[str | None] = mapped_column(String(255))
    bureau: Mapped[str | None] = mapped_column(String(255))
    position_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position_code: Mapped[str | None] = mapped_column(String(120))
    recruitment_count: Mapped[int | None] = mapped_column(Integer)
    applicant_count: Mapped[int | None] = mapped_column(Integer)
    competition_ratio: Mapped[float | None] = mapped_column(Numeric(8, 2))
    previous_min_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    education_requirement: Mapped[str | None] = mapped_column(Text)
    degree_requirement: Mapped[str | None] = mapped_column(Text)
    major_requirement: Mapped[str | None] = mapped_column(Text)
    political_requirement: Mapped[str | None] = mapped_column(Text)
    grassroots_requirement: Mapped[str | None] = mapped_column(Text)
    work_years_requirement: Mapped[str | None] = mapped_column(Text)
    household_requirement: Mapped[str | None] = mapped_column(Text)
    remarks: Mapped[str | None] = mapped_column(Text)
    source_name: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(Text)
    source_published_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PositionImportAudit(Base):
    __tablename__ = "position_import_audits"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    source_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(Text)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    errors: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="[]")
    imported_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PositionMatchReport(Base):
    __tablename__ = "position_match_reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
