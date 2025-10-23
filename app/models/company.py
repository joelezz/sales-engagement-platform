from sqlalchemy import Column, Integer, String, DateTime, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin
import uuid


class Company(Base, TimestampMixin):
    """Company (Tenant) model"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    name = Column(String(200), nullable=False)
    plan = Column(String(50), nullable=False, default="basic")  # basic, pro, enterprise
    settings = Column(JSON, default=dict)
    
    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="company", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', plan='{self.plan}')>"