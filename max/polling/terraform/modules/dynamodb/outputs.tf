# ============================================================================
# DynamoDB Module Outputs
# ============================================================================

output "table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.polling_control.name
}

output "table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.polling_control.arn
}

output "table_id" {
  description = "ID of the DynamoDB table"
  value       = aws_dynamodb_table.polling_control.id
}

output "table_stream_arn" {
  description = "ARN of the DynamoDB table stream"
  value       = aws_dynamodb_table.polling_control.stream_arn
}

output "table_stream_label" {
  description = "Timestamp of the DynamoDB table stream"
  value       = aws_dynamodb_table.polling_control.stream_label
}
