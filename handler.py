import json
import os
import re
import boto3
from datetime import datetime
from langchain_openai import ChatOpenAI
from openai import OpenAI
import google.generativeai as genai
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai

from conf import open_api_api_key, gemini_api_key, gcp_project_id, gcp_region, api_secret_key, server_api_key

os.environ["OPENAI_API_KEY"] = open_api_api_key

OpenAIClient = OpenAI(
    api_key=open_api_api_key
)

# Configure Gemini
genai.configure(api_key=gemini_api_key)

# Initialize Vertex AI
try:
    # Use environment variables first, then fall back to conf.py
    GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", gcp_project_id)
    GCP_REGION = os.environ.get("GCP_REGION", gcp_region)
    
    # For AWS Lambda, explicitly set credentials path
    # This tells Google Cloud SDK where to find the service account key
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", 
                                     "/var/task/vertex-ai-key.json")
    
    if os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        print(f"Using GCP credentials from: {credentials_path}")
    else:
        print(f"Warning: GCP credentials file not found at {credentials_path}")
    
    # Initialize Vertex AI - will use the credentials file
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    print(f"Vertex AI initialized with project: {GCP_PROJECT_ID}, region: {GCP_REGION}")
except Exception as e:
    print(f"Warning: Vertex AI initialization failed: {e}")

llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o", streaming=False)

def chatbot(event, context):
    """Original text-based chatbot - clean and simple"""
    print('event is : ', json.dumps(event))

    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None)
    if event_origin is not None and not event_origin.endswith("broadcust.co.il"):
        # If the Origin header is not from the allowed domain, deny the request
        response = {
            "statusCode": 403,
            'error': "Invalid Origin"
        }
        print('origin is not allowed: ', event_origin)

        return response

    event_body = event.get("body", None)

    if event_body is not None:
        event_body_json_load = json.loads(event_body)
        question = event_body_json_load.get("question", None)
    else:
        question = event.get("question", None)

    msg = llm.invoke(question)
    print('msg.content: ', msg.content)

    response = {
        "statusCode": 200,
        'status': "success",
        "body": msg.content,
        "headers": {
            'Access-Control-Allow-Origin': 'https://broadcust.co.il',
        }
    }
    return response

def image_generator(event, context):
    """Dedicated image generation API endpoint"""
    print('image generation event: ', json.dumps(event))

    # Same origin validation as text chatbot
    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None)
    if event_origin is not None and not event_origin.endswith("broadcust.co.il"):
        response = {
            "statusCode": 403,
            'error': "Invalid Origin"
        }
        print('origin is not allowed: ', event_origin)
        return response

    # Extract prompt from request
    event_body = event.get("body", None)
    if event_body is not None:
        event_body_json_load = json.loads(event_body)
        prompt = event_body_json_load.get("prompt", None)
    else:
        prompt = event.get("prompt", None)

    if not prompt:
        return {
            "statusCode": 400,
            "status": "error",
            "body": json.dumps({"error": "No prompt provided"}),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }

    try:
        # Generate image using DALL-E 3
        print(f'Generating image for prompt: {prompt}')
        response_dalle = OpenAIClient.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response_dalle.data[0].url
        print(f'Generated image URL: {image_url}')

        response = {
            "statusCode": 200,
            "status": "success",
            "body": json.dumps({
                "image_url": image_url,
                "prompt": prompt,
                "model": "dall-e-3"
            }),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        response = {
            "statusCode": 500,
            "status": "error",
            "body": json.dumps({"error": f"Failed to generate image: {str(e)}"}),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }

    return response

def gemini_image_generator(event, context):
    """Image generation using Google Gemini Imagen 3.0"""
    print('gemini image generation event: ', json.dumps(event))

    # Same origin validation
    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None)
    if event_origin is not None and not event_origin.endswith("broadcust.co.il"):
        response = {
            "statusCode": 403,
            'error': "Invalid Origin"
        }
        print('origin is not allowed: ', event_origin)
        return response

    # Extract prompt from request
    event_body = event.get("body", None)
    if event_body is not None:
        event_body_json_load = json.loads(event_body)
        prompt = event_body_json_load.get("prompt", None)
    else:
        prompt = event.get("prompt", None)

    if not prompt:
        return {
            "statusCode": 400,
            "status": "error",
            "body": json.dumps({"error": "No prompt provided"}),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }

    try:
        # Generate image using Vertex AI Imagen
        print(f'Generating image with Vertex AI Imagen for prompt: {prompt}')

        # Use Imagen 3 model through Vertex AI
        imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        # Generate image
        images = imagen_model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )

        # Get the generated image and convert to base64
        import base64
        import io
        
        # images[0] is an Image object with _pil_image attribute
        generated_image = images[0]
        
        img_byte_arr = io.BytesIO()
        generated_image._pil_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        image_base64 = base64.b64encode(img_byte_arr).decode('utf-8')

        print(f'Generated image with Vertex AI Imagen successfully')

        response = {
            "statusCode": 200,
            "status": "success",
            "body": json.dumps({
                "image_data": f"data:image/png;base64,{image_base64}",
                "prompt": prompt,
                "model": "imagen-3.0-vertex-ai"
            }),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }

    except Exception as e:
        print(f"Error generating image with Gemini: {str(e)}")
        response = {
            "statusCode": 500,
            "status": "error",
            "body": json.dumps({"error": f"Failed to generate image: {str(e)}"}),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }

    return response

