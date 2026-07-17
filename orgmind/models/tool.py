"""
工具注册表与审计日志模型
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, func, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from orgmind.models.base import Base, TimestampMixin


class Tool(Base, TimestampMixin):
    __tablename__ = "tools"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # NULL=全局内置
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_schema: Mapped[Dict] = mapped_column(JSONB, nullable=False)
    output_schema: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)
    execution_type: Mapped[str] = mapped_column(String(20), nullable=False)
    endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allowed_roles: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    timeout_ms: Mapped[int] = mapped_column(Integer, default=30000)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_metadata: Mapped[Dict] = mapped_column("metadata", JSONB, default=dict)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    details: Mapped[Dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
