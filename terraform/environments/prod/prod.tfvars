# ============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ============================================================================
# This file contains configuration values for the production environment.
# All values must be carefully reviewed and approved before deployment.
# Credentials should ONLY be passed via secure methods (SSO, IAM roles).
# ============================================================================

# ============================================================================
# AWS Configuration
# ============================================================================

aws_region     = "us-east-1"
aws_account_id = "" # REPLACE: Set your production AWS Account ID

# ============================================================================
# Network Configuration
# ============================================================================

# VPC and Subnet Configuration
vpc_cidr               = "10.0.0.0/16"
public_subnet_a_cidr   = "10.0.1.0/24"
private_subnet_1a_cidr = "10.0.10.0/24"
private_subnet_2a_cidr = "10.0.20.0/24"

# Multi-AZ Configuration
# IMPORTANT: Initially deployed as Single-AZ (us-east-1a)
# Set to true when ready to expand to Multi-AZ for high availability
enable_multi_az = false

# Reserved CIDRs for Multi-AZ expansion (us-east-1b)
# These are documented and reserved but not created until enable_multi_az = true
public_subnet_b_cidr   = "10.0.2.0/24"
private_subnet_1b_cidr = "10.0.11.0/24"
private_subnet_2b_cidr = "10.0.21.0/24"

# ============================================================================
# Existing Infrastructure Integration
# ============================================================================

# Existing Cencosud Redshift Cluster
# CRITICAL: Verify these values with infrastructure team before deployment
existing_redshift_cluster_id = "cencosud-redshift-prod"
existing_redshift_sg_id      = "" # REPLACE: sg-xxxxx (verify with team)

# Existing BI Systems Security Groups
# CRITICAL: Add all production BI systems that need Redshift access
existing_bi_security_groups = [
  # REPLACE: Add production BI system security groups
  # Example: "sg-powerbi-prod-xxxxx"
  # Example: "sg-tableau-prod-xxxxx"
]

# Existing BI Systems IP Ranges
# CRITICAL: Add all production BI system IP ranges
existing_bi_ip_ranges = [
  # REPLACE: Add production BI system IP ranges
  # Example: "192.168.100.0/24"  # Power BI servers
  # Example: "192.168.101.0/24"  # Tableau servers
]

# Current MySQL to Redshift Pipeline (temporary during migration)
# Remove this after migration is complete
existing_mysql_pipeline_sg_id = "" # REPLACE: sg-xxxxx (if still active)

# ============================================================================
# Tagging Strategy (Corporate AWS Tagging Policy)
# ============================================================================

application_name = "janis-cencosud-integration"
environment      = "prod"
owner            = "data-engineering-team"
cost_center      = "CC-DATA-001" # REPLACE: Add actual production cost center code
business_unit    = "Data-Analytics"
country          = "CL"
criticality      = "high"

# Legacy project_name (for resource naming)
project_name = "janis-cencosud-integration"

# Additional tags following Cencosud corporate standards
additional_tags = {
  DataClassification = "Confidential"
  BackupPolicy       = "daily"
  ComplianceLevel    = "SOC2"
  CriticalityLevel   = "High"
  DisasterRecovery   = "Required"
  MaintenanceWindow  = "Sunday 02:00-06:00 UTC"
  SupportTeam        = "data-engineering-team"
  # Add additional corporate-required tags
}

# ============================================================================
# Security Configuration
# ============================================================================

# Client's Private Network IP Ranges
# CRITICAL: These are the internal network ranges managed by the client
# All API Gateway webhook access will be restricted to these ranges
allowed_janis_ip_ranges = [
  "172.16.0.0/12", # Client's private network range 1
  "10.0.0.0/8",    # Client's private network range 2
  "192.168.0.0/16" # Client's private network range 3
]

# Note: WAF and CloudTrail are managed by the client and not included in this infrastructure
# The client's security team handles:
# - WAF Web ACL configuration and rules
# - CloudTrail logging and audit trails
# - Centralized security monitoring

# ============================================================================
# Monitoring Configuration
# ============================================================================

# Production retention periods (compliance requirements)
vpc_flow_logs_retention_days = 90
dns_logs_retention_days      = 90

