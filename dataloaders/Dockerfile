# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.10

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy dependency definition
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy all python files and directories into the execution path
COPY main.py ${LAMBDA_TASK_ROOT}
COPY lib/ ${LAMBDA_TASK_ROOT}/lib/
COPY transit_dataloader/ ${LAMBDA_TASK_ROOT}/transit_dataloader/
COPY place_dataloader/ ${LAMBDA_TASK_ROOT}/place_dataloader/

# Set the CMD to your file name and handler function name: <filename>.<handler_function>
CMD [ "main.lambda_handler" ]