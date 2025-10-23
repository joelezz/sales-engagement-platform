from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Index, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, TenantMixin


class Contact(Base, TimestampMixin, TenantMixin):
    """Contact model"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)
    company_name = Column(String(200), nullable=True)
    job_title = Column(String(100), nullable=True)
    notes = Column(String, nullable=True)  # Text type
    tags = Column(JSON, nullable=True, default=dict)
    contact_metadata = Column(JSON, nullable=True, default=dict)
    is_deleted = Column(Boolean, nullable=True, default=False)
    
    # Foreign key to company
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="contacts")
    activities = relationship("Activity", back_populates="contact", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="contact", cascade="all, delete-orphan")
    
    # Basic indexes (complex full-text search can be added later)
    __table_args__ = (
        Index('ix_contacts_tenant_id', 'tenant_id'),
    )
    
    @property
    def full_name(self) -> str:
        """Get full name of contact"""
        return f"{self.firstname} {self.lastname}"
    
    def get_is_deleted(self) -> bool:
        """Check if contact is soft deleted"""
        return bool(self.is_deleted)
    
    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.full_name}', email='{self.email}')>"