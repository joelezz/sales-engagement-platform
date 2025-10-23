from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserRegister(BaseModel):
    """User registration request schema"""
    email: EmailStr
    password: str = Field(..., min_length=12, description="Password must be at least 12 characters")
    company_name: str = Field(..., min_length=1, max_length=200)


class TokenPair(BaseModel):
    """JWT token pair response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


class UserClaims(BaseModel):
    """JWT token claims"""
    sub: str  # user_id
    email: str
    tenant_id: str
    role: str
    exp: int
    iat: int
    type: str


class AuthResult(BaseModel):
    """Authentication result"""
    success: bool
    user_id: Optional[int] = None
    tenant_id: Optional[uuid.UUID] = None
    error_message: Optional[str] = None


class UserProfile(BaseModel):
    """User profile response"""
    id: int
    email: str
    role: str
    tenant_id: uuid.UUID
    company_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True