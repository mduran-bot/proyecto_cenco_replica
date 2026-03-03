variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "public_subnet_a_cidr" {
  description = "CIDR block for public subnet in AZ A"
  type        = string
}

variable "private_subnet_1a_cidr" {
  description = "CIDR block for private subnet 1A"
  type        = string
}

variable "private_subnet_2a_cidr" {
  description = "CIDR block for private subnet 2A"
  type        = string
}

variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
}

variable "public_subnet_b_cidr" {
  description = "CIDR block for public subnet in AZ B"
  type        = string
}

variable "private_subnet_1b_cidr" {
  description = "CIDR block for private subnet 1B"
  type        = string
}

variable "private_subnet_2b_cidr" {
  description = "CIDR block for private subnet 2B"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
