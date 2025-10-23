from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserLogin, 
    UserRegister, 
    TokenPair, 
    TokenRefresh, 
    UserProfile
)
from app.core.exceptions import SalesEngagementException

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    registration_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user and company"""
    auth_service = AuthService(db)
    
    success, error_message = await auth_service.register_user(registration_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    return {
        "message": "User registered successfully",
        "email": registration_data.email
    }


@router.post("/login", response_model=dict)
async def login(
    login_data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens"""
    auth_service = AuthService(db)
    
    # Authenticate user
    auth_result = await auth_service.authenticate(login_data.email, login_data.password)
    
    if not auth_result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_result.error_message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token pair
    token_pair = await auth_service.create_token_pair(
        auth_result.user_id, 
        auth_result.tenant_id
    )
    
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=token_pair.refresh_token,
        httponly=True,
        secure=True,  # Use HTTPS in production
        samesite="strict",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    # Get user profile
    user = await auth_service.get_user_profile(auth_result.user_id)
    
    return {
        "access_token": token_pair.access_token,
        "token_type": token_pair.token_type,
        "expires_in": token_pair.expires_in,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "company_name": user.company.name
        }
    }


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: Request,
    token_data: Optional[TokenRefresh] = None,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    
    # Get refresh token from cookie or request body
    refresh_token = None
    if token_data and token_data.refresh_token:
        refresh_token = token_data.refresh_token
    else:
        refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    # Refresh tokens
    new_token_pair = await auth_service.refresh_token(refresh_token)
    
    if not new_token_pair:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return {
        "access_token": new_token_pair.access_token,
        "token_type": new_token_pair.token_type,
        "expires_in": new_token_pair.expires_in
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and revoke refresh token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    auth_service = AuthService(db)
    
    # Validate token and get user info
    user_claims = await auth_service.validate_token(credentials.credentials)
    if not user_claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Revoke refresh token
    await auth_service.revoke_token(
        int(user_claims.sub), 
        user_claims.tenant_id
    )
    
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="strict"
    )
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    auth_service = AuthService(db)
    
    # Validate token
    user_claims = await auth_service.validate_token(credentials.credentials)
    if not user_claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Get user profile
    user = await auth_service.get_user_profile(int(user_claims.sub))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfile(
        id=user.id,
        email=user.email,
        role=user.role.value,
        tenant_id=user.tenant_id,
        company_name=user.company.name,
        is_active=user.is_active,
        created_at=user.created_at
    )