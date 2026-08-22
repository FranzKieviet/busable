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

resource "aws_iam_role" "apprunner_ecr_access" {
  name = "busable-apprunner-ecr-role-${var.branch}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_access_attachment" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}