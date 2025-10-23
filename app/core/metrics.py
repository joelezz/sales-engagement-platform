"""
Prometheus metrics collection for the Sales Engagement Platform.
Provides comprehensive monitoring of API performance, business metrics, and system health.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector
import time
from typing import Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create metrics registry
registry = CollectorRegistry()

# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'tenant_id'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'tenant_id'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

# Database Metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry
)

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table', 'status'],
    registry=registry
)

# Redis Metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],
    registry=registry
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
    registry=registry
)

# WebSocket Metrics
websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections',
    ['tenant_id'],
    registry=registry
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['type', 'tenant_id'],
    registry=registry
)

websocket_notification_duration_seconds = Histogram(
    'websocket_notification_duration_seconds',
    'WebSocket notification delivery duration',
    ['tenant_id'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    registry=registry
)

# Business Logic Metrics
contacts_total = Gauge(
    'contacts_total',
    'Total number of contacts',
    ['tenant_id'],
    registry=registry
)

activities_total = Counter(
    'activities_total',
    'Total activities created',
    ['type', 'tenant_id'],
    registry=registry
)

# VoIP Metrics
voip_calls_total = Counter(
    'voip_calls_total',
    'Total VoIP calls',
    ['status', 'tenant_id'],
    registry=registry
)

voip_call_duration_seconds = Histogram(
    'voip_call_duration_seconds',
    'VoIP call duration in seconds',
    ['tenant_id'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800],
    registry=registry
)

twilio_webhook_errors_total = Counter(
    'twilio_webhook_errors_total',
    'Total Twilio webhook errors',
    ['error_type'],
    registry=registry
)

# Authentication Metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['method', 'status', 'tenant_id'],
    registry=registry
)

auth_failures_total = Counter(
    'auth_failures_total',
    'Total authentication failures',
    ['reason', 'tenant_id'],
    registry=registry
)

active_sessions = Gauge(
    'active_sessions',
    'Active user sessions',
    ['tenant_id'],
    registry=registry
)

# Security and Audit Metrics
audit_log_entries_total = Counter(
    'audit_log_entries_total',
    'Total audit log entries',
    ['action', 'resource_type', 'tenant_id'],
    registry=registry
)

gdpr_requests_total = Counter(
    'gdpr_requests_total',
    'Total GDPR requests',
    ['type', 'tenant_id'],
    registry=registry
)

# Performance Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type', 'tenant_id'],
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type', 'tenant_id'],
    registry=registry
)

# Background Task Metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status'],
    registry=registry
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=registry
)

# Tenant Metrics
tenant_users_active = Gauge(
    'tenant_users_active',
    'Active users per tenant',
    ['tenant_id'],
    registry=registry
)

tenant_api_requests_total = Counter(
    'tenant_api_requests_total',
    'Total API requests per tenant',
    ['tenant_id'],
    registry=registry
)


class MetricsCollector:
    """Centralized metrics collection and management."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, 
                          duration: float, tenant_id: Optional[str] = None):
        """Record HTTP request metrics."""
        tenant_label = tenant_id or "unknown"
        
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code),
            tenant_id=tenant_label
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            tenant_id=tenant_label
        ).observe(duration)
        
        tenant_api_requests_total.labels(tenant_id=tenant_label).inc()
    
    def record_db_query(self, operation: str, table: str, duration: float, success: bool = True):
        """Record database query metrics."""
        status = "success" if success else "error"
        
        db_queries_total.labels(
            operation=operation,
            table=table,
            status=status
        ).inc()
        
        db_query_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def record_redis_operation(self, operation: str, duration: float, success: bool = True):
        """Record Redis operation metrics."""
        status = "success" if success else "error"
        
        redis_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        redis_operation_duration_seconds.labels(operation=operation).observe(duration)
    
    def record_websocket_connection(self, tenant_id: str, connected: bool = True):
        """Record WebSocket connection metrics."""
        if connected:
            websocket_connections_active.labels(tenant_id=tenant_id).inc()
        else:
            websocket_connections_active.labels(tenant_id=tenant_id).dec()
    
    def record_websocket_message(self, message_type: str, tenant_id: str, duration: float):
        """Record WebSocket message metrics."""
        websocket_messages_total.labels(
            type=message_type,
            tenant_id=tenant_id
        ).inc()
        
        websocket_notification_duration_seconds.labels(tenant_id=tenant_id).observe(duration)
    
    def record_voip_call(self, status: str, tenant_id: str, duration: Optional[float] = None):
        """Record VoIP call metrics."""
        voip_calls_total.labels(status=status, tenant_id=tenant_id).inc()
        
        if duration is not None:
            voip_call_duration_seconds.labels(tenant_id=tenant_id).observe(duration)
    
    def record_auth_attempt(self, method: str, status: str, tenant_id: str):
        """Record authentication attempt metrics."""
        auth_attempts_total.labels(
            method=method,
            status=status,
            tenant_id=tenant_id
        ).inc()
        
        if status == "failure":
            auth_failures_total.labels(reason="invalid_credentials", tenant_id=tenant_id).inc()
    
    def record_activity(self, activity_type: str, tenant_id: str):
        """Record activity creation metrics."""
        activities_total.labels(type=activity_type, tenant_id=tenant_id).inc()
    
    def record_audit_log(self, action: str, resource_type: str, tenant_id: str):
        """Record audit log entry metrics."""
        audit_log_entries_total.labels(
            action=action,
            resource_type=resource_type,
            tenant_id=tenant_id
        ).inc()
    
    def record_cache_operation(self, cache_type: str, hit: bool, tenant_id: str):
        """Record cache operation metrics."""
        if hit:
            cache_hits_total.labels(cache_type=cache_type, tenant_id=tenant_id).inc()
        else:
            cache_misses_total.labels(cache_type=cache_type, tenant_id=tenant_id).inc()
    
    def record_celery_task(self, task_name: str, status: str, duration: float):
        """Record Celery task metrics."""
        celery_tasks_total.labels(task_name=task_name, status=status).inc()
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration)
    
    def update_tenant_metrics(self, tenant_id: str, active_users: int, total_contacts: int):
        """Update tenant-specific metrics."""
        tenant_users_active.labels(tenant_id=tenant_id).set(active_users)
        contacts_total.labels(tenant_id=tenant_id).set(total_contacts)
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        return generate_latest(registry).decode('utf-8')


# Global metrics collector instance
metrics = MetricsCollector()


def track_time(metric_name: str, labels: dict = None):
    """Decorator to track execution time of functions."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metrics based on metric name
                if metric_name == "db_query":
                    metrics.record_db_query(
                        labels.get("operation", "unknown"),
                        labels.get("table", "unknown"),
                        duration,
                        True
                    )
                elif metric_name == "redis_operation":
                    metrics.record_redis_operation(
                        labels.get("operation", "unknown"),
                        duration,
                        True
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metrics
                if metric_name == "db_query":
                    metrics.record_db_query(
                        labels.get("operation", "unknown"),
                        labels.get("table", "unknown"),
                        duration,
                        False
                    )
                elif metric_name == "redis_operation":
                    metrics.record_redis_operation(
                        labels.get("operation", "unknown"),
                        duration,
                        False
                    )
                
                raise e
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success metrics
                return result
            except Exception as e:
                duration = time.time() - start_time
                # Record error metrics
                raise e
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    
    return decorator