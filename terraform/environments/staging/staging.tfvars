# ============================================================================
# STAGING ENVIRONMENT CONFIGURATION
# ============================================================================
# This file contains configuration values for the staging environment.
# Staging mirrors production configuration for pre-production testing.
# Credentials should be passed via environment variables or command line.
# ============================================================================

# ============================================================================
# AWS Configuration
# ============================================================================

aws_region     = "us-east-1"
aws_account_id = "" # REPLACE: Set your AWS Account ID

# ============================================================================
# Network Configuration
# ============================================================================

# VPC and Subnet Configuration (Single-AZ initially, can enable Multi-AZ)
vpc_cidr               = "10.0.0.0/16"
public_subnet_a_cidr   = "10.0.1.0/24"
private_subnet_1a_cidr = "10.0.10.0/24"
private_subnet_2a_cidr = "10.0.20.0/24"

# Multi-AZ can be enabled for staging to test HA configuration
enable_multi_az = false

# Reserved CIDRs for Multi-AZ expansion
public_subnet_b_cidr   = "10.0.2.0/24"
private_subnet_1b_cidr = "10.0.11.0/24"
private_subnet_2b_cidr = "10.0.21.0/24"

# ============================================================================
# Existing Infrastructure Integration
# ============================================================================

# Redshift Cluster Configuration
# REPLACE: Update with actual staging Redshift cluster details
existing_redshift_cluster_id = "cencosud-redshift-staging"
existing_redshift_sg_id      = "" # REPLACE: sg-xxxxx

# BI Systems (subset of production systems for testing)
existing_bi_security_groups = [
  # REPLACE: Add staging BI system security groups
]

existing_bi_ip_ranges = [
  # REPLACE: Add staging BI system IP ranges
]

# MySQL Pipeline (if still active in staging)
existing_mysql_pipeline_sg_id = ""

# ============================================================================
# Tagging Strategy (Corporate AWS Tagging Policy)
# ============================================================================

application_name = "janis-cencosud-integration"
environment      = "qa"
owner            = "data-engineering-team"
cost_center      = "CC-DATA-001" # REPLACE: Add actual cost center code
business_unit    = "Data-Analytics"
country          = "CL"
criticality      = "medium"

# Legacy project_name (for resource naming)
project_name = "janis-cencosud-integration"

# Additional tags for staging environment
additional_tags = {
  DataClassification = "Internal"
  BackupPolicy       = "daily"
  ComplianceLevel    = "SOC2"
  Purpose            = "pre-production-testing"
  AutoShutdown       = "false"
}

# ============================================================================
# Security Configuration
# ============================================================================

# Client's Private Network IP Ranges
# These are the internal network ranges managed by the client
allowed_janis_ip_ranges = ["172.16.0.0/12", "10.0.0.0/8", "192.168.0.0/16"]

# Note: WAF is managed by the client and not included in this infrastructure

# ============================================================================
# Monitoring Configuration
# ============================================================================

# Production-like retention for staging
vpc_flow_logs_retention_days = 30
dns_logs_retention_days      = 30

# SNS Topic for alerts
alarm_sns_topic_arn = "" # REPLACE: Add SNS topic ARN for staging alerts

# Enable full monitoring in staging
enable_vpc_flow_logs     = true
enable_dns_query_logging = true

# ============================================================================
# EventBridge Polling Configuration
# ============================================================================

# Production-like polling frequencies for realistic testing
order_polling_rate_minutes   = 5
product_polling_rate_minutes = 60
stock_polling_rate_minutes   = 10
price_polling_rate_minutes   = 30
store_polling_rate_minutes   = 1440

# MWAA Environment ARN
mwaa_environment_arn = "" # REPLACE: Add MWAA environment ARN when created

# ============================================================================
# VPC Endpoints Configuration
# ============================================================================

# All endpoints enabled to match production
enable_s3_endpoint              = true
enable_glue_endpoint            = true
enable_secrets_manager_endpoint = true
enable_logs_endpoint            = true
enable_kms_endpoint             = true
enable_sts_endpoint             = true
enable_events_endpoint          = true

# ============================================================================
# CREDENTIAL MANAGEMENT APPROACH
# ============================================================================
#
# Staging environment uses secure credential management:
#
# Method 1: Environment Variables (Recommended)
# ----------------------------------------------------------------------
# export AWS_ACCESS_KEY_ID="your-staging-access-key"
# export AWS_SECRET_ACCESS_KEY="your-staging-secret-key"
# export AWS_SESSION_TOKEN="your-session-token"  # Optional for STS
# terraform plan -var-file="environments/staging/staging.tfvars"
#
# Method 2: AWS SSO/IAM Identity Center (Recommended for teams)
# ----------------------------------------------------------------------
# aws sso login --profile staging
# export AWS_PROFILE=staging
# terraform plan -var-file="environments/staging/staging.tfvars"
#
# Method 3: Credentials File (NOT committed to Git)
# ----------------------------------------------------------------------
# Create credentials.tfvars (add to .gitignore):
#   aws_access_key_id     = "your-staging-access-key"
#   aws_secret_access_key = "your-staging-secret-key"
#
# terraform plan \
#   -var-file="environments/staging/staging.tfvars" \
#   -var-file="credentials.tfvars"
#
# IMPORTANT SECURITY NOTES:
# - NEVER hardcode credentials in this file
# - NEVER commit credentials.tfvars to version control
# - Use separate credentials from development and production
# - Implement MFA for staging environment access
# - Rotate credentials regularly (at least quarterly)
# - Use IAM roles with temporary credentials when possible
# - Audit credential usage regularly
# - Staging should mirror production security practices
#
# DEPLOYMENT WORKFLOW:
# 1. Test changes in development environment first
# 2. Deploy to staging for integration testing
# 3. Run full test suite against staging
# 4. Obtain approval before promoting to production
# 5. Use same deployment scripts as production
#
# ============================================================================
