resource "aws_iam_role_policy" "ingestion_lambda_policy" {
  name = "AllowS3Imports"
  role = aws_iam_role.lambda_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:HeadObject", "s3:DeleteObject"]
        Resource = ["arn:aws:s3:::${aws_s3_bucket.ingestion_bucket.bucket}/imports/*"]
      },
      {
        Effect = "Allow"
        Action = "s3:ListBucket"
        Resource = "arn:aws:s3:::${aws_s3_bucket.ingestion_bucket.bucket}"
        Condition = {
          StringLike = {
            "s3:prefix" = ["imports/*"]
          }
        }
      }
    ]
  })
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "busable-ecs-execution-role-${var.branch}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
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