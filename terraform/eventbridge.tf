resource "aws_cloudwatch_event_rule" "files_uploaded_rule" {
  name        = "GTFS Ingestion Files Uploaded Rule"
  description = "Trigger GTFS ingestion when files are uploaded to the S3 bucket"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
        bucket = {
        name = [aws_s3_bucket.ingestion_bucket.bucket]
        }
        object = {
            key = {
            prefix = ["triggers/"]
            }
        }
    }
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.files_uploaded_rule.name
  target_id = "invoke-lambda"
  arn       = aws_lambda_function.dataloader.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dataloader.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.files_uploaded_rule.arn
}