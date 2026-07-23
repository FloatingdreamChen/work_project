from __future__ import annotations

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_exam: Mapped[str | None] = mapped_column(String(120))
    target_region: Mapped[str | None] = mapped_column(String(120))
    education: Mapped[str | None] = mapped_column(String(120))
    degree: Mapped[str | None] = mapped_column(String(120))
    major: Mapped[str | None] = mapped_column(String(255))
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    fresh_graduate_status: Mapped[str | None] = mapped_column(String(120))
    political_status: Mapped[str | None] = mapped_column(String(120))
    household_region: Mapped[str | None] = mapped_column(String(120))
    grassroots_experience: Mapped[str | None] = mapped_column(Text)
    work_years: Mapped[float | None] = mapped_column(Float)
    certificates: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
