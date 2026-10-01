output "bucket_id" {
  description = "GTFS Ingestion Bucket ID"
  value       = aws_s3_bucket.ingestion_bucket.id
}

output "bucket_arn" {
  description = "GTFS Ingestion Bucket ARN"
  value       = aws_s3_bucket.ingestion_bucket.arn
}

output "api_url" {
  value = aws_lambda_function_url.busable_api.function_url
}