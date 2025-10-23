"""
Monitoring and observability API endpoints.
Provides system health, metrics, and error tracking information.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.core.security import get_current_user
from app.core.error_tracking import error_tracker
from app.core.metrics import metrics
from app.schemas.auth import UserProfile
from app.schemas.monitoring import (
    HealthCheckResponse,
    SystemMetrics,
    ErrorSummary,
    PerformanceMetrics
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health", response_model=HealthCheckResponse, tags=["monitoring"])
async def health_check():
    """
    Comprehensive health check endpoint.
    Returns system status and component health.
    """
    try:
        # Check database connectivity
        from app.core.database import engine
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check Redis connectivity
    try:
        from app.core.redis import redis_client
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unhealthy"
    
    # Overall system status
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        components={
            "database": db_status,
            "redis": redis_status,
            "api": "healthy"
        },
        version="1.0.0"
    )


@router.get("/metrics/summary", response_model=SystemMetrics, tags=["monitoring"])
async def get_metrics_summary(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get system metrics summary.
    Requires authentication.
    """
    try:
        # This would typically query your metrics store
        # For now, we'll return mock data structure
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            api_requests_per_second=0.0,  # Would be calculated from metrics
            average_response_time=0.0,
            error_rate=0.0,
            active_connections=0,
            database_connections=0,
            memory_usage_percent=0.0,
            cpu_usage_percent=0.0
        )
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/errors/summary", response_model=ErrorSummary, tags=["monitoring"])
async def get_error_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get error summary for the specified time period.
    Requires authentication.
    """
    try:
        summary_data = error_tracker.get_error_summary(hours=hours)
        
        return ErrorSummary(
            timestamp=datetime.utcnow(),
            time_period_hours=hours,
            total_errors=summary_data["total_errors"],
            errors_by_severity=summary_data["by_severity"],
            errors_by_category=summary_data["by_category"],
            top_error_messages=[
                {"message": msg, "count": count}
                for msg, count in summary_data["top_errors"]
            ]
        )
    except Exception as e:
        logger.error(f"Error getting error summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error summary")


@router.get("/performance", response_model=PerformanceMetrics, tags=["monitoring"])
async def get_performance_metrics(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get performance metrics.
    Optionally filter by tenant.
    """
    try:
        # This would query your performance metrics store
        # For now, return mock structure
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            api_latency_p95=0.0,
            api_latency_p99=0.0,
            database_query_time_avg=0.0,
            cache_hit_rate=0.0,
            websocket_message_latency=0.0,
            voip_call_success_rate=0.0
        )
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.post("/errors/{error_id}/resolve", tags=["monitoring"])
async def resolve_error(
    error_id: str,
    resolution_notes: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Mark an error as resolved.
    Requires authentication.
    """
    try:
        success = await error_tracker.resolve_error(error_id, resolution_notes)
        
        if not success:
            raise HTTPException(status_code=404, detail="Error not found")
        
        return {"message": "Error marked as resolved", "error_id": error_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving error {error_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve error")


@router.get("/alerts/active", tags=["monitoring"])
async def get_active_alerts(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get currently active alerts.
    Requires authentication.
    """
    try:
        # This would query your alerting system
        # For now, return empty list
        return {"active_alerts": [], "count": 0}
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/system/status", tags=["monitoring"])
async def get_system_status(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get detailed system status information.
    Requires authentication.
    """
    try:
        # Get system information
        import psutil
        import sys
        
        return {
            "system": {
                "python_version": sys.version,
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free
                }
            },
            "application": {
                "uptime": "N/A",  # Would calculate from startup time
                "version": "1.0.0",
                "environment": "development"  # From settings
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")