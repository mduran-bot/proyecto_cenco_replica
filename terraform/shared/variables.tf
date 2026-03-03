# Common Variables for Terraform Configuration
#
# These variables are used across all environments and modules.
# Environment-specific values should be defined in {environment}.tfvars files.

# ============================================================================
# AWS Authentication Variables
# ============================================================================

variable "aws_access_key_id" {
  description = "AWS Access Key ID for authentication"
  type        = string
  sensitive   = true
  default     = null
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key for authentication"
  type        = string
  sensitive   = true
  default     = null
}

variable "aws_session_token" {
  description = "AWS Session Token for temporary credentials (optional)"
  type        = string
  sensitive   = true
  default     = null
}

# ============================================================================
# Region and Environment Configuration
# ============================================================================

variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "AWS region must be a valid region format (e.g., us-east-1)."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# ============================================================================
# Project Identification
# ============================================================================

variable "project_name" {
  description = "Name of the project for resource naming and tagging"
  type        = string
  default     = "janis-cencosud-integration"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "owner" {
  description = "Owner or team responsible for the infrastructure"
  type        = string
  default     = "cencosud-data-team"
}

variable "cost_center" {
  description = "Cost center code for billing and cost allocation"
  type        = string
  default     = "data-integration"
}

# ============================================================================
# Network Configuration
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones to use for deployment"
  type        = list(string)
  default     = ["us-east-1a"]

  validation {
    condition     = length(var.availability_zones) > 0
    error_message = "At least one availability zone must be specified."
  }
}

# ============================================================================
# Tagging Configuration
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Local Values
# ============================================================================

locals {
  # Common name prefix for resources
  name_prefix = "${var.project_name}-${var.environment}"

  # Merged tags combining required and additional tags
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
      CreatedDate = formatdate("YYYY-MM-DD", timestamp())
    },
    var.additional_tags
  )
}
