"""
统一多模态文档模型
"""
import uuid
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy import String, Float, Integer, Text, ForeignKey, func, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector  # type: ignore
from orgmind.models.base import Base, OrgMixin, TimestampMixin
from orgmind.config import EMBEDDING_DIM


class Document(Base, OrgMixin, TimestampMixin):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    doc_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    scope: Mapped[str] = mapped_column(String(20), default="department")
    sensitivity: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    graph_node_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_metadata: Mapped[Dict] = mapped_column("metadata", JSONB, default=dict)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    start_offset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_offset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class StructuredData(Base):
    __tablename__ = "structured_data"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    sheet_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    schema: Mapped[Dict] = mapped_column(JSONB, nullable=False)
    rows: Mapped[Dict] = mapped_column(JSONB, nullable=False)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())


class DataLineage(Base):
    __tablename__ = "data_lineage"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    derived_type: Mapped[str] = mapped_column(String(20), nullable=False)
    derived_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    transform_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transform_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
