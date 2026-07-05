resource "aws_s3_bucket" "ingestion_bucket" {
  bucket = "${local.project_prefix}-gtfs-ingestion-bucket"
  acl    = "private"
  tags = {
    Name        = local.project_prefix
    Environment = var.environment
  }
}