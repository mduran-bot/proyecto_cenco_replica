variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "mwaa_environment_arn" {
  description = "ARN of the MWAA environment to trigger"
  type        = string
}
