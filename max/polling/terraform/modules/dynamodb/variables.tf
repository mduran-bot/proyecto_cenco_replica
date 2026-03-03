# ============================================================================
# DynamoDB Module Variables
# ============================================================================

variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string

  validation {
    condition     = length(var.table_name) > 0 && length(var.table_name) <= 255
    error_message = "Table name must be between 1 and 255 characters."
  }
}

variable "billing_mode" {
  description = "Billing mode for the table (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PROVISIONED", "PAY_PER_REQUEST"], var.billing_mode)
    error_message = "Billing mode must be either PROVISIONED or PAY_PER_REQUEST."
  }
}

variable "read_capacity" {
  description = "Read capacity units (only used if billing_mode is PROVISIONED)"
  type        = number
  default     = 5
}

variable "write_capacity" {
  description = "Write capacity units (only used if billing_mode is PROVISIONED)"
  type        = number
  default     = 5
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for the table"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of KMS key for server-side encryption (null for AWS managed key)"
  type        = string
  default     = null
}

variable "ttl_attribute_name" {
  description = "Name of the TTL attribute (empty string to disable TTL)"
  type        = string
  default     = ""
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms for the table"
  type        = bool
  default     = true
}

variable "alarm_sns_topic_arn" {
  description = "SNS Topic ARN for CloudWatch alarms"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
