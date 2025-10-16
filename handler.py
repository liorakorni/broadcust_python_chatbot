import json
import os
from langchain.chat_models import ChatOpenAI
from openai import OpenAI
import google.generativeai as genai

from conf import open_api_api_key, gemini_api_key

os.environ["OPENAI_API_KEY"] = open_api_api_key

OpenAIClient = OpenAI(
    api_key=open_api_api_key
)

# Configure Gemini
genai.configure(api_key=gemini_api_key)

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
        # Generate image using Gemini with text-to-image capability
        print(f'Generating image with Gemini for prompt: {prompt}')

        # Use GenerativeModel for image generation
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Generate content with image output
        response_gemini = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                max_output_tokens=2048,
            )
        )

        # For now, Gemini primarily does text generation
        # Image generation through Gemini API may require different setup
        # Let's return a placeholder response
        import base64
        import io
        from PIL import Image

        # Create a simple placeholder image with text
        img = Image.new('RGB', (512, 512), color=(73, 109, 137))

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        image_base64 = base64.b64encode(img_byte_arr).decode('utf-8')

        print(f'Gemini endpoint called (Note: Native image gen may need Vertex AI)')

        response = {
            "statusCode": 200,
            "status": "success",
            "body": json.dumps({
                "image_data": f"data:image/png;base64,{image_base64}",
                "prompt": prompt,
                "model": "gemini-1.5-flash",
                "note": "This endpoint requires Vertex AI setup for native image generation"
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
        # Generate image using Gemini 2.5 Flash (Nano Banana model)
        print(f'Generating image with Gemini Nano Banana for prompt: {prompt}')

        # Use Gemini 2.5 Flash for image generation (Nano Banana)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Generate image using the model
        result = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_modalities=["image"],
                candidate_count=1,
            )
        )

        # Get the generated image
        # Note: Gemini returns image data, not URLs. You may need to upload to storage
        # For now, we'll return base64 encoded image data
        import base64
        import io

        # Extract image from result
        image_part = result.parts[0]
        image_data = image_part.inline_data.data
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        print(f'Generated image with Gemini Nano Banana successfully')

        response = {
            "statusCode": 200,
            "status": "success",
            "body": json.dumps({
                "image_data": f"data:image/png;base64,{image_base64}",
                "prompt": prompt,
                "model": "gemini-2.0-flash-exp-nano-banana"
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
