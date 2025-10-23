from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, TenantMixin
import enum


class CallStatus(str, enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no-answer"
    CANCELED = "canceled"


class CallDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Call(Base, TimestampMixin, TenantMixin):
    """Call model for tracking VoIP calls"""
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Twilio identifiers
    call_sid = Column(String(34), unique=True, nullable=False, index=True)  # Twilio Call SID
    
    # Call details
    direction = Column(Enum(CallDirection), nullable=False)
    status = Column(Enum(CallStatus), nullable=False, default=CallStatus.INITIATED)
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)
    
    # Call metrics
    duration = Column(Integer, nullable=True)  # Duration in seconds
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Recording
    has_recording = Column(Boolean, default=False)
    recording_url = Column(String(500), nullable=True)
    recording_sid = Column(String(34), nullable=True)
    
    # Cost tracking
    price = Column(Float, nullable=True)
    price_unit = Column(String(3), nullable=True)  # USD, EUR, etc.
    
    # Foreign keys
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="calls")
    user = relationship("User", back_populates="calls")
    company = relationship("Company", back_populates="calls")
    
    def __repr__(self):
        return f"<Call(id={self.id}, call_sid='{self.call_sid}', status='{self.status}')>"