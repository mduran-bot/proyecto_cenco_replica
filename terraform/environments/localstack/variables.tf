variable "environment" {
  description = "Environment name"
  type        = string
  default     = "localstack"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "janis-cencosud"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "owner" {
  description = "Owner tag"
  type        = string
}

variable "cost_center" {
  description = "Cost center tag"
  type        = string
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = false
}

variable "alarm_email" {
  description = "Email for CloudWatch alarms"
  type        = string
}
