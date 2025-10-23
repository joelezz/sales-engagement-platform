from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class ContactBase(BaseModel):
    """Base contact schema"""
    firstname: str = Field(..., min_length=1, max_length=100)
    lastname: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    contact_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            # Basic phone validation - remove spaces and check if it contains only digits, +, -, (, )
            cleaned = ''.join(c for c in v if c.isdigit() or c in '+-()')
            if len(cleaned) < 7:
                raise ValueError('Phone number too short')
        return v


class ContactCreate(ContactBase):
    """Schema for creating a contact"""
    pass


class ContactUpdate(BaseModel):
    """Schema for updating a contact"""
    firstname: Optional[str] = Field(None, min_length=1, max_length=100)
    lastname: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    contact_metadata: Optional[Dict[str, Any]] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            cleaned = ''.join(c for c in v if c.isdigit() or c in '+-()')
            if len(cleaned) < 7:
                raise ValueError('Phone number too short')
        return v


class ContactResponse(ContactBase):
    """Schema for contact response"""
    id: int
    tenant_id: uuid.UUID
    full_name: str
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """Schema for paginated contact list response"""
    contacts: list[ContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ContactFilters(BaseModel):
    """Schema for contact filtering"""
    search: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)
    include_deleted: bool = False