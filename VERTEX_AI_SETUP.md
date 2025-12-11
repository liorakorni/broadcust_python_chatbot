# Vertex AI Setup Guide

This guide will help you set up Google Cloud Vertex AI for image generation with Imagen.

## Prerequisites

1. Google Cloud Platform (GCP) account
2. GCP project with billing enabled
3. Vertex AI API enabled

## Step-by-Step Setup

### 1. Create/Select a GCP Project

```bash
# List existing projects
gcloud projects list

# Or create a new project
gcloud projects create YOUR_PROJECT_ID --name="Your Project Name"

# Set as active project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable required dependencies
gcloud services enable storage.googleapis.com
gcloud services enable compute.googleapis.com
```

### 3. Create a Service Account for Lambda

```bash
# Create service account
gcloud iam service-accounts create vertex-ai-lambda \
    --display-name="Vertex AI Lambda Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:vertex-ai-lambda@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create vertex-ai-key.json \
    --iam-account=vertex-ai-lambda@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 4. Configure Your Application

#### Option A: Using Environment Variables (Recommended for Lambda)

Update your `serverless.yml` to include GCP credentials:

```yaml
provider:
  name: aws
  runtime: python3.10
  environment:
    GCP_PROJECT_ID: "YOUR_PROJECT_ID"
    GCP_REGION: "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: "/var/task/vertex-ai-key.json"
```

Then add the service account JSON to your deployment package.

#### Option B: Using conf.py (Simpler for testing)

Update `conf.py`:

```python
gcp_project_id = "YOUR_ACTUAL_PROJECT_ID"
gcp_region = "us-central1"  # or your preferred region
```

### 5. Add Service Account JSON to Docker Image

Update your `Dockerfile`:

```dockerfile
# Copy service account credentials (if using file-based auth)
COPY vertex-ai-key.json ${LAMBDA_TASK_ROOT}/
```

**⚠️ Security Note:** For production, use AWS Secrets Manager or AWS Systems Manager Parameter Store to store the service account JSON securely.

### 6. Test Locally

```bash
# Set up application default credentials locally
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/vertex-ai-key.json"
export GCP_PROJECT_ID="YOUR_PROJECT_ID"

# Test import
python -c "import vertexai; vertexai.init(project='YOUR_PROJECT_ID', location='us-central1'); print('Success!')"
```

## Available Imagen Models

- `imagen-3.0-generate-001` - Latest Imagen 3.0 (used in `/generate-image-gemini`)
- `imagegeneration@006` - Imagen 2 (used in `/generate-image-nano-banana`)
- `imagegeneration@005` - Imagen 2 (older version)
- `imagegeneration@002` - Imagen 1

## Pricing

Vertex AI Imagen pricing (as of 2024):
- Imagen 3: ~$0.04 per image
- Imagen 2: ~$0.02 per image

Check current pricing: https://cloud.google.com/vertex-ai/pricing

## Troubleshooting

### Authentication Errors

If you see "Could not automatically determine credentials":

1. Verify service account key is in the correct location
2. Check `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Ensure service account has `roles/aiplatform.user` permission

### Model Not Found

If you see "Model not found":

1. Verify the model name is correct
2. Check that Vertex AI API is enabled
3. Ensure your region supports the model (use `us-central1` for best support)

### Permission Denied

If you see permission errors:

1. Verify your service account has the correct roles
2. Check that billing is enabled on your project
3. Ensure Vertex AI API quota is not exceeded

## Cost Optimization

1. **Use caching**: Store generated images in S3 or CDN
2. **Rate limiting**: Implement request throttling
3. **Monitor usage**: Set up billing alerts in GCP Console
4. **Use appropriate models**: Imagen 2 is cheaper than Imagen 3

## Security Best Practices

1. ✅ Use AWS Secrets Manager for service account keys
2. ✅ Rotate service account keys regularly
3. ✅ Use least privilege IAM roles
4. ✅ Enable VPC Service Controls for Vertex AI
5. ✅ Monitor API usage with Cloud Audit Logs

