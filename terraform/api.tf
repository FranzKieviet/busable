# The API runs as a Lambda from the same container image, via the Lambda Web Adapter baked into the Dockerfile
resource "aws_lambda_function" "busable_api" {
  function_name = "busable-api-${var.branch}"
  role          = aws_iam_role.api_lambda_role.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.busable_api.repository_url}:${var.image_tag}"

  # More memory also means more CPU, which shortens .NET cold starts
  timeout     = 30
  memory_size = 1024

  environment {
    variables = {
      Mongo__ConnectionString = var.mongodb_uri
      Mongo__DatabaseName     = "busable"
      ASPNETCORE_ENVIRONMENT  = "Production"
      ASPNETCORE_URLS         = "http://+:8080"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.api_lambda_role_policy,
    aws_cloudwatch_log_group.api_logs
  ]
}

# Public HTTPS endpoint for the API, replacing the ALB
resource "aws_lambda_function_url" "busable_api" {
  function_name      = aws_lambda_function.busable_api.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET"]
    allow_headers = ["*"]
  }
}

# A public function URL needs both permissions to be invokable
resource "aws_lambda_permission" "allow_public_function_url" {
  statement_id           = "AllowPublicFunctionUrl"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.busable_api.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "allow_public_invoke" {
  statement_id  = "AllowPublicInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.busable_api.function_name
  principal     = "*"
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/lambda/busable-api-${var.branch}"
  retention_in_days = 7
}
