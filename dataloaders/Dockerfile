# Use the official AWS Lambda Python base image. Must be 3.12+ (Amazon Linux 2023, glibc 2.34):
# the 3.10/3.11 images are Amazon Linux 2 (glibc 2.26), too old for DuckDB's extensions.
FROM public.ecr.aws/lambda/python:3.12

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy dependency definition
COPY requirements.txt .

# Install dependencies with no cache to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Pre-install DuckDB extensions into the image. At runtime Lambda has no HOME and a
# read-only filesystem (except /tmp), so INSTALL would fail; we only LOAD from here.
ENV DUCKDB_EXTENSION_DIR=/opt/duckdb_extensions
RUN python -c "import duckdb; con = duckdb.connect(config={'extension_directory': '${DUCKDB_EXTENSION_DIR}'}); con.sql('INSTALL spatial'); con.sql('INSTALL httpfs')"

# Copy all python files and directories into the execution path
COPY main.py .
COPY lib/ ./lib/
COPY transit_dataloader/ ./transit_dataloader/
COPY place_dataloader/ ./place_dataloader/

# Set the CMD to your file name and handler function name: <filename>.<handler_function>
CMD [ "main.lambda_handler" ]