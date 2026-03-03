# ============================================================================
# Tagging Module - Integration with AWS Provider Default Tags
# ============================================================================
# This example shows how to use the tagging module alongside AWS provider
# default_tags for comprehensive tag management

# ============================================================================
# Provider Configuration with Default Tags
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  # Default tags applied to ALL resources automatically
  default_tags {
    tags = {
      Project     = "janis-cencosud-integration"
      Environment = "production"
      ManagedBy   = "terraform"
      Owner       = "cencosud-data-team"
      CostCenter  = "data-integration"
    }
  }
}

# ============================================================================
# Component-Specific Tags Using Tagging Module
# ============================================================================

# VPC Component Tags
module "vpc_tags" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "production"
    Component   = "vpc" # Component-specific
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  optional_tags = {
    Purpose = "network-infrastructure"
  }
}

# Lambda Component Tags
module "lambda_tags" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "production"
    Component   = "lambda-webhook-processor" # Component-specific
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  optional_tags = {
    Runtime = "python3.11"
    Purpose = "webhook-ingestion"
  }
}

# ============================================================================
# Resource Creation with Combined Tags
# ============================================================================

# VPC with component-specific tags
# Provider default_tags will be automatically merged
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  # Only need to specify component-specific tags
  # Provider default_tags are automatically applied
  tags = {
    Component = "vpc"
    Purpose   = "network-infrastructure"
  }
}

# Lambda with component-specific tags
resource "aws_lambda_function" "webhook_processor" {
  function_name = "webhook-processor"
  runtime       = "python3.11"
  handler       = "index.handler"
  role          = "arn:aws:iam::123456789012:role/lambda-role"

  # Component-specific tags
  # Provider default_tags are automatically applied
  tags = {
    Component = "lambda-webhook-processor"
    Runtime   = "python3.11"
    Purpose   = "webhook-ingestion"
  }
}

# ============================================================================
# Best Practice: Use Tagging Module for Validation
# ============================================================================

# Use the tagging module to validate tags before applying
# This ensures consistency and catches errors early

module "validated_tags" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "production"
    Component   = "s3-datalake"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  optional_tags = {
    DataClassification = "internal"
    RetentionPeriod    = "90-days"
  }
}

# Apply validated tags to resource
resource "aws_s3_bucket" "datalake" {
  bucket = "cencosud-datalake-bronze"

  # Use validated tags from module
  tags = module.validated_tags.tags
}

# ============================================================================
# Outputs
# ============================================================================

output "vpc_tags_applied" {
  description = "Tags applied to VPC (includes provider defaults)"
  value       = aws_vpc.main.tags_all
}

output "lambda_tags_applied" {
  description = "Tags applied to Lambda (includes provider defaults)"
  value       = aws_lambda_function.webhook_processor.tags_all
}

output "s3_tags_applied" {
  description = "Tags applied to S3 bucket (validated)"
  value       = aws_s3_bucket.datalake.tags_all
}

output "validation_status" {
  description = "Tag validation status"
  value = {
    vpc_validated    = module.vpc_tags.validation_passed
    lambda_validated = module.lambda_tags.validation_passed
    s3_validated     = module.validated_tags.validation_passed
  }
}
