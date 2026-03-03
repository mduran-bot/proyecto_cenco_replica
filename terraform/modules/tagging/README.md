# Tagging Module

This module provides centralized tag management and validation for all AWS resources in the Janis-Cencosud infrastructure, aligned with the **Corporate AWS Tagging Policy**.

## Purpose

- Enforce mandatory tagging standards across all resources per Corporate Policy
- Validate tag keys and values according to AWS and organizational requirements
- Provide consistent tagging for cost allocation, resource management, and compliance
- Ensure all resources meet corporate governance standards

## Mandatory Tags (Corporate Policy)

All resources MUST have the following 7 tags according to the Corporate AWS Tagging Policy:

| Tag | Description | Allowed Values | Example |
|-----|-------------|----------------|---------|
| `Application` | Application name | Any non-empty string | `janis-cencosud-integration` |
| `Environment` | Environment name | `prod`, `qa`, `dev`, `uat`, `sandbox` | `prod` |
| `Owner` | Team or individual responsible | Any non-empty string | `data-engineering-team` |
| `CostCenter` | Cost center code for billing | Any non-empty string | `CC-DATA-001` |
| `BusinessUnit` | Business unit | Any non-empty string | `Data-Analytics` |
| `Country` | Country code | Any non-empty string | `CL` |
| `Criticality` | Criticality level | `high`, `medium`, `low` | `high` |

## Optional Tags

The following tags are optional but recommended:

| Tag | Description | Example |
|-----|-------------|---------|
| `CreatedBy` | Automation tool or user | `terraform`, `john.doe` |
| `CreatedDate` | Resource creation date | `2024-01-15` (auto-generated) |
| `LastModified` | Last modification date | `2024-02-20` |

## Validation Rules

The module enforces the following validation rules per Corporate Policy:

1. **Mandatory Tags**: All 7 mandatory tags must be present and non-empty
2. **Environment Values**: Must be one of `prod`, `qa`, `dev`, `uat`, `sandbox`
3. **Criticality Values**: Must be one of `high`, `medium`, `low`
4. **Tag Key Format**: Alphanumeric characters, hyphens, and underscores only
5. **Tag Value Length**: Maximum 256 characters (AWS limit)
6. **Auto-Generated Dates**: `CreatedDate` is automatically added if not provided

## Usage

### Basic Usage (Corporate Policy Compliant)

```hcl
module "tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Application  = "janis-cencosud-integration"
    Environment  = "prod"
    Owner        = "data-engineering-team"
    CostCenter   = "CC-DATA-001"
    BusinessUnit = "Data-Analytics"
    Country      = "CL"
    Criticality  = "high"
  }

  optional_tags = {
    DataClassification = "Confidential"
    BackupPolicy       = "daily"
  }
}

# Apply tags to a resource
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = module.tags.tags
}
```

### With Auto-Generated CreatedDate

```hcl
module "tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Application  = "janis-cencosud-integration"
    Environment  = "dev"
    Owner        = "data-engineering-team"
    CostCenter   = "CC-DATA-001"
    BusinessUnit = "Data-Analytics"
    Country      = "CL"
    Criticality  = "low"
  }

  include_created_date = true  # Default: true
}

# CreatedDate will be automatically added with current date
```

### Component-Specific Tags

```hcl
module "vpc_tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Application  = var.application_name
    Environment  = var.environment
    Owner        = var.owner
    CostCenter   = var.cost_center
    BusinessUnit = var.business_unit
    Country      = var.country
    Criticality  = var.criticality
  }

  optional_tags = {
    Component = "vpc"
    Purpose   = "network-infrastructure"
  }
}

module "lambda_tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Application  = var.application_name
    Environment  = var.environment
    Owner        = var.owner
    CostCenter   = var.cost_center
    BusinessUnit = var.business_unit
    Country      = var.country
    Criticality  = var.criticality
  }

  optional_tags = {
    Component = "lambda-webhook-processor"
    Runtime   = "python3.11"
    Purpose   = "webhook-ingestion"
  }
}
```

## Inputs

| Name | Description | Type | Required | Default |
|------|-------------|------|----------|---------|
| `mandatory_tags` | Mandatory tags per Corporate Policy (Application, Environment, Owner, CostCenter, BusinessUnit, Country, Criticality) | `object` | Yes | - |
| `optional_tags` | Optional tags to apply | `map(string)` | No | `{}` |
| `include_created_date` | Auto-add CreatedDate if not provided | `bool` | No | `true` |

## Outputs

| Name | Description |
|------|-------------|
| `tags` | Complete set of validated tags |
| `mandatory_tags` | Mandatory tags only |
| `optional_tags` | Optional tags only |
| `validation_passed` | Whether all validations passed |
| `tag_count` | Total number of tags |
| `mandatory_tag_keys` | List of mandatory tag keys |

## Validation Errors

The module will fail with descriptive errors if:

- Any mandatory tag is missing (all 7 required)
- Environment is not `prod`, `qa`, `dev`, `uat`, or `sandbox`
- Criticality is not `high`, `medium`, or `low`
- Tag keys contain invalid characters
- Tag values exceed 256 characters

## Integration with Provider Default Tags

This module works alongside the AWS provider's `default_tags` configuration:

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Application  = var.application_name
      Environment  = var.environment
      Owner        = var.owner
      CostCenter   = var.cost_center
      BusinessUnit = var.business_unit
      Country      = var.country
      Criticality  = var.criticality
      ManagedBy    = "terraform"
    }
  }
}
```

Use the tagging module for component-specific tags that override or extend the default tags.

## Best Practices

1. **Use Variables**: Pass mandatory tag values from root variables for consistency
2. **Corporate Compliance**: Ensure all 7 mandatory tags are always provided
3. **Environment Values**: Use only allowed values: `prod`, `qa`, `dev`, `uat`, `sandbox`
4. **Criticality Levels**: Use `high` for production, `medium` for staging, `low` for development
5. **Cost Allocation**: Ensure CostCenter tags are accurate for billing reports
6. **Documentation**: Document custom optional tags in your infrastructure code
7. **Validation**: Always check `validation_passed` output in CI/CD pipelines

## Requirements

- Terraform >= 1.0
- AWS Provider ~> 5.0

## References

- [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [Terraform AWS Provider Default Tags](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags)
- Corporate AWS Tagging Policy: `Politica_Etiquetado_AWS.md`
- Implementation Guide: `terraform/CORPORATE_TAGGING_IMPLEMENTATION.md`
- Requirements: 8.1, 8.2, 8.3, 8.4

---

**Last Updated**: January 28, 2026  
**Status**: ✅ Aligned with Corporate AWS Tagging Policy  
**Policy Version**: 1.0
