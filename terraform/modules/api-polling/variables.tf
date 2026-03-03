# ============================================================================
# API Polling System Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
  
  validation {
    condition     = length(var.name_prefix) > 0 && length(var.name_prefix) <= 50
    error_message = "Name prefix must be between 1 and 50 characters."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod", "localstack"], var.environment)
    error_message = "Environment must be dev, staging, prod, or localstack."
  }
}

# DynamoDB Configuration
variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for DynamoDB"
  type        = bool
  default     = true
}

# SNS Configuration
variable "error_notification_emails" {
  description = "List of email addresses for error notifications"
  type        = list(string)
  default     = []
}

# MWAA Configuration
variable "mwaa_environment_arn" {
  description = "ARN of the MWAA environment"
  type        = string
}

# S3 Con