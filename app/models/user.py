from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, TenantMixin
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    REP = "rep"


class User(Base, TimestampMixin, TenantMixin):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.REP)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Foreign key to company
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"