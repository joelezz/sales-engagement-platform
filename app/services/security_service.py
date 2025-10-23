from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_, func, desc
from datetime import datetime, timedelta
import uuid
import logging

from app.models.user import User, UserRole
from app.core.exceptions import SalesEngagementException

logger = logging.getLogger(__name__)


class SecurityService:
    """Service for security monitoring and tenant access control"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        tenant_id: uuid.UUID,
        user_id: Optional[int] = None,
        severity: str = "info"
    ):
        """Log security events for monitoring"""
        try:
            # Insert into audit log with security event type
            stmt = text("""
                INSERT INTO audit_log (
                    tenant_id, user_id, table_name, operation, 
                    new_values, ip_address, user_agent, created_at
                ) VALUES (
                    :tenant_id, :user_id, 'security_events', :event_type,
                    :details, inet_client_addr(), 
                    current_setting('app.user_agent', true), NOW()
                )
            """)
            
            await self.db.execute(stmt, {
                "tenant_id": str(tenant_id),
                "user_id": user_id,
                "event_type": event_type,
                "details": details
            })
            
            await self.db.commit()
            
            # Log to application logs based on severity
            log_message = f"Security event: {event_type} - {details}"
            if severity == "critical":
                logger.critical(log_message)
            elif severity == "warning":
                logger.warning(log_message)
            else:
                logger.info(log_message)
                
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def check_tenant_access_permissions(
        self,
        user_id: int,
        tenant_id: uuid.UUID,
        resource_type: str,
        operation: str
    ) -> bool:
        """Check if user has permission to access tenant resource"""
        try:
            # Get user details
            stmt = select(User).where(
                and_(
                    User.id == user_id,
                    User.tenant_id == tenant_id,
                    User.is_active == True
                )
            )
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                await self.log_security_event(
                    "unauthorized_access_attempt",
                    {
                        "user_id": user_id,
                        "tenant_id": str(tenant_id),
                        "resource_type": resource_type,
                        "operation": operation,
                        "reason": "user_not_found_or_inactive"
                    },
                    tenant_id,
                    user_id,
                    "warning"
                )
                return False
            
            # Check role-based permissions
            if not self._check_role_permissions(user.role, resource_type, operation):
                await self.log_security_event(
                    "insufficient_permissions",
                    {
                        "user_id": user_id,
                        "user_role": user.role.value,
                        "resource_type": resource_type,
                        "operation": operation
                    },
                    tenant_id,
                    user_id,
                    "warning"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking tenant access permissions: {e}")
            return False
    
    def _check_role_permissions(self, role: UserRole, resource_type: str, operation: str) -> bool:
        """Check role-based permissions for resource operations"""
        # Define permission matrix
        permissions = {
            UserRole.ADMIN: {
                "users": ["create", "read", "update", "delete"],
                "contacts": ["create", "read", "update", "delete"],
                "activities": ["create", "read", "update", "delete"],
                "calls": ["create", "read", "update", "delete"],
                "settings": ["create", "read", "update", "delete"]
            },
            UserRole.MANAGER: {
                "users": ["read"],
                "contacts": ["create", "read", "update", "delete"],
                "activities": ["create", "read", "update"],
                "calls": ["create", "read", "update"],
                "settings": ["read"]
            },
            UserRole.REP: {
                "users": ["read"],  # Only own profile
                "contacts": ["create", "read", "update"],
                "activities": ["create", "read", "update"],  # Only own activities
                "calls": ["create", "read", "update"],  # Only own calls
                "settings": ["read"]
            }
        }
        
        role_permissions = permissions.get(role, {})
        resource_permissions = role_permissions.get(resource_type, [])
        
        return operation in resource_permissions
    
    async def get_security_violations(
        self,
        tenant_id: uuid.UUID,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent security violations for tenant"""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            stmt = text("""
                SELECT 
                    id, user_id, operation, new_values, 
                    ip_address, user_agent, created_at
                FROM audit_log 
                WHERE tenant_id = :tenant_id 
                    AND created_at >= :since_time
                    AND operation IN ('SECURITY_VIOLATION', 'unauthorized_access_attempt', 'insufficient_permissions')
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(stmt, {
                "tenant_id": str(tenant_id),
                "since_time": since_time,
                "limit": limit
            })
            
            violations = []
            for row in result:
                violations.append({
                    "id": row.id,
                    "user_id": row.user_id,
                    "violation_type": row.operation,
                    "details": row.new_values,
                    "ip_address": str(row.ip_address) if row.ip_address else None,
                    "user_agent": row.user_agent,
                    "timestamp": row.created_at.isoformat()
                })
            
            return violations
            
        except Exception as e:
            logger.error(f"Error getting security violations: {e}")
            return []
    
    async def get_audit_trail(
        self,
        tenant_id: uuid.UUID,
        user_id: Optional[int] = None,
        table_name: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail for tenant"""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Build dynamic query
            where_conditions = ["tenant_id = :tenant_id", "created_at >= :since_time"]
            params = {
                "tenant_id": str(tenant_id),
                "since_time": since_time,
                "limit": limit
            }
            
            if user_id:
                where_conditions.append("user_id = :user_id")
                params["user_id"] = user_id
            
            if table_name:
                where_conditions.append("table_name = :table_name")
                params["table_name"] = table_name
            
            where_clause = " AND ".join(where_conditions)
            
            stmt = text(f"""
                SELECT 
                    id, user_id, table_name, operation, record_id,
                    old_values, new_values, ip_address, user_agent, created_at
                FROM audit_log 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(stmt, params)
            
            audit_entries = []
            for row in result:
                audit_entries.append({
                    "id": row.id,
                    "user_id": row.user_id,
                    "table_name": row.table_name,
                    "operation": row.operation,
                    "record_id": row.record_id,
                    "old_values": row.old_values,
                    "new_values": row.new_values,
                    "ip_address": str(row.ip_address) if row.ip_address else None,
                    "user_agent": row.user_agent,
                    "timestamp": row.created_at.isoformat()
                })
            
            return audit_entries
            
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            return []
    
    async def validate_tenant_isolation(self, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Validate tenant isolation integrity"""
        try:
            validation_results = {
                "tenant_id": str(tenant_id),
                "validation_time": datetime.utcnow().isoformat(),
                "issues": [],
                "status": "passed"
            }
            
            # Check for cross-tenant data leaks
            tables_to_check = ["users", "contacts", "activities", "calls"]
            
            for table in tables_to_check:
                # Check if any records exist without proper tenant_id
                stmt = text(f"""
                    SELECT COUNT(*) as count
                    FROM {table}
                    WHERE tenant_id IS NULL OR tenant_id != :tenant_id
                """)
                
                result = await self.db.execute(stmt, {"tenant_id": str(tenant_id)})
                count = result.scalar()
                
                if count > 0:
                    validation_results["issues"].append({
                        "table": table,
                        "issue": "records_with_invalid_tenant_id",
                        "count": count
                    })
                    validation_results["status"] = "failed"
            
            # Check RLS policy status
            stmt = text("""
                SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
                FROM pg_policies 
                WHERE schemaname = 'public' 
                    AND tablename IN ('users', 'contacts', 'activities', 'calls')
            """)
            
            result = await self.db.execute(stmt)
            policies = result.fetchall()
            
            expected_policies = {
                "users": ["tenant_isolation_users"],
                "contacts": ["tenant_isolation_contacts"],
                "activities": ["tenant_isolation_activities"],
                "calls": ["tenant_isolation_calls"]
            }
            
            for table, expected in expected_policies.items():
                table_policies = [p.policyname for p in policies if p.tablename == table]
                missing_policies = set(expected) - set(table_policies)
                
                if missing_policies:
                    validation_results["issues"].append({
                        "table": table,
                        "issue": "missing_rls_policies",
                        "missing_policies": list(missing_policies)
                    })
                    validation_results["status"] = "failed"
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating tenant isolation: {e}")
            return {
                "tenant_id": str(tenant_id),
                "validation_time": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def get_tenant_access_stats(self, tenant_id: uuid.UUID, days: int = 7) -> Dict[str, Any]:
        """Get tenant access statistics"""
        try:
            since_time = datetime.utcnow() - timedelta(days=days)
            
            # Get access statistics
            stmt = text("""
                SELECT 
                    COUNT(*) as total_operations,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT DATE(created_at)) as active_days,
                    COUNT(CASE WHEN operation IN ('SECURITY_VIOLATION', 'unauthorized_access_attempt') THEN 1 END) as security_violations
                FROM audit_log
                WHERE tenant_id = :tenant_id AND created_at >= :since_time
            """)
            
            result = await self.db.execute(stmt, {
                "tenant_id": str(tenant_id),
                "since_time": since_time
            })
            
            stats = result.fetchone()
            
            # Get operations by type
            stmt = text("""
                SELECT operation, COUNT(*) as count
                FROM audit_log
                WHERE tenant_id = :tenant_id AND created_at >= :since_time
                GROUP BY operation
                ORDER BY count DESC
            """)
            
            result = await self.db.execute(stmt, {
                "tenant_id": str(tenant_id),
                "since_time": since_time
            })
            
            operations_by_type = {row.operation: row.count for row in result}
            
            return {
                "tenant_id": str(tenant_id),
                "period_days": days,
                "total_operations": stats.total_operations,
                "unique_users": stats.unique_users,
                "active_days": stats.active_days,
                "security_violations": stats.security_violations,
                "operations_by_type": operations_by_type,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting tenant access stats: {e}")
            return {
                "tenant_id": str(tenant_id),
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }