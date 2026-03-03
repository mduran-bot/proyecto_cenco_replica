# ============================================================================
# Kinesis Firehose Module Outputs
# ============================================================================

output "firehose_role_arn" {
  description = "ARN of Firehose IAM role"
  value       = aws_iam_role.firehose_role.arn
}

output "orders_stream_name" {
  description = "Name of orders Firehose delivery stream"
  value       = aws_kinesis_firehose_delivery_stream.orders.name
}

output "orders_stream_arn" {
  description = "ARN of orders Firehose delivery stream"
  value       = aws_kinesis_firehose_delivery_stream.orders.arn
}

output "log_group_name" {
  description = "Name of CloudWatch Log Group for Firehose"
  value       = aws_cloudwatch_log_group.firehose_orders.name
}
