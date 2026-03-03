# LocalStack Configuration

## Overview

The `localstack.tfvars` file provides a minimal Terraform configuration specifically designed for testing the AWS infrastructure locally using LocalStack. This configuration allows developers to validate infrastructure code without incurring AWS costs.

## File Location

```
terraform/localstack.tfvars
terraform/localstack_override.tf
```

## Key Features

### Minimal Configuration
- **Single-AZ deployment**: Only us-east-1a resources to simplify testing
- **Disabled VPC Endpoints**: Not necessary in LocalStack Community edition
- **Disabled monitoring**: VPC Flow Logs and DNS logging turned off
- **Dummy values**: Placeholder values for services not fully supported in LocalStack
- **Corporate tagging**: Uses same tagging strategy as production via `local.all_tags`

### Network Configuration
```hcl
vpc_cidr               = "10.0.0.0/16"
public_subnet_a_cidr   = "10.0.1.0/24"
private_subnet_1a_cidr = "10.0.11.0/24"
private_subnet_2a_cidr = "10.0.21.0/24"
enable_multi_az        = false
```

### Disabled Features
The following features are disabled to simplify LocalStack testing:

- **VPC Endpoints**: All 7 endpoints disabled (S3, Glue, Secrets Manager, etc.)
- **VPC Flow Logs**: Disabled to reduce complexity
- **DNS Query Logging**: Disabled to reduce complexity
- **WAF**: Explicitly disabled (`enable_waf = false`) - Not supported in LocalStack Community

### Dummy Values
Services not fully supported in LocalStack use placeholder values:

```hcl
existing_redshift_cluster_id = "localstack-redshift-test"
existing_redshift_sg_id      = "sg-localstack-redshift"
mwaa_environment_arn         = ""  # Not available in LocalStack Community
nat_gateway_id               = "dummy-nat-gateway-id"  # Placeholder for NAT Gateway
```

### Provider Override Configuration

The `terraform/localstack_override.tf` file configures the AWS provider to use LocalStack:

```hcl
provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    # All AWS service endpoints redirect to LocalStack
    apigateway     = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    # ... other services
  }

  # Corporate AWS Tagging Policy - Applied to all resources
  default_tags {
    tags = local.all_tags
  }
}
```

**Key Points**:
- Uses test credentials (no real AWS credentials needed)
- All service endpoints point to LocalStack (localhost:4566)
- Skips AWS-specific validations for faster local testing
- **Applies corporate tagging policy** consistently via `local.all_tags`
- Ensures local testing follows same tagging standards as production

## Usage

### Basic Deployment

```powershell
# From terraform/ directory
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="localstack.tfvars"

# Apply configuration
terraform apply -var-file="localstack.tfvars" -auto-approve
```

### With LocalStack Running

```powershell
# 1. Start LocalStack
docker-compose -f docker-compose.localstack.yml up -d

# 2. Deploy infrastructure
cd terraform
terraform init
terraform apply -var-file="localstack.tfvars" -auto-approve

# 3. Verify resources
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs

# 4. Clean up
terraform destroy -var-file="localstack.tfvars" -auto-approve
docker-compose -f docker-compose.localstack.yml down
```

## What Gets Created

When deploying with `localstack.tfvars`, the following resources are created in LocalStack:

### Core Networking
- 1 VPC (10.0.0.0/16)
- 3 Subnets (1 public, 2 private in us-east-1a)
- 1 Internet Gateway
- 1 NAT Gateway (emulated with dummy ID: `dummy-nat-gateway-id`)
- Route Tables

### Security
- 7 Security Groups (API Gateway, Redshift, Lambda, MWAA, Glue, EventBridge, VPC Endpoints)
- 2 Network ACLs (Public and Private)

### Orchestration
- EventBridge custom event bus
- 5 EventBridge scheduled rules
- Dead Letter Queue (SQS)

### Monitoring (Minimal)
- CloudWatch Log Groups (basic)
- No VPC Flow Logs
- No DNS Query Logging

## Differences from Production

