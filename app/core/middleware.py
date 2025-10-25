from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import uuid
import time
import logging
from typing import Callable
from app.core.database import AsyncSessionLocal, set_tenant_context
from app.core.security import decode_access_token
from app.core.metrics import metrics

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set tenant context for Row-Level Security"""
    
    def _create_cors_response(self, status_code: int, content: dict, request: Request):
        """Create JSONResponse with CORS headers"""
        from app.core.config import settings
        
        response = JSONResponse(
            status_code=status_code,
            content=content
        )
        
        # Add CORS headers manually
        origin = request.headers.get("origin")
        if origin and origin in settings.cors_origins_list:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        
        return response
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip tenant context for public endpoints and OPTIONS requests
        public_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/api/v1/auth/login", "/api/v1/auth/register", "/favicon.ico", "/metrics"]
        if any(request.url.path.startswith(path) for path in public_paths) or request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract tenant_id from JWT token
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return self._create_cors_response(
                status_code=401,
                content={"error": "unauthorized", "message": "Missing or invalid authorization header"},
                request=request
            )
        
        try:
            token = authorization.split(" ")[1]
            payload = decode_access_token(token)
            tenant_id = payload.get("tenant_id")
            
            if not tenant_id:
                return self._create_cors_response(
                    status_code=401,
                    content={"error": "unauthorized", "message": "Missing tenant_id in token"},
                    request=request
                )
            
            # Set tenant context in request state
            request.state.tenant_id = uuid.UUID(tenant_id)
            request.state.user_id = payload.get("sub")
            
        except Exception as e:
            logger.error(f"Error processing token: {e}")
            return self._create_cors_response(
                status_code=401,
                content={"error": "unauthorized", "message": "Invalid token"},
                request=request
            )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with correlation IDs"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                }
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "process_time": process_time,
                }
            )
            raise


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and metrics collection"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip performance tracking for static files and health checks
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico", "/metrics"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        # Extract tenant and user info if available
        tenant_id = None
        user_id = None
        
        try:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                payload = decode_access_token(token)
                tenant_id = payload.get("tenant_id")
                user_id = payload.get("sub")
        except Exception:
            pass  # Continue without user context
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        process_time_ms = process_time * 1000  # Convert to milliseconds
        
        # Add performance headers
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
        
        # Record Prometheus metrics
        try:
            # Normalize endpoint path for metrics (remove IDs)
            endpoint_path = request.url.path
            for segment in endpoint_path.split('/'):
                if segment.isdigit() or (len(segment) == 36 and '-' in segment):  # UUID or ID
                    endpoint_path = endpoint_path.replace(segment, '{id}')
            
            metrics.record_http_request(
                method=request.method,
                endpoint=endpoint_path,
                status_code=response.status_code,
                duration=process_time,
                tenant_id=tenant_id
            )
        except Exception as e:
            logger.error(f"Error recording Prometheus metrics: {e}")
        
        # Record legacy performance metric for backward compatibility
        try:
            from app.services.performance_service import performance_service
            await performance_service.record_metric(
                name="api_response_time",
                value=process_time_ms,
                unit="ms",
                tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
                user_id=int(user_id) if user_id else None,
                endpoint=f"{request.method} {request.url.path}",
                tags={
                    "method": request.method,
                    "status_code": str(response.status_code),
                    "path": request.url.path
                }
            )
        except Exception as e:
            logger.debug(f"Performance service not available: {e}")
        
        return response


def setup_cors_middleware(app):
    """Setup CORS middleware"""
    from app.core.config import settings
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )