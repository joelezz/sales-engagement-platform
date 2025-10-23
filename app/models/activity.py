from sqlalchemy import Column, Integer, String, ForeignKey, JSON, BigInteger, Index, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TenantMixin
import enum


class ActivityType(str, enum.Enum):
    CALL = "call"
    EMAIL = "email"
    SMS = "sms"
    NOTE = "note"
    MEETING = "meeting"


class Activity(Base, TenantMixin):
    """Activity model for tracking all customer interactions"""
    __tablename__ = "activities"
    
    id = Column(BigInteger, primary_key=True, index=True)
    type = Column(Enum(ActivityType), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    description = Column(String, nullable=True)  # Text type
    activity_metadata = Column("metadata", JSON, nullable=True, default=dict)  # Activity-specific data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Foreign keys
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="activities")
    user = relationship("User", back_populates="activities")
    company = relationship("Company", back_populates="activities")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_activities_tenant_contact', 'tenant_id', 'contact_id'),
        Index('ix_activities_tenant_user', 'tenant_id', 'user_id'),
        Index('ix_activities_tenant_type_created', 'tenant_id', 'type', 'created_at'),
        Index('ix_activities_contact_created', 'contact_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Activity(id={self.id}, type='{self.type}', contact_id={self.contact_id})>"