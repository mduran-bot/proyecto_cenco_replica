variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "nat_gateway_id" {
  description = "ID of the NAT Gateway"
  type        = string
  default     = ""
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_flow_logs_retention_days" {
  description = "Retention period for VPC Flow Logs (days)"
  type        = number
}

variable "dns_logs_retention_days" {
  description = "Retention period for DNS Query Logs (days)"
  type        = number
}

variable "alarm_sns_topic_arn" {
  description = "SNS Topic ARN for CloudWatch alarms"
  type        = string
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
}

variable "enable_dns_query_logging" {
  description = "Enable DNS Query Logging"
  type        = bool
}

variable "eventbridge_rule_names" {
  description = "Names of EventBridge rules for alarms"
  type        = list(string)
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
