# ============================================================================
# API Polling System - Outputs
# ============================================================================

# ============================================================================
# DynamoDB Outputs
# ============================================================================

output "dynamodb_table_name" {
  description = "Name of the DynamoDB polling control table"
  value       = module.polling_control_table.table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB polling control table"
  value       = module.polling_control_table.table_arn
}

# ============================================================================
# S3 Outputs
# ============================================================================

output "staging_bucket_name" {
  description = "Name of the S3 staging bucket"
  value       = module.polling_staging_bucket.bucket_name
}

output "staging_bucket_arn" {
  description = "ARN of the S3 staging bucket"
  value       = module.polling_staging_bucket.bucket_arn
}

# ============================================================================
# SNS Outputs
# ============================================================================

output "error_notification_topic_arn" {
  description = "ARN of the SNS error notification topic"
  value       = module.error_notification_topic.topic_arn
}

output "error_notification_topic_name" {
  description = "Name of the SNS error notification topic"
  value       = module.error_notification_topic.topic_name
}

# ============================================================================
# IAM Outputs (roles existentes proporcionados)
# ============================================================================

output "mwaa_execution_role_arn" {
  description = "ARN of the MWAA execution role (provided externally)"
  value       = var.mwaa_execution_role_arn
}

output "eventbridge_role_arn" {
  description = "ARN of the EventBridge role (provided externally)"
  value       = var.eventbridge_role_arn
}

# ============================================================================
# MWAA Outputs
# ============================================================================

output "mwaa_environment_name" {
  description = "Name of the MWAA environment"
  value       = module.mwaa.mwaa_environment_name
}

output "mwaa_environment_arn" {
  description = "ARN of the MWAA environment"
  value       = module.mwaa.mwaa_environment_arn
}

output "mwaa_webserver_url" {
  description = "Webserver URL of the MWAA environment (use this to access Airflow UI)"
  value       = module.mwaa.mwaa_webserver_url
}

output "mwaa_s3_bucket_name" {
  description = "Name of the S3 bucket for MWAA DAGs (upload DAGs here)"
  value       = module.mwaa.mwaa_s3_bucket_name
}

output "mwaa_execution_role_arn" {
  description = "ARN of the MWAA execution role"
  value       = module.mwaa.mwaa_execution_role_arn
}

# ============================================================================
# EventBridge Outputs
# ============================================================================

output "orders_polling_rules" {
  description = "Map of client to orders polling rule ARN"
  value       = module.eventbridge.orders_rule_arns
}

output "products_polling_rules" {
  description = "Map of client to products polling rule ARN"
  value       = module.eventbridge.products_rule_arns
}

output "stock_polling_rules" {
  description = "Map of client to stock polling rule ARN"
  value       = module.eventbridge.stock_rule_arns
}

output "prices_polling_rules" {
  description = "Map of client to prices polling rule ARN"
  value       = module.eventbridge.prices_rule_arns
}

output "stores_polling_rules" {
  description = "Map of client to stores polling rule ARN"
  value       = module.eventbridge.stores_rule_arns
}

# ============================================================================
# CloudWatch Outputs
# ============================================================================

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.polling_logs.name
}

# ============================================================================
# Summary Output
# ============================================================================

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    environment          = var.environment
    region               = data.aws_region.current.name
    account_id           = data.aws_caller_identity.current.account_id
    mwaa_webserver_url   = module.mwaa.mwaa_webserver_url
    mwaa_s3_bucket       = module.mwaa.mwaa_s3_bucket_name
    dynamodb_table       = module.polling_control_table.table_name
    bronze_bucket        = var.bronze_bucket_name
    configured_clients   = var.clients
    polling_rate_minutes = var.polling_rate_minutes
  }
}

# ============================================================================
# Next Steps Output
# ============================================================================

output "next_steps" {
  description = "Next steps after deployment"
  value = <<-EOT
  
  ✅ Infraestructura de Polling desplegada exitosamente!
  
  📋 PRÓXIMOS PASOS:
  
  1. Subir DAGs a MWAA:
     aws s3 sync ../dags/ s3://${module.mwaa.mwaa_s3_bucket_name}/dags/
     aws s3 cp ../requirements.txt s3://${module.mwaa.mwaa_s3_bucket_name}/requirements.txt
  
  2. Acceder a Airflow UI:
     URL: ${module.mwaa.mwaa_webserver_url}
  
  3. Configurar Variables en Airflow:
     - JANIS_API_BASE_URL: https://oms.janis.in/api
     - DYNAMODB_TABLE_NAME: ${module.polling_control_table.table_name}
     - S3_BRONZE_BUCKET: ${var.bronze_bucket_name}
  
  4. Crear Secrets en Secrets Manager (si no existen):
     aws secretsmanager create-secret \
       --name janis-api-credentials-wongio \
       --secret-string '{"api_key":"xxx","api_secret":"yyy"}'
  
  5. Verificar EventBridge Rules:
     aws events list-rules --name-prefix ${local.name_prefix}
  
  6. Monitorear logs:
     aws logs tail ${aws_cloudwatch_log_group.polling_logs.name} --follow
  
  📊 RECURSOS CREADOS:
  - MWAA Environment: ${module.mwaa.mwaa_environment_name}
  - DynamoDB Table: ${module.polling_control_table.table_name}
  - S3 MWAA Bucket: ${module.mwaa.mwaa_s3_bucket_name}
  - EventBridge Rules: ${length(var.clients) * 5} rules (5 per client)
  - Clientes configurados: ${join(", ", var.clients)}
  
  EOT
}
