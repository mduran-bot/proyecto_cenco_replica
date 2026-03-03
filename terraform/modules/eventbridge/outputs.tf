output "event_bus_name" {
  description = "Name of EventBridge custom event bus"
  value       = aws_cloudwatch_event_bus.polling.name
}

output "event_bus_arn" {
  description = "ARN of EventBridge custom event bus"
  value       = aws_cloudwatch_event_bus.polling.arn
}

output "rule_arns" {
  description = "ARNs of EventBridge scheduled rules"
  value = {
    orders  = aws_cloudwatch_event_rule.poll_orders.arn
    catalog = aws_cloudwatch_event_rule.poll_catalog.arn
    stock   = aws_cloudwatch_event_rule.poll_stock.arn
    prices  = aws_cloudwatch_event_rule.poll_prices.arn
    stores  = aws_cloudwatch_event_rule.poll_stores.arn
  }
}

output "rule_names" {
  description = "Names of EventBridge scheduled rules"
  value = [
    aws_cloudwatch_event_rule.poll_orders.name,
    aws_cloudwatch_event_rule.poll_catalog.name,
    aws_cloudwatch_event_rule.poll_stock.name,
    aws_cloudwatch_event_rule.poll_prices.name,
    aws_cloudwatch_event_rule.poll_stores.name
  ]
}

output "dlq_url" {
  description = "URL of EventBridge Dead Letter Queue"
  value       = aws_sqs_queue.dlq.url
}

output "dlq_arn" {
  description = "ARN of EventBridge Dead Letter Queue"
  value       = aws_sqs_queue.dlq.arn
}

output "iam_role_arn" {
  description = "ARN of IAM role for EventBridge to MWAA"
  value       = aws_iam_role.eventbridge_mwaa.arn
}

output "log_group_name" {
  description = "Name of CloudWatch Log Group for EventBridge"
  value       = aws_cloudwatch_log_group.eventbridge_logs.name
}

output "log_group_arn" {
  description = "ARN of CloudWatch Log Group for EventBridge"
  value       = aws_cloudwatch_log_group.eventbridge_logs.arn
}

output "alarm_arns" {
  description = "ARNs of CloudWatch Alarms for EventBridge monitoring"
  value = {
    invocation_failures = aws_cloudwatch_metric_alarm.rule_invocation_failures.arn
    dlq_messages        = aws_cloudwatch_metric_alarm.dlq_messages.arn
    throttled_rules     = aws_cloudwatch_metric_alarm.rule_throttled.arn
  }
}
