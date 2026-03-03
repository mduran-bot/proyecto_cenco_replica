# ============================================================================
# API Polling System - Main Configuration
# ============================================================================
# This configuration orchestrates all infrastructure components for the
# API polling system including DynamoDB, S3, SNS, and IAM roles.
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

# ============================================================================
# Provider Configuration with LocalStack Support
# ============================================================================

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
  token      = var.aws_session_token

  # LocalStack endpoints (only used when LOCALSTACK_ENDPOINT is set)
  dynamic "endpoints" {
    for_each = var.localstack_endpoint != "" ? [1] : []
    content {
      apigateway     = var.localstack_endpoint
      cloudwatch     = var.localstack_endpoint
      cloudwatchlogs = var.localstack_endpoint
      dynamodb       = var.localstack_endpoint
      ec2            = var.localstack_endpoint
      events         = var.localstack_endpoint
      iam            = var.localstack_endpoint
      lambda         = var.localstack_endpoint
      s3             = var.localstack_s3_endpoint != "" ? var.localstack_s3_endpoint : var.localstack_endpoint
      secretsmanager = var.localstack_endpoint
      sns            = var.localstack_endpoint
      sqs            = var.localstack_endpoint
      sts            = var.localstack_endpoint
    }
  }

  # Skip credential validation for LocalStack
  skip_credentials_validation = var.localstack_endpoint != ""
  skip_metadata_api_check     = var.localstack_endpoint != ""
  skip_requesting_account_id  = var.localstack_endpoint != ""

  default_tags {
    tags = local.common_tags
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    Component   = "api-polling"
  }

  name_prefix = "${var.project_name}-${var.environment}"
}

# ============================================================================
# DynamoDB Control Table
# ============================================================================

module "polling_control_table" {
  source = "./modules/dynamodb"

  table_name                    = "${local.name_prefix}-polling-control"
  billing_mode                  = var.dynamodb_billing_mode
  enable_point_in_time_recovery = var.enable_point_in_time_recovery
  enable_alarms                 = var.enable_monitoring
  alarm_sns_topic_arn           = module.error_notification_topic.topic_arn

  tags = local.common_tags
}

# ============================================================================
# S3 Staging Bucket
# ============================================================================

module "polling_staging_bucket" {
  source = "./modules/s3"

  bucket_name              = "${local.name_prefix}-polling-staging"
  enable_versioning        = var.enable_s3_versioning
  intelligent_tiering_days = var.s3_intelligent_tiering_days
  glacier_transition_days  = var.s3_glacier_transition_days
  expiration_days          = var.s3_expiration_days

  tags = local.common_tags
}

# ============================================================================
# SNS Error Notification Topic
# ============================================================================

module "error_notification_topic" {
  source = "./modules/sns"

  topic_name       = "${local.name_prefix}-polling-errors"
  display_name     = "API Polling Errors - ${var.environment}"
  aws_account_id   = data.aws_caller_identity.current.account_id
  email_addresses  = var.error_notification_emails
  allowed_iam_arns = [var.mwaa_execution_role_arn]  # Usar rol existente
  enable_alarms    = var.enable_monitoring

  tags = local.common_tags
}

# ============================================================================
# CloudWatch Log Group
# ============================================================================

resource "aws_cloudwatch_log_group" "polling_logs" {
  name              = "/aws/api-polling/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-polling-logs"
    Purpose = "API Polling System Logs"
  })
}

# ============================================================================
# MWAA Environment
# ============================================================================

module "mwaa" {
  source = "./modules/mwaa"

  name_prefix         = local.name_prefix
  environment         = var.environment
  vpc_id              = var.vpc_id
  private_subnet_ids  = var.private_subnet_ids
  aws_region          = data.aws_region.current.name
  
  # MWAA Configuration
  airflow_version    = var.airflow_version
  environment_class  = var.environment_class
  min_workers        = var.min_workers
  max_workers        = var.max_workers
  
  # Resource ARNs
  dynamodb_table_arn   = module.polling_control_table.table_arn
  bronze_bucket_name   = var.bronze_bucket_name
  secrets_manager_arns = var.secrets_manager_arns
  sns_topic_arn        = module.error_notification_topic.topic_arn
  
  # IAM Role (EXISTENTE - no se crea)
  execution_role_arn = var.mwaa_execution_role_arn
  
  tags = local.common_tags
}

# ============================================================================
# EventBridge Scheduled Rules
# ============================================================================

module "eventbridge" {
  source = "./modules/eventbridge"

  name_prefix            = local.name_prefix
  mwaa_environment_arn   = module.mwaa.mwaa_environment_arn
  clients                = var.clients
  polling_rate_minutes   = var.polling_rate_minutes
  
  # IAM Role (EXISTENTE - no se crea)
  eventbridge_role_arn = var.eventbridge_role_arn
  
  tags = local.common_tags
}
