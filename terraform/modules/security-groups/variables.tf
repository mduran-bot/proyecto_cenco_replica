variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "existing_redshift_sg_id" {
  description = "Security Group ID of existing Redshift cluster"
  type        = string
}

variable "existing_bi_security_groups" {
  description = "List of Security Group IDs for existing BI systems"
  type        = list(string)
}

variable "existing_bi_ip_ranges" {
  description = "List of IP ranges for existing BI systems"
  type        = list(string)
}

variable "existing_mysql_pipeline_sg_id" {
  description = "Security Group ID of MySQL pipeline (temporary)"
  type        = string
}

variable "allowed_janis_ip_ranges" {
  description = "List of IP ranges allowed for webhooks (Client's private network ranges)"
  type        = list(string)
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