# SNS Topic for Production Alerts
# CRITICAL: Must be configured for production monitoring
alarm_sns_topic_arn = "" # REPLACE: arn:aws:sns:us-east-1:xxxxx:prod-infrastructure-alerts

# Enable all monitoring in production
enable_vpc_flow_logs     = true
enable_dns_query_logging = true

# ============================================================================
# EventBridge Polling Configuration
# ============================================================================

# Production polling frequencies (optimized for business requirements)
order_polling_rate_minutes   = 5    # Orders: every 5 minutes (critical)
product_polling_rate_minutes = 60   # Products: every hour
stock_polling_rate_minutes   = 10   # Stock: every 10 minutes (important)
price_polling_rate_minutes   = 30   # Prices: every 30 minutes
store_polling_rate_minutes   = 1440 # Stores: once per day

# MWAA Environment ARN
# CRITICAL: Must be set after MWAA environment is created
mwaa_environment_arn = "" # REPLACE: arn:aws:airflow:us-east-1:xxxxx:environment/cencosud-mwaa-prod

# ============================================================================
# VPC Endpoints Configuration
# ============================================================================

# All endpoints enabled for production (security and cost optimization)
enable_s3_endpoint              = true
enable_glue_endpoint            = true
enable_secrets_manager_endpoint = true
enable_logs_endpoint            = true
enable_kms_endpoint             = true
enable_sts_endpoint             = true
enable_events_endpoint          = true

# ============================================================================
# CREDENTIAL MANAGEMENT APPROACH - PRODUCTION
# ============================================================================
#
# CRITICAL SECURITY REQUIREMENTS FOR PRODUCTION:
#
# Method 1: AWS SSO/IAM Identity Center (STRONGLY RECOMMENDED)
# ----------------------------------------------------------------------
# aws sso login --profile production
# export AWS_PROFILE=production
# terraform plan -var-file="environments/prod/prod.tfvars"
#
# Method 2: IAM Roles (for CI/CD pipelines)
# ----------------------------------------------------------------------
# Use IAM roles with temporary credentials
# Configure in CI/CD system (GitHub Actions, Jenkins, etc.)
# Never store long-term credentials in CI/CD
#
# Method 3: Environment Variables with MFA (if SSO not available)
# ----------------------------------------------------------------------
# export AWS_ACCESS_KEY_ID="your-prod-access-key"
# export AWS_SECRET_ACCESS_KEY="your-prod-secret-key"
# export AWS_SESSION_TOKEN="your-mfa-session-token"  # REQUIRED for production
# terraform plan -var-file="environments/prod/prod.tfvars"
#
# PRODUCTION SECURITY REQUIREMENTS:
# ----------------------------------
# ✓ NEVER hardcode credentials in any file
# ✓ NEVER commit credentials to version control
# ✓ ALWAYS use MFA for production access
# ✓ ALWAYS use separate credentials from dev/staging
# ✓ ALWAYS rotate credentials monthly (at minimum)
# ✓ ALWAYS use IAM roles with temporary credentials when possible
# ✓ ALWAYS audit all production access
# ✓ ALWAYS require approval for production deployments
# ✓ ALWAYS test in staging before production deployment
# ✓ ALWAYS have rollback plan ready
# ✓ ALWAYS backup state before applying changes
# ✓ ALWAYS notify team before production changes
#
# DEPLOYMENT CHECKLIST:
# ---------------------
# [ ] All placeholder values replaced with actual production values
# [ ] Security groups and IP ranges verified with security team
# [ ] Redshift integration tested in staging
# [ ] Backup of current state created
# [ ] Change request approved
# [ ] Maintenance window scheduled
# [ ] Rollback plan documented
# [ ] Team notified of deployment
# [ ] Monitoring dashboards ready
# [ ] On-call engineer available
#
# EMERGENCY CONTACTS:
# -------------------
# Infrastructure Team: [ADD CONTACT]
# Security Team: [ADD CONTACT]
# On-Call Engineer: [ADD CONTACT]
# Escalation Manager: [ADD CONTACT]
#
# ============================================================================
