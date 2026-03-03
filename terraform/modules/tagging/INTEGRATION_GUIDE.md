# Tagging Module Integration Guide

This guide explains how to integrate the tagging module into the existing Janis-Cencosud infrastructure.

## Current State

The infrastructure currently uses AWS provider `default_tags` in `terraform/shared/providers.tf`:

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
```

This automatically applies base tags to all resources. The tagging module complements this by:
1. Validating tag values before deployment
2. Adding component-specific tags
3. Enforcing organizational standards

## Integration Approach

### Option 1: Provider Default Tags Only (Current)

**Best for**: Simple deployments where all resources share the same tags

```hcl
# No changes needed - provider default_tags handle everything
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  # Tags automatically applied by provider
}
```

### Option 2: Tagging Module for Component-Specific Tags (Recommended)

**Best for**: Complex deployments with component-specific metadata

```hcl
# Define component-specific tags
module "vpc_tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "vpc"  # Component-specific
    Owner       = var.owner
    CostCenter  = var.cost_center
  }

  optional_tags = {
    Purpose = "network-infrastructure"
  }
}

# Apply to resource
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags       = module.vpc_tags.tags
}
```

### Option 3: Hybrid Approach (Most Flexible)

**Best for**: Leveraging both provider defaults and component-specific validation

```hcl
# Provider applies base tags automatically
# Use tagging module for validation and additional tags

module "lambda_tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "lambda-webhook-processor"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }

  optional_tags = {
    Runtime = "python3.11"
    Purpose = "webhook-ingestion"
  }
}

# Only specify component-specific tags
# Provider default_tags are automatically merged
resource "aws_lambda_function" "webhook" {
  function_name = "webhook-processor"
  runtime       = "python3.11"
  
  tags = {
    Component = "lambda-webhook-processor"
    Runtime   = "python3.11"
    Purpose   = "webhook-ingestion"
  }
}
```

## Integration Steps

### Step 1: Update Module Calls

For each module that creates resources, add tagging module calls:

```hcl
# terraform/main.tf

module "vpc_tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "vpc"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }
}

module "vpc" {
  source = "./modules/vpc"
  
  # Pass validated tags to module
  tags = module.vpc_tags.tags
  
  # Other variables...
}
```

### Step 2: Update Module Variables

Add tags variable to modules that need it:

```hcl
# terraform/modules/vpc/variables.tf

variable "tags" {
  description = "Tags to apply to VPC resources"
  type        = map(string)
  default     = {}
}
```

### Step 3: Apply Tags to Resources

Update resource definitions to use tags:

```hcl
# terraform/modules/vpc/main.tf

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-vpc"
    }
  )
}
```

## Module-Specific Integration Examples

### VPC Module

```hcl
module "vpc_tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "vpc"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }

  optional_tags = {
    Purpose = "network-infrastructure"
  }
}

module "vpc" {
  source = "./modules/vpc"
  
  vpc_cidr    = var.vpc_cidr
  name_prefix = local.name_prefix
  tags        = module.vpc_tags.tags
}
```

### Security Groups Module

```hcl
module "sg_tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "security-groups"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }

  optional_tags = {
    Purpose = "network-security"
  }
}

module "security_groups" {
  source = "./modules/security-groups"
  
  vpc_id      = module.vpc.vpc_id
  name_prefix = local.name_prefix
  tags        = module.sg_tags.tags
}
```

### Lambda Functions

```hcl
module "lambda_webhook_tags" {
  source = "./modules/tagging"

  mandatory_tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "lambda-webhook-processor"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }

  optional_tags = {
    Runtime = "python3.11"
    Purpose = "webhook-ingestion"
  }
}

resource "aws_lambda_function" "webhook_processor" {
  function_name = "${local.name_prefix}-webhook-processor"
  runtime       = "python3.11"
  
  tags = module.lambda_webhook_tags.tags
}
```

## Validation in CI/CD

Add validation checks to your deployment pipeline:

```bash
#!/bin/bash
# validate-tags.sh

echo "Validating tagging configuration..."

cd terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Check for validation_passed output
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.planned_values.outputs | to_entries[] | select(.key | contains("validation_passed")) | .value.value'

# If any validation_passed is false, fail the pipeline
if terraform show -json plan.tfplan | jq '.planned_values.outputs | to_entries[] | select(.key | contains("validation_passed")) | .value.value' | grep -q false; then
  echo "ERROR: Tag validation failed!"
  exit 1
fi

echo "Tag validation passed!"
```

## Best Practices

1. **Use Variables**: Always pass tag values from root variables for consistency
2. **Component Naming**: Use descriptive component names (e.g., "vpc", "lambda-webhook", "s3-datalake-bronze")
3. **Validation First**: Run `terraform plan` to check validation before applying
4. **Document Custom Tags**: Document any custom optional tags in module README
5. **Cost Allocation**: Ensure CostCenter tags are accurate for billing reports

## Migration Strategy

### Phase 1: Add Tagging Module (No Changes to Resources)

1. Create tagging module (✓ Complete)
2. Add module calls to main.tf
3. Validate with `terraform plan` (should show no changes)

### Phase 2: Update Modules to Accept Tags

1. Add `tags` variable to each module
2. Update resource definitions to use tags
3. Test in development environment

### Phase 3: Apply to All Environments

1. Deploy to development
2. Validate tags in AWS Console
3. Deploy to staging
4. Deploy to production

## Troubleshooting

### Issue: Validation Failed

```
Error: Environment must be one of: development, staging, production
```

**Solution**: Check that `var.environment` uses the correct value:
- ✓ "development", "staging", "production"
- ✗ "dev", "stage", "prod"

### Issue: Missing Mandatory Tags

```
Error: Missing mandatory tags: Component
```

**Solution**: Ensure all 5 mandatory tags are provided in the `mandatory_tags` object.

### Issue: Tag Value Too Long

```
Error: Tag values exceed 256 characters
```

**Solution**: Shorten tag values to 256 characters or less (AWS limit).

## References

- [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [Terraform AWS Provider Default Tags](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags)
- Module README: `terraform/modules/tagging/README.md`
- Implementation Summary: `terraform/modules/tagging/IMPLEMENTATION_SUMMARY.md`
