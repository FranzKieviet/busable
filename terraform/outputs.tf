output "bucket_id" {
  description = "GTFS Ingestion Bucket ID"
  value       = aws_s3_bucket.ingestion_bucket.id
}

output "bucket_arn" {
  description = "GTFS Ingestion Bucket ARN"
  value       = aws_s3_bucket.ingestion_bucket.arn
}


output "apprunner_url" {
  value       = "https://${aws_apprunner_service.busable_api.service_url}"
  description = "Public URL for Busable API"
}