"""
Skill/Agent 统一模型 (artifacts 表)
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import String, Float, Integer, Text, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector  # type: ignore
from orgmind.models.base import Base, OrgMixin, TimestampMixin
from orgmind.config import EMBEDDING_DIM


class Artifact(Base, OrgMixin, TimestampMixin):
    __tablename__ = "artifacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_type: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    description_embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    resources: Mapped[Dict] = mapped_column(JSONB, default=dict)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    scope: Mapped[str] = mapped_column(String(20), default="department")
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=True)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), default=list)
    tools: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), default=list)
    bound_skill_ids: Mapped[Optional[List[uuid.UUID]]] = mapped_column(ARRAY(UUID), default=list)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    graph_node_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    extra_metadata: Mapped[Dict] = mapped_column("metadata", JSONB, default=dict)


class ArtifactPermission(Base):
    __tablename__ = "artifact_permissions"
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifacts.id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(20), primary_key=True)
    access: Mapped[str] = mapped_column(String(20), primary_key=True)
    scope: Mapped[str] = mapped_column(String(20), default="org")
