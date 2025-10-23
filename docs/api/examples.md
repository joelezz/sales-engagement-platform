# API Usage Examples

## Authentication Examples

### Login and Get Token

```bash
curl -X POST "https://api.salesengagement.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password"
  }'
```

```javascript
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'your-password'
  })
});

const { access_token } = await response.json();
```

```python
import requests

response = requests.post('/api/v1/auth/login', json={
    'email': 'user@example.com',
    'password': 'your-password'
})

token = response.json()['access_token']
```

## Contact Management Examples

### Create a Contact

```bash
curl -X POST "https://api.salesengagement.com/api/v1/contacts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "John",
    "lastname": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567"
  }'
```

```javascript
const contact = await fetch('/api/v1/contacts', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    firstname: 'John',
    lastname: 'Doe',
    email: 'john.doe@example.com',
    phone: '+1-555-123-4567'
  })
});
```

### Search Contacts

```bash
curl -X GET "https://api.salesengagement.com/api/v1/contacts?search=john&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

```javascript
const contacts = await fetch('/api/v1/contacts?search=john&page=1&page_size=20', {
  headers: {
    'Authorization': `Bearer ${token}`,
  }
});

const data = await contacts.json();
console.log(`Found ${data.total} contacts`);
```

### Get Contact Timeline

```bash
curl -X GET "https://api.salesengagement.com/api/v1/contacts/123/activities" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## VoIP Calling Examples

### Initiate a Call

```bash
curl -X POST "https://api.salesengagement.com/api/v1/calls" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": 123
  }'
```

```javascript
const call = await fetch('/api/v1/calls', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    contact_id: 123
  })
});

const callSession = await call.json();
console.log(`Call initiated: ${callSession.call_sid}`);
```

### Get Call History

```bash
curl -X GET "https://api.salesengagement.com/api/v1/calls?contact_id=123&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Activity Management Examples

### Create Manual Activity

```bash
curl -X POST "https://api.salesengagement.com/api/v1/activities" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "note",
    "contact_id": 123,
    "payload": {
      "title": "Follow-up meeting scheduled",
      "content": "Scheduled follow-up meeting for next week to discuss proposal."
    }
  }'
```

### Get Activity Statistics

```bash
curl -X GET "https://api.salesengagement.com/api/v1/activities/stats/overview?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## WebSocket Examples

### JavaScript WebSocket Connection

```javascript
class SalesEngagementWebSocket {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    const wsUrl = `wss://api.salesengagement.com/api/v1/ws/connect?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      // Subscribe to channels
      this.subscribe('activities');
      this.subscribe('calls');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  subscribe(channel) {
    this.send({
      type: 'subscribe',
      data: { channel }
    });
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case 'notification':
        this.handleNotification(message.data);
        break;
      case 'heartbeat':
        // Respond to heartbeat
        this.send({ type: 'heartbeat' });
        break;
    }
  }

  handleNotification(notification) {
    console.log('Received notification:', notification);
    
    switch (notification.type) {
      case 'activity_created':
        this.onActivityCreated(notification.data);
        break;
      case 'call_status_update':
        this.onCallStatusUpdate(notification.data);
        break;
      case 'contact_updated':
        this.onContactUpdated(notification.data);
        break;
    }
  }

  onActivityCreated(data) {
    console.log('New activity:', data);
    // Update UI with new activity
  }

  onCallStatusUpdate(data) {
    console.log('Call status update:', data);
    // Update call status in UI
  }

  onContactUpdated(data) {
    console.log('Contact updated:', data);
    // Refresh contact data in UI
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      
      setTimeout(() => {
        console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
        this.connect();
      }, delay);
    }
  }
}

// Usage
const wsClient = new SalesEngagementWebSocket(yourJwtToken);
wsClient.connect();
```

## Monitoring Examples

### Health Check

```bash
curl -X GET "https://api.salesengagement.com/api/v1/monitoring/health"
```

### Performance Metrics

```bash
curl -X GET "https://api.salesengagement.com/api/v1/monitoring/metrics/performance?hours=24" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Security Examples

### Export User Data (GDPR)

```bash
curl -X POST "https://api.salesengagement.com/api/v1/security/gdpr/export/user/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Audit Trail

```bash
curl -X GET "https://api.salesengagement.com/api/v1/security/audit/trail?hours=24&limit=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Error Handling Examples

### JavaScript Error Handling

```javascript
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(endpoint, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(error.message, response.status, error);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      // Handle API errors
      console.error('API Error:', error.message);
      
      switch (error.status) {
        case 401:
          // Redirect to login
          window.location.href = '/login';
          break;
        case 429:
          // Rate limited - retry after delay
          await new Promise(resolve => setTimeout(resolve, 60000));
          return apiCall(endpoint, options);
        default:
          // Show error to user
          showErrorMessage(error.message);
      }
    } else {
      // Handle network errors
      console.error('Network Error:', error);
      showErrorMessage('Network error. Please try again.');
    }
    
    throw error;
  }
}

class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}
```

## Batch Operations Examples

### Bulk Contact Creation

```javascript
async function createContactsBatch(contacts) {
  const results = [];
  const batchSize = 10;
  
  for (let i = 0; i < contacts.length; i += batchSize) {
    const batch = contacts.slice(i, i + batchSize);
    const promises = batch.map(contact => 
      fetch('/api/v1/contacts', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(contact)
      })
    );
    
    const batchResults = await Promise.allSettled(promises);
    results.push(...batchResults);
    
    // Rate limiting - wait between batches
    if (i + batchSize < contacts.length) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  return results;
}
```