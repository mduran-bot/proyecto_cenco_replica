# ============================================================================
# S3 Module Variables
# ============================================================================

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.bucket_name))
    error_message = "Bucket name must be lowercase alphanumeric with hyphens."
  }
}

variable "enable_versioning" {
  description = "Enable versioning for the bucket"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of KMS key for server-side encryption (null for AWS managed key)"
  type        = string
  default     = null
}

variable "intelligent_tiering_days" {
  description = "Days before transitioning to Intelligent Tiering"
  type        = number
  default     = 30
}

variable "glacier_transition_days" {
  description = "Days before transitioning to Glacier"
  type        = number
  default     = 90
}

variable "expiration_days" {
  description = "Days before objects expire and are deleted"
  type        = number
  default     = 365
}

variable "logging_bucket_name" {
  description = "Name of the bucket for access logs (empty to disable logging)"
  type        = string
  default     = ""
}

variable "lambda_notifications" {
  description = "List of Lambda function notifications"
  type = list(object({
    function_arn  = string
    events        = list(string)
    filter_prefix = string
    filter_suffix = string
  }))
  default = []
}

variable "sqs_notifications" {
  description = "List of SQS queue notifications"
  type = list(object({
    queue_arn     = string
    events        = list(string)
    filter_prefix = string
    filter_suffix = string
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