def nano_banana_generator(event, context):
    """Image generation using Google Gemini 2.5 Flash (Nano Banana model)"""
    print('nano banana image generation event: ', json.dumps(event))

    # Same origin validation
    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None)
    if event_origin is not None and not event_origin.endswith("broadcust.co.il"):
        response = {
            "statusCode": 403,
            'error': "Invalid Origin"
        }
        print('origin is not allowed: ', event_origin)
        return response

    # Extract prompt from request
    event_body = event.get("body", None)
    if event_body is not None:
        event_body_json_load = json.loads(event_body)
        prompt = event_body_json_load.get("prompt", None)
    else:
        prompt = event.get("prompt", None)

    if not prompt:
        return {
            "statusCode": 400,
            "status": "error",
            "body": json.dumps({"error": "No prompt provided"}),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }

    try:
        # Generate image using Vertex AI Imagen (Nano Banana style)
        print(f'Generating Nano Banana style image with Vertex AI for prompt: {prompt}')

        # Use Imagen model through Vertex AI
        # Note: "Nano Banana" is a marketing name, actual model is Imagen
        imagen_model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Add style modifier for more realistic/3D figurine style (Nano Banana aesthetic)
        enhanced_prompt = f"{prompt}, high quality, detailed, professional 3D render style"
        
        # Generate image
        images = imagen_model.generate_images(
            prompt=enhanced_prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )

        # Get the generated image and convert to base64
        import base64
        import io
        
        generated_image = images[0]
        
        img_byte_arr = io.BytesIO()
        generated_image._pil_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        image_base64 = base64.b64encode(img_byte_arr).decode('utf-8')

        print(f'Generated Nano Banana style image with Vertex AI successfully')

        response = {
            "statusCode": 200,
            "status": "success",
            "body": json.dumps({
                "image_data": f"data:image/png;base64,{image_base64}",
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "model": "imagen-vertex-ai-nano-banana"
            }),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }

    except Exception as e:
        print(f"Error generating image with Nano Banana: {str(e)}")
        response = {
            "statusCode": 500,
            "status": "error",
            "body": json.dumps({"error": f"Failed to generate image: {str(e)}"}),
            "headers": {
                'Access-Control-Allow-Origin': 'https://broadcust.co.il',
                'Content-Type': 'application/json'
            }
        }

    return response

