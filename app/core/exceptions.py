from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class SalesEngagementException(Exception):
    """Base exception for Sales Engagement Platform"""
    def __init__(self, message: str, error_code: str = "internal_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TenantAccessError(SalesEngagementException):
    """Raised when user tries to access resources from different tenant"""
    def __init__(self, message: str = "Access denied to tenant resource"):
        super().__init__(message, "tenant_access_denied")


class ResourceNotFoundError(SalesEngagementException):
    """Raised when requested resource is not found"""
    def __init__(self, resource: str, resource_id: str):
        message = f"{resource} with id {resource_id} not found"
        super().__init__(message, "resource_not_found")


def _add_cors_headers(response: JSONResponse, request: Request):
    """Add CORS headers to response"""
    from app.core.config import settings
    
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    
    return response


async def sales_engagement_exception_handler(request: Request, exc: SalesEngagementException):
    """Handle custom Sales Engagement Platform exceptions"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.error(
        f"Sales Engagement Exception: {exc.message}",
        extra={
            "correlation_id": correlation_id,
            "error_code": exc.error_code,
            "path": request.url.path,
        }
    )
    
    status_code = 400
    if exc.error_code == "tenant_access_denied":
        status_code = 403
    elif exc.error_code == "resource_not_found":
        status_code = 404
    
    response = JSONResponse(
        status_code=status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "request_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    
    return _add_cors_headers(response, request)


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.warning(
        f"Validation error: {exc}",
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
        }
    )
    
    response = JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": exc.errors(),
            "request_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    
    return _add_cors_headers(response, request)


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.error(
        f"Database integrity error: {exc}",
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
        }
    )
    
    response = JSONResponse(
        status_code=409,
        content={
            "error": "conflict",
            "message": "Resource conflict - data already exists or violates constraints",
            "request_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    
    return _add_cors_headers(response, request)


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
        },
        exc_info=True
    )
    
    response = JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "request_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    
    return _add_cors_headers(response, request)