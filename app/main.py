from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
import logging

from app.core.config import settings
from app.core.middleware import (
    TenantContextMiddleware,
    RequestLoggingMiddleware,
    PerformanceMiddleware,
    setup_cors_middleware
)
from app.core.exceptions import (
    SalesEngagementException,
    sales_engagement_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    general_exception_handler
)
from app.core.redis import redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI app with comprehensive metadata
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="""
    ## Sales Engagement Platform API

    Enterprise-grade Sales Engagement Platform that combines VoIP calling, email synchronization, 
    SMS messaging, and lightweight CRM capabilities with real-time notifications and comprehensive analytics.

    ### Key Features
    - **Multi-tenant Architecture**: Complete data isolation per tenant with Row-Level Security
    - **VoIP Integration**: Twilio-powered calling with recording and activity tracking
    - **Real-time Notifications**: WebSocket-based instant updates
    - **Contact Management**: Advanced search, timeline, and relationship tracking
    - **Activity Timeline**: Comprehensive interaction history across all channels
    - **Security & Compliance**: GDPR-compliant with comprehensive audit logging
    - **Performance Monitoring**: Real-time metrics and optimization recommendations

    ### Authentication
    All API endpoints (except public ones) require JWT authentication via the `Authorization` header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```

    ### Rate Limiting
    API requests are rate-limited per user and tenant to ensure fair usage and system stability.

    ### Support
    For API support, please contact your system administrator or refer to the integration guides.
    """,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Sales Engagement Platform Support",
        "email": "support@salesengagement.com",
    },
    license_info={
        "name": "Proprietary License",
        "url": "https://salesengagement.com/license",
    },
    servers=[
        {
            "url": "http://localhost:8001",
            "description": "Local development server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server (alternative port)"
        },
        {
            "url": "https://staging-api.salesengagement.com", 
            "description": "Staging server"
        },
        {
            "url": "https://api.salesengagement.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "authentication",
            "description": "User authentication and authorization operations"
        },
        {
            "name": "contacts",
            "description": "Contact management operations including CRUD, search, and timeline"
        },
        {
            "name": "calls",
            "description": "VoIP calling operations with Twilio integration"
        },
        {
            "name": "activities",
            "description": "Activity timeline and interaction tracking"
        },
        {
            "name": "websocket",
            "description": "Real-time WebSocket connections and notifications"
        },
        {
            "name": "security",
            "description": "Security monitoring, audit logs, and GDPR compliance"
        },
        {
            "name": "monitoring",
            "description": "Performance monitoring and system health checks"
        },
        {
            "name": "webhooks",
            "description": "External webhook handlers (Twilio, etc.)"
        }
    ]
)

# Setup middleware (order matters - last added is executed first)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
setup_cors_middleware(app)  # CORS must be last (executed first)

# Setup exception handlers
app.add_exception_handler(SalesEngagementException, sales_engagement_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await redis_client.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await redis_client.disconnect()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    from app.core.metrics import metrics
    from fastapi.responses import PlainTextResponse
    
    return PlainTextResponse(
        content=metrics.get_metrics(),
        media_type="text/plain"
    )


# Include API routers
from app.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")