def gemini_chat(event, context):
    """Gemini-based text chatbot"""
    print('gemini chat event: ', json.dumps(event))

    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None)
    
    # Validate API Key (optional - only if configured in conf.py)
    if api_secret_key:  # Only validate if API key is configured
        provided_api_key = event_headers.get("x-api-key") if event_headers else None
        if not provided_api_key or provided_api_key != api_secret_key:
            print('Invalid or missing API key')
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Invalid or missing API key"}),
                "headers": {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                }
            }
    
    # Validate origin and set appropriate CORS header
    allowed_origin = 'https://broadcust.co.il'  # default
    if event_origin is not None:
        if event_origin.endswith("broadcust.co.il"):
            allowed_origin = event_origin  # Use the actual origin (stg, prod, etc.)
        else:
            # If the Origin header is not from the allowed domain, deny the request
            response = {
                "statusCode": 403,
                'error': "Invalid Origin"
            }
            print('origin is not allowed: ', event_origin)
            return response

    event_body = event.get("body", None)

    if event_body is not None:
        event_body_json_load = json.loads(event_body)
        prompt = event_body_json_load.get("prompt", None)
    else:
        prompt = event.get("prompt", None)

    if not prompt:
        return {
            "statusCode": 400,
            "status": "error",
            "body": json.dumps({"error": "No prompt provided"}),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }

    try:
        # Use Gemini for chat
        print(f'Processing prompt with Gemini: {prompt}')
        
        # List available models for debugging
        try:
            available_models = [m.name for m in genai.list_models()]
            print(f'Available models: {available_models[:10]}')  # Print first 10
        except Exception as e:
            print(f'Could not list models: {e}')
        
        # Configure generation settings for longer responses
        generation_config = {
            "max_output_tokens": 8192,  # Maximum tokens for output
            "temperature": 0.3,  # Lower temperature for more consistent, factual responses
        }
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response_gemini = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Check if response was blocked or incomplete
        print(f'Gemini finish_reason: {response_gemini.candidates[0].finish_reason}')
        print(f'Gemini safety_ratings: {response_gemini.candidates[0].safety_ratings}')
        
        # Get the full response text
        response_text = response_gemini.text
        print(f'Gemini response length: {len(response_text)} characters')
        print(f'Gemini response preview: {response_text[:200]}...')

        response = {
            "statusCode": 200,
            'status': "success",
            "body": response_text,
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'text/plain; charset=utf-8'
            }
        }
    except Exception as e:
        print(f"Error with Gemini chat: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        response = {
            "statusCode": 500,
            "status": "error",
            "body": json.dumps({"error": f"Failed to process chat: {str(e)}"}),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }

    return response

def gemini_pro_chat(event, context):
    """Gemini Pro (most advanced) - Uses Lambda Function URL for longer timeout"""
    print('gemini pro chat event: ', json.dumps(event))

    event_headers = event.get("headers", None)
    
    # Validate API Key (optional - only if configured in conf.py)
    if api_secret_key:  # Only validate if API key is configured
        provided_api_key = event_headers.get("x-api-key") if event_headers else None
        if not provided_api_key or provided_api_key != api_secret_key:
            print('Invalid or missing API key')
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Invalid or missing API key"}),
                "headers": {
                    # CORS handled by Lambda Function URL config (serverless.yml)
                    'Content-Type': 'application/json'
                }
            }
    
    # Note: Origin validation is handled by Lambda Function URL CORS config in serverless.yml
    # No need to validate origin in code - AWS does it based on allowedOrigins

    event_body = event.get("body", None)

    if event_body is not None:
        event_body_json_load = json.loads(event_body)
        prompt = event_body_json_load.get("prompt", None)
    else:
        prompt = event.get("prompt", None)

    if not prompt:
        return {
            "statusCode": 400,
            "status": "error",
            "body": json.dumps({"error": "No prompt provided"}),
            "headers": {
                # CORS handled by Lambda Function URL config
                'Content-Type': 'application/json'
            }
        }

    try:
        # Use Gemini Pro (most advanced model)
        print(f'Processing prompt with Gemini Pro: {prompt}')
        
        # Configure generation settings for longer responses
        generation_config = {
            "max_output_tokens": 8192,  # Maximum tokens for output
            "temperature": 0.3,  # Lower temperature for more consistent, factual responses
        }
        
        # Try Gemini 3 Pro Preview (if available)
        model = genai.GenerativeModel('gemini-3-pro-preview')
        response_gemini = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Check if response was blocked or incomplete
        print(f'Gemini Pro finish_reason: {response_gemini.candidates[0].finish_reason}')
        print(f'Gemini Pro safety_ratings: {response_gemini.candidates[0].safety_ratings}')
        
        # Get the full response text
        response_text = response_gemini.text
        print(f'Gemini Pro response length: {len(response_text)} characters')
        print(f'Gemini Pro response preview: {response_text[:200]}...')

        response = {
            "statusCode": 200,
            'status': "success",
            "body": response_text,
            "headers": {
                # CORS is handled by Lambda Function URL config (serverless.yml)
                # Don't set Access-Control-Allow-Origin here to avoid conflicts
                'Content-Type': 'text/plain; charset=utf-8'
            }
        }
    except Exception as e:
        print(f"Error with Gemini Pro chat: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        response = {
            "statusCode": 500,
            "status": "error",
            "body": json.dumps({"error": f"Failed to process chat: {str(e)}"}),
            "headers": {
                # CORS is handled by Lambda Function URL config (serverless.yml)
                'Content-Type': 'application/json'
            }
        }

    return response

