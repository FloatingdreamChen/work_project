from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_path: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False, server_default="local")
    published_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    version: Mapped[str] = mapped_column(String(80), nullable=False, server_default="v1")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
