# VPC Module

This module creates an AWS VPC with the specified CIDR block, DNS settings, and mandatory tags according to the Janis-Cencosud integration project requirements.

## Features

- Creates VPC with CIDR block 10.0.0.0/16 (65,536 IP addresses)
- Enables DNS resolution and DNS hostnames
- Configures IPv4 support (IPv6 ready for future expansion)
- Applies mandatory tags: Project, Environment, Component, Owner, CostCenter
- Designed for single-AZ deployment with reserved CIDR blocks for future multi-AZ expansion

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | ~> 5.0 |

## Inputs

| Name | Description | Type | Required | Default |
|------|-------------|------|----------|---------|
| vpc_cidr | CIDR block for the VPC (must be 10.0.0.0/16) | string | yes | - |
| name_prefix | Prefix for resource names | string | yes | - |
| common_tags | Common tags including Project, Environment, Owner, CostCenter | map(string) | yes | - |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | ID of the VPC |
| vpc_cidr_block | CIDR block of the VPC |
| vpc_arn | ARN of the VPC |
| default_security_group_id | ID of the default security group |
| default_network_acl_id | ID of the default network ACL |
| default_route_table_id | ID of the default route table |
| enable_dns_support | Whether DNS support is enabled |
| enable_dns_hostnames | Whether DNS hostnames are enabled |

## Usage Example

```hcl
module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr    = "10.0.0.0/16"
  name_prefix = "janis-cencosud-integration-dev"
  
  common_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "dev"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration-dev"
    ManagedBy   = "terraform"
  }
}
```

## Design Decisions

### Single-AZ Deployment
The VPC is designed for initial deployment in a single Availability Zone (us-east-1a) to reduce costs and complexity. Reserved CIDR blocks are documented for future multi-AZ expansion:
- Public Subnet B: 10.0.2.0/24 (reserved for us-east-1b)
- Private Subnet 1B: 10.0.11.0/24 (reserved for us-east-1b)
- Private Subnet 2B: 10.0.21.0/24 (reserved for us-east-1b)

### DNS Configuration
Both DNS resolution and DNS hostnames are enabled to support:
- Private DNS for VPC endpoints
- Internal service discovery
- Integration with Route 53 private hosted zones

### Tagging Strategy
All resources include mandatory tags for:
- Resource identification and organization
- Cost allocation and tracking
- Compliance and governance
- Operational management

## Validation

The module includes validation rules to ensure:
- VPC CIDR is a valid IPv4 CIDR block
- VPC CIDR is exactly 10.0.0.0/16 (65,536 IP addresses)
- Name prefix follows naming conventions
- All mandatory tags are present

## References

- Requirements: 1.1, 1.3, 1.4, 8.1
- Design Document: `.kiro/specs/aws-infrastructure/design.md`
- AWS VPC Documentation: https://docs.aws.amazon.com/vpc/
