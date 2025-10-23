from typing import Dict, Any, List, Optional
import time
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging
import uuid
from dataclasses import dataclass, asdict

from app.core.redis import redis_client
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tenant_id: Optional[uuid.UUID] = None
    user_id: Optional[int] = None
    endpoint: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class PerformanceService:
    """Service for performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics_buffer: List[PerformanceMetric] = []
        self.buffer_size = 100
        self.flush_interval = 60  # seconds
        self._flush_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure background tasks are started"""
        if not self._initialized:
            try:
                if not self._flush_task or self._flush_task.done():
                    self._flush_task = asyncio.create_task(self._periodic_flush())
                self._initialized = True
            except RuntimeError:
                # No event loop running, will initialize later
                pass
    
    async def _periodic_flush(self):
        """Periodically flush metrics to storage"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush_metrics()
            except Exception as e:
                logger.error(f"Error in periodic metrics flush: {e}")
    
    async def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "ms",
        tenant_id: Optional[uuid.UUID] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a performance metric"""
        await self._ensure_initialized()
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint=endpoint,
            tags=tags or {}
        )
        
        self.metrics_buffer.append(metric)
        
        # Flush if buffer is full
        if len(self.metrics_buffer) >= self.buffer_size:
            await self.flush_metrics()
    
    async def flush_metrics(self):
        """Flush metrics buffer to Redis"""
        if not self.metrics_buffer:
            return
        
        try:
            # Move metrics to local variable and clear buffer
            metrics_to_flush = self.metrics_buffer.copy()
            self.metrics_buffer.clear()
            
            # Store metrics in Redis with TTL
            for metric in metrics_to_flush:
                await self._store_metric(metric)
            
            logger.debug(f"Flushed {len(metrics_to_flush)} metrics to storage")
            
        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
            # Re-add metrics to buffer if flush failed
            self.metrics_buffer.extend(metrics_to_flush)
    
    async def _store_metric(self, metric: PerformanceMetric):
        """Store individual metric in Redis"""
        try:
            # Create time-series key
            timestamp_key = metric.timestamp.strftime("%Y%m%d%H%M")
            
            if metric.tenant_id:
                key = f"metrics:{metric.tenant_id}:{metric.name}:{timestamp_key}"
            else:
                key = f"metrics:global:{metric.name}:{timestamp_key}"
            
            # Store metric data
            metric_data = asdict(metric)
            metric_data['timestamp'] = metric.timestamp.isoformat()
            
            await redis_client.set(
                key,
                metric_data,
                tenant_id=metric.tenant_id,
                ttl=7 * 24 * 3600  # 7 days retention
            )
            
        except Exception as e:
            logger.error(f"Error storing metric: {e}")
    
    @asynccontextmanager
    async def measure_time(
        self,
        metric_name: str,
        tenant_id: Optional[uuid.UUID] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """Context manager to measure execution time"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            await self.record_metric(
                name=metric_name,
                value=duration,
                unit="ms",
                tenant_id=tenant_id,
                user_id=user_id,
                endpoint=endpoint,
                tags=tags
            )
    
    async def get_performance_summary(
        self,
        tenant_id: Optional[uuid.UUID] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance summary for the specified period"""
        try:
            # This is a simplified implementation
            # In production, you'd aggregate metrics from time-series data
            
            summary = {
                "period_hours": hours,
                "tenant_id": str(tenant_id) if tenant_id else "global",
                "generated_at": datetime.utcnow().isoformat(),
                "metrics": {}
            }
            
            # Get cached summary if available
            cache_key = f"perf_summary:{hours}h"
            cached_summary = await cache_service.get_cached_statistics(cache_key, tenant_id)
            
            if cached_summary:
                return cached_summary
            
            # Calculate metrics (placeholder implementation)
            # In production, this would query actual stored metrics
            summary["metrics"] = {
                "api_response_time": {
                    "avg": 150.5,
                    "p95": 280.0,
                    "p99": 450.0,
                    "unit": "ms"
                },
                "database_query_time": {
                    "avg": 45.2,
                    "p95": 120.0,
                    "p99": 200.0,
                    "unit": "ms"
                },
                "cache_hit_ratio": {
                    "value": 85.5,
                    "unit": "percent"
                },
                "request_count": {
                    "total": 15420,
                    "per_hour": 642.5,
                    "unit": "requests"
                }
            }
            
            # Cache the summary
            await cache_service.cache_statistics(cache_key, summary, tenant_id, ttl=300)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def get_endpoint_performance(
        self,
        endpoint: str,
        tenant_id: Optional[uuid.UUID] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific endpoint"""
        try:
            # Placeholder implementation
            # In production, this would query metrics filtered by endpoint
            
            performance_data = {
                "endpoint": endpoint,
                "period_hours": hours,
                "tenant_id": str(tenant_id) if tenant_id else "global",
                "metrics": {
                    "request_count": 1250,
                    "avg_response_time": 145.2,
                    "p95_response_time": 275.0,
                    "p99_response_time": 420.0,
                    "error_rate": 0.8,
                    "slowest_requests": [
                        {"timestamp": "2025-01-23T10:15:30Z", "duration": 1250.5},
                        {"timestamp": "2025-01-23T09:42:15Z", "duration": 980.2}
                    ]
                }
            }
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Error getting endpoint performance: {e}")
            return {"error": str(e)}
    
    async def get_slow_queries(
        self,
        tenant_id: Optional[uuid.UUID] = None,
        threshold_ms: float = 1000.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get slow database queries"""
        try:
            # Placeholder implementation
            # In production, this would query actual slow query logs
            
            slow_queries = [
                {
                    "query": "SELECT * FROM activities WHERE tenant_id = ? ORDER BY created_at DESC",
                    "duration_ms": 1250.5,
                    "timestamp": "2025-01-23T10:15:30Z",
                    "table": "activities",
                    "rows_examined": 15000
                },
                {
                    "query": "SELECT COUNT(*) FROM contacts WHERE tenant_id = ? AND deleted_at IS NULL",
                    "duration_ms": 980.2,
                    "timestamp": "2025-01-23T09:42:15Z",
                    "table": "contacts",
                    "rows_examined": 8500
                }
            ]
            
            return slow_queries[:limit]
            
        except Exception as e:
            logger.error(f"Error getting slow queries: {e}")
            return []
    
    async def get_resource_usage(self, tenant_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Get current resource usage metrics"""
        try:
            # Get cache statistics
            cache_stats = await cache_service.get_cache_stats(tenant_id)
            
            # Placeholder for other resource metrics
            # In production, this would include CPU, memory, disk usage, etc.
            
            resource_usage = {
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": str(tenant_id) if tenant_id else "global",
                "cache": cache_stats,
                "database": {
                    "active_connections": 15,
                    "max_connections": 100,
                    "connection_usage": 15.0
                },
                "memory": {
                    "used_mb": 512.5,
                    "available_mb": 2048.0,
                    "usage_percent": 25.1
                },
                "cpu": {
                    "usage_percent": 35.2,
                    "load_average": [0.8, 0.9, 1.1]
                }
            }
            
            return resource_usage
            
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {"error": str(e)}
    
    async def check_performance_thresholds(
        self,
        tenant_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Check if performance metrics exceed defined thresholds"""
        try:
            thresholds = {
                "api_response_time_p95": 200.0,  # ms
                "database_query_time_p95": 100.0,  # ms
                "cache_hit_ratio_min": 80.0,  # percent
                "error_rate_max": 1.0  # percent
            }
            
            # Get current performance summary
            summary = await self.get_performance_summary(tenant_id, hours=1)
            
            violations = []
            
            # Check thresholds (placeholder implementation)
            if summary.get("metrics", {}).get("api_response_time", {}).get("p95", 0) > thresholds["api_response_time_p95"]:
                violations.append({
                    "metric": "api_response_time_p95",
                    "current_value": summary["metrics"]["api_response_time"]["p95"],
                    "threshold": thresholds["api_response_time_p95"],
                    "severity": "warning"
                })
            
            return {
                "tenant_id": str(tenant_id) if tenant_id else "global",
                "checked_at": datetime.utcnow().isoformat(),
                "thresholds": thresholds,
                "violations": violations,
                "status": "healthy" if not violations else "degraded"
            }
            
        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")
            return {"error": str(e)}
    
    async def optimize_queries_for_tenant(self, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Analyze and suggest query optimizations for tenant"""
        try:
            optimization_report = {
                "tenant_id": str(tenant_id),
                "analyzed_at": datetime.utcnow().isoformat(),
                "recommendations": []
            }
            
            # Placeholder implementation
            # In production, this would analyze actual query patterns
            
            recommendations = [
                {
                    "type": "missing_index",
                    "table": "activities",
                    "suggested_index": "CREATE INDEX idx_activities_tenant_type_created ON activities(tenant_id, type, created_at DESC)",
                    "impact": "high",
                    "estimated_improvement": "40% faster timeline queries"
                },
                {
                    "type": "query_optimization",
                    "query_pattern": "Contact search queries",
                    "suggestion": "Use full-text search index instead of LIKE queries",
                    "impact": "medium",
                    "estimated_improvement": "25% faster search"
                }
            ]
            
            optimization_report["recommendations"] = recommendations
            
            return optimization_report
            
        except Exception as e:
            logger.error(f"Error analyzing query optimization: {e}")
            return {"error": str(e)}


# Global performance service instance
performance_service = PerformanceService()