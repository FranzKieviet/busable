output "bucket_id" {
  description = "Test bucket"
  value       = aws_s3_bucket.site_bucket.id
}

output "bucket_arn" {
  description = "Test Bucket"
  value       = aws_s3_bucket.site_bucket.arn
}
