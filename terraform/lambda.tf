# Lambda function using Docker image from ECR
# This avoids the 50 MB zip size limit - Docker images can be up to 10 GB
resource "aws_lambda_function" "dataloader" {
  function_name = "${local.project_prefix}-gtfs-ingestion-lambda"
  role          = aws_iam_role.lambda_role.arn
  
  # Use Docker image instead of zip file
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.dataloader.repository_url}:${var.image_tag != null ? var.image_tag : "latest"}"

  # Sized for the Bay Area places load (DuckDB scan of Overture over S3)
  timeout     = 900
  memory_size = 2048

  environment {
    variables = {
      MONGO_URI = var.mongodb_uri
      DB_NAME   = "busable"
    }
  }
}

# ECR repository for dataloader
resource "aws_ecr_repository" "dataloader" {
  name = "busable-dataloader"

  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Name = "busable-dataloader"
  }
}