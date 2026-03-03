# ============================================================================
# DynamoDB Module - API Polling Control Table
# ============================================================================
# This module creates a DynamoDB table for managing polling state and locks
# to prevent concurrent executions and enable incremental polling.
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
# DynamoDB Table
# ============================================================================

resource "aws_dynamodb_table" "polling_control" {
  name         = var.table_name
  billing_mode = var.billing_mode
  hash_key     = "data_type"

  # Optional: Configure provisioned capacity if not using PAY_PER_REQUEST
  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null

  attribute {
    name = "data_type"
    type = "S"
  }

  # Enable point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Enable server-side encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  # Enable TTL if specified
  dynamic "ttl" {
    for_each = var.ttl_attribute_name != "" ? [1] : []
    content {
      attribute_name = var.ttl_attribute_name
      enabled        = true
    }
  }

  tags = merge(var.tags, {
    Name      = var.table_name
    Purpose   = "API Polling State Management"
    ManagedBy = "terraform"
  })
}

# ============================================================================
# CloudWatch Alarms for DynamoDB
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "read_throttle" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.table_name}-read-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ReadThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when DynamoDB table experiences read throttling"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    TableName = aws_dynamodb_table.polling_control.name
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "write_throttle" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.table_name}-write-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "WriteThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when DynamoDB table experiences write throttling"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    TableName = aws_dynamodb_table.polling_control.name
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "conditional_check_failed" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.table_name}-conditional-check-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ConditionalCheckFailedRequests"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 50
  alarm_description   = "Alert when many lock acquisition attempts fail (high contention)"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    TableName = aws_dynamodb_table.polling_control.name
  }

  tags = var.tags
}
