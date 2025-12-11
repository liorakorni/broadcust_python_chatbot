# AWS Lambda Deployment with Vertex AI

This guide shows how to deploy your Lambda functions on AWS while calling Google Cloud Vertex AI for image generation.

## Why This Works

**AWS Lambda can call any external API**, including Google Cloud services. The Lambda function makes HTTPS requests to Vertex AI's API endpoints using Google's service account credentials.

Think of it as: AWS Lambda → (Internet) → Google Cloud Vertex AI

## Setup Steps

### 1. Get Google Cloud Service Account Key

First, set up Vertex AI and download the service account JSON:

```bash
# Follow VERTEX_AI_SETUP.md to:
# 1. Create GCP project
# 2. Enable Vertex AI API
# 3. Create service account
# 4. Download JSON key

# This will create a file named: vertex-ai-key.json
```

### 2. Add Service Account Key to Your Project

```bash
# Place the JSON file in your project root
cp ~/Downloads/vertex-ai-key-*.json ./vertex-ai-key.json

# Add to .gitignore to avoid committing secrets
echo "vertex-ai-key.json" >> .gitignore
```

### 3. Update Configuration Files

#### a. Update `serverless.yml`

Replace `YOUR_GCP_PROJECT_ID` with your actual GCP project ID:

```yaml
environment:
  GCP_PROJECT_ID: "my-actual-project-123"  # Your real project ID
  GCP_REGION: "us-central1"
  GOOGLE_APPLICATION_CREDENTIALS: "/var/task/vertex-ai-key.json"
```

#### b. Update `Dockerfile`

Uncomment the line to copy the service account key:

```dockerfile
# Copy Google Cloud service account key (create this file after GCP setup)
COPY vertex-ai-key.json ${LAMBDA_TASK_ROOT}/vertex-ai-key.json
```

Change to:

```dockerfile
# Copy Google Cloud service account key
COPY vertex-ai-key.json ${LAMBDA_TASK_ROOT}/vertex-ai-key.json
```

### 4. Deploy to AWS

```bash
# Deploy with serverless
serverless deploy

# This will:
# 1. Build Docker image with vertex-ai-key.json included
# 2. Push to AWS ECR
# 3. Create/update Lambda functions
# 4. Set up API Gateway endpoints
```

### 5. Test Your Endpoints

```bash
# Get your API endpoint from serverless deploy output
export API_URL="https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com"

# Test DALL-E (OpenAI) - already working
curl -X POST "$API_URL/generate-image" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cute cat"}'

# Test Imagen 3.0 (Vertex AI)
curl -X POST "$API_URL/generate-image-gemini" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a futuristic cityscape"}'

# Test Nano Banana (Vertex AI with 3D style)
curl -X POST "$API_URL/generate-image-nano-banana" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a person in superhero costume"}'
```

## How Authentication Works

1. **Service Account JSON**: Contains Google Cloud credentials
2. **Included in Docker Image**: The JSON file is copied into the Lambda container
3. **Environment Variable**: `GOOGLE_APPLICATION_CREDENTIALS` points to the JSON file
4. **Vertex AI SDK**: Automatically reads the credentials and authenticates

## Network Flow

```
User Request
    ↓
API Gateway (AWS)
    ↓
Lambda Function (AWS)
    ↓ (HTTPS with GCP credentials)
Google Cloud Vertex AI
    ↓ (Image data response)
Lambda Function (AWS)
    ↓
User (Base64 image)
```

## Security Best Practices

### ⚠️ Current Setup (Quick Start)
- Service account key embedded in Docker image
- Simple and works for testing
- **Not recommended for production**

### ✅ Production Setup (Recommended)

Use AWS Secrets Manager to store the GCP credentials:

```bash
# Store credentials in AWS Secrets Manager
aws secretsmanager create-secret \
    --name vertex-ai-credentials \
    --secret-string file://vertex-ai-key.json

# Update Lambda to fetch from Secrets Manager
# (requires code changes to retrieve secret at runtime)
```

## Cost Considerations

### AWS Costs (Your Lambda)
- Lambda execution time: $0.0000166667 per GB-second
- API Gateway requests: $1.00 per million requests
- Data transfer: Free for first 100GB

### Google Cloud Costs (Vertex AI)
- Imagen 3.0: ~$0.04 per image
- Imagen 2: ~$0.02 per image
- No data transfer charges for API calls

**Example:** 1,000 images/day = $20-40/day in GCP costs

## Monitoring

### Check Lambda Logs
```bash
# View logs
serverless logs -f gemini_image_generator -t

# Look for:
# ✅ "Vertex AI initialized with project: your-project-id"
# ✅ "Generated image with Vertex AI Imagen successfully"
# ❌ "Warning: Vertex AI initialization failed"
```

### Check CloudWatch
1. Go to AWS CloudWatch Console
2. Select Log Groups → `/aws/lambda/python-chatbot-api-*`
3. Look for Vertex AI initialization messages

## Troubleshooting

### Error: "Could not automatically determine credentials"
**Solution:** Ensure `vertex-ai-key.json` is copied in Dockerfile and uncommented

### Error: "Permission denied"
**Solution:** Check service account has `roles/aiplatform.user` in GCP

### Error: "Project not found"
**Solution:** Verify `GCP_PROJECT_ID` in `serverless.yml` matches your GCP project

### Lambda timeout
**Solution:** Increase timeout in `serverless.yml` (already set to 180s)

## Alternative: AWS Secrets Manager (Production)

For production deployments, store credentials securely:

1. Upload to Secrets Manager
2. Grant Lambda IAM role access to the secret
3. Fetch credentials at runtime
4. Initialize Vertex AI with fetched credentials

This keeps credentials out of your Docker image.

## Quick Checklist

- [ ] Created GCP project and enabled Vertex AI API
- [ ] Created service account with Vertex AI User role
- [ ] Downloaded `vertex-ai-key.json`
- [ ] Placed JSON file in project root
- [ ] Updated `serverless.yml` with GCP project ID
- [ ] Uncommented COPY line in `Dockerfile`
- [ ] Added `vertex-ai-key.json` to `.gitignore`
- [ ] Deployed with `serverless deploy`
- [ ] Tested endpoints successfully

You're all set! 🚀

