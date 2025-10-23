# 📞 Sales Engagement Platform

> Enterprise-grade CRM with VoIP calling capabilities

[![Production Ready](https://img.shields.io/badge/Production-Ready-green.svg)](https://call.duoai.tech)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](./docker-compose.prod.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![Twilio](https://img.shields.io/badge/Twilio-VoIP-red.svg)](https://www.twilio.com/)

## 🎯 Overview

Sales Engagement Platform is a modern, enterprise-grade CRM system with integrated VoIP calling capabilities. Built with FastAPI and React, it provides a complete solution for sales teams to manage contacts, track activities, and make calls directly from the web interface.

**🌐 Live Demo:** [call.duoai.tech](https://call.duoai.tech)  
**📚 API Docs:** [api.call.duoai.tech/docs](https://api.call.duoai.tech/docs)

## ✨ Features

### 🔐 Authentication & Security
- **JWT-based authentication** with refresh tokens
- **Multi-tenant architecture** with Row-Level Security
- **GDPR compliance** with data export/deletion
- **Comprehensive audit logging**
- **Password policies** and secure session management

### 👥 Contact Management
- **Full CRUD operations** for contacts
- **Advanced search** with fuzzy matching
- **Contact timeline** with activity history
- **Bulk operations** and data import/export
- **Custom fields** and metadata support

### 📞 VoIP Integration
- **Twilio-powered calling** directly from the interface
- **Click-to-call** functionality
- **Call recording** and playback
- **Real-time call status** updates
- **Automatic activity creation** for calls

### 📊 Activity Tracking
- **Comprehensive timeline** for all interactions
- **Multiple activity types** (calls, emails, notes, meetings)
- **Real-time notifications** via WebSocket
- **Activity analytics** and reporting
- **Automated activity creation**

### 🚀 Performance & Scalability
- **Async FastAPI backend** for high performance
- **Redis caching** for optimal response times
- **Database connection pooling**
- **Prometheus metrics** collection
- **Structured logging** with correlation IDs

### 🌐 Modern Frontend
- **React 18** with TypeScript
- **Responsive design** for mobile and desktop
- **Real-time updates** with React Query
- **Intuitive UI/UX** with loading states
- **Progressive Web App** capabilities

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Primary database with RLS
- **Redis** - Caching and pub/sub messaging
- **Alembic** - Database migrations
- **Celery** - Background task processing

### Frontend
- **React 18** - UI library with hooks
- **TypeScript** - Type-safe JavaScript
- **React Query** - Data fetching and caching
- **React Router** - Client-side routing
- **Axios** - HTTP client with interceptors

### Infrastructure
- **Docker** - Containerization
- **Nginx** - Reverse proxy and load balancer
- **Let's Encrypt** - SSL certificates
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards

### Integrations
- **Twilio** - VoIP calling and SMS
- **WebSocket** - Real-time notifications
- **OAuth2/OIDC** - External authentication

## 🚀 Quick Start

### Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/sales-engagement-platform.git
   cd sales-engagement-platform
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   # Backend
   python -m uvicorn app.main:app --reload --port 8001
   
   # Frontend
   cd frontend && npm install && npm start
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8001
   - API Docs: http://localhost:8001/docs

### Production Deployment

**🎯 Deploy to call.duoai.tech with one command:**

```bash
./deploy.sh
```

For detailed deployment instructions, see [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md)

## 📋 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/sales_engagement
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Twilio VoIP
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-phone-number

# Application
BASE_URL=https://api.call.duoai.tech
ALLOWED_ORIGINS=https://call.duoai.tech
DEBUG=false
```

### Twilio Setup

1. Create a Twilio account
2. Get your Account SID and Auth Token
3. Purchase a phone number
4. Set webhook URL: `https://api.call.duoai.tech/api/v1/webhooks/twilio/call-status`

## 🧪 Testing

### Run Tests
```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test

# E2E tests
./scripts/run_e2e_tests.sh

# CORS tests
./test_cors_and_api.sh
```

### Test Coverage
- **Backend:** 95%+ test coverage
- **Frontend:** Component and integration tests
- **E2E:** Complete user workflows
- **API:** All endpoints tested

## 📊 Monitoring

### Health Checks
- **Backend:** `/health` endpoint
- **Database:** Connection and query tests
- **Redis:** Cache connectivity
- **External APIs:** Twilio status

### Metrics
- **Response times** for all endpoints
- **Database query performance**
- **Cache hit rates**
- **VoIP call statistics**
- **User activity metrics**

### Logging
- **Structured JSON logs** with correlation IDs
- **Request/response logging**
- **Error tracking** with stack traces
- **Audit logs** for compliance

## 🔧 Development

### Project Structure
```
sales-engagement-platform/
├── app/                    # FastAPI backend
│   ├── api/               # API routes
│   ├── core/              # Core functionality
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── schemas/           # Pydantic schemas
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   └── contexts/      # React contexts
│   └── public/            # Static assets
├── tests/                 # Test suites
├── scripts/               # Utility scripts
├── monitoring/            # Monitoring config
└── docs/                  # Documentation
```

### API Documentation

The API is fully documented with OpenAPI/Swagger:
- **Interactive docs:** [api.call.duoai.tech/docs](https://api.call.duoai.tech/docs)
- **ReDoc:** [api.call.duoai.tech/redoc](https://api.call.duoai.tech/redoc)
- **OpenAPI spec:** [api.call.duoai.tech/openapi.json](https://api.call.duoai.tech/openapi.json)

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📚 Documentation

- [Production Deployment Guide](./PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Quick Deploy Guide](./QUICK_DEPLOY.md)
- [VoIP Setup Guide](./VOIP_SETUP_GUIDE.md)
- [E2E Testing Guide](./E2E_TEST_GUIDE.md)
- [Project Completion Summary](./PROJECT_COMPLETION_SUMMARY.md)

## 🆘 Support

### Common Issues

1. **CORS Errors** - Check ALLOWED_ORIGINS configuration
2. **VoIP Not Working** - Verify Twilio webhook URL is accessible
3. **Database Connection** - Ensure PostgreSQL is running
4. **Redis Connection** - Check Redis server status

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/your-username/sales-engagement-platform/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-username/sales-engagement-platform/discussions)
- **Email:** dev@duoai.tech

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Amazing Python web framework
- **React** - Powerful UI library
- **Twilio** - Reliable VoIP services
- **PostgreSQL** - Robust database system
- **Docker** - Containerization platform

---

**Built with ❤️ by the Duoai Team**

🌐 **Website:** [duoai.tech](https://duoai.tech)  
📧 **Contact:** dev@duoai.tech  
🐙 **GitHub:** [github.com/duoai](https://github.com/duoai)