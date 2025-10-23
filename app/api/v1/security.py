from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.security_service import SecurityService
from app.services.gdpr_service import GDPRService
from app.models.user import User, UserRole

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/audit/trail")
async def get_audit_trail(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit trail (admin/manager only)"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    security_service = SecurityService(db)
    
    audit_trail = await security_service.get_audit_trail(
        current_user.tenant_id,
        user_id=user_id,
        table_name=table_name,
        hours=hours,
        limit=limit
    )
    
    return {
        "audit_trail": audit_trail,
        "total_records": len(audit_trail),
        "filters": {
            "user_id": user_id,
            "table_name": table_name,
            "hours": hours
        }
    }


@router.get("/violations")
async def get_security_violations(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get security violations (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    security_service = SecurityService(db)
    
    violations = await security_service.get_security_violations(
        current_user.tenant_id,
        hours=hours,
        limit=limit
    )
    
    return {
        "violations": violations,
        "total_violations": len(violations),
        "period_hours": hours
    }


@router.get("/tenant/validation")
async def validate_tenant_isolation(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate tenant isolation integrity (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    security_service = SecurityService(db)
    
    validation_result = await security_service.validate_tenant_isolation(
        current_user.tenant_id
    )
    
    return validation_result


@router.get("/tenant/stats")
async def get_tenant_access_stats(
    days: int = Query(7, ge=1, le=30, description="Days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tenant access statistics (admin/manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    security_service = SecurityService(db)
    
    stats = await security_service.get_tenant_access_stats(
        current_user.tenant_id,
        days=days
    )
    
    return stats


@router.post("/gdpr/export/user/{user_id}")
async def export_user_data(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export user data for GDPR compliance (admin only or own data)"""
    # Users can export their own data, admins can export any user's data
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only export own data or admin access required"
        )
    
    gdpr_service = GDPRService(db)
    
    try:
        export_data = await gdpr_service.export_user_data(user_id, current_user.tenant_id)
        return export_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/gdpr/export/contact/{contact_id}")
async def export_contact_data(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export contact data for GDPR compliance (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    gdpr_service = GDPRService(db)
    
    try:
        export_data = await gdpr_service.export_contact_data(contact_id, current_user.tenant_id)
        return export_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/gdpr/anonymize/user/{user_id}")
async def anonymize_user_data(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Anonymize user data for GDPR right to be forgotten (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Prevent self-anonymization
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot anonymize own account"
        )
    
    gdpr_service = GDPRService(db)
    
    try:
        anonymization_report = await gdpr_service.anonymize_user_data(user_id, current_user.tenant_id)
        return anonymization_report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/gdpr/contact/{contact_id}")
async def delete_contact_data(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete all contact data for GDPR compliance (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    gdpr_service = GDPRService(db)
    
    try:
        deletion_report = await gdpr_service.delete_contact_data(contact_id, current_user.tenant_id)
        return deletion_report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/gdpr/retention/check")
async def check_data_retention(
    retention_days: int = Query(2555, ge=365, le=3650, description="Retention period in days"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check data retention compliance (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    gdpr_service = GDPRService(db)
    
    try:
        cleanup_report = await gdpr_service.schedule_data_retention_cleanup(
            current_user.tenant_id,
            retention_days=retention_days
        )
        return cleanup_report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/gdpr/compliance/report")
async def get_gdpr_compliance_report(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get GDPR compliance report (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    gdpr_service = GDPRService(db)
    
    try:
        compliance_report = await gdpr_service.get_gdpr_compliance_report(current_user.tenant_id)
        return compliance_report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/log/event")
async def log_security_event(
    event_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Log custom security event (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    security_service = SecurityService(db)
    
    await security_service.log_security_event(
        event_type=event_data.get("event_type", "custom_event"),
        details=event_data.get("details", {}),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        severity=event_data.get("severity", "info")
    )
    
    return {"status": "logged", "event_type": event_data.get("event_type")}


@router.get("/permissions/check")
async def check_user_permissions(
    resource_type: str = Query(..., description="Resource type to check"),
    operation: str = Query(..., description="Operation to check"),
    target_user_id: Optional[int] = Query(None, description="Check permissions for specific user"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check user permissions for resource operations"""
    security_service = SecurityService(db)
    
    # If checking for another user, require admin access
    check_user_id = target_user_id if target_user_id else current_user.id
    
    if target_user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to check other users' permissions"
        )
    
    has_permission = await security_service.check_tenant_access_permissions(
        check_user_id,
        current_user.tenant_id,
        resource_type,
        operation
    )
    
    return {
        "user_id": check_user_id,
        "resource_type": resource_type,
        "operation": operation,
        "has_permission": has_permission,
        "checked_at": datetime.utcnow().isoformat()
    }