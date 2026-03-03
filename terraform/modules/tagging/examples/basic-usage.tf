# ============================================================================
# Tagging Module - Basic Usage Example
# ============================================================================

# Example 1: Basic VPC tagging
module "vpc_tags" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "production"
    Component   = "vpc"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  optional_tags = {
    Purpose = "network-infrastructure"
  }

  include_created_date = true
}

resource "aws_vpc" "example" {
  cidr_block = "10.0.0.0/16"

  tags = module.vpc_tags.tags
}

# Example 2: Lambda function tagging with runtime info
module "lambda_tags" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "production"
    Component   = "lambda-webhook-processor"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  optional_tags = {
    Runtime   = "python3.11"
    Purpose   = "webhook-ingestion"
    CreatedBy = "terraform"
  }
}

# Example 3: S3 bucket tagging with lifecycle info
module "s3_tags" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "production"
    Component   = "s3-datalake-bronze"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  optional_tags = {
    DataClassification = "internal"
    RetentionPeriod    = "90-days"
    Purpose            = "data-lake-bronze-layer"
  }
}

# Example 4: Using variables for consistency
variable "project_name" {
  default = "janis-cencosud-integration"
}

variable "environment" {
  default = "production"
}

variable "owner" {
  default = "cencosud-data-team"
}

variable "cost_center" {
  default = "data-integration"
}

module "reusable_tags" {
  source = "../"

  mandatory_tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "security-group"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }

  optional_tags = {
    ManagedBy = "terraform"
  }
}

# Example 5: Validation output check
output "tags_validated" {
  description = "Check if all tag validations passed"
  value       = module.vpc_tags.validation_passed
}

output "total_tags" {
  description = "Total number of tags applied"
  value       = module.vpc_tags.tag_count
}

output "applied_tags" {
  description = "All tags that will be applied"
  value       = module.vpc_tags.tags
}
