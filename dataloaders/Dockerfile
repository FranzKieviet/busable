# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

# Copy dependency definition
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies into the task root
RUN pip install -r requirements.txt

# Copy your python files into the execution path
COPY main.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your file name and handler function name: <filename>.<handler_function>
CMD [ "main.lambda_handler" ]