# ============================================================================
# AWS Configuration
# ============================================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

# ============================================================================
# Network Configuration
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC (must provide 65,536 IPs)"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0)) && tonumber(split("/", var.vpc_cidr)[1]) == 16
    error_message = "VPC CIDR must be a valid /16 IPv4 CIDR block."
  }
}

variable "public_subnet_a_cidr" {
  description = "CIDR block for public subnet in AZ A"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_1a_cidr" {
  description = "CIDR block for private subnet 1A (Lambda, MWAA, Redshift)"
  type        = string
  default     = "10.0.10.0/24"
}

variable "private_subnet_2a_cidr" {
  description = "CIDR block for private subnet 2A (Glue ENIs)"
  type        = string
  default     = "10.0.20.0/24"
}

variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment (creates resources in us-east-1b)"
  type        = bool
  default     = false
}

# Reserved CIDRs for future Multi-AZ expansion (documented, not created unless enable_multi_az = true)
variable "public_subnet_b_cidr" {
  description = "CIDR block for public subnet in AZ B (reserved for Multi-AZ)"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_1b_cidr" {
  description = "CIDR block for private subnet 1B (reserved for Multi-AZ)"
  type        = string
  default     = "10.0.11.0/24"
}

variable "private_subnet_2b_cidr" {
  description = "CIDR block for private subnet 2B (reserved for Multi-AZ)"
  type        = string
  default     = "10.0.21.0/24"
}

# ============================================================================
# Existing Infrastructure Integration
# ============================================================================

variable "existing_redshift_cluster_id" {
  description = "ID of existing Cencosud Redshift cluster"
  type        = string
}

variable "existing_redshift_sg_id" {
  description = "Security Group ID of existing Redshift cluster"
  type        = string
}

variable "existing_bi_security_groups" {
  description = "List of Security Group IDs for existing BI systems (Power BI, Tableau, etc.)"
  type        = list(string)
  default     = []
}

variable "existing_bi_ip_ranges" {
  description = "List of IP ranges for existing BI systems"
  type        = list(string)
  default     = []
}

variable "existing_mysql_pipeline_sg_id" {
  description = "Security Group ID of current MySQL to Redshift pipeline (temporary during migration)"
  type        = string
  default     = ""
}

# ============================================================================
# Tagging Strategy (Corporate AWS Tagging Policy)
# ============================================================================

variable "application_name" {
  description = "Application name for tagging (Corporate Policy)"
  type        = string
  default     = "janis-cencosud-integration"
}

variable "environment" {
  description = "Environment name (Corporate Policy: prod, qa, dev, uat, sandbox)"
  type        = string

  validation {
    condition     = contains(["prod", "qa", "dev", "uat", "sandbox"], var.environment)
    error_message = "Environment must be one of: prod, qa, dev, uat, sandbox (per Corporate Policy)."
  }
}

variable "owner" {
  description = "Team or individual responsible for the infrastructure (Corporate Policy)"
  type        = string
  default     = "data-engineering-team"
}

variable "cost_center" {
  description = "Cost center code for billing (Corporate Policy - REQUIRED)"
  type        = string

  validation {
    condition     = length(var.cost_center) > 0
    error_message = "Cost center is required per Corporate Tagging Policy."
  }
}

variable "business_unit" {
  description = "Business unit (Corporate Policy - REQUIRED)"
  type        = string
  default     = "Data-Analytics"

  validation {
    condition     = length(var.business_unit) > 0
    error_message = "Business unit is required per Corporate Tagging Policy."
  }
}

variable "country" {
  description = "Country code (Corporate Policy - REQUIRED)"
  type        = string
  default     = "CL"

  validation {
    condition     = length(var.country) > 0
    error_message = "Country is required per Corporate Tagging Policy."
  }
}

variable "criticality" {
  description = "Criticality level (Corporate Policy: high, medium, low)"
  type        = string
  default     = "high"

  validation {
    condition     = contains(["high", "medium", "low"], var.criticality)
    error_message = "Criticality must be one of: high, medium, low (per Corporate Policy)."
  }
}

