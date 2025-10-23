from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid

from app.models.user import User, UserRole
from app.models.company import Company
from app.schemas.auth import AuthResult, TokenPair, UserClaims, UserRegister
from app.core.security import (
    verify_password, 
    get_password_hash, 
    validate_password_policy,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token
)
from app.core.config import settings
from app.core.exceptions import SalesEngagementException
from app.core.redis import redis_client


class AuthService:
    """Authentication service for user management and JWT tokens"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate user with email and password"""
        try:
            # Find user by email with company relationship loaded
            from sqlalchemy.orm import selectinload
            stmt = select(User).options(selectinload(User.company)).join(Company).where(User.email == email, User.is_active == True)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or not verify_password(password, user.password_hash):
                return AuthResult(
                    success=False,
                    error_message="Invalid email or password"
                )
            
            return AuthResult(
                success=True,
                user_id=user.id,
                tenant_id=user.tenant_id
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"Authentication failed: {str(e)}"
            )
    
    async def register_user(self, registration_data: UserRegister) -> Tuple[bool, Optional[str]]:
        """Register a new user and company"""
        try:
            # Validate password policy
            if not validate_password_policy(registration_data.password):
                return False, "Password does not meet policy requirements"
            
            # Check if user already exists
            stmt = select(User).where(User.email == registration_data.email)
            result = await self.db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                return False, "User with this email already exists"
            
            # Create new company (tenant)
            company = Company(
                name=registration_data.company_name,
                plan="basic"
            )
            self.db.add(company)
            await self.db.flush()  # Get the company ID
            
            # Create new user
            user = User(
                email=registration_data.email,
                password_hash=get_password_hash(registration_data.password),
                role=UserRole.ADMIN,  # First user is admin
                tenant_id=company.tenant_id,
                company_id=company.id
            )
            self.db.add(user)
            await self.db.commit()
            
            return True, None
            
        except Exception as e:
            await self.db.rollback()
            return False, f"Registration failed: {str(e)}"
    
    async def create_token_pair(self, user_id: int, tenant_id: uuid.UUID) -> TokenPair:
        """Create access and refresh token pair"""
        # Get user details
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one()
        
        # Create token data
        token_data = {
            "sub": str(user_id),
            "email": user.email,
            "tenant_id": str(tenant_id),
            "role": user.role.value,
            "iat": int(datetime.utcnow().timestamp())
        }
        
        # Generate tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token in Redis with expiration
        refresh_key = f"refresh_token:{user_id}"
        await redis_client.set(
            refresh_key, 
            refresh_token, 
            tenant_id=tenant_id,
            ttl=settings.refresh_token_expire_days * 24 * 3600
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def refresh_token(self, refresh_token: str) -> Optional[TokenPair]:
        """Refresh access token using refresh token"""
        try:
            # Decode refresh token
            payload = decode_refresh_token(refresh_token)
            user_id = int(payload.get("sub"))
            tenant_id = uuid.UUID(payload.get("tenant_id"))
            
            # Verify refresh token exists in Redis
            refresh_key = f"refresh_token:{user_id}"
            stored_token = await redis_client.get(refresh_key, tenant_id=tenant_id)
            
            if not stored_token or stored_token != refresh_token:
                return None
            
            # Verify user is still active
            stmt = select(User).where(User.id == user_id, User.is_active == True)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                # Clean up invalid refresh token
                await redis_client.delete(refresh_key, tenant_id=tenant_id)
                return None
            
            # Create new token pair
            return await self.create_token_pair(user_id, tenant_id)
            
        except Exception:
            return None
    
    async def revoke_token(self, user_id: int, tenant_id: uuid.UUID) -> bool:
        """Revoke refresh token for user"""
        try:
            refresh_key = f"refresh_token:{user_id}"
            await redis_client.delete(refresh_key, tenant_id=tenant_id)
            return True
        except Exception:
            return False
    
    async def validate_token(self, token: str) -> Optional[UserClaims]:
        """Validate access token and return claims"""
        try:
            payload = decode_access_token(token)
            
            # Verify user is still active
            user_id = int(payload.get("sub"))
            stmt = select(User).where(User.id == user_id, User.is_active == True)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            return UserClaims(**payload)
            
        except Exception:
            return None
    
    async def get_user_profile(self, user_id: int) -> Optional[User]:
        """Get user profile with company information"""
        from sqlalchemy.orm import selectinload
        stmt = select(User).options(selectinload(User.company)).join(Company).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()