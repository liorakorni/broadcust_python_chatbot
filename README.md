# Broadcust Python Chatbot API

A comprehensive serverless API providing AI chat capabilities, image generation, user profile management, and system prompt storage using AWS Lambda, API Gateway, and DynamoDB.

## Features

- 🤖 **Multiple AI Chat Models**
  - OpenAI GPT-4o
  - Google Gemini 2.0 Flash
  - Google Gemini 3 Pro Preview (no timeout limits)

- 🎨 **Image Generation**
  - OpenAI DALL-E 3
  - Google Imagen 3.0
  - Nano Banana (3D style)

- 👤 **User Profile Management**
  - Historical tracking with timestamps
  - Query user profile history

- 📝 **System Prompts CRUD**
  - Store and manage reusable AI prompts
  - Full create, read, update, delete operations

## Quick Start

### Prerequisites
- Python 3.10+
- AWS Account
- Serverless Framework
- Docker (for containerized deployment)

### Configuration

1. Configure API keys in `conf.py`:
```python
open_api_api_key = "sk-..."
gemini_api_key = "AIza..."
server_api_key = "your-server-key"
```

2. Set up Google Cloud credentials:
   - Place your `vertex-ai-key.json` in the project root
   - Update GCP project ID in `conf.py`

### Deployment

```bash
serverless deploy
```

After deployment, note the API endpoint URLs and Lambda Function URLs from the output.

## API Endpoints

The API provides 12 endpoints organized into 4 categories:

### Chat (3 endpoints)
- `POST /prompt` - OpenAI GPT-4o chat
- `POST /prompt-gemini` - Gemini 2.0 Flash chat
- `POST [Function URL]` - Gemini 3 Pro chat (no timeout)

### Image Generation (3 endpoints)
- `POST /generate-image` - DALL-E 3
- `POST /generate-image-gemini` - Imagen 3.0
- `POST /generate-image-nano-banana` - Nano Banana style

### User Profiles (2 endpoints)
- `POST /add-user-profile` - Add profile with timestamp
- `GET /get-user-profiles?UserID=xxx` - Get user history

### System Prompts (4 endpoints)
- `GET /system-prompts` - List all prompts
- `GET /system-prompt?name=xxx` - Get specific prompt
- `POST /system-prompt` - Create/update prompt
- `DELETE /system-prompt?name=xxx` - Delete prompt

## 📚 Full API Documentation

**See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete details** including:
- Request/response examples
- Authentication requirements
- Error handling
- Code examples in JavaScript, Python, and cURL

## Quick Examples

### Chat Request
```bash
curl -X POST https://your-api-url/prompt-gemini \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is AI?"}'
```

### Add User Profile (Requires API Key)
```bash
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
```

### Create System Prompt
```bash
curl -X POST https://your-api-url/system-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "name": "greeting",
    "prompt": "You are a helpful assistant"
  }'
```

## Architecture

- **Compute:** AWS Lambda (Python 3.10, Docker containers)
- **API Gateway:** HTTP API with CORS and rate limiting
- **Storage:** DynamoDB (2 tables)
  - User Profiles (composite key: UserID + Timestamp)
  - System Prompts (primary key: name)
- **AI Services:** 
  - OpenAI API (GPT-4o, DALL-E 3)
  - Google Gemini API (2.0 Flash, 3 Pro)
  - Google Vertex AI (Imagen 3.0)

## Security

- **CORS Protection:** Only `broadcust.co.il` and `stg.broadcust.co.il` origins allowed
- **Rate Limiting:** 10 requests/second per IP
- **API Keys:** Optional for browser endpoints, required for server-to-server
- **Environment Variables:** Sensitive data stored in `conf.py` (not in git)

## DynamoDB Tables

### User Profiles Table
- Tracks user profile changes over time
- Composite key allows multiple records per user
- Sorted by timestamp (newest first)

### System Prompts Table
- Stores reusable AI prompts
- Simple key-value structure
- CRUD operations available via API

## Configuration Files

- `serverless.yml` - Infrastructure and function definitions
- `conf.py` - API keys and configuration (not in git)
- `handler.py` - Lambda function handlers
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration

## Monitoring

- **CloudWatch Logs:** All Lambda invocations logged
- **CloudWatch Alarms:** High usage alerts configured
- **Metrics:** Available in AWS Console

## Cost Optimization

- **DynamoDB:** PAY_PER_REQUEST billing (only pay for what you use)
- **Lambda:** Charged per invocation and execution time
- **Rate Limiting:** Prevents excessive usage
- **Container Reuse:** Warm Lambda containers reduce cold starts

## Development Notes

See additional documentation:
- [AWS_LAMBDA_DEPLOYMENT.md](./AWS_LAMBDA_DEPLOYMENT.md) - Deployment guide
- [VERTEX_AI_SETUP.md](./VERTEX_AI_SETUP.md) - Google Cloud setup

## Support

For issues or questions, refer to the API documentation or check CloudWatch logs for error details.
