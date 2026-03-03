# ============================================================================
# IAM Module Outputs - API Polling System
# ============================================================================

# MWAA Role Outputs
output "mwaa_role_arn" {
  description = "ARN of the MWAA execution role"
  value       = aws_iam_role.mwaa_execution.arn
}

output "mwaa_role_name" {
  description = "Name of the MWAA execution role"
  value       = aws_iam_role.mwaa_execution.name
}

output "mwaa_role_id" {
  description = "ID of the MWAA execution role"
  value       = aws_iam_role.mwaa_execution.id
}

# EventBridge Role Outputs
output "eventbridge_role_arn" {
  description = "ARN of the EventBridge role"
  value       = aws_iam_role.eventbridge_mwaa.arn
}

output "eventbridge_role_name" {
  description = "Name of the EventBridge role"
  value       = aws_iam_role.eventbridge_mwaa.name
}

output "eventbridge_role_id" {
  description = "ID of the EventBridge role"
  value       = aws_iam_role.eventbridge_mwaa.id
}
