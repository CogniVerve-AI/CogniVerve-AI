# CogniVerve-AI API Reference

## Overview

The CogniVerve-AI API is a RESTful API that provides programmatic access to all platform features. This documentation covers all available endpoints, request/response formats, and authentication methods.

## Base URL

```
Production: https://api.cogniverve.ai/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

### JWT Token Authentication

All API requests require authentication using JWT tokens.

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

#### Using the Token
Include the token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "details": {}
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error

## Endpoints

### Authentication

#### Register User
```http
POST /auth/register
```

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string"
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer {token}
```

#### Update Profile
```http
PUT /auth/me
Authorization: Bearer {token}
```

### Agents

#### List Agents
```http
GET /agents
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip` (int): Number of records to skip
- `limit` (int): Maximum number of records to return
- `search` (string): Search term for agent names

**Response:**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "id": "uuid",
        "name": "string",
        "description": "string",
        "model": "string",
        "temperature": 0.7,
        "tools": ["tool1", "tool2"],
        "is_public": false,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 10,
    "skip": 0,
    "limit": 20
  }
}
```

#### Create Agent
```http
POST /agents
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "instructions": "string",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "tools": ["web_search", "calculator"],
  "is_public": false
}
```

#### Get Agent
```http
GET /agents/{agent_id}
Authorization: Bearer {token}
```

#### Update Agent
```http
PUT /agents/{agent_id}
Authorization: Bearer {token}
```

#### Delete Agent
```http
DELETE /agents/{agent_id}
Authorization: Bearer {token}
```

### Tasks

#### List Tasks
```http
GET /tasks
Authorization: Bearer {token}
```

**Query Parameters:**
- `status` (string): Filter by status (pending, running, completed, failed)
- `agent_id` (uuid): Filter by agent ID

#### Create Task
```http
POST /tasks
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "agent_id": "uuid",
  "metadata": {}
}
```

#### Get Task
```http
GET /tasks/{task_id}
Authorization: Bearer {token}
```

#### Cancel Task
```http
POST /tasks/{task_id}/cancel
Authorization: Bearer {token}
```

### Conversations

#### List Conversations
```http
GET /conversations
Authorization: Bearer {token}
```

#### Create Conversation
```http
POST /conversations
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "title": "string",
  "agent_id": "uuid"
}
```

#### Send Message
```http
POST /conversations/{conversation_id}/messages
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "content": "string",
  "role": "user"
}
```

### Tools

#### List Available Tools
```http
GET /tools
Authorization: Bearer {token}
```

#### Get Tool Details
```http
GET /tools/{tool_name}
Authorization: Bearer {token}
```

### Billing

#### Get Subscription Plans
```http
GET /billing/plans
```

#### Get Current Subscription
```http
GET /billing/current
Authorization: Bearer {token}
```

#### Create Checkout Session
```http
POST /billing/create-checkout-session
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "plan": "basic",
  "billing_cycle": "monthly"
}
```

#### Get Usage Statistics
```http
GET /billing/usage
Authorization: Bearer {token}
```

## WebSocket API

### Real-time Updates

Connect to WebSocket for real-time updates:
```
ws://localhost:8000/ws/{token}
```

### Message Types

#### Task Updates
```json
{
  "type": "task_update",
  "data": {
    "task_id": "uuid",
    "status": "running",
    "progress": 50
  }
}
```

#### Agent Messages
```json
{
  "type": "agent_message",
  "data": {
    "conversation_id": "uuid",
    "message": {
      "content": "string",
      "role": "assistant"
    }
  }
}
```

## Rate Limiting

API requests are rate-limited based on your subscription plan:

| Plan | Requests per minute |
|------|-------------------|
| Free | 60 |
| Basic | 600 |
| Pro | 6000 |
| Enterprise | Unlimited |

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640995200
```

## SDKs and Libraries

### Python SDK
```bash
pip install cogniverve-python
```

```python
from cogniverve import CogniVerveClient

client = CogniVerveClient(api_key="your_token")
agents = client.agents.list()
```

### JavaScript SDK
```bash
npm install cogniverve-js
```

```javascript
import { CogniVerveClient } from 'cogniverve-js';

const client = new CogniVerveClient({ apiKey: 'your_token' });
const agents = await client.agents.list();
```

## Examples

### Creating and Running an Agent

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'your_username',
    'password': 'your_password'
})
token = response.json()['data']['access_token']

headers = {'Authorization': f'Bearer {token}'}

# Create agent
agent_data = {
    'name': 'Research Assistant',
    'description': 'Helps with research tasks',
    'instructions': 'You are a helpful research assistant...',
    'model': 'gpt-3.5-turbo',
    'tools': ['web_search', 'text_processor']
}

response = requests.post(
    'http://localhost:8000/api/v1/agents',
    json=agent_data,
    headers=headers
)
agent = response.json()['data']

# Create conversation
conv_data = {
    'title': 'Research Session',
    'agent_id': agent['id']
}

response = requests.post(
    'http://localhost:8000/api/v1/conversations',
    json=conv_data,
    headers=headers
)
conversation = response.json()['data']

# Send message
message_data = {
    'content': 'Research the latest AI trends',
    'role': 'user'
}

response = requests.post(
    f'http://localhost:8000/api/v1/conversations/{conversation["id"]}/messages',
    json=message_data,
    headers=headers
)
```

## Webhooks

### Setting Up Webhooks

Configure webhooks to receive real-time notifications:

```http
POST /webhooks
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["task.completed", "agent.created"],
  "secret": "your_webhook_secret"
}
```

### Webhook Events

#### Task Completed
```json
{
  "event": "task.completed",
  "data": {
    "task_id": "uuid",
    "status": "completed",
    "result": {}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Verifying Webhooks

Verify webhook signatures using HMAC-SHA256:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## Pagination

Large result sets are paginated:

```http
GET /agents?skip=20&limit=10
```

**Response:**
```json
{
  "data": {
    "agents": [...],
    "total": 100,
    "skip": 20,
    "limit": 10,
    "has_more": true
  }
}
```

## Filtering and Sorting

### Filtering
```http
GET /tasks?status=completed&agent_id=uuid
```

### Sorting
```http
GET /agents?sort=created_at&order=desc
```

## API Versioning

The API uses URL versioning:
- Current version: `v1`
- Future versions: `v2`, `v3`, etc.

Deprecated versions will be supported for at least 12 months after replacement.

## Support

For API support:
- Email: api-support@cogniverve.ai
- Documentation: https://docs.cogniverve.ai
- Status Page: https://status.cogniverve.ai

