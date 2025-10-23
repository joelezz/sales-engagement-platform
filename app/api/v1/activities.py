from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.activity_service import ActivityService
from app.schemas.activity import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
    ActivityTimelineResponse,
    ActivityFilters,
    ActivityStats,
    ActivitySummary
)
from app.models.user import User
from app.models.activity import ActivityType

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=ActivityTimelineResponse)
async def get_activities(
    contact_id: Optional[int] = Query(None, description="Filter by contact ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    activity_type: Optional[ActivityType] = Query(None, description="Filter by activity type"),
    date_from: Optional[datetime] = Query(None, description="Filter activities from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter activities to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activities with filtering and pagination"""
    activity_service = ActivityService(db)
    
    filters = ActivityFilters(
        contact_id=contact_id,
        user_id=user_id,
        activity_type=activity_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    
    return await activity_service.get_activities(filters, current_user.tenant_id)


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new activity"""
    activity_service = ActivityService(db)
    
    activity = await activity_service.create_activity(
        activity_data,
        current_user.id,
        current_user.tenant_id,
        current_user.company_id
    )
    
    return activity


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific activity by ID"""
    from sqlalchemy import select, and_
    from app.models.activity import Activity
    
    stmt = select(Activity).where(
        and_(
            Activity.id == activity_id,
            Activity.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(stmt)
    activity = result.scalar_one_or_none()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    return activity


@router.patch("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: int,
    updates: ActivityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an activity"""
    activity_service = ActivityService(db)
    
    activity = await activity_service.update_activity(
        activity_id,
        updates,
        current_user.tenant_id
    )
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an activity"""
    activity_service = ActivityService(db)
    
    success = await activity_service.delete_activity(activity_id, current_user.tenant_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )


@router.get("/stats/overview", response_model=ActivityStats)
async def get_activity_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activity statistics overview"""
    activity_service = ActivityService(db)
    
    stats = await activity_service.get_activity_stats(current_user.tenant_id, days)
    
    return stats


@router.get("/search/content", response_model=List[ActivityResponse])
async def search_activities(
    q: str = Query(..., min_length=2, description="Search query"),
    activity_type: Optional[ActivityType] = Query(None, description="Filter by activity type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search activities by content"""
    activity_service = ActivityService(db)
    
    activities = await activity_service.search_activities(
        q,
        current_user.tenant_id,
        activity_type=activity_type,
        limit=limit
    )
    
    return activities


@router.get("/summaries/contacts", response_model=List[ActivitySummary])
async def get_contact_activity_summaries(
    limit: int = Query(20, ge=1, le=100, description="Maximum contacts to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activity summaries for contacts"""
    activity_service = ActivityService(db)
    
    summaries = await activity_service.get_contact_activity_summaries(
        current_user.tenant_id,
        limit=limit
    )
    
    return summaries