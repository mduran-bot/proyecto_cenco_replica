# Terraform and Provider Configuration
#
# This file defines the required Terraform version and AWS provider configuration.
# Credentials should be passed via environment variables or command-line parameters.

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS Provider Configuration
# 
# Authentication methods (in order of precedence):
# 1. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
# 2. Command-line variables: -var="aws_access_key_id=..." -var="aws_secret_access_key=..."
# 3. Shared credentials file: ~/.aws/credentials
#
# NEVER hardcode credentials in this file!

provider "aws" {
  region = var.aws_region

  # Optional: Pass credentials via variables (recommended for automation)
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
  token      = var.aws_session_token

  # Apply default tags to all resources
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
