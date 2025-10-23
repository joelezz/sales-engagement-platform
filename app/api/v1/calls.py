from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.voip_service import VoIPService
from app.schemas.call import (
    CallInitiate,
    CallResponse,
    CallSession,
    CallRecording,
    TwilioWebhook,
    CallFilters,
    CallStats
)
from app.models.user import User
from app.models.call import CallStatus, CallDirection

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("", response_model=CallSession, status_code=status.HTTP_201_CREATED)
async def initiate_call(
    call_data: CallInitiate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Initiate an outbound call to a contact"""
    voip_service = VoIPService(db)
    
    try:
        call_session = await voip_service.initiate_call(
            contact_id=call_data.contact_id,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            from_number=call_data.from_number
        )
        return call_session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[CallResponse])
async def get_call_history(
    contact_id: Optional[int] = Query(None, description="Filter by contact ID"),
    call_status: Optional[CallStatus] = Query(None, description="Filter by call status"),
    direction: Optional[CallDirection] = Query(None, description="Filter by call direction"),
    date_from: Optional[datetime] = Query(None, description="Filter calls from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter calls to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get call history with filtering and pagination"""
    voip_service = VoIPService(db)
    
    filters = CallFilters(
        contact_id=contact_id,
        status=call_status,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    
    calls, total = await voip_service.get_call_history(filters, current_user.tenant_id)
    
    return calls


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific call by ID"""
    from sqlalchemy import select, and_
    from app.models.call import Call
    
    stmt = select(Call).where(
        and_(
            Call.id == call_id,
            Call.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(stmt)
    call = result.scalar_one_or_none()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    return call


@router.post("/{call_sid}/end")
async def end_call(
    call_sid: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """End an active call"""
    voip_service = VoIPService(db)
    
    success = await voip_service.end_call(call_sid, current_user.tenant_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found or could not be ended"
        )
    
    return {"message": "Call ended successfully"}


@router.get("/{call_sid}/recording", response_model=CallRecording)
async def get_call_recording(
    call_sid: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get call recording information"""
    voip_service = VoIPService(db)
    
    recording = await voip_service.get_call_recording(call_sid, current_user.tenant_id)
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call recording not found"
        )
    
    return recording


@router.get("/stats/overview")
async def get_call_stats(
    date_from: Optional[datetime] = Query(None, description="Stats from this date"),
    date_to: Optional[datetime] = Query(None, description="Stats to this date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get call statistics overview"""
    from sqlalchemy import select, func, and_
    from app.models.call import Call
    
    # Base query
    stmt = select(Call).where(Call.tenant_id == current_user.tenant_id)
    
    # Apply date filters
    if date_from:
        stmt = stmt.where(Call.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Call.created_at <= date_to)
    
    # Total calls
    total_calls_result = await db.execute(
        select(func.count(Call.id)).select_from(stmt.subquery())
    )
    total_calls = total_calls_result.scalar()
    
    # Completed calls
    completed_calls_result = await db.execute(
        select(func.count(Call.id)).select_from(
            stmt.where(Call.status == CallStatus.COMPLETED).subquery()
        )
    )
    completed_calls = completed_calls_result.scalar()
    
    # Failed calls (including busy, no-answer, canceled)
    failed_statuses = [CallStatus.FAILED, CallStatus.BUSY, CallStatus.NO_ANSWER, CallStatus.CANCELED]
    failed_calls_result = await db.execute(
        select(func.count(Call.id)).select_from(
            stmt.where(Call.status.in_(failed_statuses)).subquery()
        )
    )
    failed_calls = failed_calls_result.scalar()
    
    # Total duration
    duration_result = await db.execute(
        select(func.coalesce(func.sum(Call.duration), 0)).select_from(
            stmt.where(Call.duration.is_not(None)).subquery()
        )
    )
    total_duration = duration_result.scalar()
    
    # Average duration
    avg_duration_result = await db.execute(
        select(func.coalesce(func.avg(Call.duration), 0)).select_from(
            stmt.where(Call.duration.is_not(None)).subquery()
        )
    )
    average_duration = float(avg_duration_result.scalar())
    
    # Success rate
    success_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
    
    # Total cost
    cost_result = await db.execute(
        select(func.coalesce(func.sum(Call.price), 0)).select_from(
            stmt.where(Call.price.is_not(None)).subquery()
        )
    )
    total_cost = float(cost_result.scalar())
    
    return CallStats(
        total_calls=total_calls,
        completed_calls=completed_calls,
        failed_calls=failed_calls,
        total_duration=int(total_duration),
        average_duration=average_duration,
        success_rate=round(success_rate, 2),
        total_cost=total_cost if total_cost > 0 else None
    )