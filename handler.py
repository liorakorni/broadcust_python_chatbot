import json
import os
from langchain.chat_models import ChatOpenAI
from openai import OpenAI

from conf import open_api_api_key

os.environ["OPENAI_API_KEY"] = open_api_api_key

OpenAIClient = OpenAI(
    api_key=open_api_api_key
)

llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o", streaming=False)

def chatbot(event, context):
    """Original text-based chatbot - clean and simple"""
    print('event: ', json.dumps(event))

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
