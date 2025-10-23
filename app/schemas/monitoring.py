"""
Pydantic schemas for monitoring and observability endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    components: Dict[str, str] = Field(..., description="Component health status")
    version: str = Field(..., description="Application version")


class SystemMetrics(BaseModel):
    """System metrics summary schema."""
    timestamp: datetime = Field(..., description="Metrics timestamp")
    api_requests_per_second: float = Field(..., description="Current API requests per second")
    average_response_time: float = Field(..., description="Average response time in seconds")
    error_rate: float = Field(..., description="Error rate as percentage")
    active_connections: int = Field(..., description="Active WebSocket connections")
    database_connections: int = Field(..., description="Active database connections")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")


class ErrorMessage(BaseModel):
    """Error message with count schema."""
    message: str = Field(..., description="Error message")
    count: int = Field(..., description="Number of occurrences")


class ErrorSummary(BaseModel):
    """Error summary schema."""
    timestamp: datetime = Field(..., description="Summary timestamp")
    time_period_hours: int = Field(..., description="Time period in hours")
    total_errors: int = Field(..., description="Total number of errors")
    errors_by_severity: Dict[str, int] = Field(..., description="Errors grouped by severity")
    errors_by_category: Dict[str, int] = Field(..., description="Errors grouped by category")
    top_error_messages: List[ErrorMessage] = Field(..., description="Most frequent error messages")


class PerformanceMetrics(BaseModel):
    """Performance metrics schema."""
    timestamp: datetime = Field(..., description="Metrics timestamp")
    tenant_id: Optional[str] = Field(None, description="Tenant ID filter")
    api_latency_p95: float = Field(..., description="95th percentile API latency in seconds")
    api_latency_p99: float = Field(..., description="99th percentile API latency in seconds")
    database_query_time_avg: float = Field(..., description="Average database query time in seconds")
    cache_hit_rate: float = Field(..., description="Cache hit rate as percentage")
    websocket_message_latency: float = Field(..., description="WebSocket message latency in seconds")
    voip_call_success_rate: float = Field(..., description="VoIP call success rate as percentage")


class AlertInfo(BaseModel):
    """Alert information schema."""
    alert_id: str = Field(..., description="Unique alert identifier")
    severity: str = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    timestamp: datetime = Field(..., description="Alert timestamp")
    status: str = Field(..., description="Alert status")
    affected_components: List[str] = Field(..., description="Affected system components")


class ActiveAlertsResponse(BaseModel):
    """Active alerts response schema."""
    active_alerts: List[AlertInfo] = Field(..., description="List of active alerts")
    count: int = Field(..., description="Number of active alerts")
    timestamp: datetime = Field(..., description="Response timestamp")