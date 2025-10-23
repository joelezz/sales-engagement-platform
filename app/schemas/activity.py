from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.models.activity import ActivityType


class ActivityBase(BaseModel):
    """Base activity schema"""
    type: ActivityType
    payload: Dict[str, Any] = Field(..., description="Activity-specific data")


class ActivityCreate(ActivityBase):
    """Schema for creating an activity"""
    contact_id: int = Field(..., description="ID of the associated contact")


class ActivityResponse(ActivityBase):
    """Schema for activity response"""
    id: int
    contact_id: int
    user_id: int
    tenant_id: uuid.UUID
    created_at: datetime
    
    # Computed fields from payload
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    
    class Config:
        from_attributes = True
    
    @validator('title', pre=False, always=True)
    def generate_title(cls, v, values):
        """Generate activity title based on type and payload"""
        if v:
            return v
        
        activity_type = values.get('type')
        payload = values.get('payload', {})
        
        if activity_type == ActivityType.CALL:
            direction = payload.get('direction', 'outbound')
            duration = payload.get('duration', 0)
            if duration:
                return f"{direction.title()} call ({duration}s)"
            else:
                return f"{direction.title()} call"
        
        elif activity_type == ActivityType.EMAIL:
            subject = payload.get('subject', 'Email')
            return f"Email: {subject}"
        
        elif activity_type == ActivityType.SMS:
            return "SMS message"
        
        elif activity_type == ActivityType.NOTE:
            return payload.get('title', 'Note')
        
        elif activity_type == ActivityType.MEETING:
            return payload.get('title', 'Meeting')
        
        return f"{activity_type.value.title()} activity"
    
    @validator('description', pre=False, always=True)
    def generate_description(cls, v, values):
        """Generate activity description based on type and payload"""
        if v:
            return v
        
        activity_type = values.get('type')
        payload = values.get('payload', {})
        
        if activity_type == ActivityType.CALL:
            from_num = payload.get('from_number', '')
            to_num = payload.get('to_number', '')
            return f"Call from {from_num} to {to_num}"
        
        elif activity_type == ActivityType.EMAIL:
            return payload.get('preview', payload.get('body', ''))[:100]
        
        elif activity_type == ActivityType.SMS:
            return payload.get('message', '')[:100]
        
        elif activity_type == ActivityType.NOTE:
            return payload.get('content', '')[:100]
        
        elif activity_type == ActivityType.MEETING:
            return payload.get('description', '')[:100]
        
        return ""


class ActivityUpdate(BaseModel):
    """Schema for updating an activity"""
    payload: Optional[Dict[str, Any]] = None


class ActivityFilters(BaseModel):
    """Schema for activity filtering"""
    contact_id: Optional[int] = None
    user_id: Optional[int] = None
    activity_type: Optional[ActivityType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)


class ActivityTimelineResponse(BaseModel):
    """Schema for activity timeline response"""
    activities: List[ActivityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ActivityStats(BaseModel):
    """Schema for activity statistics"""
    total_activities: int
    activities_by_type: Dict[str, int]
    activities_this_week: int
    activities_this_month: int
    most_active_day: Optional[str] = None
    average_activities_per_day: float


class ActivitySummary(BaseModel):
    """Schema for activity summary"""
    contact_id: int
    contact_name: str
    total_activities: int
    last_activity_date: Optional[datetime]
    last_activity_type: Optional[ActivityType]
    activities_by_type: Dict[str, int]