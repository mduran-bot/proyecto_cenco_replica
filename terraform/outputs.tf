# ============================================================================
# Outputs
# ============================================================================

# ============================================================================
# VPC Outputs
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway"
  value       = module.vpc.nat_gateway_id
}

output "nat_gateway_public_ip" {
  description = "Public IP of the NAT Gateway"
  value       = module.vpc.nat_gateway_public_ip
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.internet_gateway_id
}

# ============================================================================
# Security Group Outputs
# ============================================================================

output "sg_api_gateway_id" {
  description = "ID of API Gateway Security Group"
  value       = module.security_groups.sg_api_gateway_id
}

output "sg_lambda_id" {
  description = "ID of Lambda Security Group"
  value       = module.security_groups.sg_lambda_id
}

output "sg_mwaa_id" {
  description = "ID of MWAA Security Group"
  value       = module.security_groups.sg_mwaa_id
}

output "sg_glue_id" {
  description = "ID of Glue Security Group"
  value       = module.security_groups.sg_glue_id
}

output "sg_redshift_id" {
  description = "ID of Redshift Security Group"
  value       = module.security_groups.sg_redshift_id
}

output "sg_eventbridge_id" {
  description = "ID of EventBridge Security Group"
  value       = module.security_groups.sg_eventbridge_id
}

output "sg_vpc_endpoints_id" {
  description = "ID of VPC Endpoints Security Group"
  value       = module.security_groups.sg_vpc_endpoints_id
}

# ============================================================================
# VPC Endpoints Outputs
# ============================================================================

output "s3_endpoint_id" {
  description = "ID of S3 Gateway Endpoint"
  value       = module.vpc_endpoints.s3_endpoint_id
}

output "interface_endpoint_ids" {
  description = "IDs of Interface Endpoints"
  value       = module.vpc_endpoints.interface_endpoint_ids
}

# ============================================================================
# WAF Outputs
# ============================================================================
# Note: WAF is managed by the client and not included in this infrastructure
# WAF Web ACL configuration is handled by the client's security team

# ============================================================================
# EventBridge Outputs
# ============================================================================

output "eventbridge_bus_name" {
  description = "Name of EventBridge custom event bus"
  value       = module.eventbridge.event_bus_name
}

output "eventbridge_bus_arn" {
  description = "ARN of EventBridge custom event bus"
  value       = module.eventbridge.event_bus_arn
}

output "eventbridge_rule_arns" {
  description = "ARNs of EventBridge scheduled rules"
  value       = module.eventbridge.rule_arns
}

output "eventbridge_dlq_url" {
  description = "URL of EventBridge Dead Letter Queue"
  value       = module.eventbridge.dlq_url
}

# ============================================================================
# Monitoring Outputs
# ============================================================================

output "vpc_flow_logs_log_group" {
  description = "CloudWatch Log Group for VPC Flow Logs"
  value       = module.monitoring.vpc_flow_logs_log_group
}

output "dns_query_logs_log_group" {
  description = "CloudWatch Log Group for DNS Query Logs"
  value       = module.monitoring.dns_query_logs_log_group
}

output "cloudwatch_alarm_arns" {
  description = "ARNs of CloudWatch Alarms"
  value       = module.monitoring.alarm_arns
}

output "metric_filter_names" {
  description = "Names of CloudWatch Log Metric Filters"
  value       = module.monitoring.metric_filter_names
}

# ============================================================================
# Summary Output
# ============================================================================

output "deployment_summary" {
  description = "Summary of deployed infrastructure"
  value = {
    vpc_id             = module.vpc.vpc_id
    vpc_cidr           = module.vpc.vpc_cidr
    availability_zones = module.vpc.availability_zones
    nat_gateway_ip     = module.vpc.nat_gateway_public_ip
    multi_az_enabled   = var.enable_multi_az
    # Note: WAF is managed by the client
    event_bus_name     = module.eventbridge.event_bus_name
    monitoring_enabled = var.enable_vpc_flow_logs || var.enable_dns_query_logging
  }
}

# ============================================================================
# S3 Data Lake Outputs
# ============================================================================

output "bronze_bucket_name" {
  description = "Name of Bronze layer bucket"
  value       = module.s3.bronze_bucket_id
}

output "bronze_bucket_arn" {
  description = "ARN of Bronze layer bucket"
  value       = module.s3.bronze_bucket_arn
}

output "silver_bucket_name" {
  description = "Name of Silver layer bucket"
  value       = module.s3.silver_bucket_id
}

output "silver_bucket_arn" {
  description = "ARN of Silver layer bucket"
  value       = module.s3.silver_bucket_arn
}

