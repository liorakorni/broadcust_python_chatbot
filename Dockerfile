### Dockerfile

FROM public.ecr.aws/lambda/python:3.10-arm64

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .

# Upgrade pip to get access to prebuilt wheels for ARM64
RUN pip3 install --upgrade pip

# Install dependencies with newer pip that has ARM64 wheels
# Use --prefer-binary to avoid building from source
RUN pip3 install --prefer-binary -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}

COPY conf.py ${LAMBDA_TASK_ROOT}

# Copy Google Cloud service account key (create this file after GCP setup)
COPY vertex-ai-key.json ${LAMBDA_TASK_ROOT}/vertex-ai-key.json

# Set the CMD to your handler
CMD [ "handler.chatbot" ]