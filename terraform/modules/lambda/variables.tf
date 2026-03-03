# ============================================================================
# Lambda Module Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
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
  description = "List of private subnet IDs for Lambda functions"
  type        = list(string)
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  type        = string
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
  default     = ""
}

variable "scripts_bucket_arn" {
  description = "ARN of scripts S3 bucket"
  type        = string
}

# ============================================================================
# Kinesis Firehose Configuration
# ============================================================================

variable "firehose_delivery_stream_name" {
  description = "Name of Kinesis Firehose delivery stream"
  type        = string
  default     = ""
}

variable "firehose_delivery_stream_arn" {
  description = "ARN of Kinesis Firehose delivery stream"
  type        = string
  default     = ""
}

# ============================================================================
# API Gateway Configuration
# ============================================================================

variable "api_gateway_execution_arn" {
  description = "Execution ARN of API Gateway (for Lambda permissions)"
  type        = string
  default     = ""
}

# ============================================================================
# Lambda Function Configuration
# ============================================================================

variable "lambda_runtime" {
  description = "Lambda runtime (e.g., python3.11, nodejs18.x)"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 90
}

variable "lambda_environment_variables" {
  description = "Additional environment variables for Lambda functions"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Function Creation Flags
# ============================================================================

variable "create_webhook_processor" {
  description = "Create webhook processor Lambda function"
  type        = bool
  default     = true
}

variable "create_data_enrichment" {
  description = "Create data enrichment Lambda function"
  type        = bool
  default     = true
}

variable "create_api_polling" {
  description = "Create API polling Lambda function"
  type        = bool
  default     = true
}

# ============================================================================
# Deployment Package Paths
# ============================================================================

variable "webhook_processor_zip_path" {
  description = "Path to webhook processor deployment package (.zip)"
  type        = string
  default     = ""
}

variable "data_enrichment_zip_path" {
  description = "Path to data enrichment deployment package (.zip)"
  type        = string
  default     = ""
}

variable "api_polling_zip_path" {
  description = "Path to API polling deployment package (.zip)"
  type        = string
  default     = ""
}
