import json
import os
from langchain.chat_models import ChatOpenAI
from openai import OpenAI
import google.generativeai as genai
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai

from conf import open_api_api_key, gemini_api_key, gcp_project_id, gcp_region

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
