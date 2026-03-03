# ============================================================================
# MWAA Module Outputs
# ============================================================================

output "mwaa_execution_role_arn" {
  description = "ARN of MWAA execution role"
  value       = aws_iam_role.mwaa_execution_role.arn
}

output "mwaa_execution_role_name" {
  description = "Name of MWAA execution role"
  value       = aws_iam_role.mwaa_execution_role.name
}

output "mwaa_environment_arn" {
  description = "ARN of MWAA environment"
  value       = var.create_mwaa_environment ? aws_mwaa_environment.main[0].arn : ""
}

output "mwaa_environment_name" {
  description = "Name of MWAA environment"
  value       = var.create_mwaa_environment ? aws_mwaa_environment.main[0].name : ""
}

output "mwaa_webserver_url" {
  description = "Webserver URL of MWAA environment"
  value       = var.create_mwaa_environment ? aws_mwaa_environment.main[0].webserver_url : ""
}

output "mwaa_service_role_arn" {
  description = "Service role ARN of MWAA environment"
  value       = var.create_mwaa_environment ? aws_mwaa_environment.main[0].service_role_arn : ""
}
