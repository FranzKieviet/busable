# 1. Install dependencies with --no-cache-dir to reduce footprint
# Force re-run on every apply by including a timestamp trigger
resource "null_resource" "install_dependencies" {
  triggers = {
    requirements = filemd5("${path.module}/../dataloaders/requirements.txt")
    dataloader_files = filemd5("${path.module}/../dataloaders/main.py")
    # Force re-install on every CI run to ensure dependencies are fresh
    build_id = var.image_tag != null ? var.image_tag : timestamp()
  }

  provisioner "local-exec" {
    command = "docker run --rm -w /var/task -v ${abspath("${path.module}/../dataloaders")}:/var/task public.ecr.aws/sam/build-python3.10:latest bash -c 'pip install --no-cache-dir -r requirements.txt -t /var/task && test -d /var/task/pymongo || (echo \"ERROR: pymongo not installed!\" && exit 1)'"
  }
}

data "archive_file" "dataloader_lambda_zip" {
  type        = "zip"
  source_dir  = abspath("${path.module}/../dataloaders")
  output_path = "${path.module}/dataloader_lambda.zip"
  
  # Only exclude files we're certain we don't need - everything else goes in the zip
  excludes = [
    ".git",
    ".gitignore",
    ".pytest_cache",
    "data",
    "Dockerfile",
    ".env",
    ".dockerignore"
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