variable "project_name" {
  description = "Project name for resource naming (legacy - use application_name for tagging)"
  type        = string
  default     = "janis-cencosud-integration"
}

variable "additional_tags" {
  description = "Additional optional tags (beyond Corporate Policy requirements)"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Security Configuration
# ============================================================================

variable "allowed_janis_ip_ranges" {
  description = "List of IP ranges allowed to access API Gateway webhooks (Client's private network ranges)"
  type        = list(string)
  default     = ["172.16.0.0/12", "10.0.0.0/8", "192.168.0.0/16"]
}


# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "vpc_flow_logs_retention_days" {
  description = "Retention period for VPC Flow Logs in CloudWatch (days)"
  type        = number
  default     = 90
}

variable "dns_logs_retention_days" {
  description = "Retention period for DNS Query Logs in CloudWatch (days)"
  type        = number
  default     = 90
}

variable "alarm_sns_topic_arn" {
  description = "SNS Topic ARN for CloudWatch alarms"
  type        = string
  default     = ""
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "enable_dns_query_logging" {
  description = "Enable DNS Query Logging"
  type        = bool
  default     = true
}

# ============================================================================
# EventBridge Configuration
# ============================================================================

variable "order_polling_rate_minutes" {
  description = "Polling frequency for orders (minutes)"
  type        = number
  default     = 5
}

variable "product_polling_rate_minutes" {
  description = "Polling frequency for products (minutes)"
  type        = number
  default     = 60
}

variable "stock_polling_rate_minutes" {
  description = "Polling frequency for stock (minutes)"
  type        = number
  default     = 10
}

variable "price_polling_rate_minutes" {
  description = "Polling frequency for prices (minutes)"
  type        = number
  default     = 30
}

variable "store_polling_rate_minutes" {
  description = "Polling frequency for stores (minutes)"
  type        = number
  default     = 1440 # Once per day
}

variable "mwaa_environment_arn" {
  description = "ARN of MWAA environment (leave empty if not yet created)"
  type        = string
  default     = ""
}

# ============================================================================
# VPC Endpoints Configuration
# ============================================================================

variable "enable_s3_endpoint" {
  description = "Enable S3 Gateway Endpoint"
  type        = bool
  default     = true
}

variable "enable_glue_endpoint" {
  description = "Enable Glue Interface Endpoint"
  type        = bool
  default     = true
}

variable "enable_secrets_manager_endpoint" {
  description = "Enable Secrets Manager Interface Endpoint"
  type        = bool
  default     = true
}

variable "enable_logs_endpoint" {
  description = "Enable CloudWatch Logs Interface Endpoint"
  type        = bool
  default     = true
}

variable "enable_kms_endpoint" {
  description = "Enable KMS Interface Endpoint"
  type        = bool
  default     = true
}

variable "enable_sts_endpoint" {
  description = "Enable STS Interface Endpoint"
  type        = bool
  default     = true
}

variable "enable_events_endpoint" {
  description = "Enable EventBridge Interface Endpoint"
  type        = bool
  default     = true
}

# ============================================================================
# S3 Data Lake Configuration
# ============================================================================

variable "bronze_glacier_transition_days" {
  description = "Days before transitioning Bronze layer data to Glacier"
  type        = number
  default     = 90
}

variable "bronze_expiration_days" {
  description = "Days before expiring Bronze layer data"
  type        = number
  default     = 365
}

variable "silver_glacier_transition_days" {
  description = "Days before transitioning Silver layer data to Glacier"
  type        = number
  default     = 180
}

variable "silver_expiration_days" {
  description = "Days before expiring Silver layer data"
  type        = number
  default     = 730
}

variable "gold_intelligent_tiering_days" {
  description = "Days before transitioning Gold layer data to Intelligent Tiering"
  type        = number
  default     = 30
}

variable "logs_expiration_days" {
  description = "Days before expiring log files"
  type        = number
  default     = 365
}

# ============================================================================
# Kinesis Firehose Configuration
# ============================================================================

variable "firehose_buffering_size" {
  description = "Firehose buffer size in MB"
  type        = number
  default     = 5
}

variable "firehose_buffering_interval" {
  description = "Firehose buffer interval in seconds"
  type        = number
  default     = 300
}

variable "firehose_compression_format" {
  description = "Compression format for Firehose (GZIP, SNAPPY, ZIP, HADOOP_SNAPPY, UNCOMPRESSED)"
  type        = string
  default     = "GZIP"

  validation {
    condition     = contains(["GZIP", "SNAPPY", "ZIP", "HADOOP_SNAPPY", "UNCOMPRESSED"], var.firehose_compression_format)
    error_message = "Compression format must be one of: GZIP, SNAPPY, ZIP, HADOOP_SNAPPY, UNCOMPRESSED."
  }
}

# ============================================================================
# Lambda Configuration
# ============================================================================

variable "lambda_runtime" {
  description = "Lambda runtime version"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "create_lambda_webhook_processor" {
  description = "Create webhook processor Lambda function"
  type        = bool
  default     = true
}

variable "create_lambda_data_enrichment" {
  description = "Create data enrichment Lambda function"
  type        = bool
  default     = true
}

variable "create_lambda_api_polling" {
  description = "Create API polling Lambda function"
  type        = bool
  default     = true
}

# ============================================================================
# API Gateway Configuration
# ============================================================================

variable "create_api_gateway" {
  description = "Create API Gateway for webhooks"
  type        = bool
  default     = true
}

variable "api_gateway_create_usage_plan" {
  description = "Create usage plan for API Gateway"
  type        = bool
  default     = true
}

variable "api_gateway_quota_limit" {
  description = "API Gateway quota limit (requests per day)"
  type        = number
  default     = 100000
}

variable "api_gateway_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 5000
}

variable "api_gateway_throttle_rate_limit" {
  description = "API Gateway throttle rate limit (requests per second)"
  type        = number
  default     = 2000
}

variable "api_gateway_create_api_key" {
  description = "Create API key for API Gateway"
  type        = bool
  default     = true
}

# ============================================================================
# AWS Glue Configuration
# ============================================================================

variable "glue_worker_type" {
  description = "Glue worker type (G.1X, G.2X, G.025X, G.4X, G.8X)"
  type        = string
  default     = "G.1X"

  validation {
    condition     = contains(["G.1X", "G.2X", "G.025X", "G.4X", "G.8X"], var.glue_worker_type)
    error_message = "Glue worker type must be one of: G.1X, G.2X, G.025X, G.4X, G.8X."
  }
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 2
}

variable "create_glue_bronze_to_silver_job" {
  description = "Create Glue job for Bronze to Silver transformation"
  type        = bool
  default     = true
}

variable "create_glue_silver_to_gold_job" {
  description = "Create Glue job for Silver to Gold transformation"
  type        = bool
  default     = true
}

# ============================================================================
# MWAA Configuration
# ============================================================================

variable "create_mwaa_environment" {
  description = "Create MWAA (Managed Airflow) environment"
  type        = bool
  default     = true
}

variable "mwaa_airflow_version" {
  description = "MWAA Airflow version"
  type        = string
  default     = "2.7.2"
}

variable "mwaa_environment_class" {
  description = "MWAA environment class (mw1.small, mw1.medium, mw1.large)"
  type        = string
  default     = "mw1.small"

  validation {
    condition     = contains(["mw1.small", "mw1.medium", "mw1.large"], var.mwaa_environment_class)
    error_message = "MWAA environment class must be one of: mw1.small, mw1.medium, mw1.large."
  }
}

variable "mwaa_max_workers" {
  description = "MWAA maximum workers"
  type        = number
  default     = 10
}

variable "mwaa_min_workers" {
  description = "MWAA minimum workers"
  type        = number
  default     = 1
}