def add_user_profile(event, context):
    """Add user profile to DynamoDB - Server-to-server endpoint with API key auth"""
    print('add user profile event: ', json.dumps(event))

    event_headers = event.get("headers", None)
    
    # Validate Server API Key (required for this endpoint)
    if not server_api_key or server_api_key == "your-secret-key-here":
        print('ERROR: server_api_key not configured in conf.py')
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Server configuration error"}),
            "headers": {'Content-Type': 'application/json'}
        }
    
    provided_api_key = event_headers.get("x-api-key") if event_headers else None
    if not provided_api_key or provided_api_key != server_api_key:
        print('Invalid or missing API key')
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Invalid or missing API key"}),
            "headers": {'Content-Type': 'application/json'}
        }

    # Parse request body
    event_body = event.get("body", None)
    if event_body is not None:
        try:
            body_data = json.loads(event_body)
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid JSON in request body"}),
                "headers": {'Content-Type': 'application/json'}
            }
    else:
        body_data = event

    # Validate required fields
    required_fields = ['UserID', 'Mobile', 'Email', 'RawBizChar', 'OptBizChar']
    missing_fields = [field for field in required_fields if not body_data.get(field)]
    
    if missing_fields:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }),
            "headers": {'Content-Type': 'application/json'}
        }

    # Extract and validate fields
    user_id = body_data.get('UserID').strip()
    mobile = body_data.get('Mobile').strip()
    email = body_data.get('Email').strip()
    raw_biz_char = body_data.get('RawBizChar').strip()
    opt_biz_char = body_data.get('OptBizChar').strip()

    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid email format",
                "field": "Email"
            }),
            "headers": {'Content-Type': 'application/json'}
        }

    # Validate mobile format (basic validation - must contain digits)
    mobile_pattern = r'^[\d\s\-\+\(\)]+$'
    if not re.match(mobile_pattern, mobile) or len(re.sub(r'\D', '', mobile)) < 9:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid mobile format - must contain at least 9 digits",
                "field": "Mobile"
            }),
            "headers": {'Content-Type': 'application/json'}
        }

    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('USER_PROFILES_TABLE')
        
        if not table_name:
            print('ERROR: USER_PROFILES_TABLE environment variable not set')
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Server configuration error"}),
                "headers": {'Content-Type': 'application/json'}
            }
        
        table = dynamodb.Table(table_name)
        
        # Generate timestamp (ISO 8601 format with 'Z' suffix for UTC)
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Put item to DynamoDB (creates new record with timestamp, no overwrite)
        table.put_item(
            Item={
                'UserID': user_id,
                'Timestamp': timestamp,
                'Mobile': mobile,
                'Email': email,
                'RawBizChar': raw_biz_char,
                'OptBizChar': opt_biz_char
            }
        )
        
        print(f'Successfully added user profile for UserID: {user_id} at {timestamp}')
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "message": "User profile added successfully",
                "userId": user_id,
                "timestamp": timestamp
            }),
            "headers": {'Content-Type': 'application/json'}
        }
        
    except Exception as e:
        print(f"Error storing user profile: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to store user profile",
                "details": str(e)
            }),
            "headers": {'Content-Type': 'application/json'}
        }

