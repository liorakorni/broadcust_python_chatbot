# Broadcust Python Chatbot API Documentation

Complete API reference for all available endpoints.

---

## Table of Contents
1. [Chat Endpoints](#chat-endpoints)
2. [Image Generation Endpoints](#image-generation-endpoints)
3. [User Profile Management](#user-profile-management)
4. [System Prompts Management](#system-prompts-management)
5. [Authentication](#authentication)
6. [CORS Configuration](#cors-configuration)

---

## Base URL

After deployment, your API will be available at:
```
https://[api-id].execute-api.us-east-1.amazonaws.com
```

---

## Chat Endpoints

### 1. OpenAI Chat (GPT-4)
**Endpoint:** `POST /prompt`

**Description:** Text-based chatbot using OpenAI's GPT-4o model.

**Headers:**
- `Content-Type: application/json`
- `Origin: https://broadcust.co.il` (or `https://stg.broadcust.co.il`)

**Request Body:**
```json
{
  "question": "What is the capital of France?"
}
```

**Response:**
```json
{
  "statusCode": 200,
  "status": "success",
  "body": "The capital of France is Paris."
}
```

**Authentication:** None (CORS protected)

---

### 2. Gemini Chat (Fast)
**Endpoint:** `POST /prompt-gemini`

**Description:** Text-based chatbot using Google's Gemini 2.0 Flash model.

**Headers:**
- `Content-Type: application/json`
- `Origin: https://broadcust.co.il`

**Request Body:**
```json
{
  "prompt": "Explain quantum computing"
}
```

**Response:**
```json
{
  "statusCode": 200,
  "status": "success",
  "body": "Quantum computing is..."
}
```

**Authentication:** None (CORS protected)

---

### 3. Gemini Pro Chat (Advanced)
**Endpoint:** `POST [Lambda Function URL]`

**Description:** Text-based chatbot using Google's Gemini 3 Pro Preview model. No timeout limits (15 min max).

**Headers:**
- `Content-Type: application/json`
- `Origin: https://broadcust.co.il`

**Request Body:**
```json
{
  "prompt": "Write a detailed legal analysis..."
}
```

**Response:**
```json
{
  "statusCode": 200,
  "status": "success",
  "body": "Detailed response..."
}
```

**Authentication:** None (CORS protected)
**Note:** Uses Lambda Function URL (no API Gateway timeout)

---

## Image Generation Endpoints

### 4. DALL-E 3 Image Generator
**Endpoint:** `POST /generate-image`

**Description:** Generate images using OpenAI's DALL-E 3 model.

**Headers:**
- `Content-Type: application/json`
- `Origin: https://broadcust.co.il`

**Request Body:**
```json
{
  "prompt": "A futuristic city at sunset"
}
```

**Response:**
```json
{
  "statusCode": 200,
  "status": "success",
  "body": {
    "image_url": "https://oaidalleapiprodscus.blob.core.windows.net/...",
    "prompt": "A futuristic city at sunset",
    "model": "dall-e-3"
  }
}
```

**Authentication:** None (CORS protected)

---

### 5. Gemini Imagen Generator
**Endpoint:** `POST /generate-image-gemini`

**Description:** Generate images using Google's Imagen 3.0 model via Vertex AI.

**Headers:**
- `Content-Type: application/json`
- `Origin: https://broadcust.co.il`

**Request Body:**
```json
{
  "prompt": "A peaceful mountain landscape"
}
```

**Response:**
```json
{
  "statusCode": 200,
  "status": "success",
  "body": {
    "image_data": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "prompt": "A peaceful mountain landscape",
    "model": "imagen-3.0-vertex-ai"
  }
}
```

**Authentication:** None (CORS protected)
**Note:** Returns base64-encoded image

---

### 6. Nano Banana Image Generator
**Endpoint:** `POST /generate-image-nano-banana`

**Description:** Generate images with 3D render style using Vertex AI Imagen.

**Headers:**
- `Content-Type: application/json`
- `Origin: https://broadcust.co.il`

**Request Body:**
```json
{
  "prompt": "A cute robot"
}
```

**Response:**
```json
{
  "statusCode": 200,
  "status": "success",
  "body": {
    "image_data": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "prompt": "A cute robot",
    "enhanced_prompt": "A cute robot, high quality, detailed...",
    "model": "imagen-vertex-ai-nano-banana"
  }
}
```

**Authentication:** None (CORS protected)
**Note:** Automatically enhances prompt for 3D style

---

## User Profile Management

### 7. Add User Profile
**Endpoint:** `POST /add-user-profile`

**Description:** Add a new user profile record with timestamp. Creates new record each time (no overwrite).

**Headers:**
- `Content-Type: application/json`
- `x-api-key: facb80df-8f14-42c7-b87a-37a05ae926ee`

**Request Body:**
```json
{
  "UserID": "user123",
  "Mobile": "+1-555-123-4567",
  "Email": "user@example.com",
  "RawBizChar": "some-value",
  "OptBizChar": "another-value"
}
```

**Response:**
```json
{
  "statusCode": 200,
  "status": "success",
  "message": "User profile added successfully",
  "userId": "user123",
  "timestamp": "2025-12-11T15:30:45.123456Z"
}
```

**Authentication:** Required (`server_api_key`)
**Note:** Timestamp is auto-generated server-side

---

### 8. Get User Profile History
**Endpoint:** `GET /get-user-profiles?UserID=user123`

**Description:** Retrieve all profile records for a specific user, sorted newest first.

**Headers:**
- `x-api-key: facb80df-8f14-42c7-b87a-37a05ae926ee`

**Query Parameters:**
- `UserID` (required): User identifier

**Response:**
```json
{
  "statusCode": 200,
  "status": "success",
  "userId": "user123",
  "count": 3,
  "records": [
    {
      "UserID": "user123",
      "Timestamp": "2025-12-11T15:30:45Z",
      "Mobile": "+1-555-123-4567",
      "Email": "user@example.com",
      "RawBizChar": "value1",
      "OptBizChar": "value2"
    },
    {
      "UserID": "user123",
      "Timestamp": "2025-12-11T14:20:30Z",
      "Mobile": "+1-555-987-6543",
      "Email": "old@example.com",
      "RawBizChar": "oldvalue1",
      "OptBizChar": "oldvalue2"
    }
  ]
}
```

**Authentication:** Required (`server_api_key`)

---

## System Prompts Management

### 9. List All System Prompts
**Endpoint:** `GET /system-prompts`

**Description:** Retrieve all system prompts stored in the database.

**Headers:**
- `Origin: https://broadcust.co.il`

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "prompts": [
    {
      "name": "greeting",
      "prompt": "You are a helpful assistant specialized in..."
    },
    {
      "name": "legal",
      "prompt": "You are a legal expert who..."
    }
  ]
}
```

**Authentication:** None (CORS protected)

---

### 10. Get Specific System Prompt
**Endpoint:** `GET /system-prompt?name=greeting`

**Description:** Retrieve a specific system prompt by name.

**Headers:**
- `Origin: https://broadcust.co.il`

**Query Parameters:**
- `name` (required): Prompt identifier

**Response:**
```json
{
  "status": "success",
  "prompt": {
    "name": "greeting",
    "prompt": "You are a helpful assistant..."
  }
}
```

**404 Response (Not Found):**
```json
{
  "error": "System prompt 'greeting' not found"
}
```

**Authentication:** None (CORS protected)

---

### 11. Create/Update System Prompt
**Endpoint:** `POST /system-prompt`

**Description:** Create a new system prompt or update an existing one.

**Headers:**
- `Content-Type: application/json`
- `Origin: https://broadcust.co.il`

**Request Body:**
```json
{
  "name": "greeting",
  "prompt": "You are a helpful assistant specialized in providing clear and concise answers."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "System prompt saved successfully",
  "name": "greeting"
}
```

**Authentication:** None (CORS protected)
**Note:** If prompt with same name exists, it will be overwritten

---

### 12. Delete System Prompt
**Endpoint:** `DELETE /system-prompt?name=greeting`

**Description:** Delete a specific system prompt by name.

**Headers:**
- `Origin: https://broadcust.co.il`

**Query Parameters:**
- `name` (required): Prompt identifier

**Response:**
```json
{
  "status": "success",
  "message": "System prompt deleted successfully",
  "name": "greeting"
}
```

**Authentication:** None (CORS protected)

---

## Authentication

### API Key Types

The API uses two separate API keys configured in `conf.py`:

#### 1. Browser Endpoints Key (`api_secret_key`)
- **Currently:** Disabled (empty string)
- **Used by:** `gemini_chat`, `gemini_pro_chat`
- **Optional:** Only validates if configured
- **Header:** `x-api-key: [your-key]`

#### 2. Server-to-Server Key (`server_api_key`)
- **Value:** `facb80df-8f14-42c7-b87a-37a05ae926ee`
- **Used by:** `add_user_profile`, `get_user_profiles`
- **Required:** Always validates
- **Header:** `x-api-key: facb80df-8f14-42c7-b87a-37a05ae926ee`

### Endpoints by Authentication

**No Authentication Required:**
- `/prompt` (OpenAI Chat)
- `/prompt-gemini` (Gemini Chat)
- `/generate-image` (DALL-E)
- `/generate-image-gemini` (Imagen)
- `/generate-image-nano-banana` (Nano Banana)
- `/system-prompts` (List)
- `/system-prompt` (Get/Create/Update/Delete)
- Gemini Pro Chat (Function URL)

**Authentication Required:**
- `/add-user-profile`
- `/get-user-profiles`

---

## CORS Configuration

### Allowed Origins
- `https://broadcust.co.il`
- `https://stg.broadcust.co.il`

### API Gateway Endpoints
- CORS: Enabled globally
- Rate Limiting: 10 requests/second per IP
- Burst Limit: 20 requests

### Lambda Function URL Endpoints
- CORS: Configured at function level
- Allowed Methods: POST, OPTIONS
- Credentials: Allowed

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Missing required fields",
  "missing_fields": ["UserID", "Email"]
}
```

### 403 Forbidden
```json
{
  "error": "Invalid or missing API key"
}
```

or

```json
{
  "error": "Invalid Origin"
}
```

### 404 Not Found
```json
{
  "error": "System prompt 'xyz' not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to process request",
  "details": "Error details here..."
}
```

---

## Rate Limiting

All API Gateway endpoints are rate-limited:
- **Rate Limit:** 10 requests per second per IP address
- **Burst Limit:** 20 requests (burst capacity)
- **Scope:** Per client IP address

---

## Environment Variables

Configure these in `conf.py`:

```python
# OpenAI Configuration
open_api_api_key = "sk-..."

# Google Gemini Configuration
gemini_api_key = "AIza..."

# API Keys
api_secret_key = ""  # Optional for browser endpoints
server_api_key = "facb80df-..."  # Required for server endpoints

# Google Cloud Platform
gcp_project_id = "gen-lang-client-0517916478"
gcp_region = "us-central1"
```

---

## DynamoDB Tables

### User Profiles Table
- **Name:** `python-chatbot-api-{stage}-user-profiles`
- **Partition Key:** `UserID` (String)
- **Sort Key:** `Timestamp` (String)
- **Purpose:** Store user profile history

### System Prompts Table
- **Name:** `python-chatbot-api-{stage}-system-prompts`
- **Primary Key:** `name` (String)
- **Purpose:** Store reusable system prompts

---

## Deployment

```bash
# Deploy all endpoints
serverless deploy

# Deploy specific function
serverless deploy function -f chatbot
```

---

## Examples

### JavaScript (Browser)
```javascript
// Chat example
fetch('https://your-api-url/prompt-gemini', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: "What is AI?"
  })
})
.then(response => response.json())
.then(data => console.log(data.body));

// System prompt example
fetch('https://your-api-url/system-prompt', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "assistant",
    prompt: "You are a helpful AI assistant"
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Python
```python
import requests

# Chat example
response = requests.post(
    'https://your-api-url/prompt-gemini',
    json={'prompt': 'What is AI?'}
)
print(response.json())

# User profile example (requires API key)
response = requests.post(
    'https://your-api-url/add-user-profile',
    headers={'x-api-key': 'facb80df-8f14-42c7-b87a-37a05ae926ee'},
    json={
        'UserID': 'user123',
        'Mobile': '+1-555-123-4567',
        'Email': 'user@example.com',
        'RawBizChar': 'value1',
        'OptBizChar': 'value2'
    }
)
print(response.json())
```

### cURL
```bash
# Chat
curl -X POST https://your-api-url/prompt \
  -H "Content-Type: application/json" \
  -d '{"question":"What is AI?"}'

# Add user profile (with API key)
curl -X POST https://your-api-url/add-user-profile \
  -H "Content-Type: application/json" \
  -H "x-api-key: facb80df-8f14-42c7-b87a-37a05ae926ee" \
  -d '{
    "UserID": "user123",
    "Mobile": "+1-555-123-4567",
    "Email": "user@example.com",
    "RawBizChar": "value1",
    "OptBizChar": "value2"
  }'

# Get system prompt
curl "https://your-api-url/system-prompt?name=greeting"
```

---

## Support

For issues or questions, please refer to the project repository or contact the development team.

