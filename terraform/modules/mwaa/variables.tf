# ============================================================================
# MWAA Module Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for resource naming"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Network Configuration
# ============================================================================

variable "private_subnet_ids" {
  description = "List of private subnet IDs for MWAA"
  type        = list(string)
}

variable "mwaa_security_group_id" {
  description = "Security group ID for MWAA"
  type        = string
}

# ============================================================================
# S3 Bucket Configuration
# ============================================================================

variable "scripts_bucket_arn" {
  description = "ARN of scripts S3 bucket (for DAGs)"
  type        = string
}

variable "bronze_bucket_arn" {
  description = "ARN of Bronze layer S3 bucket"
  type        = string
}

variable "silver_bucket_arn" {
  description = "ARN of Silver layer S3 bucket"
  type        = string
}

variable "gold_bucket_arn" {
  description = "ARN of Gold layer S3 bucket"
  type        = string
}

# ============================================================================
# Lambda Configuration
# ============================================================================

variable "lambda_function_arns" {
  description = "List of Lambda function ARNs that MWAA can invoke"
  type        = list(string)
  default     = []
}

# ============================================================================
# MWAA Configuration
# ============================================================================

variable "create_mwaa_environment" {
  description = "Create MWAA environment"
  type        = bool
  default     = true
}

variable "airflow_version" {
  description = "Airflow version"
  type        = string
  default     = "2.7.2"
}

variable "environment_class" {
  description = "Environment class (mw1.small, mw1.medium, mw1.large)"
  type        = string
  default     = "mw1.small"
}

variable "max_workers" {
  description = "Maximum number of workers"
  type        = number
  default     = 10
}

variable "min_workers" {
  description = "Minimum number of workers"
  type        = number
  default     = 1
}

variable "requirements_s3_path" {
  description = "S3 path to requirements.txt (optional)"
  type        = string
  default     = null
}

variable "plugins_s3_path" {
  description = "S3 path to plugins.zip (optional)"
  type        = string
  default     = null
}

# ============================================================================
# Logging Configuration
# ============================================================================

variable "dag_processing_log_level" {
  description = "Log level for DAG processing (CRITICAL, ERROR, WARNING, INFO, DEBUG)"
  type        = string
  default     = "INFO"
}

variable "scheduler_log_level" {
  description = "Log level for scheduler"
  type        = string
  default     = "INFO"
}

variable "task_log_level" {
  description = "Log level for tasks"
  type        = string
  default     = "INFO"
}

variable "webserver_log_level" {
  description = "Log level for webserver"
  type        = string
  default     = "INFO"
}

variable "worker_log_level" {
  description = "Log level for workers"
  type        = string
  default     = "INFO"
}

# ============================================================================
# Airflow Configuration Options
# ============================================================================

variable "airflow_configuration_options" {
  description = "Airflow configuration options"
  type        = map(string)
  default     = {}
}
