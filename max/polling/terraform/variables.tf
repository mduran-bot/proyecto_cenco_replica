# ============================================================================
# API Polling System - Variables
# ============================================================================

# ============================================================================
# AWS Configuration
# ============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID"
  type        = string
  sensitive   = true
  default     = null
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
  default     = null
}

variable "aws_session_token" {
  description = "AWS Session Token (optional for STS)"
  type        = string
  sensitive   = true
  default     = null
}

# ============================================================================
# LocalStack Configuration
# ============================================================================

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL (empty for AWS)"
  type        = string
  default     = ""
}

variable "localstack_s3_endpoint" {
  description = "LocalStack S3 endpoint URL (empty to use localstack_endpoint)"
  type        = string
  default     = ""
}

# ============================================================================
# Project Configuration
# ============================================================================

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod", "localstack"], var.environment)
    error_message = "Environment must be dev, staging, prod, or localstack."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "janis-polling"
}

# ============================================================================
# DynamoDB Configuration
# ============================================================================

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

# ============================================================================
# S3 Configuration
# ============================================================================

variable "enable_s3_versioning" {
  description = "Enable versioning for S3 bucket"
  type        = bool
  default     = true
}

variable "s3_intelligent_tiering_days" {
  description = "Days before transitioning to Intelligent Tiering"
  type        = number
  default     = 30
}

variable "s3_glacier_transition_days" {
  description = "Days before transitioning to Glacier"
  type        = number
  default     = 90
}

variable "s3_expiration_days" {
  description = "Days before objects expire"
  type        = number
  default     = 365
}

# ============================================================================
# SNS Configuration
# ============================================================================

variable "error_notification_emails" {
  description = "List of email addresses for error notifications"
  type        = list(string)
  default     = []
}

# ============================================================================
# VPC Configuration
# ============================================================================

variable "vpc_id" {
  description = "VPC ID where MWAA will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for MWAA (minimum 2 in different AZs)"
  type        = list(string)
  
  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "At least 2 private subnets in different AZs are required for MWAA."
  }
}

# ============================================================================
# MWAA Configuration
# ============================================================================

variable "airflow_version" {
  description = "Airflow version for MWAA"
  type        = string
  default     = "2.7.2"
}

variable "environment_class" {
  description = "MWAA environment class (mw1.small, mw1.medium, mw1.large)"
  type        = string
  default     = "mw1.small"
  
  validation {
    condition     = contains(["mw1.small", "mw1.medium", "mw1.large"], var.environment_class)
    error_message = "Environment class must be mw1.small, mw1.medium, or mw1.large."
  }
}

variable "min_workers" {
  description = "Minimum number of MWAA workers"
  type        = number
  default     = 1
}

variable "max_workers" {
  description = "Maximum number of MWAA workers"
  type        = number
  default     = 3
}

# ============================================================================
# S3 Bronze Bucket Configuration
# ============================================================================

variable "bronze_bucket_name" {
  description = "Name of the S3 Bronze bucket for data output"
  type        = string
}

# ============================================================================
# IAM Roles (EXISTENTES - no se crean)
# ============================================================================

variable "mwaa_execution_role_arn" {
  description = "ARN del rol IAM existente para MWAA (debe tener permisos para DynamoDB, S3, Secrets Manager, SNS)"
  type        = string
}

variable "eventbridge_role_arn" {
  description = "ARN del rol IAM existente para EventBridge (debe tener permiso airflow:CreateCliToken)"
  type        = string
}

# ============================================================================
# Secrets Manager Configuration
# ============================================================================

variable "secrets_manager_arns" {
  description = "List of Secrets Manager secret ARNs for API credentials"
  type        = list(string)
  default     = []
}

# ============================================================================
# Multi-Tenant Configuration
# ============================================================================

variable "clients" {
  description = "List of client identifiers (metro, wongio, etc.)"
  type        = list(string)
  default     = ["wongio"]
}

# ============================================================================
# EventBridge Configuration
# ============================================================================

variable "polling_rate_minutes" {
  description = "Polling rate in minutes for all data types"
  type        = number
  default     = 5
  
  validation {
    condition     = var.polling_rate_minutes >= 1 && var.polling_rate_minutes <= 60
    error_message = "Polling rate must be between 1 and 60 minutes."
  }
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "enable_monitoring" {
  description = "Enable CloudWatch alarms and monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}
