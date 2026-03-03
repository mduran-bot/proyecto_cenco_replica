# ============================================================================
# API Polling System - LocalStack Configuration
# ============================================================================
# Configuration for testing with LocalStack
# ============================================================================

# LocalStack Configuration
localstack_endpoint    = "http://localhost:4566"
localstack_s3_endpoint = "http://s3.localhost.localstack.cloud:4566"

# AWS Configuration (dummy credentials for LocalStack)
aws_region            = "us-east-1"
aws_access_key_id     = "test"
aws_secret_access_key = "test"

# Project Configuration
environment  = "localstack"
project_name = "janis-polling"

# DynamoDB Configuration
dynamodb_billing_mode         = "PAY_PER_REQUEST"
enable_point_in_time_recovery = false # Not fully supported in LocalStack

# S3 Configuration
enable_s3_versioning        = true
s3_intelligent_tiering_days = 30
s3_glacier_transition_days  = 90
s3_expiration_days          = 365

# SNS Configuration
error_notification_emails = [] # Email not supported in LocalStack

# MWAA Configuration
mwaa_environment_arn = "arn:aws:airflow:us-east-1:000000000000:environment/janis-mwaa-localstack"

# Secrets Manager Configuration
secrets_manager_arns = []

# Monitoring Configuration
enable_monitoring  = false # Disable alarms for LocalStack
log_retention_days = 7
