### Dockerfile

FROM public.ecr.aws/lambda/python:3.8-arm64

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}

COPY conf.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "handler.chatbot" ]