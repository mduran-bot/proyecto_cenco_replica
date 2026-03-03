variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of private subnets for Interface Endpoints"
  type        = list(string)
}

variable "route_table_ids" {
  description = "IDs of route tables for Gateway Endpoints"
  type        = list(string)
}

variable "vpc_endpoints_security_group_id" {
  description = "Security Group ID for Interface Endpoints"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "enable_s3_endpoint" {
  description = "Enable S3 Gateway Endpoint"
  type        = bool
}

variable "enable_glue_endpoint" {
  description = "Enable Glue Interface Endpoint"
  type        = bool
}

variable "enable_secrets_manager_endpoint" {
  description = "Enable Secrets Manager Interface Endpoint"
  type        = bool
}

variable "enable_logs_endpoint" {
  description = "Enable CloudWatch Logs Interface Endpoint"
  type        = bool
}

variable "enable_kms_endpoint" {
  description = "Enable KMS Interface Endpoint"
  type        = bool
}

variable "enable_sts_endpoint" {
  description = "Enable STS Interface Endpoint"
  type        = bool
}

variable "enable_events_endpoint" {
  description = "Enable EventBridge Interface Endpoint"
  type        = bool
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
