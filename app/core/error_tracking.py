"""
Error tracking and notification system for the Sales Engagement Platform.
Provides centralized error handling, alerting, and performance monitoring.
"""

import logging
import traceback
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio
from dataclasses import dataclass, asdict

from app.core.config import settings
from app.core.metrics import metrics

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    PERFORMANCE = "performance"


@dataclass
class ErrorContext:
    """Context information for error tracking."""
    user_id: Optional[int] = None
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    additional_context: Optional[Dict[str, Any]] = None


@dataclass
class ErrorEvent:
    """Structured error event for tracking and alerting."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    stack_trace: str
    context: ErrorContext
    resolved: bool = False
    resolution_notes: Optional[str] = None


class ErrorTracker:
    """Centralized error tracking and alerting system."""
    
    def __init__(self):
        self.error_store: List[ErrorEvent] = []
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,  # Alert immediately
            ErrorSeverity.HIGH: 5,      # Alert after 5 occurrences in 5 minutes
            ErrorSeverity.MEDIUM: 10,   # Alert after 10 occurrences in 15 minutes
            ErrorSeverity.LOW: 50       # Alert after 50 occurrences in 1 hour
        }
    
    async def track_error(
        self,
        exception: Exception,
        severity: ErrorSeverity,
        category: ErrorCategory,
        context: Optional[ErrorContext] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track an error event and trigger alerts if necessary."""
        
        error_id = f"err_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(exception)}"
        
        error_event = ErrorEvent(
            error_id=error_id,
            timestamp=datetime.utcnow(),
            severity=severity,
            category=category,
            message=str(exception),
            exception_type=type(exception).__name__,
            stack_trace=traceback.format_exc(),
            context=context or ErrorContext()
        )
        
        # Store error event
        self.error_store.append(error_event)
        
        # Log error with structured data
        await self._log_error(error_event, additional_info)
        
        # Update metrics
        await self._update_metrics(error_event)
        
        # Check if alerting is needed
        await self._check_alert_thresholds(error_event)
        
        return error_id
    
    async def _log_error(self, error_event: ErrorEvent, additional_info: Optional[Dict[str, Any]]):
        """Log error with structured format."""
        
        log_data = {
            "error_id": error_event.error_id,
            "timestamp": error_event.timestamp.isoformat(),
            "severity": error_event.severity.value,
            "category": error_event.category.value,
            "message": error_event.message,
            "exception_type": error_event.exception_type,
            "context": asdict(error_event.context),
            "additional_info": additional_info or {}
        }
        
        # Log based on severity
        if error_event.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error_event.message}", extra=log_data)
        elif error_event.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {error_event.message}", extra=log_data)
        elif error_event.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {error_event.message}", extra=log_data)
        else:
            logger.info(f"LOW SEVERITY ERROR: {error_event.message}", extra=log_data)
    
    async def _update_metrics(self, error_event: ErrorEvent):
        """Update Prometheus metrics for error tracking."""
        
        # Update error counters
        if error_event.category == ErrorCategory.AUTHENTICATION:
            metrics.auth_failures_total.labels(
                reason="system_error",
                tenant_id=error_event.context.tenant_id or "unknown"
            ).inc()
        
        # Update audit log metrics for security-related errors
        if error_event.category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
            metrics.audit_log_entries_total.labels(
                action="error",
                resource_type="security",
                tenant_id=error_event.context.tenant_id or "unknown"
            ).inc()
    
    async def _check_alert_thresholds(self, error_event: ErrorEvent):
        """Check if error frequency exceeds alert thresholds."""
        
        # Count recent errors of same severity and category
        now = datetime.utcnow()
        time_windows = {
            ErrorSeverity.CRITICAL: 60,      # 1 minute
            ErrorSeverity.HIGH: 300,         # 5 minutes
            ErrorSeverity.MEDIUM: 900,       # 15 minutes
            ErrorSeverity.LOW: 3600          # 1 hour
        }
        
        window_seconds = time_windows.get(error_event.severity, 300)
        threshold = self.alert_thresholds.get(error_event.severity, 10)
        
        recent_errors = [
            err for err in self.error_store
            if (now - err.timestamp).total_seconds() <= window_seconds
            and err.severity == error_event.severity
            and err.category == error_event.category
        ]
        
        if len(recent_errors) >= threshold:
            await self._send_alert(error_event, len(recent_errors))
    
    async def _send_alert(self, error_event: ErrorEvent, error_count: int):
        """Send alert notification for error threshold breach."""
        
        alert_data = {
            "alert_type": "error_threshold_exceeded",
            "severity": error_event.severity.value,
            "category": error_event.category.value,
            "error_count": error_count,
            "latest_error": {
                "id": error_event.error_id,
                "message": error_event.message,
                "timestamp": error_event.timestamp.isoformat()
            },
            "context": asdict(error_event.context)
        }
        
        # Log alert
        logger.critical(f"ERROR ALERT: {error_count} {error_event.severity.value} errors in {error_event.category.value}", extra=alert_data)
        
        # Send to external alerting systems (Slack, PagerDuty, etc.)
        await self._send_external_alert(alert_data)
    
    async def _send_external_alert(self, alert_data: Dict[str, Any]):
        """Send alert to external systems."""
        
        # Webhook notification (can be configured for Slack, Teams, etc.)
        if settings.alert_webhook_url:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        settings.alert_webhook_url,
                        json=alert_data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    )
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")
        
        # Email notification (if configured)
        if settings.alert_email_enabled:
            await self._send_email_alert(alert_data)
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert notification."""
        
        try:
            # Email implementation would go here
            # This is a placeholder for email service integration
            logger.info(f"Email alert would be sent: {alert_data}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        
        now = datetime.utcnow()
        cutoff = now.timestamp() - (hours * 3600)
        
        recent_errors = [
            err for err in self.error_store
            if err.timestamp.timestamp() >= cutoff
        ]
        
        summary = {
            "total_errors": len(recent_errors),
            "by_severity": {},
            "by_category": {},
            "top_errors": [],
            "time_period_hours": hours
        }
        
        # Group by severity
        for severity in ErrorSeverity:
            count = len([err for err in recent_errors if err.severity == severity])
            summary["by_severity"][severity.value] = count
        
        # Group by category
        for category in ErrorCategory:
            count = len([err for err in recent_errors if err.category == category])
            summary["by_category"][category.value] = count
        
        # Top error messages
        error_messages = {}
        for err in recent_errors:
            key = f"{err.exception_type}: {err.message[:100]}"
            error_messages[key] = error_messages.get(key, 0) + 1
        
        summary["top_errors"] = sorted(
            error_messages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return summary
    
    async def resolve_error(self, error_id: str, resolution_notes: str) -> bool:
        """Mark an error as resolved."""
        
        for error_event in self.error_store:
            if error_event.error_id == error_id:
                error_event.resolved = True
                error_event.resolution_notes = resolution_notes
                
                logger.info(f"Error {error_id} marked as resolved: {resolution_notes}")
                return True
        
        return False


# Global error tracker instance
error_tracker = ErrorTracker()


async def track_error(
    exception: Exception,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    context: Optional[ErrorContext] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> str:
    """Convenience function to track errors."""
    return await error_tracker.track_error(
        exception=exception,
        severity=severity,
        category=category,
        context=context,
        additional_info=additional_info
    )


def create_error_context(
    user_id: Optional[int] = None,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    **kwargs
) -> ErrorContext:
    """Create error context from request information."""
    return ErrorContext(
        user_id=user_id,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        endpoint=endpoint,
        method=method,
        additional_context=kwargs
    )