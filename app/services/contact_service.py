from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid
import math

from app.models.contact import Contact
from app.models.company import Company
from app.schemas.contact import ContactCreate, ContactUpdate, ContactFilters, ContactListResponse
from app.core.exceptions import ResourceNotFoundError, TenantAccessError


class ContactService:
    """Service for contact management operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_contact(self, contact_data: ContactCreate, tenant_id: uuid.UUID, company_id: int) -> Contact:
        """Create a new contact"""
        contact = Contact(
            firstname=contact_data.firstname,
            lastname=contact_data.lastname,
            email=contact_data.email,
            phone=contact_data.phone,
            contact_metadata=contact_data.contact_metadata or {},
            tenant_id=tenant_id,
            company_id=company_id
        )
        
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        
        # Create activity for contact creation
        await self._create_contact_activity(contact, "created", None)
        
        # Publish contact creation notification
        from app.services.notification_service import NotificationService
        contact_data = {
            "id": contact.id,
            "firstname": contact.firstname,
            "lastname": contact.lastname,
            "email": contact.email,
            "phone": contact.phone,
            "full_name": contact.full_name,
            "created_at": contact.created_at.isoformat()
        }
        await NotificationService.publish_contact_event(contact_data, contact.tenant_id, "created")
        
        return contact
    
    async def get_contact(self, contact_id: int, tenant_id: uuid.UUID) -> Optional[Contact]:
        """Get a single contact by ID"""
        stmt = select(Contact).where(
            and_(
                Contact.id == contact_id,
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_contacts(self, filters: ContactFilters, tenant_id: uuid.UUID) -> ContactListResponse:
        """Get paginated list of contacts with filtering"""
        # Base query
        stmt = select(Contact).where(Contact.tenant_id == tenant_id)
        
        # Apply deleted filter
        if not filters.include_deleted:
            stmt = stmt.where(Contact.is_deleted.is_(False))
        
        # Apply search filter
        if filters.search:
            search_term = f"%{filters.search}%"
            stmt = stmt.where(
                or_(
                    Contact.firstname.ilike(search_term),
                    Contact.lastname.ilike(search_term),
                    Contact.email.ilike(search_term),
                    Contact.phone.ilike(search_term)
                )
            )
        
        # Apply email filter
        if filters.email:
            stmt = stmt.where(Contact.email.ilike(f"%{filters.email}%"))
        
        # Apply phone filter
        if filters.phone:
            stmt = stmt.where(Contact.phone.ilike(f"%{filters.phone}%"))
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.offset(offset).limit(filters.page_size)
        
        # Order by created_at desc
        stmt = stmt.order_by(Contact.created_at.desc())
        
        # Execute query
        result = await self.db.execute(stmt)
        contacts = result.scalars().all()
        
        # Calculate pagination info
        total_pages = math.ceil(total / filters.page_size)
        
        return ContactListResponse(
            contacts=contacts,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages
        )
    
    async def update_contact(self, contact_id: int, updates: ContactUpdate, tenant_id: uuid.UUID, user_id: Optional[int] = None) -> Optional[Contact]:
        """Update a contact with partial updates"""
        # Get existing contact
        contact = await self.get_contact(contact_id, tenant_id)
        if not contact:
            return None
        
        # Apply updates
        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)
        
        contact.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(contact)
        
        # Create activity for contact update
        if user_id:
            await self._create_contact_activity(contact, "updated", user_id)
        
        # Publish contact update notification
        from app.services.notification_service import NotificationService
        contact_data = {
            "id": contact.id,
            "firstname": contact.firstname,
            "lastname": contact.lastname,
            "email": contact.email,
            "phone": contact.phone,
            "full_name": contact.full_name,
            "updated_at": contact.updated_at.isoformat()
        }
        await NotificationService.publish_contact_event(contact_data, contact.tenant_id, "updated")
        
        return contact
    
    async def delete_contact(self, contact_id: int, tenant_id: uuid.UUID) -> bool:
        """Soft delete a contact"""
        contact = await self.get_contact(contact_id, tenant_id)
        if not contact:
            return False
        
        contact.is_deleted = True
        await self.db.commit()
        
        return True
    
    async def search_contacts(self, query: str, tenant_id: uuid.UUID, limit: int = 20) -> List[Contact]:
        """Search contacts using PostgreSQL full-text search"""
        if not query.strip():
            return []
        
        # Use PostgreSQL full-text search
        search_vector = func.to_tsvector('english', 
            func.coalesce(Contact.firstname, '') + ' ' +
            func.coalesce(Contact.lastname, '') + ' ' +
            func.coalesce(Contact.email, '') + ' ' +
            func.coalesce(Contact.phone, '')
        )
        
        search_query = func.plainto_tsquery('english', query)
        
        stmt = select(Contact).where(
            and_(
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False),
                search_vector.op('@@')(search_query)
            )
        ).order_by(
            func.ts_rank(search_vector, search_query).desc()
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_contact_stats(self, tenant_id: uuid.UUID) -> dict:
        """Get contact statistics for tenant"""
        # Total contacts
        total_stmt = select(func.count(Contact.id)).where(
            and_(
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False)
            )
        )
        total_result = await self.db.execute(total_stmt)
        total_contacts = total_result.scalar()
        
        # Contacts with email
        email_stmt = select(func.count(Contact.id)).where(
            and_(
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False),
                Contact.email.is_not(None)
            )
        )
        email_result = await self.db.execute(email_stmt)
        contacts_with_email = email_result.scalar()
        
        # Contacts with phone
        phone_stmt = select(func.count(Contact.id)).where(
            and_(
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False),
                Contact.phone.is_not(None)
            )
        )
        phone_result = await self.db.execute(phone_stmt)
        contacts_with_phone = phone_result.scalar()
        
        return {
            "total_contacts": total_contacts,
            "contacts_with_email": contacts_with_email,
            "contacts_with_phone": contacts_with_phone,
            "email_percentage": round((contacts_with_email / total_contacts * 100) if total_contacts > 0 else 0, 1),
            "phone_percentage": round((contacts_with_phone / total_contacts * 100) if total_contacts > 0 else 0, 1)
        }  
  
    async def advanced_search_contacts(
        self, 
        query: str, 
        tenant_id: uuid.UUID, 
        filters: Optional[ContactFilters] = None,
        limit: int = 50
    ) -> Tuple[List[Contact], int]:
        """Advanced search with ranking and filtering"""
        if not query.strip():
            return [], 0
        
        # Create search vector for full-text search
        search_vector = func.to_tsvector('english', 
            func.coalesce(Contact.firstname, '') + ' ' +
            func.coalesce(Contact.lastname, '') + ' ' +
            func.coalesce(Contact.email, '') + ' ' +
            func.coalesce(Contact.phone, '')
        )
        
        search_query = func.plainto_tsquery('english', query)
        
        # Base query with full-text search
        stmt = select(Contact).where(
            and_(
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False),
                search_vector.op('@@')(search_query)
            )
        )
        
        # Apply additional filters if provided
        if filters:
            if filters.email:
                stmt = stmt.where(Contact.email.ilike(f"%{filters.email}%"))
            if filters.phone:
                stmt = stmt.where(Contact.phone.ilike(f"%{filters.phone}%"))
        
        # Get total count for pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # Order by relevance (ts_rank) and then by created_at
        stmt = stmt.order_by(
            func.ts_rank(search_vector, search_query).desc(),
            Contact.created_at.desc()
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        contacts = result.scalars().all()
        
        return contacts, total
    
    async def get_contact_suggestions(self, partial_query: str, tenant_id: uuid.UUID, limit: int = 10) -> List[str]:
        """Get contact name suggestions for autocomplete"""
        if len(partial_query) < 2:
            return []
        
        # Search for contacts matching the partial query
        search_term = f"{partial_query}%"
        
        stmt = select(
            (Contact.firstname + ' ' + Contact.lastname).label('full_name')
        ).where(
            and_(
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False),
                or_(
                    Contact.firstname.ilike(search_term),
                    Contact.lastname.ilike(search_term),
                    (Contact.firstname + ' ' + Contact.lastname).ilike(search_term)
                )
            )
        ).distinct().limit(limit)
        
        result = await self.db.execute(stmt)
        suggestions = [row.full_name for row in result]
        
        return suggestions
    
    async def search_contacts_by_field(
        self, 
        field: str, 
        value: str, 
        tenant_id: uuid.UUID,
        exact_match: bool = False
    ) -> List[Contact]:
        """Search contacts by specific field"""
        if field not in ['firstname', 'lastname', 'email', 'phone']:
            raise ValueError(f"Invalid search field: {field}")
        
        column = getattr(Contact, field)
        
        if exact_match:
            condition = column == value
        else:
            condition = column.ilike(f"%{value}%")
        
        stmt = select(Contact).where(
            and_(
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False),
                condition
            )
        ).order_by(Contact.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()   
 
    async def _create_contact_activity(self, contact: Contact, action: str, user_id: Optional[int] = None):
        """Create an activity record for contact modifications"""
        from app.models.activity import Activity, ActivityType
        
        # Skip if no user context (e.g., system operations)
        if not user_id:
            return
        
        activity_payload = {
            "action": action,
            "contact_id": contact.id,
            "contact_name": contact.full_name,
            "contact_email": contact.email,
            "contact_phone": contact.phone,
            "title": f"Contact {action}",
            "description": f"Contact {contact.full_name} was {action}"
        }
        
        activity = Activity(
            type=ActivityType.NOTE,
            payload=activity_payload,
            contact_id=contact.id,
            user_id=user_id,
            tenant_id=contact.tenant_id,
            company_id=contact.company_id
        )
        
        self.db.add(activity)
        await self.db.commit()