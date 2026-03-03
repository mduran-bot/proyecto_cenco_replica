# ============================================================================
# Main Terraform Configuration
# Janis-Cencosud AWS Infrastructure
# ============================================================================

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # Corporate AWS Tagging Policy - Mandatory Tags
  common_tags = {
    Application  = var.application_name
    Environment  = var.environment
    Owner        = var.owner
    CostCenter   = var.cost_center
    BusinessUnit = var.business_unit
    Country      = var.country
    Criticality  = var.criticality
    ManagedBy    = "terraform"
  }

  # Merge with additional optional tags
  all_tags = merge(local.common_tags, var.additional_tags)
}

# ============================================================================
# VPC Module
# Creates VPC, Subnets, Internet Gateway, NAT Gateway, Route Tables
# ============================================================================

module "vpc" {
  source = "./modules/vpc"

  # Network Configuration
  vpc_cidr               = var.vpc_cidr
  public_subnet_a_cidr   = var.public_subnet_a_cidr
  private_subnet_1a_cidr = var.private_subnet_1a_cidr
  private_subnet_2a_cidr = var.private_subnet_2a_cidr

  # Multi-AZ Configuration
  enable_multi_az        = var.enable_multi_az
  public_subnet_b_cidr   = var.public_subnet_b_cidr
  private_subnet_1b_cidr = var.private_subnet_1b_cidr
  private_subnet_2b_cidr = var.private_subnet_2b_cidr

  # General Configuration
  aws_region  = var.aws_region
  name_prefix = local.name_prefix

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# Security Groups Module
# Creates all security groups for the infrastructure
# ============================================================================

module "security_groups" {
  source = "./modules/security-groups"

  vpc_id      = module.vpc.vpc_id
  vpc_cidr    = var.vpc_cidr
  name_prefix = local.name_prefix

  # Existing Infrastructure
  existing_redshift_sg_id       = var.existing_redshift_sg_id
  existing_bi_security_groups   = var.existing_bi_security_groups
  existing_bi_ip_ranges         = var.existing_bi_ip_ranges
  existing_mysql_pipeline_sg_id = var.existing_mysql_pipeline_sg_id

  # Janis IPs
  allowed_janis_ip_ranges = var.allowed_janis_ip_ranges

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# VPC Endpoints Module
# Creates Gateway and Interface Endpoints
# ============================================================================

module "vpc_endpoints" {
  source = "./modules/vpc-endpoints"

  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  route_table_ids    = module.vpc.route_table_ids
  name_prefix        = local.name_prefix

  # Security Group for Interface Endpoints
  vpc_endpoints_security_group_id = module.security_groups.sg_vpc_endpoints_id

  # Enable/Disable specific endpoints
  enable_s3_endpoint              = var.enable_s3_endpoint
  enable_glue_endpoint            = var.enable_glue_endpoint
  enable_secrets_manager_endpoint = var.enable_secrets_manager_endpoint
  enable_logs_endpoint            = var.enable_logs_endpoint
  enable_kms_endpoint             = var.enable_kms_endpoint
  enable_sts_endpoint             = var.enable_sts_endpoint
  enable_events_endpoint          = var.enable_events_endpoint

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# Network ACLs Module 
# Creates NACLs for public and private subnets
# ============================================================================

module "nacls" {
  source = "./modules/nacls"

  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = var.vpc_cidr
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  name_prefix        = local.name_prefix

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# WAF Module - DISABLED
# ============================================================================
# WAF is managed by the client's security team and not included in this
# infrastructure deployment. The client handles:
# - WAF Web ACL configuration
# - Rate limiting rules
# - Geo-blocking policies
# - Managed rule groups
# - Centralized WAF logging
#
# This infrastructure focuses on VPC, networking, and data pipeline components.
# ============================================================================

# ============================================================================
# EventBridge Module
# Creates Event Bus, Scheduled Rules, and Dead Letter Queue
# ============================================================================

module "eventbridge" {
  source = "./modules/eventbridge"

  name_prefix = local.name_prefix
  # Use MWAA ARN from module if created, otherwise use variable (for manual override)
  mwaa_environment_arn = var.create_mwaa_environment ? module.mwaa[0].mwaa_environment_arn : var.mwaa_environment_arn
  environment          = var.environment

  # Polling frequencies
  order_polling_rate_minutes   = var.order_polling_rate_minutes
  product_polling_rate_minutes = var.product_polling_rate_minutes
  stock_polling_rate_minutes   = var.stock_polling_rate_minutes
  price_polling_rate_minutes   = var.price_polling_rate_minutes
  store_polling_rate_minutes   = var.store_polling_rate_minutes

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# Monitoring Module
# Creates VPC Flow Logs, DNS Query Logging, and CloudWatch Alarms
# ============================================================================

module "monitoring" {
  source = "./modules/monitoring"

  vpc_id         = module.vpc.vpc_id
  nat_gateway_id = module.vpc.nat_gateway_id
  name_prefix    = local.name_prefix

  # Configuration
  vpc_flow_logs_retention_days = var.vpc_flow_logs_retention_days
  dns_logs_retention_days      = var.dns_logs_retention_days
  alarm_sns_topic_arn          = var.alarm_sns_topic_arn

  # Enable/Disable
  enable_vpc_flow_logs     = var.enable_vpc_flow_logs
  enable_dns_query_logging = var.enable_dns_query_logging

