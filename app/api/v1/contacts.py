from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.contact_service import ContactService
from app.schemas.contact import (
    ContactCreate, 
    ContactUpdate, 
    ContactResponse, 
    ContactListResponse,
    ContactFilters
)
from app.schemas.activity import ActivityTimelineResponse
from app.services.activity_service import ActivityService
from app.models.user import User

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=ContactListResponse)
async def get_contacts(
    search: Optional[str] = Query(None, description="Search contacts by name, email, or phone"),
    email: Optional[str] = Query(None, description="Filter by email"),
    phone: Optional[str] = Query(None, description="Filter by phone"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    include_deleted: bool = Query(False, description="Include soft-deleted contacts"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of contacts with filtering"""
    contact_service = ContactService(db)
    
    filters = ContactFilters(
        search=search,
        email=email,
        phone=phone,
        page=page,
        page_size=page_size,
        include_deleted=include_deleted
    )
    
    return await contact_service.get_contacts(filters, current_user.tenant_id)


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new contact"""
    contact_service = ContactService(db)
    
    contact = await contact_service.create_contact(
        contact_data, 
        current_user.tenant_id,
        current_user.company_id
    )
    
    return contact


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single contact by ID"""
    contact_service = ContactService(db)
    
    contact = await contact_service.get_contact(contact_id, current_user.tenant_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    updates: ContactUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a contact with partial updates"""
    contact_service = ContactService(db)
    
    contact = await contact_service.update_contact(
        contact_id, 
        updates, 
        current_user.tenant_id,
        current_user.id
    )
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a contact"""
    contact_service = ContactService(db)
    
    success = await contact_service.delete_contact(contact_id, current_user.tenant_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )


@router.get("/search/advanced", response_model=List[ContactResponse])
async def advanced_search_contacts(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Advanced search contacts with full-text search"""
    contact_service = ContactService(db)
    
    contacts, total = await contact_service.advanced_search_contacts(
        q, 
        current_user.tenant_id,
        limit=limit
    )
    
    return contacts


@router.get("/search/suggestions", response_model=List[str])
async def get_contact_suggestions(
    q: str = Query(..., min_length=2, description="Partial query for autocomplete"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contact name suggestions for autocomplete"""
    contact_service = ContactService(db)
    
    suggestions = await contact_service.get_contact_suggestions(
        q, 
        current_user.tenant_id,
        limit=limit
    )
    
    return suggestions


@router.get("/stats/overview")
async def get_contact_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contact statistics overview"""
    contact_service = ContactService(db)
    
    stats = await contact_service.get_contact_stats(current_user.tenant_id)
    
    return stats


@router.get("/search/by-field", response_model=List[ContactResponse])
async def search_contacts_by_field(
    field: str = Query(..., description="Field to search (firstname, lastname, email, phone)"),
    value: str = Query(..., min_length=1, description="Value to search for"),
    exact_match: bool = Query(False, description="Whether to use exact match"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search contacts by specific field"""
    contact_service = ContactService(db)
    
    try:
        contacts = await contact_service.search_contacts_by_field(
            field, 
            value, 
            current_user.tenant_id,
            exact_match=exact_match
        )
        return contacts
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{contact_id}/activities", response_model=ActivityTimelineResponse)
async def get_contact_activities(
    contact_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activity timeline for a specific contact"""
    activity_service = ActivityService(db)
    
    timeline = await activity_service.get_contact_timeline(
        contact_id,
        current_user.tenant_id,
        page=page,
        page_size=page_size
    )
    
    return timeline