# ============================================================================
# EventBridge Module
# Creates Event Bus, Scheduled Rules for API Polling, and Dead Letter Queue
# ============================================================================

# ============================================================================
# Custom Event Bus
# ============================================================================

resource "aws_cloudwatch_event_bus" "polling" {
  name = "${var.name_prefix}-polling-bus"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-polling-bus"
    Component = "eventbridge"
    Purpose   = "polling-orchestration"
  })
}

# ============================================================================
# Dead Letter Queue (SQS)
# ============================================================================

resource "aws_sqs_queue" "dlq" {
  name                       = "${var.name_prefix}-eventbridge-dlq"
  message_retention_seconds  = 1209600 # 14 days
  visibility_timeout_seconds = 300

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-eventbridge-dlq"
    Component = "eventbridge"
    Purpose   = "dead-letter-queue"
  })
}

# ============================================================================
# IAM Role for EventBridge to invoke MWAA
# ============================================================================

resource "aws_iam_role" "eventbridge_mwaa" {
  name = "${var.name_prefix}-eventbridge-mwaa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-eventbridge-mwaa-role"
    Component = "eventbridge"
  })
}

resource "aws_iam_role_policy" "eventbridge_mwaa" {
  name = "${var.name_prefix}-eventbridge-mwaa-policy"
  role = aws_iam_role.eventbridge_mwaa.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "airflow:CreateCliToken"
        ]
        Resource = var.mwaa_environment_arn != "" ? [var.mwaa_environment_arn] : ["*"]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = [aws_sqs_queue.dlq.arn]
      }
    ]
  })
}

# ============================================================================
# EventBridge Scheduled Rules for API Polling
# ============================================================================

# Order Polling Rule - Every 5 minutes
resource "aws_cloudwatch_event_rule" "poll_orders" {
  name                = "${var.name_prefix}-poll-orders-schedule"
  description         = "Trigger MWAA DAG for order polling every 5 minutes (multi-tenant)"
  schedule_expression = "rate(${var.order_polling_rate})"
  state               = var.mwaa_environment_arn != "" ? "ENABLED" : "DISABLED"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-poll-orders-schedule"
    Component = "eventbridge"
    Purpose   = "order-polling"
    DataType  = "orders"
    Clients   = "metro,wongio"
  })
}

resource "aws_cloudwatch_event_target" "poll_orders" {
  count = var.mwaa_environment_arn != "" ? 1 : 0

  rule     = aws_cloudwatch_event_rule.poll_orders.name
  arn      = var.mwaa_environment_arn
  role_arn = aws_iam_role.eventbridge_mwaa.arn

  input = jsonencode({
    dag_id = "poll_orders"
    conf = {
      clients  = ["metro", "wongio"]
      endpoint = "/order"
      base_url = "https://oms.janis.in/api"
    }
  })

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }

  retry_policy {
    maximum_retry_attempts = 2
  }
}

# Product Polling Rule - Every 1 hour (renamed to Catalog)
resource "aws_cloudwatch_event_rule" "poll_catalog" {
  name                = "${var.name_prefix}-poll-catalog-schedule"
  description         = "Trigger MWAA DAG for catalog polling every 1 hour (multi-tenant, 4 endpoints)"
  schedule_expression = "rate(${var.catalog_polling_rate})"
  state               = var.mwaa_environment_arn != "" ? "ENABLED" : "DISABLED"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-poll-catalog-schedule"
    Component = "eventbridge"
    Purpose   = "catalog-polling"
    DataType  = "catalog"
    Clients   = "metro,wongio"
    Endpoints = "product,sku,category,brand"
  })
}

resource "aws_cloudwatch_event_target" "poll_catalog" {
  count = var.mwaa_environment_arn != "" ? 1 : 0

  rule     = aws_cloudwatch_event_rule.poll_catalog.name
  arn      = var.mwaa_environment_arn
  role_arn = aws_iam_role.eventbridge_mwaa.arn

  input = jsonencode({
    dag_id = "poll_catalog"
    conf = {
      clients   = ["metro", "wongio"]
      endpoints = ["/product", "/sku", "/category", "/brand"]
      base_url  = "https://catalog.janis.in/api"
    }
  })

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }

  retry_policy {
    maximum_retry_attempts = 2
  }
}

# Stock Polling Rule - Every 10 minutes
resource "aws_cloudwatch_event_rule" "poll_stock" {
  name                = "${var.name_prefix}-poll-stock-schedule"
  description         = "Trigger MWAA DAG for stock polling every 10 minutes (multi-tenant)"
  schedule_expression = "rate(${var.stock_polling_rate})"
  state               = var.mwaa_environment_arn != "" ? "ENABLED" : "DISABLED"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-poll-stock-schedule"
    Component = "eventbridge"
    Purpose   = "stock-polling"
    DataType  = "stock"
    Clients   = "metro,wongio"
  })
}

