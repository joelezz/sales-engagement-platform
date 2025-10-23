import React, { useState } from 'react';
import { FileText, Database, Lock, Code, TestTube, Plug, ChevronRight, Download } from 'lucide-react';

const SpecViewer = () => {
  const [activeSpec, setActiveSpec] = useState('prd');

  const specs = {
    prd: {
      title: '01_PRD.md',
      subtitle: 'Product Requirements',
      icon: FileText,
      color: 'blue',
      content: `# Sales Engagement Platform - Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** 2025-10-23  
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Product Vision
Enterprise-grade Sales Engagement Platform that combines VoIP calling, email synchronization, SMS messaging, and lightweight CRM capabilities with an optional CRM-Pro module for deal management.

### 1.2 Success Metrics
- **User Adoption**: 80% MAU/total users within 3 months
- **Activity Volume**: 1000+ activities/day/tenant at scale
- **Uptime SLA**: 99.9% for core features
- **API Latency**: p95 < 200ms for CRUD operations
- **WebSocket Latency**: < 500ms for real-time notifications

---

## 2. User Personas

### 2.1 Primary: Sales Representative
- **Goals**: Contact customers efficiently, track all interactions
- **Pain Points**: Context switching between tools, missed follow-ups
- **Key Features**: Quick dial, activity timeline, email sync

### 2.2 Secondary: Sales Manager
- **Goals**: Monitor team performance, manage pipeline
- **Pain Points**: No visibility into team activities
- **Key Features**: Dashboard, reporting, deal pipeline (CRM-Pro)

### 2.3 Tertiary: System Administrator
- **Goals**: Manage users, billing, integrations
- **Pain Points**: Complex permission models
- **Key Features**: User management, Stripe integration, audit logs

---

## 3. Functional Requirements (Prioritized)

### 3.1 P0 - MVP Core Features

#### FR-001: User Authentication
- **Given** a user with valid credentials
- **When** they attempt to log in
- **Then** they receive a JWT token valid for 24h
- **Acceptance**: OAuth2 + OIDC support, MFA optional

#### FR-002: Contact Management
- **Given** an authenticated user
- **When** they create/update/delete a contact
- **Then** changes are reflected immediately with < 200ms latency
- **Acceptance**: CRUD + search (fuzzy), pagination, multi-tenant isolation

#### FR-003: VoIP Outbound Calling
- **Given** a contact with valid phone number
- **When** user initiates call
- **Then** Twilio call is established within 3s
- **Acceptance**: Call recording, duration tracking, automatic activity log

#### FR-004: Activity Timeline
- **Given** a contact
- **When** user views contact details
- **Then** chronological activity feed is displayed (calls, emails, SMS)
- **Acceptance**: Real-time updates via WebSocket, < 500ms notification delay

#### FR-005: Real-time Notifications
- **Given** an active user session
- **When** relevant activity occurs (inbound call, email reply)
- **Then** user receives browser notification within 500ms
- **Acceptance**: WebSocket connection with auto-reconnect

---

## 4. Non-Functional Requirements

### NFR-001: Multi-Tenancy
- **Requirement**: Complete data isolation per tenant
- **Acceptance**: Row-Level Security (RLS) enforced at DB level

### NFR-002: Scalability
- **Requirement**: Support 10,000 users across 100 tenants
- **Acceptance**: Horizontal scaling of API/workers, Redis pub/sub

### NFR-003: GDPR Compliance
- **Requirement**: Data portability, right to be forgotten
- **Acceptance**: Export API, soft-delete + anonymization pipeline

---

## 5. Release Criteria

### MVP Release (V1.0)
- All P0 features implemented
- 90% test coverage (unit + integration)
- Security audit passed
- Load testing: 100 concurrent users, < 200ms p95 latency
`
    },
    
    technical: {
      title: '02_TECHNICAL_SPEC.md',
      subtitle: 'Architecture & Design',
      icon: Code,
      color: 'purple',
      content: `# Technical Specification

**Version:** 1.0  
**Date:** 2025-10-23

---

## 1. Technology Stack

### Backend
- Language: Python 3.11+
- Framework: FastAPI 0.104+
- Task Queue: Celery 5.3+
- ORM: SQLAlchemy 2.0+

### Data Layer
- Primary DB: PostgreSQL 15+
- Cache: Redis 7+
- Object Storage: S3-compatible

### Infrastructure
- Containers: Docker + Kubernetes
- CI/CD: GitHub Actions
- Secrets: HashiCorp Vault

---

## 2. Architecture Principles

1. Multi-tenancy by design: tenant_id in every query
2. Idempotency: All external webhooks use event deduplication
3. Async by default: Heavy operations via task queue
4. Observability-first: Structured logging, tracing, metrics

---

## 3. Multi-Tenancy with RLS

PostgreSQL Row-Level Security:

ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON contacts
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

Application setup per request:

await db.execute(
    text("SET app.current_tenant = :tenant_id"),
    params
)

---

## 4. API Design Standards

### REST Conventions
- GET /contacts - List (paginated)
- POST /contacts - Create
- GET /contacts/:id - Retrieve
- PATCH /contacts/:id - Partial update
- DELETE /contacts/:id - Soft delete

### Response Format
All responses follow data/meta/errors pattern

---

## 5. Performance Targets

- GET /contacts: p95 < 150ms
- POST /contacts: p95 < 200ms
- WebSocket notification: < 500ms
`
    },

    datamodel: {
      title: '03_DATA_MODEL.md',
      subtitle: 'Schema & Validation',
      icon: Database,
      color: 'green',
      content: `# Data Model Specification

**Version:** 1.0

---

## 1. Core Tables

### companies
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| tenant_id | UUID | UNIQUE, NOT NULL |
| name | VARCHAR(200) | NOT NULL |
| plan | VARCHAR(50) | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| tenant_id | UUID | FK companies |
| email | VARCHAR(255) | NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| role | VARCHAR(50) | NOT NULL |

### contacts
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| tenant_id | UUID | FK companies |
| firstname | VARCHAR(100) | NOT NULL |
| lastname | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | |
| phone | VARCHAR(20) | |
| metadata | JSONB | |

### activities
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY |
| tenant_id | UUID | FK companies |
| type | VARCHAR(50) | NOT NULL |
| contact_id | INT | FK contacts |
| payload | JSONB | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

---

## 2. Validation Rules

### ContactCreate Schema

from pydantic import BaseModel, EmailStr, Field

class ContactCreate(BaseModel):
    firstname: str = Field(..., min_length=1, max_length=100)
    lastname: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    metadata: dict = Field(default_factory=dict)
`
    },

    api: {
      title: '04_API_SPEC.md',
      subtitle: 'OpenAPI Contract',
      icon: Plug,
      color: 'orange',
      content: `# API Specification

**Base URL:** https://api.example.com/api/v1

---

## Authentication

### POST /auth/login

Request:
{
  "email": "user@example.com",
  "password": "password"
}

Response (200):
{
  "data": {
    "access_token": "eyJ...",
    "user": {
      "id": 1,
      "email": "user@example.com"
    }
  }
}

---

## Contacts

### GET /contacts

Query Params:
- page: int (default: 1)
- page_size: int (default: 50)
- search: string

Response (200):
{
  "data": [...],
  "meta": {
    "page": 1,
    "total": 100
  }
}

### POST /contacts

Request:
{
  "firstname": "Jane",
  "lastname": "Doe",
  "email": "jane@example.com"
}

Response (201):
{
  "data": {
    "id": 1,
    ...
  }
}
`
    },

    integration: {
      title: '05_INTEGRATION_SPEC.md',
      subtitle: 'External Services',
      icon: Plug,
      color: 'cyan',
      content: `# Integration Specification

---

## 1. Twilio Integration

### Voice API

Outbound Call Flow:
1. User clicks "Call"
2. POST /calls endpoint
3. Celery task creates call
4. Twilio webhook callbacks
5. Store activity

Code Example:

from twilio.rest import Client

client = Client(account_sid, auth_token)

call = client.calls.create(
    to=contact.phone,
    from_=from_number,
    url=callback_url,
    record=True
)

---

## 2. Gmail OAuth

### Setup
1. Create Google Cloud project
2. Enable Gmail API
3. Configure OAuth consent
4. Store client_id/secret in Vault

### Token Flow
1. Redirect user to OAuth URL
2. Handle callback with code
3. Exchange for tokens
4. Store encrypted in DB
5. Refresh before expiry

---

## 3. Stripe Integration

### Subscription Flow
1. Create Stripe customer
2. Create subscription
3. Handle webhooks
4. Update license count

Webhook Events:
- invoice.paid
- customer.subscription.updated
- customer.subscription.deleted
`
    },

    security: {
      title: '06_SECURITY_SPEC.md',
      subtitle: 'Security & Compliance',
      icon: Lock,
      color: 'red',
      content: `# Security & Compliance Specification

---

## 1. Authentication

### JWT Strategy
- Access token: 15 minutes
- Refresh token: 7 days
- Store refresh in httpOnly cookie
- Rotate on each refresh

### Password Policy
- Min 12 characters
- Must include: upper, lower, number, special
- bcrypt with cost factor 12

---

## 2. Multi-Tenant Security

### Row-Level Security
- Enforce at database level
- Set tenant context per request
- Cannot bypass in application code

### API Authorization
- Validate tenant_id in JWT
- Check resource ownership
- Implement RBAC

---

## 3. GDPR Compliance

### Right to Access
- Export API endpoint
- JSON format with all user data
- Includes activities, contacts

### Right to Deletion
- Soft delete with deleted_at
- Hard delete after 90 days
- Anonymize referenced data

### Data Retention
- Configure per tenant
- Scheduled purge job
- Audit log retention: 7 years

---

## 4. Secrets Management

- Store in HashiCorp Vault
- Rotate credentials monthly
- Never log secrets
- Encrypt OAuth tokens at rest
`
    },

    testing: {
      title: '07_TESTING_SPEC.md',
      subtitle: 'Test Strategy',
      icon: TestTube,
      color: 'pink',
      content: `# Testing Specification

---

## 1. Test Pyramid

### Unit Tests (70%)
- All business logic
- Pydantic validators
- Utility functions
- Target: 90% coverage

### Integration Tests (20%)
- API endpoints
- Database operations
- Task queue
- Use testcontainers for Postgres/Redis

### E2E Tests (10%)
- Critical user flows
- Auth + Create contact + Call
- Playwright for UI tests

---

## 2. Test Data

### Fixtures
- Use pytest fixtures
- Factory pattern for models
- Separate tenant per test

Example:

@pytest.fixture
async def contact_factory(db_session):
    async def _create(tenant_id, **kwargs):
        contact = Contact(
            tenant_id=tenant_id,
            **kwargs
        )
        db_session.add(contact)
        await db_session.commit()
        return contact
    return _create

---

## 3. API Testing

### Contract Tests
- Validate request/response schemas
- Test all status codes
- Pagination edge cases

Example:

async def test_create_contact(client, auth_headers):
    response = await client.post(
        "/contacts",
        json={"firstname": "Jane", "lastname": "Doe"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["firstname"] == "Jane"

---

## 4. Load Testing

### Tools
- Locust or k6
- Target: 100 concurrent users
- Duration: 10 minutes

### Scenarios
- 70% reads (GET /contacts)
- 20% writes (POST /contacts)
- 10% calls (POST /calls)

### Success Criteria
- p95 latency < 200ms
- Error rate < 0.1%
- No memory leaks
`
    }
  };

  const currentSpec = specs[activeSpec];
  const SpecIcon = currentSpec.icon;

  const downloadSpec = (specKey) => {
    const spec = specs[specKey];
    const blob = new Blob([spec.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = spec.title;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadAll = () => {
    Object.keys(specs).forEach(key => {
      setTimeout(() => downloadSpec(key), 100 * Object.keys(specs).indexOf(key));
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Sales Engagement Platform
          </h1>
          <p className="text-slate-600 text-lg">
            Spec-Driven Development Documentation
          </p>
          <button
            onClick={downloadAll}
            className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download All Specs
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1 space-y-2">
            {Object.entries(specs).map(([key, spec]) => {
              const Icon = spec.icon;
              const isActive = activeSpec === key;
              return (
                <button
                  key={key}
                  onClick={() => setActiveSpec(key)}
                  className={`w-full flex items-center gap-3 p-4 rounded-lg transition-all ${
                    isActive
                      ? 'bg-white shadow-lg ring-2 ring-' + spec.color + '-500'
                      : 'bg-white/50 hover:bg-white hover:shadow-md'
                  }`}
                >
                  <Icon className={`w-5 h-5 text-${spec.color}-600`} />
                  <div className="flex-1 text-left">
                    <div className="font-semibold text-slate-900 text-sm">
                      {spec.title}
                    </div>
                    <div className="text-xs text-slate-500">
                      {spec.subtitle}
                    </div>
                  </div>
                  {isActive && <ChevronRight className="w-4 h-4 text-slate-400" />}
                </button>
              );
            })}
          </div>

          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <SpecIcon className={`w-8 h-8 text-${currentSpec.color}-600`} />
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">
                      {currentSpec.title}
                    </h2>
                    <p className="text-slate-600">{currentSpec.subtitle}</p>
                  </div>
                </div>
                <button
                  onClick={() => downloadSpec(activeSpec)}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>

              <div className="prose prose-slate max-w-none">
                <pre className="bg-slate-50 p-6 rounded-lg overflow-x-auto text-sm leading-relaxed whitespace-pre-wrap">
                  {currentSpec.content}
                </pre>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-2">
            Implementation Approach (Spec-Driven Development)
          </h3>
          <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
            <li>Review and approve all specs with stakeholders</li>
            <li>Write tests based on acceptance criteria in specs</li>
            <li>Implement features to pass tests (TDD approach)</li>
            <li>Validate implementation against spec requirements</li>
            <li>Update specs as requirements evolve (living documentation)</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default SpecViewer;