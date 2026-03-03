# ============================================================================
# Kinesis Firehose Module Variables
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
# S3 Configuration
# ============================================================================

variable "bronze_bucket_arn" {
  description = "ARN of Bronze layer S3 bucket"
  type        = string
}

# ============================================================================
# Buffering Configuration
# ============================================================================

variable "buffering_size" {
  description = "Buffer size in MB before delivering to S3"
  type        = number
  default     = 5
}

variable "buffering_interval" {
  description = "Buffer interval in seconds before delivering to S3"
  type        = number
  default     = 300
}

variable "compression_format" {
  description = "Compression format (GZIP, SNAPPY, ZIP, UNCOMPRESSED)"
  type        = string
  default     = "GZIP"
}

# ============================================================================
# Lambda Transformation
# ============================================================================

variable "transformation_lambda_arn" {
  description = "ARN of Lambda function for data transformation (optional)"
  type        = string
  default     = ""
}

# ============================================================================
# Logging Configuration
# ============================================================================

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 90
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "alarm_sns_topic_arn" {
  description = "SNS Topic ARN for CloudWatch alarms"
  type        = string
  default     = ""
}