resource "aws_cloudwatch_event_target" "poll_stock" {
  count = var.mwaa_environment_arn != "" ? 1 : 0

  rule     = aws_cloudwatch_event_rule.poll_stock.name
  arn      = var.mwaa_environment_arn
  role_arn = aws_iam_role.eventbridge_mwaa.arn

  input = jsonencode({
    dag_id = "poll_stock"
    conf = {
      clients  = ["metro", "wongio"]
      endpoint = "/sku-stock"
      base_url = "https://wms.janis.in/api"
    }
  })

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }

  retry_policy {
    maximum_retry_attempts = 2
  }
}

# Price Polling Rule - Every 30 minutes
resource "aws_cloudwatch_event_rule" "poll_prices" {
  name                = "${var.name_prefix}-poll-prices-schedule"
  description         = "Trigger MWAA DAG for price polling every 30 minutes (multi-tenant, 3 endpoints)"
  schedule_expression = "rate(${var.price_polling_rate})"
  state               = var.mwaa_environment_arn != "" ? "ENABLED" : "DISABLED"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-poll-prices-schedule"
    Component = "eventbridge"
    Purpose   = "price-polling"
    DataType  = "prices"
    Clients   = "metro,wongio"
    Endpoints = "price,price-sheet,base-price"
  })
}

resource "aws_cloudwatch_event_target" "poll_prices" {
  count = var.mwaa_environment_arn != "" ? 1 : 0

  rule     = aws_cloudwatch_event_rule.poll_prices.name
  arn      = var.mwaa_environment_arn
  role_arn = aws_iam_role.eventbridge_mwaa.arn

  input = jsonencode({
    dag_id = "poll_prices"
    conf = {
      clients   = ["metro", "wongio"]
      endpoints = ["/price", "/price-sheet", "/base-price"]
      base_url  = "https://vtex.pricing.janis.in/api"
    }
  })

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }

  retry_policy {
    maximum_retry_attempts = 2
  }
}

# Store Polling Rule - Every 1 day
resource "aws_cloudwatch_event_rule" "poll_stores" {
  name                = "${var.name_prefix}-poll-stores-schedule"
  description         = "Trigger MWAA DAG for store polling every 1 day (multi-tenant)"
  schedule_expression = "rate(${var.store_polling_rate})"
  state               = var.mwaa_environment_arn != "" ? "ENABLED" : "DISABLED"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-poll-stores-schedule"
    Component = "eventbridge"
    Purpose   = "store-polling"
    DataType  = "stores"
    Clients   = "metro,wongio"
  })
}

resource "aws_cloudwatch_event_target" "poll_stores" {
  count = var.mwaa_environment_arn != "" ? 1 : 0

  rule     = aws_cloudwatch_event_rule.poll_stores.name
  arn      = var.mwaa_environment_arn
  role_arn = aws_iam_role.eventbridge_mwaa.arn

  input = jsonencode({
    dag_id = "poll_stores"
    conf = {
      clients  = ["metro", "wongio"]
      endpoint = "/location"
      base_url = "https://commerce.janis.in/api"
    }
  })

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }

  retry_policy {
    maximum_retry_attempts = 2
  }
}

# ============================================================================
# CloudWatch Monitoring
# ============================================================================

# CloudWatch Log Group for EventBridge rule execution logs
resource "aws_cloudwatch_log_group" "eventbridge_logs" {
  name              = "/aws/events/${var.name_prefix}-polling"
  retention_in_days = 90

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-eventbridge-logs"
    Component = "eventbridge"
    Purpose   = "rule-execution-logs"
  })
}

# CloudWatch Metric Alarms for EventBridge Rules

# Alarm for failed rule invocations
resource "aws_cloudwatch_metric_alarm" "rule_invocation_failures" {
  alarm_name          = "${var.name_prefix}-eventbridge-invocation-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FailedInvocations"
  namespace           = "AWS/Events"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when EventBridge rule invocations fail"
  treat_missing_data  = "notBreaching"

  dimensions = {
    RuleName = aws_cloudwatch_event_rule.poll_orders.name
  }

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-eventbridge-invocation-failures"
    Component = "eventbridge"
    Purpose   = "monitoring"
  })
}

# Alarm for DLQ message count
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.name_prefix}-eventbridge-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alert when messages appear in EventBridge DLQ"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-eventbridge-dlq-messages"
    Component = "eventbridge"
    Purpose   = "monitoring"
  })
}

# Alarm for throttled rule invocations
resource "aws_cloudwatch_metric_alarm" "rule_throttled" {
  alarm_name          = "${var.name_prefix}-eventbridge-throttled"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ThrottledRules"
  namespace           = "AWS/Events"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when EventBridge rules are throttled"
  treat_missing_data  = "notBreaching"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-eventbridge-throttled"
    Component = "eventbridge"
    Purpose   = "monitoring"
  })
}
