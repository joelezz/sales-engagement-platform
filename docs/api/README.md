# Sales Engagement Platform API Documentation

## Overview

The Sales Engagement Platform API provides a comprehensive set of endpoints for managing customer relationships, communications, and sales activities. Built with FastAPI, it offers high performance, automatic validation, and interactive documentation.

## Base URL

- **Production**: `https://api.salesengagement.com`
- **Staging**: `https://staging-api.salesengagement.com`
- **Development**: `http://localhost:8000`

## Authentication

### JWT Token Authentication

All API endpoints require JWT authentication via the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "rep",
    "company_name": "Acme Corp"
  }
}
```

### Token Refresh

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

## Rate Limiting

API requests are rate-limited to ensure fair usage:

- **Standard users**: 1000 requests per hour
- **Premium users**: 5000 requests per hour
- **Enterprise users**: 10000 requests per hour

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per hour
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "total": 100,
    "total_pages": 10
  }
}
```

### Error Response
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": { ... },
  "request_id": "req_123456789",
  "timestamp": "2025-01-23T10:30:00Z"
}
```

## Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)

## Filtering and Search

Many endpoints support filtering and search:

- `search`: Full-text search across relevant fields
- `date_from`: Filter by date range (start)
- `date_to`: Filter by date range (end)
- Additional field-specific filters

## WebSocket Connections

Real-time notifications are available via WebSocket:

```javascript
const ws = new WebSocket('wss://api.salesengagement.com/api/v1/ws/connect?token=your-jwt-token');

ws.onmessage = function(event) {
  const notification = JSON.parse(event.data);
  console.log('Received notification:', notification);
};
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid request format |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Validation Error - Request validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

## SDKs and Libraries

Official SDKs are available for:

- **JavaScript/TypeScript**: `npm install @salesengagement/api-client`
- **Python**: `pip install salesengagement-api`
- **PHP**: `composer require salesengagement/api-client`

## Webhooks

The platform supports webhooks for real-time event notifications:

### Supported Events
- `contact.created`
- `contact.updated`
- `call.completed`
- `activity.created`

### Webhook Configuration
Configure webhooks in your tenant settings or via the API:

```http
POST /api/v1/webhooks/configure
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/salesengagement",
  "events": ["contact.created", "call.completed"],
  "secret": "your-webhook-secret"
}
```

## Support

- **Documentation**: [https://docs.salesengagement.com](https://docs.salesengagement.com)
- **API Status**: [https://status.salesengagement.com](https://status.salesengagement.com)
- **Support Email**: support@salesengagement.com
- **Developer Forum**: [https://community.salesengagement.com](https://community.salesengagement.com)

## Changelog

### v1.0.0 (2025-01-23)
- Initial API release
- Contact management endpoints
- VoIP calling integration
- Real-time notifications
- Security and compliance features
- Performance monitoring