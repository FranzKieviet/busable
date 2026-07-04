resource "aws_s3_bucket" "site_bucket" {
  bucket = "${local.project_prefix}-test-bucket"
  acl    = "private"
  tags = {
    Name        = local.project_prefix
    Environment = var.environment
  }
}