resource "aws_iam_role_policy" "ingestion_lambda_policy" {
  name = "AllowS3Imports"
  role = aws_iam_role.lambda_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:HeadObject"]
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