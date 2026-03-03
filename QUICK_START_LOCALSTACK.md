# Quick Start: LocalStack Testing

## Prerequisites
- ✅ Docker Desktop running
- ✅ Terraform installed
- ✅ PowerShell (Windows)

## Option 1: Automated Script (Recommended)

```powershell
# Run the complete initialization script
.\scripts\init-localstack.ps1
```

This script will:
1. Check prerequisites (Docker, Terraform)
2. Start LocalStack container
3. Wait for LocalStack to be ready
4. Initialize Terraform
5. Validate configuration
6. Plan deployment
7. Apply infrastructure
8. Verify deployment

## Option 2: Simple Script (If Option 1 Fails)

```powershell
# Run the simplified version
.\scripts\start-localstack-simple.ps1
```

## Option 3: Manual Steps

If both scripts fail, run these commands one by one:

```powershell
# 1. Start LocalStack
docker-compose -f docker-compose.localstack.yml up -d

# 2. Wait 30 seconds
Start-Sleep -Seconds 30

# 3. Verify LocalStack is running
curl http://localhost:4566/_localstack/health

# 4. Initialize Terraform
cd terraform
terraform init

# 5. Validate
terraform validate

# 6. Plan
terraform plan -var-file="terraform.tfvars"

# 7. Apply
terraform apply -var-file="terraform.tfvars" -auto-approve

# 8. View results
terraform output
terraform state list
```

## Verify Deployment

### Check Resources
```powershell
cd terraform
terraform state list
```

### Check Tags
```powershell
# VPC tags
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs --query 'Vpcs[*].Tags'

# Subnet tags
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets --query 'Subnets[*].Tags'

# Security Group tags
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups --query 'SecurityGroups[*].Tags'
```

### Expected Tags
All resources should have these 7 mandatory tags:
- Application
- Environment
- Owner
- CostCenter
- BusinessUnit
- Country
- Criticality

## Cleanup

```powershell
# Destroy infrastructure
cd terraform
terraform destroy -var-file="terraform.tfvars" -auto-approve

# Stop LocalStack
cd ..
docker-compose -f docker-compose.localstack.yml down
```

## Troubleshooting

### Docker not running
```powershell
# Check Docker status
docker info

# If not running, start Docker Desktop and wait for it to be ready
```

### LocalStack not responding
```powershell
# Check container status
docker ps | findstr localstack

# View logs
docker logs localstack-janis-cencosud --tail 50

# Restart if needed
docker-compose -f docker-compose.localstack.yml restart
```

### Terraform errors
```powershell
# Clean and reinitialize
cd terraform
Remove-Item .terraform -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item terraform.tfstate* -Force -ErrorAction SilentlyContinue
terraform init
```

## Next Steps

After successful LocalStack testing:

1. ✅ Verify all resources created
2. ✅ Verify all tags applied correctly
3. ✅ Update cost center placeholder in environment tfvars
4. ✅ Prepare for AWS deployment

## Documentation

- **Complete Guide:** `COMPLETE_TAGGING_AND_LOCALSTACK_UPDATE.md`
- **Troubleshooting:** `LOCALSTACK_TROUBLESHOOTING.md`
- **Tagging Policy:** `Politica_Etiquetado_AWS.md`
- **Terraform Guide:** `.kiro/steering/Terraform Best Practices.md`

## Support

If you encounter issues:
1. Check `LOCALSTACK_TROUBLESHOOTING.md`
2. Review `COMPLETE_TAGGING_AND_LOCALSTACK_UPDATE.md`
3. Use manual steps (Option 3)
4. Check Docker and Terraform logs
