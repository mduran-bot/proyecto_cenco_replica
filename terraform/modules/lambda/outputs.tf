# ============================================================================
# Lambda Module Outputs
# ============================================================================

# IAM Role
output "lambda_execution_role_arn" {
  description = "ARN of Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "lambda_execution_role_name" {
  description = "Name of Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.name
}

# Webhook Processor Function
output "webhook_processor_function_name" {
  description = "Name of webhook processor Lambda function"
  value       = var.create_webhook_processor ? aws_lambda_function.webhook_processor[0].function_name : ""
}

output "webhook_processor_function_arn" {
  description = "ARN of webhook processor Lambda function"
  value       = var.create_webhook_processor ? aws_lambda_function.webhook_processor[0].arn : ""
}

output "webhook_processor_invoke_arn" {
  description = "Invoke ARN of webhook processor Lambda function"
  value       = var.create_webhook_processor ? aws_lambda_function.webhook_processor[0].invoke_arn : ""
}

# Data Enrichment Function
output "data_enrichment_function_name" {
  description = "Name of data enrichment Lambda function"
  value       = var.create_data_enrichment ? aws_lambda_function.data_enrichment[0].function_name : ""
}

output "data_enrichment_function_arn" {
  description = "ARN of data enrichment Lambda function"
  value       = var.create_data_enrichment ? aws_lambda_function.data_enrichment[0].arn : ""
}

# API Polling Function
output "api_polling_function_name" {
  description = "Name of API polling Lambda function"
  value       = var.create_api_polling ? aws_lambda_function.api_polling[0].function_name : ""
}

output "api_polling_function_arn" {
  description = "ARN of API polling Lambda function"
  value       = var.create_api_polling ? aws_lambda_function.api_polling[0].arn : ""
}

# All Function ARNs
output "all_function_arns" {
  description = "Map of all Lambda function ARNs"
  value = {
    webhook_processor = var.create_webhook_processor ? aws_lambda_function.webhook_processor[0].arn : ""
    data_enrichment   = var.create_data_enrichment ? aws_lambda_function.data_enrichment[0].arn : ""
    api_polling       = var.create_api_polling ? aws_lambda_function.api_polling[0].arn : ""
  }
}

# Log Groups
output "log_group_names" {
  description = "Map of CloudWatch Log Group names"
  value = {
    webhook_processor = var.create_webhook_processor ? aws_cloudwatch_log_group.webhook_processor[0].name : ""
    data_enrichment   = var.create_data_enrichment ? aws_cloudwatch_log_group.data_enrichment[0].name : ""
    api_polling       = var.create_api_polling ? aws_cloudwatch_log_group.api_polling[0].name : ""
  }
}
