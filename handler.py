import json
# import weaviate
import os
from langchain.chat_models import ChatOpenAI
# from langchain.chains.question_answering import load_qa_chain
# from langchain.vectorstores.weaviate import Weaviate
from openai import OpenAI

from conf import open_api_api_key

os.environ["OPENAI_API_KEY"] = open_api_api_key

# auth_config = weaviate.AuthApiKey(api_key="m1r1tdtaVScNSUuygYakEhp7is4gBBBHfVxO")

# WEAVIATE_URL = "https://chatbot-api-cluster-wjg8l18u.weaviate.network"

# client = weaviate.Client(
#     url=WEAVIATE_URL,
#     additional_headers={"X-OpenAI-Api-Key": "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"},
#     auth_client_secret=auth_config
# )

OpenAIClient = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=open_api_api_key
)

# vectorstore = Weaviate(client, "Paragraph", "content", attributes=["source"])
llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", streaming=False)
# chain = load_qa_chain(llm, chain_type="stuff")


# def chatbot_test(event, context):
#     question = event['queryStringParameters']['question']
#     msg = llm.invoke(question)
#
#     response = {
#         "statusCode": 200,
#         'status': "success",
#         "body": msg.content,
#         "headers": {
#             'Access-Control-Allow-Origin': '*',
#             'Access-Control-Allow-Credentials': True,
#         }
#     }
#     return response


def chatbot(event, context):
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
