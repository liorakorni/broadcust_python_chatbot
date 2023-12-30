import json
# import weaviate
import os
from langchain.chat_models import ChatOpenAI
# from langchain.chains.question_answering import load_qa_chain
# from langchain.vectorstores.weaviate import Weaviate
from openai import OpenAI

os.environ["OPENAI_API_KEY"] = "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"

# auth_config = weaviate.AuthApiKey(api_key="m1r1tdtaVScNSUuygYakEhp7is4gBBBHfVxO")

# WEAVIATE_URL = "https://chatbot-api-cluster-wjg8l18u.weaviate.network"

# client = weaviate.Client(
#     url=WEAVIATE_URL,
#     additional_headers={"X-OpenAI-Api-Key": "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"},
#     auth_client_secret=auth_config
# )

OpenAIClient = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="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",
)
# vectorstore = Weaviate(client, "Paragraph", "content", attributes=["source"])
llm = ChatOpenAI(temperature=0, model_name="gpt-4", streaming=True)
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
    print('event:', json.dumps(event))
    # print('context function_name:', context.function_name)
    # print('context log_group_name:', context.log_group_name)

    event_body = event.get("body", None)
    print('event_body reg:', event_body)

    # event_body_json_dump = json.dumps(event_body)
    # print('event_body json.dumps:', event_body_json_dump)
    # event_body_json_load = json.loads(event_body)
    # print('event_body json.loads:', event_body_json_load)

    if event_body is not None:
        event_body_json_load = json.loads(event_body)
        question = event_body_json_load.get("question", None)
    else:
        question = event.get("question", None)

    msg = llm.invoke(question)

    response = {
        "statusCode": 200,
        'status': "success",
        "body": msg.content,
        "headers": {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        }
    }
    return response
