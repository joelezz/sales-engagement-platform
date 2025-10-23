from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db, set_tenant_context
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.auth import UserClaims
import uuid

security = HTTPBearer()


async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserClaims:
    """Get current user claims from JWT token"""
    auth_service = AuthService(db)
    
    user_claims = await auth_service.validate_token(credentials.credentials)
    if not user_claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_claims


async def get_current_user(
    user_claims: UserClaims = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user object"""
    # Note: User agent logging can be added via middleware if needed
    user_agent = None
    
    # Set comprehensive context for RLS and audit logging
    await set_tenant_context(
        db, 
        uuid.UUID(user_claims.tenant_id),
        user_id=int(user_claims.sub),
        user_role=user_claims.role,
        user_agent=user_agent
    )
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_profile(int(user_claims.sub))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user