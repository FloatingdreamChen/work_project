from __future__ import annotations

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class CurrentInformationSource(Base):
    __tablename__ = "current_information_sources"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    source_type: Mapped[str] = mapped_column(String(80), nullable=False, server_default="web")
    provider: Mapped[str | None] = mapped_column(String(80))
    query: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    credibility: Mapped[str | None] = mapped_column(String(40))
    credibility_score: Mapped[int | None] = mapped_column(Integer)
    credibility_reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
