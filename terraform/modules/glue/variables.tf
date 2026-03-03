# ============================================================================
# AWS Glue Module Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for resource naming"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# ============================================================================
# S3 Bucket Configuration
# ============================================================================

variable "bronze_bucket_name" {
  description = "Name of Bronze layer S3 bucket"
  type        = string
}

variable "bronze_bucket_arn" {
  description = "ARN of Bronze layer S3 bucket"
  type        = string
}

variable "silver_bucket_name" {
  description = "Name of Silver layer S3 bucket"
  type        = string
}

variable "silver_bucket_arn" {
  description = "ARN of Silver layer S3 bucket"
  type        = string
}

variable "gold_bucket_name" {
  description = "Name of Gold layer S3 bucket"
  type        = string
}

variable "gold_bucket_arn" {
  description = "ARN of Gold layer S3 bucket"
  type        = string
}

variable "scripts_bucket_name" {
  description = "Name of scripts S3 bucket"
  type        = string
}

variable "scripts_bucket_arn" {
  description = "ARN of scripts S3 bucket"
  type        = string
}

# ============================================================================
# Glue Job Configuration
# ============================================================================

variable "glue_worker_type" {
  description = "Glue worker type (G.1X, G.2X, G.025X)"
  type        = string
  default     = "G.1X"
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 2
}

variable "create_bronze_to_silver_job" {
  description = "Create Bronze to Silver Glue job"
  type        = bool
  default     = true
}

variable "create_silver_to_gold_job" {
  description = "Create Silver to Gold Glue job"
  type        = bool
  default     = true
}

# ============================================================================
# Logging Configuration
# ============================================================================

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 90
}
