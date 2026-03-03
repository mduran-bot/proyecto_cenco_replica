# ============================================================================
# SNS Module Variables
# ============================================================================

variable "topic_name" {
  description = "Name of the SNS topic"
  type        = string

  validation {
    condition     = length(var.topic_name) > 0 && length(var.topic_name) <= 256
    error_message = "Topic name must be between 1 and 256 characters."
  }
}

variable "display_name" {
  description = "Display name for the SNS topic"
  type        = string
  default     = ""
}

variable "fifo_topic" {
  description = "Whether the topic is FIFO (must end with .fifo)"
  type        = bool
  default     = false
}

variable "content_based_deduplication" {
  description = "Enable content-based deduplication for FIFO topics"
  type        = bool
  default     = false
}

variable "kms_master_key_id" {
  description = "KMS key ID for server-side encryption (null for AWS managed key)"
  type        = string
  default     = null
}

variable "allowed_services" {
  description = "List of AWS services allowed to publish to the topic"
  type        = list(string)
  default     = ["lambda.amazonaws.com", "events.amazonaws.com", "cloudwatch.amazonaws.com"]
}

variable "allowed_iam_arns" {
  description = "List of IAM role/user ARNs allowed to publish to the topic"
  type        = list(string)
  default     = []
}

variable "aws_account_id" {
  description = "AWS account ID for policy conditions"
  type        = string
}

variable "email_addresses" {
  description = "List of email addresses to subscribe to the topic"
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for email in var.email_addresses : can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email))
    ])
    error_message = "All email addresses must be valid."
  }
}

variable "sqs_queue_arns" {
  description = "List of SQS queue ARNs to subscribe to the topic"
  type        = list(string)
  default     = []
}

variable "lambda_function_arns" {
  description = "List of Lambda function ARNs to subscribe to the topic"
  type        = list(string)
  default     = []
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms for the topic"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