def get_user_profiles(event, context):
    """Query all profile records for a specific user - Server-to-server endpoint with API key auth"""
    print('get user profiles event: ', json.dumps(event))

    event_headers = event.get("headers", None)
    
    # Validate Server API Key (required for this endpoint)
    if not server_api_key or server_api_key == "your-secret-key-here":
        print('ERROR: server_api_key not configured in conf.py')
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Server configuration error"}),
            "headers": {'Content-Type': 'application/json'}
        }
    
    provided_api_key = event_headers.get("x-api-key") if event_headers else None
    if not provided_api_key or provided_api_key != server_api_key:
        print('Invalid or missing API key')
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Invalid or missing API key"}),
            "headers": {'Content-Type': 'application/json'}
        }

    # Extract UserID from query string parameters
    query_params = event.get("queryStringParameters", {})
    if not query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing query parameters"}),
            "headers": {'Content-Type': 'application/json'}
        }
    
    user_id = query_params.get("UserID")
    if not user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required parameter: UserID"}),
            "headers": {'Content-Type': 'application/json'}
        }

    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('USER_PROFILES_TABLE')
        
        if not table_name:
            print('ERROR: USER_PROFILES_TABLE environment variable not set')
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Server configuration error"}),
                "headers": {'Content-Type': 'application/json'}
            }
        
        table = dynamodb.Table(table_name)
        
        # Query DynamoDB for all records with the given UserID
        # ScanIndexForward=False returns items in descending order (newest first)
        from boto3.dynamodb.conditions import Key
        
        response = table.query(
            KeyConditionExpression=Key('UserID').eq(user_id),
            ScanIndexForward=False  # Descending order (newest first)
        )
        
        items = response.get('Items', [])
        print(f'Found {len(items)} records for UserID: {user_id}')
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "userId": user_id,
                "count": len(items),
                "records": items
            }, default=str),  # default=str to handle datetime serialization
            "headers": {'Content-Type': 'application/json'}
        }
        
    except Exception as e:
        print(f"Error querying user profiles: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to query user profiles",
                "details": str(e)
            }),
            "headers": {'Content-Type': 'application/json'}
        }

def list_system_prompts(event, context):
    """List all system prompts - No authentication, CORS only"""
    print('list system prompts event: ', json.dumps(event))

    # Validate origin for CORS
    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None) if event_headers else None
    
    allowed_origin = 'https://broadcust.co.il'  # default
    if event_origin is not None and event_origin.endswith("broadcust.co.il"):
        allowed_origin = event_origin
    elif event_origin is not None:
        # Invalid origin
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Invalid Origin"}),
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
        }

    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('SYSTEM_PROMPTS_TABLE')
        
        if not table_name:
            print('ERROR: SYSTEM_PROMPTS_TABLE environment variable not set')
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Server configuration error"}),
                "headers": {'Content-Type': 'application/json'}
            }
        
        table = dynamodb.Table(table_name)
        
        # Scan table to get all prompts
        response = table.scan()
        items = response.get('Items', [])
        
        print(f'Found {len(items)} system prompts')
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "count": len(items),
                "prompts": items
            }, default=str),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        print(f"Error listing system prompts: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to list system prompts",
                "details": str(e)
            }),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }

