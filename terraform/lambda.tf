# 1. Install dependencies into a build directory before zipping
resource "null_resource" "install_dependencies" {
  triggers = {
    requirements = filemd5("${path.module}/../dataloaders/requirements.txt")
    dataloader_files = filemd5("${path.module}/../dataloaders/main.py")
  }

  provisioner "local-exec" {
    command = "docker run --rm -w /var/task -v ${abspath("${path.module}/../dataloaders")}:/var/task public.ecr.aws/sam/build-python3.10:latest bash -c 'pip install -r requirements.txt -t /var/task && find /var/task -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && find /var/task -type f -name \"*.dist-info\" -delete && find /var/task -type f -name \"*.pyc\" -delete && echo \"Dependencies installed and cleaned successfully\"'"
  }
}

data "archive_file" "dataloader_lambda_zip" {
  type        = "zip"
  source_dir  = abspath("${path.module}/../dataloaders")
  output_path = "${path.module}/dataloader_lambda.zip"
  
  excludes = [
    "*.git*",
    "__pycache__",
    "*.egg-info",
    ".pytest_cache",
    "data",
    "Dockerfile",
    ".env"
  ]

  depends_on = [null_resource.install_dependencies]
}

# 3. Create/Update Lambda Function
resource "aws_lambda_function" "dataloader" {
  filename         = data.archive_file.dataloader_lambda_zip.output_path
  source_code_hash = data.archive_file.dataloader_lambda_zip.output_base64sha256

  function_name = "${local.project_prefix}-gtfs-ingestion-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.10"

  timeout     = 300
  memory_size = 512

  environment {
    variables = {
      MONGO_URI = var.mongodb_uri
      DB_NAME   = "busable"
    }
  }
}