output "gold_bucket_name" {
  description = "Name of Gold layer bucket"
  value       = module.s3.gold_bucket_id
}

output "gold_bucket_arn" {
  description = "ARN of Gold layer bucket"
  value       = module.s3.gold_bucket_arn
}

output "scripts_bucket_name" {
  description = "Name of scripts bucket"
  value       = module.s3.scripts_bucket_id
}

output "scripts_bucket_arn" {
  description = "ARN of scripts bucket"
  value       = module.s3.scripts_bucket_arn
}

output "logs_bucket_name" {
  description = "Name of logs bucket"
  value       = module.s3.logs_bucket_id
}

output "logs_bucket_arn" {
  description = "ARN of logs bucket"
  value       = module.s3.logs_bucket_arn
}

output "all_s3_buckets" {
  description = "Map of all S3 bucket names"
  value       = module.s3.all_bucket_names
}

output "all_s3_bucket_arns" {
  description = "Map of all S3 bucket ARNs"
  value       = module.s3.all_bucket_arns
}

# ============================================================================
# Kinesis Firehose Outputs
# ============================================================================

output "firehose_orders_stream_name" {
  description = "Name of Kinesis Firehose orders stream"
  value       = module.kinesis_firehose.orders_stream_name
}

output "firehose_orders_stream_arn" {
  description = "ARN of Kinesis Firehose orders stream"
  value       = module.kinesis_firehose.orders_stream_arn
}

# ============================================================================
# Lambda Outputs
# ============================================================================

output "lambda_execution_role_arn" {
  description = "ARN of Lambda execution role"
  value       = module.lambda.lambda_execution_role_arn
}

output "webhook_processor_function_name" {
  description = "Name of webhook processor Lambda function"
  value       = module.lambda.webhook_processor_function_name
}

output "webhook_processor_function_arn" {
  description = "ARN of webhook processor Lambda function"
  value       = module.lambda.webhook_processor_function_arn
}

output "data_enrichment_function_name" {
  description = "Name of data enrichment Lambda function"
  value       = module.lambda.data_enrichment_function_name
}

output "api_polling_function_name" {
  description = "Name of API polling Lambda function"
  value       = module.lambda.api_polling_function_name
}

output "all_lambda_function_arns" {
  description = "Map of all Lambda function ARNs"
  value       = module.lambda.all_function_arns
}

# ============================================================================
# API Gateway Outputs
# ============================================================================

output "api_gateway_id" {
  description = "ID of API Gateway REST API"
  value       = var.create_api_gateway ? module.api_gateway[0].api_id : null
}

output "api_gateway_stage_invoke_url" {
  description = "Invoke URL of API Gateway stage"
  value       = var.create_api_gateway ? module.api_gateway[0].stage_invoke_url : null
}

output "api_gateway_webhook_endpoint_url" {
  description = "Webhook endpoint URL"
  value       = var.create_api_gateway ? module.api_gateway[0].webhook_endpoint_url : null
}

output "api_gateway_api_key_value" {
  description = "API Gateway API key value (sensitive)"
  value       = var.create_api_gateway && var.api_gateway_create_api_key ? module.api_gateway[0].api_key_value : null
  sensitive   = true
}

# ============================================================================
# AWS Glue Outputs
# ============================================================================

output "glue_bronze_database_name" {
  description = "Name of Glue Bronze database"
  value       = module.glue.bronze_database_name
}

output "glue_silver_database_name" {
  description = "Name of Glue Silver database"
  value       = module.glue.silver_database_name
}

output "glue_gold_database_name" {
  description = "Name of Glue Gold database"
  value       = module.glue.gold_database_name
}

output "glue_bronze_to_silver_job_name" {
  description = "Name of Glue Bronze to Silver job"
  value       = module.glue.bronze_to_silver_job_name
}

output "glue_silver_to_gold_job_name" {
  description = "Name of Glue Silver to Gold job"
  value       = module.glue.silver_to_gold_job_name
}

output "all_glue_job_names" {
  description = "List of all Glue job names"
  value       = module.glue.all_job_names
}

# ============================================================================
# MWAA Outputs
# ============================================================================

output "mwaa_environment_arn" {
  description = "ARN of MWAA environment"
  value       = var.create_mwaa_environment ? module.mwaa[0].mwaa_environment_arn : null
}

output "mwaa_webserver_url" {
  description = "MWAA Airflow webserver URL"
  value       = var.create_mwaa_environment ? module.mwaa[0].mwaa_webserver_url : null
}

output "mwaa_execution_role_arn" {
  description = "ARN of MWAA execution role"
  value       = var.create_mwaa_environment ? module.mwaa[0].mwaa_execution_role_arn : null
}
