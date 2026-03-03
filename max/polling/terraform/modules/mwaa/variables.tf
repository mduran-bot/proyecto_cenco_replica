# ============================================================================
# MWAA Module - Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where MWAA will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for MWAA"
  type        = list(string)
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "airflow_version" {
  description = "Airflow version for MWAA"
  type        = string
  default     = "2.7.2"
}

variable "environment_class" {
  description = "MWAA environment class (mw1.small, mw1.medium, mw1.large)"
  type        = string
  default     = "mw1.small"
}

variable "min_workers" {
  description = "Minimum number of workers"
  type        = number
  default     = 1
}

variable "max_workers" {
  description = "Maximum number of workers"
  type        = number
  default     = 3
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB polling control table"
  type        = string
}

variable "bronze_bucket_name" {
  description = "Name of the S3 Bronze bucket"
  type        = string
}

variable "secrets_manager_arns" {
  description = "List of Secrets Manager ARNs for API credentials"
  type        = list(string)
}

variable "sns_topic_arn" {
  description = "ARN of the SNS topic for error notifications"
  type        = string
}

variable "execution_role_arn" {
  description = "ARN of existing IAM role for MWAA execution"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
