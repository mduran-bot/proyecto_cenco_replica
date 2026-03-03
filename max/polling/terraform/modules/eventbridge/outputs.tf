# ============================================================================
# EventBridge Module - Outputs
# ============================================================================

output "orders_rule_arns" {
  description = "Map of client to orders polling rule ARN"
  value       = { for k, v in aws_cloudwatch_event_rule.poll_orders : k => v.arn }
}

output "products_rule_arns" {
  description = "Map of client to products polling rule ARN"
  value       = { for k, v in aws_cloudwatch_event_rule.poll_products : k => v.arn }
}

output "stock_rule_arns" {
  description = "Map of client to stock polling rule ARN"
  value       = { for k, v in aws_cloudwatch_event_rule.poll_stock : k => v.arn }
}

output "prices_rule_arns" {
  description = "Map of client to prices polling rule ARN"
  value       = { for k, v in aws_cloudwatch_event_rule.poll_prices : k => v.arn }
}

output "stores_rule_arns" {
  description = "Map of client to stores polling rule ARN"
  value       = { for k, v in aws_cloudwatch_event_rule.poll_stores : k => v.arn }
}
