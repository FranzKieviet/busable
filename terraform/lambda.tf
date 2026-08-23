# 1. Install dependencies into a build directory before zipping
resource "null_resource" "install_dependencies" {
  triggers = {
    requirements = filemd5("${path.module}/../dataloaders/requirements.txt")
  }

  provisioner "local-exec" {
    # Uses platform-independent python/pip invocation
    command = "python -m pip install -r ${path.module}/../dataloaders/requirements.txt -t ${path.module}/../dataloaders/"
  }
}

# 2. Zip the dataloaders folder AFTER dependencies are installed
data "archive_file" "dataloader_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../dataloaders"
  output_path = "${path.module}/dataloader_lambda.zip"

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
}