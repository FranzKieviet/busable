# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.10

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy dependency definition
COPY requirements.txt .

# Install dependencies with no cache to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy all python files and directories into the execution path
COPY main.py .
COPY lib/ ./lib/
COPY transit_dataloader/ ./transit_dataloader/
COPY place_dataloader/ ./place_dataloader/

# Set the CMD to your file name and handler function name: <filename>.<handler_function>
CMD [ "main.lambda_handler" ]