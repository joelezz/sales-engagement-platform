# Sales Engagement Platform

Enterprise-grade Sales Engagement Platform built with FastAPI, PostgreSQL, and Redis.

## Features

- Multi-tenant architecture with Row-Level Security
- VoIP calling integration with Twilio
- Real-time notifications via WebSocket
- Contact management with full-text search
- Activity timeline tracking
- JWT-based authentication
- GDPR compliance features

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15+ with Row-Level Security
- **Cache**: Redis 7+
- **Task Queue**: Celery
- **Authentication**: JWT with OAuth2/OIDC support

## Quick Start

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Start with Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Apply Row-Level Security policies:
   ```bash
   psql -f sql/setup_rls.sql
   ```

## Project Structure

```
app/
├── api/           # API endpoints
├── core/          # Core configuration and utilities
├── models/        # SQLAlchemy models
├── schemas/       # Pydantic schemas
├── services/      # Business logic services
└── tasks/         # Celery tasks
```

## Development Status

✅ **Task 1**: Project structure and core infrastructure
- FastAPI application with middleware
- Database models and migrations
- Docker configuration
- Redis integration
- Celery setup

✅ **Task 2**: Authentication and authorization system
- JWT token management with refresh tokens
- Password policy enforcement
- User registration and login endpoints
- OAuth2/OIDC ready architecture
- Secure token storage with httpOnly cookies

✅ **Task 3**: Contact management system
- Full CRUD operations with tenant isolation
- Advanced search with PostgreSQL full-text search
- Pagination and filtering
- Contact suggestions and autocomplete
- Statistics and analytics endpoints

✅ **Task 4**: VoIP calling integration
- Twilio integration for outbound calls
- Call status tracking and webhooks
- Call recording management
- Background call processing with Celery
- Call history and statistics
- Automatic activity creation

✅ **Task 5**: Activity timeline system
- Comprehensive activity tracking for all interactions
- Chronological timeline view per contact
- Activity search and filtering
- Real-time notifications via Redis pub/sub
- Activity statistics and analytics
- Integration with contact and call services

✅ **Task 6**: Real-time notification system
- WebSocket connection management with authentication
- Multi-channel subscription system
- Real-time activity, call, and contact notifications
- Offline notification queuing
- Heartbeat monitoring and auto-reconnection
- Tenant and user-specific broadcasting

✅ **Task 7**: Multi-tenant security and compliance
- Enhanced Row-Level Security with comprehensive policies
- Cross-tenant access violation detection
- GDPR compliance features (data export, anonymization, deletion)
- Comprehensive audit logging system
- Security monitoring and violation tracking
- Data retention and cleanup policies

✅ **Task 8**: Performance optimization and monitoring
- Comprehensive database indexing for optimal query performance
- Redis caching layer with tenant isolation
- Performance metrics collection and analysis
- Real-time monitoring and alerting
- Resource usage tracking
- Query optimization recommendations

✅ **Task 9**: API documentation and deployment preparation
- Comprehensive API documentation with examples
- Production-ready Kubernetes manifests
- Multi-stage Docker builds with security hardening
- CI/CD pipeline with automated testing and deployment
- Health checks and monitoring integration
- Auto-scaling and resource management

🎉 **Project Complete**: Enterprise-ready Sales Engagement Platform

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Production Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- Docker registry access
- PostgreSQL 15+ (managed service recommended)
- Redis 7+ (managed service recommended)

### Quick Deploy
```bash
# Build and deploy to Kubernetes
./scripts/deploy.sh v1.0.0

# Or use Docker Compose for development
docker-compose up -d
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key (generate secure key)
- `TWILIO_*`: Twilio API credentials

### Health Checks
- Health: `GET /health`
- Detailed: `GET /monitoring/health/detailed`
- Metrics: `GET /monitoring/metrics/performance`

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Mobile Client  │    │  Admin Panel    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      Load Balancer        │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     FastAPI Cluster       │
                    │  (Auto-scaling 3-10)     │
                    └─────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                       │                        │
┌───────┴────────┐    ┌─────────┴─────────┐    ┌─────────┴─────────┐
│   PostgreSQL   │    │      Redis        │    │   Celery Workers  │
│   (Multi-AZ)   │    │   (Cluster)       │    │  (Auto-scaling)   │
└────────────────┘    └───────────────────┘    └───────────────────┘
```