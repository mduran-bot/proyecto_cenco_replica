# ============================================================================
# MWAA Module - Outputs
# ============================================================================

output "mwaa_environment_arn" {
  description = "ARN of the MWAA environment"
  value       = aws_mwaa_environment.this.arn
}

output "mwaa_environment_name" {
  description = "Name of the MWAA environment"
  value       = aws_mwaa_environment.this.name
}

output "mwaa_webserver_url" {
  description = "Webserver URL of the MWAA environment"
  value       = aws_mwaa_environment.this.webserver_url
}

output "mwaa_execution_role_arn" {
  description = "ARN of the MWAA execution role (provided externally)"
  value       = var.execution_role_arn
}

output "mwaa_s3_bucket_name" {
  description = "Name of the S3 bucket for MWAA DAGs"
  value       = aws_s3_bucket.mwaa.id
}

output "mwaa_s3_bucket_arn" {
  description = "ARN of the S3 bucket for MWAA DAGs"
  value       = aws_s3_bucket.mwaa.arn
}

output "mwaa_security_group_id" {
  description = "ID of the MWAA security group"
  value       = aws_security_group.mwaa.id
}
