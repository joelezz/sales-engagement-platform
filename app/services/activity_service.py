from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid
import math

from app.models.activity import Activity, ActivityType
from app.models.contact import Contact
from app.models.user import User
from app.schemas.activity import (
    ActivityCreate, 
    ActivityUpdate, 
    ActivityFilters, 
    ActivityTimelineResponse,
    ActivityStats,
    ActivitySummary
)
from app.core.exceptions import ResourceNotFoundError, TenantAccessError


class ActivityService:
    """Service for activity timeline management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_activity(
        self, 
        activity_data: ActivityCreate, 
        user_id: int,
        tenant_id: uuid.UUID,
        company_id: int
    ) -> Activity:
        """Create a new activity"""
        # Verify contact exists and belongs to tenant
        contact_stmt = select(Contact).where(
            and_(
                Contact.id == activity_data.contact_id,
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False)
            )
        )
        contact_result = await self.db.execute(contact_stmt)
        contact = contact_result.scalar_one_or_none()
        
        if not contact:
            raise ResourceNotFoundError("Contact", str(activity_data.contact_id))
        
        # Create activity
        activity = Activity(
            type=activity_data.type,
            title=activity_data.payload.get('title'),
            description=activity_data.payload.get('description'),
            activity_metadata=activity_data.payload,
            contact_id=activity_data.contact_id,
            user_id=user_id,
            tenant_id=tenant_id,
            company_id=company_id
        )
        
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        
        # Publish real-time notification
        from app.services.notification_service import NotificationService
        await NotificationService.publish_activity_event(activity)
        
        return activity
    
    async def get_contact_timeline(
        self, 
        contact_id: int, 
        tenant_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50
    ) -> ActivityTimelineResponse:
        """Get chronological activity timeline for a contact"""
        # Verify contact exists and belongs to tenant
        contact_stmt = select(Contact).where(
            and_(
                Contact.id == contact_id,
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False)
            )
        )
        contact_result = await self.db.execute(contact_stmt)
        contact = contact_result.scalar_one_or_none()
        
        if not contact:
            raise ResourceNotFoundError("Contact", str(contact_id))
        
        # Base query for activities
        stmt = select(Activity).where(
            and_(
                Activity.contact_id == contact_id,
                Activity.tenant_id == tenant_id
            )
        )
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(Activity.created_at)).offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(stmt)
        activities = result.scalars().all()
        
        # Calculate pagination info
        total_pages = math.ceil(total / page_size)
        
        return ActivityTimelineResponse(
            activities=activities,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def get_activities(
        self, 
        filters: ActivityFilters, 
        tenant_id: uuid.UUID
    ) -> ActivityTimelineResponse:
        """Get activities with filtering"""
        # Base query
        stmt = select(Activity).where(Activity.tenant_id == tenant_id)
        
        # Apply filters
        if filters.contact_id:
            stmt = stmt.where(Activity.contact_id == filters.contact_id)
        
        if filters.user_id:
            stmt = stmt.where(Activity.user_id == filters.user_id)
        
        if filters.activity_type:
            stmt = stmt.where(Activity.type == filters.activity_type)
        
        if filters.date_from:
            stmt = stmt.where(Activity.created_at >= filters.date_from)
        
        if filters.date_to:
            stmt = stmt.where(Activity.created_at <= filters.date_to)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.order_by(desc(Activity.created_at)).offset(offset).limit(filters.page_size)
        
        # Execute query
        result = await self.db.execute(stmt)
        activities = result.scalars().all()
        
        # Calculate pagination info
        total_pages = math.ceil(total / filters.page_size)
        
        return ActivityTimelineResponse(
            activities=activities,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages
        )
    
    async def update_activity(
        self, 
        activity_id: int, 
        updates: ActivityUpdate, 
        tenant_id: uuid.UUID
    ) -> Optional[Activity]:
        """Update an activity"""
        # Get existing activity
        stmt = select(Activity).where(
            and_(
                Activity.id == activity_id,
                Activity.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(stmt)
        activity = result.scalar_one_or_none()
        
        if not activity:
            return None
        
        # Apply updates
        if updates.payload is not None:
            # Merge with existing metadata
            activity.activity_metadata = {**activity.activity_metadata, **updates.payload}
            # Update title and description if provided
            if 'title' in updates.payload:
                activity.title = updates.payload['title']
            if 'description' in updates.payload:
                activity.description = updates.payload['description']
        
        await self.db.commit()
        await self.db.refresh(activity)
        
        return activity
    
    async def delete_activity(self, activity_id: int, tenant_id: uuid.UUID) -> bool:
        """Delete an activity"""
        stmt = select(Activity).where(
            and_(
                Activity.id == activity_id,
                Activity.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(stmt)
        activity = result.scalar_one_or_none()
        
        if not activity:
            return False
        
        await self.db.delete(activity)
        await self.db.commit()
        
        return True
    
    async def get_activity_stats(self, tenant_id: uuid.UUID, days: int = 30) -> ActivityStats:
        """Get activity statistics for tenant"""
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total activities
        total_stmt = select(func.count(Activity.id)).where(
            and_(
                Activity.tenant_id == tenant_id,
                Activity.created_at >= start_date
            )
        )
        total_result = await self.db.execute(total_stmt)
        total_activities = total_result.scalar()
        
        # Activities by type
        type_stmt = select(
            Activity.type,
            func.count(Activity.id).label('count')
        ).where(
            and_(
                Activity.tenant_id == tenant_id,
                Activity.created_at >= start_date
            )
        ).group_by(Activity.type)
        
        type_result = await self.db.execute(type_stmt)
        activities_by_type = {row.type.value: row.count for row in type_result}
        
        # Activities this week
        week_start = end_date - timedelta(days=7)
        week_stmt = select(func.count(Activity.id)).where(
            and_(
                Activity.tenant_id == tenant_id,
                Activity.created_at >= week_start
            )
        )
        week_result = await self.db.execute(week_stmt)
        activities_this_week = week_result.scalar()
        
        # Activities this month
        month_start = end_date - timedelta(days=30)
        month_stmt = select(func.count(Activity.id)).where(
            and_(
                Activity.tenant_id == tenant_id,
                Activity.created_at >= month_start
            )
        )
        month_result = await self.db.execute(month_stmt)
        activities_this_month = month_result.scalar()
        
        # Most active day of week
        dow_stmt = select(
            func.extract('dow', Activity.created_at).label('day_of_week'),
            func.count(Activity.id).label('count')
        ).where(
            and_(
                Activity.tenant_id == tenant_id,
                Activity.created_at >= start_date
            )
        ).group_by(func.extract('dow', Activity.created_at)).order_by(desc('count'))
        
        dow_result = await self.db.execute(dow_stmt)
        dow_row = dow_result.first()
        
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        most_active_day = day_names[int(dow_row.day_of_week)] if dow_row else None
        
        # Average activities per day
        average_per_day = total_activities / days if days > 0 else 0
        
        return ActivityStats(
            total_activities=total_activities,
            activities_by_type=activities_by_type,
            activities_this_week=activities_this_week,
            activities_this_month=activities_this_month,
            most_active_day=most_active_day,
            average_activities_per_day=round(average_per_day, 2)
        )
    
    async def get_contact_activity_summaries(
        self, 
        tenant_id: uuid.UUID,
        limit: int = 20
    ) -> List[ActivitySummary]:
        """Get activity summaries for contacts"""
        # Query to get contact activity summaries
        stmt = text("""
            SELECT 
                c.id as contact_id,
                c.firstname || ' ' || c.lastname as contact_name,
                COUNT(a.id) as total_activities,
                MAX(a.created_at) as last_activity_date,
                (
                    SELECT a2.type 
                    FROM activities a2 
                    WHERE a2.contact_id = c.id 
                    ORDER BY a2.created_at DESC 
                    LIMIT 1
                ) as last_activity_type
            FROM contacts c
            LEFT JOIN activities a ON c.id = a.contact_id
            WHERE c.tenant_id = :tenant_id 
                AND c.is_deleted = false
            GROUP BY c.id, c.firstname, c.lastname
            HAVING COUNT(a.id) > 0
            ORDER BY last_activity_date DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(stmt, {
            'tenant_id': str(tenant_id),
            'limit': limit
        })
        
        summaries = []
        for row in result:
            # Get activities by type for this contact
            type_stmt = select(
                Activity.type,
                func.count(Activity.id).label('count')
            ).where(
                and_(
                    Activity.contact_id == row.contact_id,
                    Activity.tenant_id == tenant_id
                )
            ).group_by(Activity.type)
            
            type_result = await self.db.execute(type_stmt)
            activities_by_type = {r.type.value: r.count for r in type_result}
            
            summaries.append(ActivitySummary(
                contact_id=row.contact_id,
                contact_name=row.contact_name,
                total_activities=row.total_activities,
                last_activity_date=row.last_activity_date,
                last_activity_type=ActivityType(row.last_activity_type) if row.last_activity_type else None,
                activities_by_type=activities_by_type
            ))
        
        return summaries
    
    async def search_activities(
        self, 
        query: str, 
        tenant_id: uuid.UUID,
        activity_type: Optional[ActivityType] = None,
        limit: int = 50
    ) -> List[Activity]:
        """Search activities by content"""
        if not query.strip():
            return []
        
        # Search in activity metadata and text fields using PostgreSQL operators
        stmt = select(Activity).where(
            and_(
                Activity.tenant_id == tenant_id,
                or_(
                    Activity.title.ilike(f'%{query}%'),
                    Activity.description.ilike(f'%{query}%'),
                    Activity.activity_metadata.op('->>')('content').ilike(f'%{query}%'),
                    Activity.activity_metadata.op('->>')('subject').ilike(f'%{query}%'),
                    Activity.activity_metadata.op('->>')('message').ilike(f'%{query}%')
                )
            )
        )
        
        if activity_type:
            stmt = stmt.where(Activity.type == activity_type)
        
        stmt = stmt.order_by(desc(Activity.created_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()