  # EventBridge rule names for alarms
  eventbridge_rule_names = module.eventbridge.rule_names

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# S3 Module
# Creates Data Lake buckets (Bronze, Silver, Gold) and supporting buckets
# ============================================================================

module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix

  # Lifecycle configuration
  bronze_glacier_transition_days = var.bronze_glacier_transition_days
  bronze_expiration_days         = var.bronze_expiration_days
  silver_glacier_transition_days = var.silver_glacier_transition_days
  silver_expiration_days         = var.silver_expiration_days
  gold_intelligent_tiering_days  = var.gold_intelligent_tiering_days
  logs_expiration_days           = var.logs_expiration_days

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# Kinesis Firehose Module
# Creates Firehose delivery streams for real-time data ingestion
# ============================================================================

module "kinesis_firehose" {
  source = "./modules/kinesis-firehose"

  name_prefix       = local.name_prefix
  bronze_bucket_arn = module.s3.bronze_bucket_arn

  # Buffering configuration
  buffering_size     = var.firehose_buffering_size
  buffering_interval = var.firehose_buffering_interval
  compression_format = var.firehose_compression_format

  # Monitoring
  alarm_sns_topic_arn = var.alarm_sns_topic_arn

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# Lambda Module
# Creates Lambda functions for data processing
# ============================================================================

module "lambda" {
  source = "./modules/lambda"

  name_prefix              = local.name_prefix
  environment              = var.environment
  private_subnet_ids       = module.vpc.private_subnet_ids
  lambda_security_group_id = module.security_groups.sg_lambda_id

  # S3 Configuration
  bronze_bucket_name = module.s3.bronze_bucket_id
  bronze_bucket_arn  = module.s3.bronze_bucket_arn
  silver_bucket_name = module.s3.silver_bucket_id
  scripts_bucket_arn = module.s3.scripts_bucket_arn

  # Kinesis Firehose Configuration
  firehose_delivery_stream_name = module.kinesis_firehose.orders_stream_name
  firehose_delivery_stream_arn  = module.kinesis_firehose.orders_stream_arn

  # Lambda Configuration
  lambda_runtime     = var.lambda_runtime
  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  # Function creation flags
  create_webhook_processor = var.create_lambda_webhook_processor
  create_data_enrichment   = var.create_lambda_data_enrichment
  create_api_polling       = var.create_lambda_api_polling

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# API Gateway Module
# Creates REST API for webhooks
# ============================================================================

module "api_gateway" {
  count = var.create_api_gateway ? 1 : 0

  source = "./modules/api-gateway"

  name_prefix                  = local.name_prefix
  environment                  = var.environment
  webhook_processor_invoke_arn = module.lambda.webhook_processor_invoke_arn

  # Usage Plan Configuration
  create_usage_plan    = var.api_gateway_create_usage_plan
  quota_limit          = var.api_gateway_quota_limit
  throttle_burst_limit = var.api_gateway_throttle_burst_limit
  throttle_rate_limit  = var.api_gateway_throttle_rate_limit

  # API Key
  create_api_key = var.api_gateway_create_api_key

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# AWS Glue Module
# Creates Glue catalog and ETL jobs
# ============================================================================

module "glue" {
  source = "./modules/glue"

  name_prefix = local.name_prefix

  # S3 Bucket Configuration
  bronze_bucket_name  = module.s3.bronze_bucket_id
  bronze_bucket_arn   = module.s3.bronze_bucket_arn
  silver_bucket_name  = module.s3.silver_bucket_id
  silver_bucket_arn   = module.s3.silver_bucket_arn
  gold_bucket_name    = module.s3.gold_bucket_id
  gold_bucket_arn     = module.s3.gold_bucket_arn
  scripts_bucket_name = module.s3.scripts_bucket_id
  scripts_bucket_arn  = module.s3.scripts_bucket_arn

  # Glue Job Configuration
  glue_worker_type            = var.glue_worker_type
  glue_number_of_workers      = var.glue_number_of_workers
  create_bronze_to_silver_job = var.create_glue_bronze_to_silver_job
  create_silver_to_gold_job   = var.create_glue_silver_to_gold_job

  # Corporate Tags
  tags = local.all_tags
}

# ============================================================================
# MWAA Module
# Creates Managed Apache Airflow environment
# ============================================================================

module "mwaa" {
  count = var.create_mwaa_environment ? 1 : 0

  source = "./modules/mwaa"

  name_prefix            = local.name_prefix
  aws_region             = var.aws_region
  private_subnet_ids     = module.vpc.private_subnet_ids
  mwaa_security_group_id = module.security_groups.sg_mwaa_id

  # S3 Bucket Configuration
  scripts_bucket_arn = module.s3.scripts_bucket_arn
  bronze_bucket_arn  = module.s3.bronze_bucket_arn
  silver_bucket_arn  = module.s3.silver_bucket_arn
  gold_bucket_arn    = module.s3.gold_bucket_arn

  # Lambda Integration
  lambda_function_arns = [
    module.lambda.api_polling_function_arn
  ]

  # MWAA Configuration
  airflow_version   = var.mwaa_airflow_version
  environment_class = var.mwaa_environment_class
  max_workers       = var.mwaa_max_workers
  min_workers       = var.mwaa_min_workers

  # Corporate Tags
  tags = local.all_tags
}
