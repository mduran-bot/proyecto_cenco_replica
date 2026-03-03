# ============================================================================
# Tagging Module Variables
# Aligned with Corporate AWS Tagging Policy
# ============================================================================

variable "mandatory_tags" {
  description = "Mandatory tags that must be present on all resources (Corporate Policy)"
  type = object({
    Application  = string
    Environment  = string
    Owner        = string
    CostCenter   = string
    BusinessUnit = string
    Country      = string
    Criticality  = string
  })

  validation {
    condition     = length(var.mandatory_tags.Application) > 0
    error_message = "Application tag cannot be empty."
  }

  validation {
    condition     = contains(["prod", "qa", "dev", "uat", "sandbox"], var.mandatory_tags.Environment)
    error_message = "Environment must be one of: prod, qa, dev, uat, sandbox."
  }

  validation {
    condition     = length(var.mandatory_tags.Owner) > 0
    error_message = "Owner tag cannot be empty."
  }

  validation {
    condition     = length(var.mandatory_tags.CostCenter) > 0
    error_message = "CostCenter tag cannot be empty."
  }

  validation {
    condition     = length(var.mandatory_tags.BusinessUnit) > 0
    error_message = "BusinessUnit tag cannot be empty."
  }

  validation {
    condition     = length(var.mandatory_tags.Country) > 0
    error_message = "Country tag cannot be empty."
  }

  validation {
    condition     = contains(["high", "medium", "low"], var.mandatory_tags.Criticality)
    error_message = "Criticality must be one of: high, medium, low."
  }
}

variable "optional_tags" {
  description = "Optional tags to apply to resources"
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for key, value in var.optional_tags :
      can(regex("^[A-Za-z0-9_-]+$", key)) && length(value) <= 256
    ])
    error_message = "Optional tag keys must be alphanumeric with hyphens/underscores, and values must be <= 256 characters."
  }
}

variable "include_created_date" {
  description = "Automatically add CreatedDate tag if not provided"
  type        = bool
  default     = true
}
