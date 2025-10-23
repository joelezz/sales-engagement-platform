from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantMixin:
    """Mixin for multi-tenant support"""
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)