def get_system_prompt(event, context):
    """Get a specific system prompt by name - No authentication, CORS only"""
    print('get system prompt event: ', json.dumps(event))

    # Validate origin for CORS
    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None) if event_headers else None
    
    allowed_origin = 'https://broadcust.co.il'  # default
    if event_origin is not None and event_origin.endswith("broadcust.co.il"):
        allowed_origin = event_origin
    elif event_origin is not None:
        # Invalid origin
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Invalid Origin"}),
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
        }

    # Extract name from query string parameters
    query_params = event.get("queryStringParameters", {})
    if not query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing query parameters"}),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }
    
    name = query_params.get("name")
    if not name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required parameter: name"}),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }

    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('SYSTEM_PROMPTS_TABLE')
        
        if not table_name:
            print('ERROR: SYSTEM_PROMPTS_TABLE environment variable not set')
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Server configuration error"}),
                "headers": {'Content-Type': 'application/json'}
            }
        
        table = dynamodb.Table(table_name)
        
        # Get item from DynamoDB
        response = table.get_item(Key={'name': name})
        
        if 'Item' not in response:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": f"System prompt '{name}' not found"}),
                "headers": {
                    'Access-Control-Allow-Origin': allowed_origin,
                    'Content-Type': 'application/json'
                }
            }
        
        item = response['Item']
        print(f'Found system prompt: {name}')
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "prompt": item
            }, default=str),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        print(f"Error getting system prompt: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to get system prompt",
                "details": str(e)
            }),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }

def save_system_prompt(event, context):
    """Create or update a system prompt - No authentication, CORS only"""
    print('save system prompt event: ', json.dumps(event))

    # Validate origin for CORS
    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None) if event_headers else None
    
    allowed_origin = 'https://broadcust.co.il'  # default
    if event_origin is not None and event_origin.endswith("broadcust.co.il"):
        allowed_origin = event_origin
    elif event_origin is not None:
        # Invalid origin
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Invalid Origin"}),
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
        }

    # Parse request body
    event_body = event.get("body", None)
    if event_body is not None:
        try:
            body_data = json.loads(event_body)
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid JSON in request body"}),
                "headers": {
                    'Access-Control-Allow-Origin': allowed_origin,
                    'Content-Type': 'application/json'
                }
            }
    else:
        body_data = event

    # Validate required fields
    name = body_data.get('name')
    prompt = body_data.get('prompt')
    
    if not name or not prompt:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Missing required fields",
                "required": ["name", "prompt"]
            }),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }

    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('SYSTEM_PROMPTS_TABLE')
        
        if not table_name:
            print('ERROR: SYSTEM_PROMPTS_TABLE environment variable not set')
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Server configuration error"}),
                "headers": {'Content-Type': 'application/json'}
            }
        
        table = dynamodb.Table(table_name)
        
        # Put item to DynamoDB (creates or updates)
        table.put_item(
            Item={
                'name': name.strip(),
                'prompt': prompt.strip()
            }
        )
        
        print(f'Successfully saved system prompt: {name}')
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "message": "System prompt saved successfully",
                "name": name
            }),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        print(f"Error saving system prompt: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to save system prompt",
                "details": str(e)
            }),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }

def delete_system_prompt(event, context):
    """Delete a system prompt by name - No authentication, CORS only"""
    print('delete system prompt event: ', json.dumps(event))

    # Validate origin for CORS
    event_headers = event.get("headers", None)
    event_origin = event_headers.get("origin", None) if event_headers else None
    
    allowed_origin = 'https://broadcust.co.il'  # default
    if event_origin is not None and event_origin.endswith("broadcust.co.il"):
        allowed_origin = event_origin
    elif event_origin is not None:
        # Invalid origin
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Invalid Origin"}),
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
        }

    # Extract name from query string parameters
    query_params = event.get("queryStringParameters", {})
    if not query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing query parameters"}),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }
    
    name = query_params.get("name")
    if not name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required parameter: name"}),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }

    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('SYSTEM_PROMPTS_TABLE')
        
        if not table_name:
            print('ERROR: SYSTEM_PROMPTS_TABLE environment variable not set')
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Server configuration error"}),
                "headers": {'Content-Type': 'application/json'}
            }
        
        table = dynamodb.Table(table_name)
        
        # Delete item from DynamoDB
        table.delete_item(Key={'name': name})
        
        print(f'Successfully deleted system prompt: {name}')
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "message": "System prompt deleted successfully",
                "name": name
            }),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        print(f"Error deleting system prompt: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to delete system prompt",
                "details": str(e)
            }),
            "headers": {
                'Access-Control-Allow-Origin': allowed_origin,
                'Content-Type': 'application/json'
            }
        }
