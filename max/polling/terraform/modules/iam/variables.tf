# ============================================================================
# IAM Module Variables - API Polling System
# ============================================================================

# MWAA Role Configuration
variable "mwaa_role_name" {
  description = "Name of the MWAA execution role"
  type        = string
}

variable "mwaa_environment_arn" {
  description = "ARN of the MWAA environment"
  type        = string
}

# EventBridge Role Configuration
variable "eventbridge_role_name" {
  description = "Name of the EventBridge role for MWAA invocation"
  type        = string
}

# Resource ARNs
variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB polling control table"
  type        = string
}

variable "sns_topic_arn" {
  description = "ARN of the SNS error notification topic"
  type        = string
}

variable "s3_bucket_arns" {
  description = "List of S3 bucket ARNs (DAGs, staging, etc.)"
  type        = list(string)
}

variable "secrets_manager_arns" {
  description = "List of Secrets Manager secret ARNs"
  type        = list(string)
  default     = []
}

# AWS Configuration
variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
