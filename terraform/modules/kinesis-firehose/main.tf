# ============================================================================
# Kinesis Firehose Module - Data Streaming
# Creates Firehose delivery streams for real-time data ingestion
# ============================================================================

# ============================================================================
# IAM Role for Firehose
# ============================================================================

resource "aws_iam_role" "firehose_role" {
  name = "${var.name_prefix}-firehose-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "firehose.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-firehose-role"
  })
}

# ============================================================================
# IAM Policy for Firehose
# ============================================================================

resource "aws_iam_role_policy" "firehose_policy" {
  name = "${var.name_prefix}-firehose-policy"
  role = aws_iam_role.firehose_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ]
        Resource = [
          var.bronze_bucket_arn,
          "${var.bronze_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/kinesisfirehose/*:log-stream:*"
      }
      ],
      var.transformation_lambda_arn != "" ? [{
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction",
          "lambda:GetFunctionConfiguration"
        ]
        Resource = var.transformation_lambda_arn
      }] : []
    )
  })
}

# ============================================================================
# Kinesis Firehose Delivery Stream - Orders
# ============================================================================

resource "aws_kinesis_firehose_delivery_stream" "orders" {
  name        = "${var.name_prefix}-orders-stream"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn            = aws_iam_role.firehose_role.arn
    bucket_arn          = var.bronze_bucket_arn
    prefix              = "orders/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"
    error_output_prefix = "errors/orders/!{firehose:error-output-type}/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"

    buffering_size     = var.buffering_size
    buffering_interval = var.buffering_interval
    compression_format = var.compression_format

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose_orders.name
      log_stream_name = "S3Delivery"
    }

    dynamic "processing_configuration" {
      for_each = var.transformation_lambda_arn != "" ? [1] : []
      content {
        enabled = true

        processors {
          type = "Lambda"

          parameters {
            parameter_name  = "LambdaArn"
            parameter_value = "${var.transformation_lambda_arn}:$LATEST"
          }
        }
      }
    }
  }

  tags = merge(var.tags, {
    Name   = "${var.name_prefix}-orders-stream"
    Entity = "orders"
  })
}

# ============================================================================
# CloudWatch Log Groups
# ============================================================================

resource "aws_cloudwatch_log_group" "firehose_orders" {
  name              = "/aws/kinesisfirehose/${var.name_prefix}-orders"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_stream" "firehose_orders_s3" {
  name           = "S3Delivery"
  log_group_name = aws_cloudwatch_log_group.firehose_orders.name
}

# ============================================================================
# CloudWatch Alarms
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "firehose_delivery_to_s3_failed" {
  alarm_name          = "${var.name_prefix}-firehose-delivery-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DeliveryToS3.DataFreshness"
  namespace           = "AWS/Firehose"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "900" # 15 minutes
  alarm_description   = "Firehose delivery to S3 is delayed"
  treat_missing_data  = "notBreaching"

  dimensions = {
    DeliveryStreamName = aws_kinesis_firehose_delivery_stream.orders.name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}
