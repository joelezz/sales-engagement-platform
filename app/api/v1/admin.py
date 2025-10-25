from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.company import Company
from app.core.security import get_password_hash
from app.schemas.auth import UserProfile
from app.core.exceptions import SalesEngagementException

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/create-initial-admin", status_code=status.HTTP_201_CREATED)
async def create_initial_admin(
    db: AsyncSession = Depends(get_db)
):
    """
    Create the initial admin user - only works if no users exist yet
    This is a one-time setup endpoint for initial deployment
    """
    
    # Check if any users exist
    result = await db.execute(select(User))
    existing_users = result.scalars().all()
    
    if existing_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists or users are present in the system"
        )
    
    try:
        # Create default company
        company = Company(
            name="Sales Engagement Platform",
            domain="salesengagement.com",
            is_active=True
        )
        db.add(company)
        await db.flush()
        
        # Create admin user
        admin_user = User(
            email="admin@salesengagement.com",
            hashed_password=get_password_hash("Admin123!@#"),  # Change this!
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            tenant_id=company.id,
            company_id=company.id
        )
        
        db.add(admin_user)
        await db.commit()
        
        return {
            "message": "Initial admin user created successfully",
            "email": "admin@salesengagement.com",
            "password": "Admin123!@#",
            "warning": "Please change the password immediately after login"
        }
        
    except Exception as e:
        await db.rollback()
        raise SalesEngagementException(
            message=f"Failed to create admin user: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/users", response_model=List[UserProfile])
async def list_all_users(
    db: AsyncSession = Depends(get_db)
):
    """
    List all users in the system (for admin purposes)
    Note: This endpoint has no authentication for initial setup
    """
    
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return users


@router.patch("/promote/{user_id}")
async def promote_user_to_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Promote a user to admin role
    """
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_verified = True
    
    await db.commit()
    
    return {
        "message": f"User {user.email} promoted to admin",
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value
    }