data "archive_file" "dataloader_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../dataloaders"
  output_path = "${path.module}/dataloader_lambda.zip"
}

resource "aws_lambda_function" "dataloader" {
  filename         = data.archive_file.dataloader_lambda_zip.output_path
  source_code_hash = data.archive_file.dataloader_lambda_zip.output_base64sha256
  
  function_name    = "${local.project_prefix}-gtfs-ingestion-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.10"

  timeout          = 300
  memory_size      = 512
}