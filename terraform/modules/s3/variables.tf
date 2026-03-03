# ============================================================================
# S3 Module Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for resource naming (e.g., janis-cencosud-dev)"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all S3 resources"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Bronze Layer Lifecycle Configuration
# ============================================================================

variable "bronze_glacier_transition_days" {
  description = "Days before transitioning Bronze data to Glacier"
  type        = number
  default     = 90
}

variable "bronze_expiration_days" {
  description = "Days before expiring Bronze data"
  type        = number
  default     = 365
}

# ============================================================================
# Silver Layer Lifecycle Configuration
# ============================================================================

variable "silver_glacier_transition_days" {
  description = "Days before transitioning Silver data to Glacier"
  type        = number
  default     = 180
}

variable "silver_expiration_days" {
  description = "Days before expiring Silver data"
  type        = number
  default     = 730
}

# ============================================================================
# Gold Layer Lifecycle Configuration
# ============================================================================

variable "gold_intelligent_tiering_days" {
  description = "Days before transitioning Gold data to Intelligent Tiering"
  type        = number
  default     = 30
}

# ============================================================================
# Logs Lifecycle Configuration
# ============================================================================

variable "logs_expiration_days" {
  description = "Days before expiring log files"
  type        = number
  default     = 365
}