| Feature | LocalStack | Production |
|---------|-----------|------------|
| **Multi-AZ** | Disabled | Initially disabled, can enable |
| **VPC Endpoints** | Disabled | All 7 enabled |
| **VPC Flow Logs** | Disabled | Enabled |
| **DNS Logging** | Disabled | Enabled |
| **WAF** | Not created | Full WAF with rules |
| **Redshift** | Dummy values | Real cluster integration |
| **MWAA** | Not available | Real Airflow environment |
| **Retention** | 7 days | 90 days (prod) |

## LocalStack Limitations

### Fully Supported
- ✅ VPC, Subnets, Security Groups
- ✅ Route Tables, Internet Gateway
- ✅ EventBridge (basic)
- ✅ CloudWatch Logs (basic)
- ✅ IAM, STS

### Limited Support
- ⚠️ NAT Gateway (emulated with dummy ID, not real routing)
- ⚠️ VPC Endpoints (created but don't affect routing)
- ⚠️ Redshift (basic emulation only)

### Not Supported (Community)
- ❌ MWAA (Managed Airflow)
- ❌ WAF
- ❌ VPC Flow Logs (full functionality)
- ❌ DNS Query Logging

## Customization

To modify the LocalStack configuration:

1. **Edit localstack.tfvars** to change values
2. **Enable features** by setting flags to `true`
3. **Add resources** by modifying Terraform modules

Example - Enable VPC Flow Logs:
```hcl
enable_vpc_flow_logs = true
```

Example - Enable S3 Endpoint:
```hcl
enable_s3_endpoint = true
```

## Troubleshooting

**📖 GUÍA COMPLETA:** Ver **[../LOCALSTACK_TROUBLESHOOTING.md](../LOCALSTACK_TROUBLESHOOTING.md)** para soluciones detalladas a todos los problemas.

### Resources Not Created
```powershell
# Check LocalStack is running
curl http://localhost:4566/_localstack/health

# Check Terraform logs
$env:TF_LOG="DEBUG"
terraform apply -var-file="localstack.tfvars"
```

### Terraform Can't Connect
```powershell
# Verify endpoint configuration in providers.tf
# Should point to localhost:4566

# Check LocalStack logs
docker-compose -f docker-compose.localstack.yml logs -f
```

### State Issues
```powershell
# Remove state and start fresh
rm terraform.tfstate*
rm -rf .terraform/
terraform init
terraform apply -var-file="localstack.tfvars" -auto-approve
```

### PowerShell Script Errors
```powershell
# Use simplified script
..\scripts\start-localstack-simple.ps1

# Or use manual commands
# See LOCALSTACK_TROUBLESHOOTING.md for step-by-step commands
```

Para más ayuda, consulta:
- **[LOCALSTACK_TROUBLESHOOTING.md](../LOCALSTACK_TROUBLESHOOTING.md)** - Guía completa de troubleshooting
- **[README-LOCALSTACK.md](../README-LOCALSTACK.md)** - Documentación completa de LocalStack

## Best Practices

### Development Workflow
1. **Start LocalStack** before Terraform operations
2. **Use auto-approve** for faster iteration
3. **Destroy resources** when done to start fresh
4. **Stop LocalStack** to clean up completely

### Testing Strategy
1. **Test modules individually** first
2. **Test full stack** with localstack.tfvars
3. **Validate in dev environment** before staging/prod
4. **Use LocalStack** for rapid iteration

### Cost Optimization
- LocalStack is **completely free** for testing
- No AWS costs incurred
- Ideal for development and CI/CD pipelines
- Use for training and experimentation

## Related Documentation

- **[GUIA_INICIO_LOCALSTACK.md](../GUIA_INICIO_LOCALSTACK.md)** - Step-by-step beginner's guide (Spanish)
- **[README-LOCALSTACK.md](../README-LOCALSTACK.md)** - Complete LocalStack guide
- **[GUIA_COMPARTIR_PROYECTO.md](../GUIA_COMPARTIR_PROYECTO.md)** - Project setup guide
- **[terraform/README.md](./README.md)** - Terraform documentation
- **[docker-compose.localstack.yml](../docker-compose.localstack.yml)** - LocalStack configuration

## Next Steps

After validating with LocalStack:

1. **Test in AWS dev** environment
2. **Promote to staging** for integration testing
3. **Deploy to production** with full configuration

---

**Last Updated**: January 27, 2026  
**Status**: ✅ Ready for use  
**Purpose**: Local testing without AWS costs
