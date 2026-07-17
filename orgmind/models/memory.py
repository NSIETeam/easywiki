"""
记忆模型 (情景记忆/语义记忆)
"""
import uuid
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy import String, Float, Integer, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector  # type: ignore
from orgmind.models.base import Base, OrgMixin, TimestampMixin
from orgmind.config import EMBEDDING_DIM


class Memory(Base, OrgMixin, TimestampMixin):
    __tablename__ = "memories"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), default="department")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    sensitivity: Mapped[str] = mapped_column(String(20), default="normal")
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    decay_score: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("memories.id"), nullable=True)
    graph_node_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_metadata: Mapped[Dict] = mapped_column("metadata", JSONB, default=dict)
