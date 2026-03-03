# ============================================================================
# SNS Module - Error Notifications
# ============================================================================
# This module creates an SNS topic for error notifications from the API
# polling system, with optional email subscriptions.
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# SNS Topic
# ============================================================================

resource "aws_sns_topic" "error_notifications" {
  name                        = var.topic_name
  display_name                = var.display_name
  fifo_topic                  = var.fifo_topic
  content_based_deduplication = var.fifo_topic ? var.content_based_deduplication : null

  # Enable server-side encryption
  kms_master_key_id = var.kms_master_key_id

  # Delivery policy for retries
  delivery_policy = jsonencode({
    http = {
      defaultHealthyRetryPolicy = {
        minDelayTarget     = 20
        maxDelayTarget     = 20
        numRetries         = 3
        numMaxDelayRetries = 0
        numNoDelayRetries  = 0
        numMinDelayRetries = 0
        backoffFunction    = "linear"
      }
      disableSubscriptionOverrides = false
    }
  })

  tags = merge(var.tags, {
    Name      = var.topic_name
    Purpose   = "API Polling Error Notifications"
    ManagedBy = "terraform"
  })
}

# ============================================================================
# SNS Topic Policy
# ============================================================================

resource "aws_sns_topic_policy" "error_notifications" {
  arn = aws_sns_topic.error_notifications.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowPublishFromServices"
        Effect = "Allow"
        Principal = {
          Service = var.allowed_services
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.error_notifications.arn
      },
      {
        Sid    = "AllowPublishFromIAMRoles"
        Effect = "Allow"
        Principal = {
          AWS = var.allowed_iam_arns
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.error_notifications.arn
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = var.aws_account_id
          }
        }
      }
    ]
  })
}

# ============================================================================
# Email Subscriptions
# ============================================================================

resource "aws_sns_topic_subscription" "email" {
  count = length(var.email_addresses)

  topic_arn = aws_sns_topic.error_notifications.arn
  protocol  = "email"
  endpoint  = var.email_addresses[count.index]

  # Email subscriptions require manual confirmation
  # The subscription will be in "PendingConfirmation" state until confirmed
}

# ============================================================================
# SQS Subscriptions (for dead letter queue or processing)
# ============================================================================

resource "aws_sns_topic_subscription" "sqs" {
  count = length(var.sqs_queue_arns)

  topic_arn = aws_sns_topic.error_notifications.arn
  protocol  = "sqs"
  endpoint  = var.sqs_queue_arns[count.index]

  # Enable raw message delivery for SQS
  raw_message_delivery = true
}

# ============================================================================
# Lambda Subscriptions (for custom processing)
# ============================================================================

resource "aws_sns_topic_subscription" "lambda" {
  count = length(var.lambda_function_arns)

  topic_arn = aws_sns_topic.error_notifications.arn
  protocol  = "lambda"
  endpoint  = var.lambda_function_arns[count.index]
}

# ============================================================================
# CloudWatch Alarm for Failed Notifications
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "failed_notifications" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.topic_name}-failed-notifications"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "NumberOfNotificationsFailed"
  namespace           = "AWS/SNS"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when SNS notifications fail to deliver"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TopicName = aws_sns_topic.error_notifications.name
  }

  tags = var.tags
}
