# ============================================================================
# DEVELOPMENT ENVIRONMENT CONFIGURATION
# ============================================================================
# This file contains configuration values for the development environment.
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

# VPC and Subnet Configuration (Single-AZ for development)
vpc_cidr               = "10.0.0.0/16"
public_subnet_a_cidr   = "10.0.1.0/24"
private_subnet_1a_cidr = "10.0.10.0/24"
private_subnet_2a_cidr = "10.0.20.0/24"

# Multi-AZ disabled for development (cost optimization)
enable_multi_az = false

# Reserved CIDRs for future Multi-AZ expansion
public_subnet_b_cidr   = "10.0.2.0/24"
private_subnet_1b_cidr = "10.0.11.0/24"
private_subnet_2b_cidr = "10.0.21.0/24"

# ============================================================================
# Existing Infrastructure Integration
# ============================================================================

# Redshift Cluster Configuration
# REPLACE: Update with actual development Redshift cluster details
existing_redshift_cluster_id = "cencosud-redshift-dev"
existing_redshift_sg_id      = "" # REPLACE: sg-xxxxx

# BI Systems (typically fewer in dev environment)
existing_bi_security_groups = []
existing_bi_ip_ranges       = []

# MySQL Pipeline (if still active in dev)
existing_mysql_pipeline_sg_id = ""

# ============================================================================
# Tagging Strategy (Corporate AWS Tagging Policy)
# ============================================================================

application_name = "janis-cencosud-integration"
environment      = "dev"
owner            = "data-engineering-team"
cost_center      = "CC-DATA-001" # REPLACE: Add actual cost center code
business_unit    = "Data-Analytics"
country          = "CL"
criticality      = "low"

# Legacy project_name (for resource naming)
project_name = "janis-cencosud-integration"

# Additional tags for development environment
additional_tags = {
  DataClassification = "Internal"
  BackupPolicy       = "weekly"
  AutoShutdown       = "true"
  Purpose            = "development-testing"
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

# Shorter retention for development (cost optimization)
vpc_flow_logs_retention_days = 7
dns_logs_retention_days      = 7

# SNS Topic for alerts (optional in dev)
alarm_sns_topic_arn = ""

# Enable monitoring (can be disabled to reduce costs)
enable_vpc_flow_logs     = true
enable_dns_query_logging = false # Disabled to reduce costs

# ============================================================================
# EventBridge Polling Configuration
# ============================================================================

# More frequent polling for development testing
order_polling_rate_minutes   = 5
product_polling_rate_minutes = 30 # More frequent than prod
stock_polling_rate_minutes   = 5
price_polling_rate_minutes   = 15 # More frequent than prod
store_polling_rate_minutes   = 60 # More frequent than prod

# MWAA Environment ARN (leave empty if not yet created)
mwaa_environment_arn = ""

# ============================================================================
# VPC Endpoints Configuration
# ============================================================================

# All endpoints enabled for development testing
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
# Development environment uses one of the following methods for AWS credentials:
#
# Method 1: Environment Variables (Recommended for local development)
# ----------------------------------------------------------------------
# export AWS_ACCESS_KEY_ID="your-dev-access-key"
# export AWS_SECRET_ACCESS_KEY="your-dev-secret-key"
# export AWS_SESSION_TOKEN="your-session-token"  # Optional for STS
# terraform plan -var-file="environments/dev/dev.tfvars"
#
# Method 2: Command Line Parameters
# ----------------------------------------------------------------------
# terraform plan \
#   -var-file="environments/dev/dev.tfvars" \
#   -var="aws_access_key_id=your-dev-access-key" \
#   -var="aws_secret_access_key=your-dev-secret-key"
#
# Method 3: Credentials File (NOT committed to Git)
# ----------------------------------------------------------------------
# Create credentials.tfvars (add to .gitignore):
#   aws_access_key_id     = "your-dev-access-key"
#   aws_secret_access_key = "your-dev-secret-key"
#
# terraform plan \
#   -var-file="environments/dev/dev.tfvars" \
#   -var-file="credentials.tfvars"
#
# IMPORTANT SECURITY NOTES:
# - NEVER hardcode credentials in this file
# - NEVER commit credentials.tfvars to version control
# - Use IAM roles with temporary credentials when possible
# - Rotate credentials regularly
# - Use different credentials for each environment
# - Consider using AWS SSO or IAM Identity Center for authentication
#
# ============================================================================
