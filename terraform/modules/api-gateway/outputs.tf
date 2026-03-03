# ============================================================================
# API Gateway Module Outputs
# ============================================================================

output "rest_api_id" {
  description = "ID of the REST API"
  value       = aws_api_gateway_rest_api.webhooks.id
}

output "rest_api_arn" {
  description = "ARN of the REST API"
  value       = aws_api_gateway_rest_api.webhooks.arn
}

output "rest_api_execution_arn" {
  description = "Execution ARN of the REST API"
  value       = aws_api_gateway_rest_api.webhooks.execution_arn
}

output "stage_name" {
  description = "Name of the API Gateway stage"
  value       = aws_api_gateway_stage.main.stage_name
}

output "stage_invoke_url" {
  description = "Invoke URL of the API Gateway stage"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "webhook_endpoint_url" {
  description = "Full URL for webhook endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/webhooks/{entity}"
}

output "api_key_id" {
  description = "ID of the API key (if created)"
  value       = var.create_api_key ? aws_api_gateway_api_key.main[0].id : ""
}

output "api_key_value" {
  description = "Value of the API key (if created)"
  value       = var.create_api_key ? aws_api_gateway_api_key.main[0].value : ""
  sensitive   = true
}

output "usage_plan_id" {
  description = "ID of the usage plan (if created)"
  value       = var.create_usage_plan ? aws_api_gateway_usage_plan.main[0].id : ""
}

output "log_group_name" {
  description = "Name of CloudWatch Log Group for API Gateway"
  value       = aws_cloudwatch_log_group.api_gateway.name
}
