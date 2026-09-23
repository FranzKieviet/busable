resource "aws_cloudwatch_event_rule" "agency_files_uploaded_rule" {
  name        = "${local.project_prefix}-gtfs-ingestion-trigger-rule"
  description = "Trigger GTFS ingestion when files are uploaded to the S3 bucket  under triggers/gtfs/"

  event_pattern = jsonencode({
    source = ["aws.s3"]
    "detail-type" = ["Object Created"]
    detail = {
        bucket = {
        name = [aws_s3_bucket.ingestion_bucket.bucket]
        }
        object = {
        key = [{
            prefix = "triggers/gtfs/"
        }]
        }
    }
})
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.agency_files_uploaded_rule.name
  target_id = "invoke-lambda"
  arn       = aws_lambda_function.dataloader.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dataloader.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.agency_files_uploaded_rule.arn
}

// Rule for triggering places lambda
resource "aws_cloudwatch_event_rule" "places_files_uploaded_rule" {
  name        = "${local.project_prefix}-places-ingestion-trigger-rule"
  description = "Trigger ingestion when files are uploaded to the S3 bucket under triggers/places/"

  event_pattern = jsonencode({
    source = ["aws.s3"]
    "detail-type" = ["Object Created"]
    detail = {
      bucket = {
        name = [aws_s3_bucket.ingestion_bucket.bucket]
      }
      object = {
        key = [{ prefix = "triggers/places/" }]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "lambda_places" {
  rule      = aws_cloudwatch_event_rule.places_files_uploaded_rule.name
  target_id = "invoke-lambda-places"
  arn       = aws_lambda_function.dataloader.arn
}

resource "aws_lambda_permission" "allow_eventbridge_places" {
  statement_id  = "AllowExecutionFromEventBridgePlaces"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dataloader.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.places_files_uploaded_rule.arn
}