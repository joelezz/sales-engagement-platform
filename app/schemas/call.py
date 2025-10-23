from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid

from app.models.call import CallStatus, CallDirection


class CallInitiate(BaseModel):
    """Schema for initiating a call"""
    contact_id: int = Field(..., description="ID of the contact to call")
    from_number: Optional[str] = Field(None, description="Override default from number")


class CallResponse(BaseModel):
    """Schema for call response"""
    id: int
    call_sid: str
    direction: CallDirection
    status: CallStatus
    from_number: str
    to_number: str
    duration: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    has_recording: bool
    recording_url: Optional[str]
    price: Optional[float]
    price_unit: Optional[str]
    contact_id: int
    user_id: int
    tenant_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class CallSession(BaseModel):
    """Schema for active call session"""
    call_id: int
    call_sid: str
    status: CallStatus
    from_number: str
    to_number: str
    contact_name: str
    started_at: datetime


class CallRecording(BaseModel):
    """Schema for call recording"""
    call_id: int
    recording_sid: str
    recording_url: str
    duration: int
    file_size: Optional[int] = None
    format: str = "mp3"


class TwilioWebhook(BaseModel):
    """Schema for Twilio webhook data"""
    CallSid: str
    CallStatus: str
    From: str
    To: str
    Direction: str
    CallDuration: Optional[str] = None
    RecordingUrl: Optional[str] = None
    RecordingSid: Optional[str] = None
    Price: Optional[str] = None
    PriceUnit: Optional[str] = None


class CallFilters(BaseModel):
    """Schema for call filtering"""
    contact_id: Optional[int] = None
    status: Optional[CallStatus] = None
    direction: Optional[CallDirection] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)


class CallStats(BaseModel):
    """Schema for call statistics"""
    total_calls: int
    completed_calls: int
    failed_calls: int
    total_duration: int  # in seconds
    average_duration: float  # in seconds
    success_rate: float  # percentage
    total_cost: Optional[float] = None