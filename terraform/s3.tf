resource "aws_s3_bucket" "ingestion_bucket" {
  bucket = "${local.project_prefix}-gtfs-ingestion-bucket"
  acl    = "private"
  tags = {
    Name        = local.project_prefix
    Environment = var.environment
  }
}

resource "aws_s3_bucket_notification" "gtfs_ingestion" {
  bucket = aws_s3_bucket.ingestion_bucket.id

  eventbridge = true
}