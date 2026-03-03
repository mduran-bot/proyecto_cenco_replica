# ============================================================================
# Example: Basic EventBridge Configuration for API Polling
# ============================================================================

# This example shows how to use the EventBridge module to configure
# scheduled polling of Janis APIs using MWAA (Apache Airflow)

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
  region = var.aws_region
}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  name_prefix = "janis-cencosud"
  environment = "prod"
  
  common_tags = {
    Environment = local.environment
    Project     = "janis-cencosud"
    ManagedBy   = "terraform"
    Component   = "api-polling"
  }
}

# ============================================================================
# EventBridge Module
# ============================================================================

module "eventbridge" {
  source = "../../"

  name_prefix          = local.name_prefix
  environment          = local.environment
  mwaa_environment_arn = var.mwaa_environment_arn

  # Polling schedules according to requirements
  order_polling_rate   = "5 minutes"   # Requirement 1.2
  product_polling_rate = "1 hour"      # Requirement 1.3
  stock_polling_rate   = "10 minutes"  # Requirement 1.4
  price_polling_rate   = "30 minutes"  # Requirement 1.5
  store_polling_rate   = "1 day"       # Requirement 1.6

  tags = local.common_tags
}

# ============================================================================
# Outputs
# ============================================================================

output "event_bus_arn" {
  description = "ARN of the EventBridge event bus"
  value       = module.eventbridge.event_bus_arn
}

output "rule_arns" {
  description = "ARNs of all EventBridge rules"
  value       = module.eventbridge.rule_arns
}

output "dlq_url" {
  description = "URL of the Dead Letter Queue"
  value       = module.eventbridge.dlq_url
}

output "iam_role_arn" {
  description = "ARN of IAM role for EventBridge to MWAA"
  value       = module.eventbridge.iam_role_arn
}
