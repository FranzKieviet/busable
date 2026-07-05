data "archive_file" "dataloader_lambda_zip" {
    type        = "zip"
    source_file = "${path.module}/dataloader.py"
    output_path = "${path.module}/lambda_function.zip"
}

resource "aws_lambda_function" "dataloader" {
    filename      = data.archive_file.dataloader_lambda_zip.output_path
    function_name = "dataloader"
    role          = aws_iam_role.lambda_role.arn
    handler       = "dataloader.lambda_handler"
    runtime       = "python3.10"

    source_code_hash = data.archive_file.dataloader_lambda_zip.output_base64sha256
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
}