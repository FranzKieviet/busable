data "archive_file" "dataloader_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../dataloaders/transit_dataloader/dataloader.py"
  output_path = "${path.module}/dataloader_lambda.zip"
}

resource "aws_lambda_function" "dataloader" {
    filename      = data.archive_file.dataloader_lambda_zip.output_path
    function_name = "${local.project_prefix}-gtfs-ingestion-lambda"
    role          = aws_iam_role.lambda_role.arn
    handler       = "dataloader.lambda_handler"
    runtime       = "python3.10"

    source_code_hash = data.archive_file.dataloader_lambda_zip.output_base64sha256

    timeout     = 300
    memory_size = 512
}

resource "aws_iam_role" "lambda_role" {
    name = "dataloader-lambda-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "lambda.amazonaws.com"
                }
            }
        ]
    })
    managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
  ]
}