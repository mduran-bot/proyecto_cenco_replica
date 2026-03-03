# Development Environment Main Configuration
#
# This file serves as the entry point for the development environment.
# It references shared configuration and includes module calls.

# ============================================================================
# VPC Module
# ============================================================================

module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr               = var.vpc_cidr
  aws_region             = var.aws_region
  name_prefix            = local.name_prefix
  tags                   = local.common_tags
  enable_multi_az        = false
  public_subnet_a_cidr   = "10.0.1.0/24"
  public_subnet_b_cidr   = "10.0.2.0/24"
  private_subnet_1a_cidr = "10.0.11.0/24"
  private_subnet_1b_cidr = "10.0.12.0/24"
  private_subnet_2a_cidr = "10.0.21.0/24"
  private_subnet_2b_cidr = "10.0.22.0/24"
}

# ============================================================================
# Outputs
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "vpc_arn" {
  description = "ARN of the VPC"
  value       = module.vpc.vpc_arn
}
