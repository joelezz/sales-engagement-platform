from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, text, and_, func
from datetime import datetime, timedelta
import uuid
import json
import logging

from app.models.user import User
from app.models.contact import Contact
from app.models.activity import Activity
from app.models.call import Call
from app.models.company import Company
from app.core.exceptions import SalesEngagementException

logger = logging.getLogger(__name__)


class GDPRService:
    """Service for GDPR compliance operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def export_user_data(self, user_id: int, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Export all user data for GDPR data portability"""
        try:
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "tenant_id": str(tenant_id),
                "data": {}
            }
            
            # Export user profile
            user_stmt = select(User).where(
                and_(User.id == user_id, User.tenant_id == tenant_id)
            )
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise SalesEngagementException("User not found", "user_not_found")
            
            export_data["data"]["user_profile"] = {
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            
            # Export user's activities
            activities_stmt = select(Activity).where(
                and_(Activity.user_id == user_id, Activity.tenant_id == tenant_id)
            ).order_by(Activity.created_at.desc())
            
            activities_result = await self.db.execute(activities_stmt)
            activities = activities_result.scalars().all()
            
            export_data["data"]["activities"] = []
            for activity in activities:
                export_data["data"]["activities"].append({
                    "id": activity.id,
                    "type": activity.type.value,
                    "contact_id": activity.contact_id,
                    "payload": activity.payload,
                    "created_at": activity.created_at.isoformat()
                })
            
            # Export user's calls
            calls_stmt = select(Call).where(
                and_(Call.user_id == user_id, Call.tenant_id == tenant_id)
            ).order_by(Call.created_at.desc())
            
            calls_result = await self.db.execute(calls_stmt)
            calls = calls_result.scalars().all()
            
            export_data["data"]["calls"] = []
            for call in calls:
                export_data["data"]["calls"].append({
                    "id": call.id,
                    "call_sid": call.call_sid,
                    "direction": call.direction.value,
                    "status": call.status.value,
                    "from_number": call.from_number,
                    "to_number": call.to_number,
                    "duration": call.duration,
                    "start_time": call.start_time.isoformat() if call.start_time else None,
                    "end_time": call.end_time.isoformat() if call.end_time else None,
                    "has_recording": call.has_recording,
                    "created_at": call.created_at.isoformat()
                })
            
            # Export audit logs for this user
            audit_stmt = text("""
                SELECT table_name, operation, record_id, old_values, new_values, created_at
                FROM audit_log
                WHERE user_id = :user_id AND tenant_id = :tenant_id
                ORDER BY created_at DESC
            """)
            
            audit_result = await self.db.execute(audit_stmt, {
                "user_id": user_id,
                "tenant_id": str(tenant_id)
            })
            
            export_data["data"]["audit_logs"] = []
            for row in audit_result:
                export_data["data"]["audit_logs"].append({
                    "table_name": row.table_name,
                    "operation": row.operation,
                    "record_id": row.record_id,
                    "old_values": row.old_values,
                    "new_values": row.new_values,
                    "timestamp": row.created_at.isoformat()
                })
            
            # Log the export request
            await self._log_gdpr_action("data_export", user_id, tenant_id, {
                "exported_records": {
                    "activities": len(export_data["data"]["activities"]),
                    "calls": len(export_data["data"]["calls"]),
                    "audit_logs": len(export_data["data"]["audit_logs"])
                }
            })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            raise SalesEngagementException(f"Data export failed: {str(e)}", "export_failed")
    
    async def export_contact_data(self, contact_id: int, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Export all data related to a specific contact"""
        try:
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "contact_id": contact_id,
                "tenant_id": str(tenant_id),
                "data": {}
            }
            
            # Export contact profile
            contact_stmt = select(Contact).where(
                and_(
                    Contact.id == contact_id, 
                    Contact.tenant_id == tenant_id,
                    Contact.deleted_at.is_(None)
                )
            )
            contact_result = await self.db.execute(contact_stmt)
            contact = contact_result.scalar_one_or_none()
            
            if not contact:
                raise SalesEngagementException("Contact not found", "contact_not_found")
            
            export_data["data"]["contact_profile"] = {
                "id": contact.id,
                "firstname": contact.firstname,
                "lastname": contact.lastname,
                "email": contact.email,
                "phone": contact.phone,
                "contact_metadata": contact.contact_metadata,
                "created_at": contact.created_at.isoformat(),
                "updated_at": contact.updated_at.isoformat() if contact.updated_at else None
            }
            
            # Export activities related to this contact
            activities_stmt = select(Activity).where(
                and_(Activity.contact_id == contact_id, Activity.tenant_id == tenant_id)
            ).order_by(Activity.created_at.desc())
            
            activities_result = await self.db.execute(activities_stmt)
            activities = activities_result.scalars().all()
            
            export_data["data"]["activities"] = []
            for activity in activities:
                export_data["data"]["activities"].append({
                    "id": activity.id,
                    "type": activity.type.value,
                    "user_id": activity.user_id,
                    "payload": activity.payload,
                    "created_at": activity.created_at.isoformat()
                })
            
            # Export calls related to this contact
            calls_stmt = select(Call).where(
                and_(Call.contact_id == contact_id, Call.tenant_id == tenant_id)
            ).order_by(Call.created_at.desc())
            
            calls_result = await self.db.execute(calls_stmt)
            calls = calls_result.scalars().all()
            
            export_data["data"]["calls"] = []
            for call in calls:
                export_data["data"]["calls"].append({
                    "id": call.id,
                    "call_sid": call.call_sid,
                    "direction": call.direction.value,
                    "status": call.status.value,
                    "from_number": call.from_number,
                    "to_number": call.to_number,
                    "duration": call.duration,
                    "user_id": call.user_id,
                    "created_at": call.created_at.isoformat()
                })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting contact data: {e}")
            raise SalesEngagementException(f"Contact data export failed: {str(e)}", "export_failed")
    
    async def anonymize_user_data(self, user_id: int, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Anonymize user data for GDPR right to be forgotten"""
        try:
            anonymization_report = {
                "anonymization_timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "tenant_id": str(tenant_id),
                "anonymized_records": {}
            }
            
            # First, verify user exists and belongs to tenant
            user_stmt = select(User).where(
                and_(User.id == user_id, User.tenant_id == tenant_id)
            )
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise SalesEngagementException("User not found", "user_not_found")
            
            # Anonymize user profile
            anonymized_email = f"anonymized_user_{user_id}@deleted.local"
            user_update_stmt = update(User).where(
                and_(User.id == user_id, User.tenant_id == tenant_id)
            ).values(
                email=anonymized_email,
                is_active=False,
                updated_at=datetime.utcnow()
            )
            
            await self.db.execute(user_update_stmt)
            anonymization_report["anonymized_records"]["user_profile"] = 1
            
            # Anonymize activities - remove PII from payload
            activities_stmt = select(Activity).where(
                and_(Activity.user_id == user_id, Activity.tenant_id == tenant_id)
            )
            activities_result = await self.db.execute(activities_stmt)
            activities = activities_result.scalars().all()
            
            anonymized_activities = 0
            for activity in activities:
                # Remove PII from activity payload
                anonymized_payload = self._anonymize_activity_payload(activity.payload)
                
                activity_update_stmt = update(Activity).where(
                    Activity.id == activity.id
                ).values(payload=anonymized_payload)
                
                await self.db.execute(activity_update_stmt)
                anonymized_activities += 1
            
            anonymization_report["anonymized_records"]["activities"] = anonymized_activities
            
            # Anonymize calls - remove phone numbers and PII
            calls_stmt = select(Call).where(
                and_(Call.user_id == user_id, Call.tenant_id == tenant_id)
            )
            calls_result = await self.db.execute(calls_stmt)
            calls = calls_result.scalars().all()
            
            anonymized_calls = 0
            for call in calls:
                call_update_stmt = update(Call).where(
                    Call.id == call.id
                ).values(
                    from_number="***ANONYMIZED***",
                    to_number="***ANONYMIZED***",
                    recording_url=None  # Remove recording URLs
                )
                
                await self.db.execute(call_update_stmt)
                anonymized_calls += 1
            
            anonymization_report["anonymized_records"]["calls"] = anonymized_calls
            
            # Anonymize audit logs - remove IP addresses and user agents
            audit_update_stmt = text("""
                UPDATE audit_log 
                SET ip_address = NULL, user_agent = 'ANONYMIZED'
                WHERE user_id = :user_id AND tenant_id = :tenant_id
            """)
            
            audit_result = await self.db.execute(audit_update_stmt, {
                "user_id": user_id,
                "tenant_id": str(tenant_id)
            })
            
            anonymization_report["anonymized_records"]["audit_logs"] = audit_result.rowcount
            
            await self.db.commit()
            
            # Log the anonymization
            await self._log_gdpr_action("data_anonymization", user_id, tenant_id, anonymization_report)
            
            return anonymization_report
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error anonymizing user data: {e}")
            raise SalesEngagementException(f"Data anonymization failed: {str(e)}", "anonymization_failed")
    
    async def delete_contact_data(self, contact_id: int, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Delete all data related to a contact (GDPR right to be forgotten)"""
        try:
            deletion_report = {
                "deletion_timestamp": datetime.utcnow().isoformat(),
                "contact_id": contact_id,
                "tenant_id": str(tenant_id),
                "deleted_records": {}
            }
            
            # Verify contact exists
            contact_stmt = select(Contact).where(
                and_(Contact.id == contact_id, Contact.tenant_id == tenant_id)
            )
            contact_result = await self.db.execute(contact_stmt)
            contact = contact_result.scalar_one_or_none()
            
            if not contact:
                raise SalesEngagementException("Contact not found", "contact_not_found")
            
            # Delete activities related to this contact
            activities_delete_stmt = delete(Activity).where(
                and_(Activity.contact_id == contact_id, Activity.tenant_id == tenant_id)
            )
            activities_result = await self.db.execute(activities_delete_stmt)
            deletion_report["deleted_records"]["activities"] = activities_result.rowcount
            
            # Delete calls related to this contact
            calls_delete_stmt = delete(Call).where(
                and_(Call.contact_id == contact_id, Call.tenant_id == tenant_id)
            )
            calls_result = await self.db.execute(calls_delete_stmt)
            deletion_report["deleted_records"]["calls"] = calls_result.rowcount
            
            # Delete the contact
            contact_delete_stmt = delete(Contact).where(
                and_(Contact.id == contact_id, Contact.tenant_id == tenant_id)
            )
            contact_result = await self.db.execute(contact_delete_stmt)
            deletion_report["deleted_records"]["contact"] = contact_result.rowcount
            
            await self.db.commit()
            
            # Log the deletion
            await self._log_gdpr_action("data_deletion", None, tenant_id, {
                "deleted_contact_id": contact_id,
                **deletion_report["deleted_records"]
            })
            
            return deletion_report
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting contact data: {e}")
            raise SalesEngagementException(f"Data deletion failed: {str(e)}", "deletion_failed")
    
    async def schedule_data_retention_cleanup(self, tenant_id: uuid.UUID, retention_days: int = 2555) -> Dict[str, Any]:
        """Schedule cleanup of old data based on retention policy (7 years default)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            cleanup_report = {
                "cleanup_timestamp": datetime.utcnow().isoformat(),
                "tenant_id": str(tenant_id),
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "cleanup_summary": {}
            }
            
            # Find old activities
            old_activities_stmt = select(func.count(Activity.id)).where(
                and_(
                    Activity.tenant_id == tenant_id,
                    Activity.created_at < cutoff_date
                )
            )
            old_activities_result = await self.db.execute(old_activities_stmt)
            old_activities_count = old_activities_result.scalar()
            
            # Find old calls
            old_calls_stmt = select(func.count(Call.id)).where(
                and_(
                    Call.tenant_id == tenant_id,
                    Call.created_at < cutoff_date
                )
            )
            old_calls_result = await self.db.execute(old_calls_stmt)
            old_calls_count = old_calls_result.scalar()
            
            # Find old audit logs
            old_audit_stmt = text("""
                SELECT COUNT(*) FROM audit_log
                WHERE tenant_id = :tenant_id AND created_at < :cutoff_date
            """)
            old_audit_result = await self.db.execute(old_audit_stmt, {
                "tenant_id": str(tenant_id),
                "cutoff_date": cutoff_date
            })
            old_audit_count = old_audit_result.scalar()
            
            cleanup_report["cleanup_summary"] = {
                "activities_to_cleanup": old_activities_count,
                "calls_to_cleanup": old_calls_count,
                "audit_logs_to_cleanup": old_audit_count,
                "total_records": old_activities_count + old_calls_count + old_audit_count
            }
            
            # Log the retention policy check
            await self._log_gdpr_action("retention_policy_check", None, tenant_id, cleanup_report)
            
            return cleanup_report
            
        except Exception as e:
            logger.error(f"Error scheduling data retention cleanup: {e}")
            raise SalesEngagementException(f"Retention cleanup scheduling failed: {str(e)}", "cleanup_failed")
    
    async def get_gdpr_compliance_report(self, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Generate GDPR compliance report for tenant"""
        try:
            report = {
                "report_timestamp": datetime.utcnow().isoformat(),
                "tenant_id": str(tenant_id),
                "compliance_status": {}
            }
            
            # Check data retention compliance
            retention_days = 2555  # 7 years
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count records older than retention period
            old_records_stmt = text("""
                SELECT 
                    'activities' as table_name, COUNT(*) as count
                FROM activities 
                WHERE tenant_id = :tenant_id AND created_at < :cutoff_date
                UNION ALL
                SELECT 
                    'calls' as table_name, COUNT(*) as count
                FROM calls 
                WHERE tenant_id = :tenant_id AND created_at < :cutoff_date
                UNION ALL
                SELECT 
                    'audit_log' as table_name, COUNT(*) as count
                FROM audit_log 
                WHERE tenant_id = :tenant_id AND created_at < :cutoff_date
            """)
            
            old_records_result = await self.db.execute(old_records_stmt, {
                "tenant_id": str(tenant_id),
                "cutoff_date": cutoff_date
            })
            
            old_records = {row.table_name: row.count for row in old_records_result}
            
            # Check for anonymized users
            anonymized_users_stmt = select(func.count(User.id)).where(
                and_(
                    User.tenant_id == tenant_id,
                    User.email.like('%@deleted.local')
                )
            )
            anonymized_users_result = await self.db.execute(anonymized_users_stmt)
            anonymized_users_count = anonymized_users_result.scalar()
            
            # Get GDPR action history
            gdpr_actions_stmt = text("""
                SELECT operation, COUNT(*) as count
                FROM audit_log
                WHERE tenant_id = :tenant_id 
                    AND table_name = 'gdpr_actions'
                    AND created_at >= :since_date
                GROUP BY operation
            """)
            
            since_date = datetime.utcnow() - timedelta(days=365)  # Last year
            gdpr_actions_result = await self.db.execute(gdpr_actions_stmt, {
                "tenant_id": str(tenant_id),
                "since_date": since_date
            })
            
            gdpr_actions = {row.operation: row.count for row in gdpr_actions_result}
            
            report["compliance_status"] = {
                "data_retention": {
                    "retention_period_days": retention_days,
                    "records_exceeding_retention": old_records,
                    "compliance": sum(old_records.values()) == 0
                },
                "right_to_be_forgotten": {
                    "anonymized_users": anonymized_users_count,
                    "recent_anonymizations": gdpr_actions.get("data_anonymization", 0)
                },
                "data_portability": {
                    "recent_exports": gdpr_actions.get("data_export", 0)
                },
                "audit_trail": {
                    "gdpr_actions_last_year": sum(gdpr_actions.values())
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating GDPR compliance report: {e}")
            raise SalesEngagementException(f"Compliance report generation failed: {str(e)}", "report_failed")
    
    def _anonymize_activity_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize PII in activity payload"""
        anonymized = payload.copy()
        
        # Fields to anonymize
        pii_fields = [
            "email", "phone", "phone_number", "from_number", "to_number",
            "contact_email", "contact_phone", "user_email", "ip_address"
        ]
        
        for field in pii_fields:
            if field in anonymized:
                anonymized[field] = "***ANONYMIZED***"
        
        # Anonymize nested objects
        for key, value in anonymized.items():
            if isinstance(value, dict):
                anonymized[key] = self._anonymize_activity_payload(value)
        
        return anonymized
    
    async def _log_gdpr_action(
        self, 
        action_type: str, 
        user_id: Optional[int], 
        tenant_id: uuid.UUID, 
        details: Dict[str, Any]
    ):
        """Log GDPR-related actions for audit trail"""
        try:
            stmt = text("""
                INSERT INTO audit_log (
                    tenant_id, user_id, table_name, operation, 
                    new_values, created_at
                ) VALUES (
                    :tenant_id, :user_id, 'gdpr_actions', :action_type,
                    :details, NOW()
                )
            """)
            
            await self.db.execute(stmt, {
                "tenant_id": str(tenant_id),
                "user_id": user_id,
                "action_type": action_type,
                "details": details
            })
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log GDPR action: {e}")