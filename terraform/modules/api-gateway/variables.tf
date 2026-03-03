# ============================================================================
# API Gateway Module Variables
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
# Lambda Integration
# ============================================================================

variable "webhook_processor_invoke_arn" {
  description = "Invoke ARN of webhook processor Lambda function"
  type        = string
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
# Usage Plan Configuration
# ============================================================================

variable "create_usage_plan" {
  description = "Create API Gateway usage plan"
  type        = bool
  default     = true
}

variable "quota_limit" {
  description = "Maximum number of requests per day"
  type        = number
  default     = 100000
}

variable "throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 5000
}

variable "throttle_rate_limit" {
  description = "API Gateway throttle rate limit (requests per second)"
  type        = number
  default     = 2000
}

# ============================================================================
# API Key Configuration
# ============================================================================

variable "create_api_key" {
  description = "Create API key for authentication"
  type        = bool
  default     = false
}
