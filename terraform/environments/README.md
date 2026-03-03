# Environment-Specific Configurations

This directory contains environment-specific Terraform variable files for deploying the Janis-Cencosud integration infrastructure across different environments.

## Directory Structure

```
environments/
├── dev/
│   └── dev.tfvars          # Development environment configuration
├── staging/
│   └── staging.tfvars      # Staging environment configuration
├── prod/
│   └── prod.tfvars         # Production environment configuration
└── README.md               # This file
```

## Environment Overview

### Development (dev/)
- **Purpose**: Local development and feature testing
- **Characteristics**:
  - Single-AZ deployment for cost optimization
  - Relaxed security settings for easier testing
  - Shorter log retention periods (7 days)
  - More frequent polling for faster feedback
  - Optional monitoring to reduce costs
- **Use Case**: Individual developer testing, proof of concepts

### Staging (staging/)
- **Purpose**: Pre-production testing and integration validation
- **Characteristics**:
  - Mirrors production configuration
  - Production-like security settings
  - Medium log retention (30 days)
  - Production polling frequencies
  - Full monitoring enabled
- **Use Case**: Integration testing, UAT, performance testing

### Production (prod/)
- **Purpose**: Live production workload
- **Characteristics**:
  - Initially Single-AZ (can expand to Multi-AZ)
  - Strict security requirements
  - Long log retention (90 days)
  - Optimized polling frequencies
  - Full monitoring and alerting
  - Requires MFA and approval for changes
- **Use Case**: Production data integration pipeline

## Configuration Files

Each environment has a `.tfvars` file containing:

1. **AWS Configuration**: Region, account ID
2. **Network Configuration**: VPC, subnets, Multi-AZ settings
3. **Existing Infrastructure**: Redshift cluster, BI systems integration
4. **Tagging Strategy**: Project metadata, cost allocation
5. **Security Configuration**: IP allowlists, WAF settings
6. **Monitoring Configuration**: Log retention, alerting
7. **EventBridge Configuration**: Polling frequencies
8. **VPC Endpoints**: Service endpoint enablement

## Before Deployment

### Required Actions

1. **Replace Placeholder Values**:
   - Search for `REPLACE:` comments in each `.tfvars` file
   - Update with actual values for your environment
   - Verify all security groups and IP ranges

2. **Configure Credentials**:
   - NEVER hardcode credentials in `.tfvars` files
   - Use one of the secure methods documented below
   - Ensure credentials are environment-specific

3. **Review Security Settings**:
   - Verify IP allowlists are restrictive
   - Confirm security group configurations
   - Validate WAF settings
   - Check compliance with corporate policies

4. **Verify Integration Points**:
   - Confirm Redshift cluster details
   - Validate BI system access requirements
   - Check MWAA environment ARN (if created)

## Credential Management

### Method 1: Environment Variables (Recommended for Local)

```bash
# Set AWS credentials as environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"  # Optional for STS

# Deploy to development
cd terraform
terraform plan -var-file="environments/dev/dev.tfvars"
terraform apply -var-file="environments/dev/dev.tfvars"
```

### Method 2: AWS SSO/IAM Identity Center (Recommended for Teams)

```bash
# Configure AWS SSO profile
aws configure sso --profile dev

# Login to SSO
aws sso login --profile dev

# Set profile for Terraform
export AWS_PROFILE=dev

# Deploy
cd terraform
terraform plan -var-file="environments/dev/dev.tfvars"
terraform apply -var-file="environments/dev/dev.tfvars"
```

### Method 3: Credentials File (NOT Committed)

```bash
# Create credentials.tfvars (add to .gitignore)
cat > credentials.tfvars << EOF
aws_access_key_id     = "your-access-key"
aws_secret_access_key = "your-secret-key"
EOF

# Deploy with credentials file
cd terraform
terraform plan \
  -var-file="environments/dev/dev.tfvars" \
  -var-file="credentials.tfvars"
```

**IMPORTANT**: Add `credentials.tfvars` to `.gitignore` to prevent accidental commits.

## Deployment Workflow

**📖 GUÍA RÁPIDA:** Ver [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) para pasos simplificados de deployment

### Automated Deployment (Recommended)

El proyecto incluye scripts automatizados en `terraform/scripts/` para facilitar el deployment:

#### 1. Inicializar Ambiente

```bash
cd terraform/scripts
./init-environment.sh dev
```

Este script:
- Crea la estructura de directorios del ambiente
- Configura symlinks a archivos compartidos
- Genera archivos base (main.tf, outputs.tf, .tfvars)
- Ejecuta terraform init y validate

#### 2. Desplegar con Script Automatizado

```bash
cd terraform/scripts

# Usando variables de entorno
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
./deploy.sh dev

# O pasando credenciales como argumentos
./deploy.sh dev $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY
```

El script de deployment:
- ✅ Crea backup automático del state
- ✅ Valida formato y configuración
- ✅ Ejecuta security scan (si tfsec está instalado)
- ✅ Genera plan para revisión
- ✅ Requiere confirmación manual antes de apply
- ✅ Guarda metadata del deployment

#### 3. Gestionar Backups

```bash
cd terraform/scripts

# Crear backup manual
./backup-state.sh dev

# Listar backups
./backup-state.sh dev --list

# Limpiar backups antiguos
./backup-state.sh dev --clean 10
```

Ver documentación completa en [terraform/scripts/README.md](../scripts/README.md).

### Manual Deployment Process

Si prefieres ejecutar los comandos manualmente:

### Development Environment

```bash
# 1. Navigate to terraform directory
cd terraform

# 2. Initialize Terraform (first time only)
terraform init

# 3. Format and validate
terraform fmt -recursive
terraform validate

# 4. Plan changes
terraform plan -var-file="environments/dev/dev.tfvars"

# 5. Apply changes
terraform apply -var-file="environments/dev/dev.tfvars"
```

### Staging Environment

```bash
# 1. Ensure changes tested in dev first
# 2. Navigate to terraform directory
cd terraform

# 3. Plan changes
terraform plan -var-file="environments/staging/staging.tfvars"

# 4. Review plan carefully
# 5. Apply with approval
terraform apply -var-file="environments/staging/staging.tfvars"

# 6. Run integration tests
# 7. Validate functionality
```

### Production Environment

```bash
# CRITICAL: Follow production deployment checklist

# 1. Ensure changes tested in staging
# 2. Obtain change approval
# 3. Schedule maintenance window
# 4. Backup current state
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)

# 5. Navigate to terraform directory
cd terraform

# 6. Plan changes
terraform plan -var-file="environments/prod/prod.tfvars" -out=prod.tfplan

# 7. Review plan with team
# 8. Apply during maintenance window
terraform apply prod.tfplan

# 9. Verify deployment
# 10. Monitor for issues
```

## State Management

### Local State (Current Approach)

Each environment maintains its own local state file:

```
terraform/
├── terraform.tfstate           # State file (NOT committed)
├── terraform.tfstate.backup    # Automatic backup
└── .terraform/                 # Provider plugins
```

### State Backup Strategy

```bash
# Manual backup before major changes
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)

# Automated backup script
./scripts/backup-state.sh <environment>
```

### State File Security

- **NEVER commit** `terraform.tfstate` to Git
- **Add to .gitignore**: `*.tfstate`, `*.tfstate.*`
- **Backup regularly** before applying changes
- **Coordinate with team** to avoid concurrent modifications
- **Store backups securely** with appropriate access controls

## Environment-Specific Considerations

### Development
- **Cost Optimization**: Disable unnecessary monitoring, use smaller instances
- **Flexibility**: More permissive security for testing
- **Iteration Speed**: Faster polling for quick feedback
- **Auto-Shutdown**: Consider implementing auto-shutdown for cost savings

### Staging
- **Production Parity**: Mirror production configuration as closely as possible
- **Testing**: Full integration and performance testing
- **Validation**: Verify all production scenarios
- **Approval**: Require approval before promoting to production

### Production
- **Security**: Strict security controls, MFA required
- **Monitoring**: Full monitoring and alerting enabled
- **Compliance**: Meet all corporate compliance requirements
- **Change Control**: Formal change management process
- **High Availability**: Plan for Multi-AZ expansion
- **Disaster Recovery**: Documented recovery procedures

## Troubleshooting

### Common Issues

**Issue**: Terraform can't find credentials
```bash
# Solution: Verify environment variables are set
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Or check AWS profile
aws sts get-caller-identity --profile dev
```

**Issue**: State file conflicts
```bash
# Solution: Coordinate with team, use state locking
# For local state, ensure only one person applies at a time
```

**Issue**: Variable validation errors
```bash
# Solution: Check variable values in .tfvars file
# Ensure all required variables are set
# Verify format matches validation rules
```

**Issue**: Resource already exists
```bash
# Solution: Import existing resource into state
terraform import -var-file="environments/dev/dev.tfvars" \
  aws_vpc.main vpc-xxxxx
```

## Security Best Practices

### Credentials
- ✓ Use environment variables or AWS SSO
- ✓ Rotate credentials regularly (monthly minimum)
- ✓ Use different credentials per environment
- ✓ Enable MFA for production access
- ✗ NEVER hardcode credentials in files
- ✗ NEVER commit credentials to Git

### Access Control
- ✓ Implement least privilege IAM policies
- ✓ Use IAM roles for service access
- ✓ Audit access regularly
- ✓ Require approval for production changes

### Network Security
- ✓ Restrict IP allowlists to known ranges
- ✓ Use security groups with minimal permissions
- ✓ Enable VPC Flow Logs
- ✓ Configure WAF with appropriate rules

## Migration Path

### Single-AZ to Multi-AZ

When ready to expand to Multi-AZ for high availability:

1. **Update Configuration**:
   ```hcl
   enable_multi_az = true
   ```

2. **Review Reserved CIDRs**:
   - Verify reserved CIDR blocks don't conflict
   - Confirm us-east-1b availability

3. **Plan Migration**:
   ```bash
   terraform plan -var-file="environments/prod/prod.tfvars"
   ```

4. **Apply During Maintenance Window**:
   ```bash
   terraform apply -var-file="environments/prod/prod.tfvars"
   ```

5. **Validate**:
   - Verify resources created in both AZs
   - Test failover scenarios
   - Update monitoring dashboards

## Additional Resources

- [Terraform Best Practices](../.kiro/steering/Terraform%20Best%20Practices.md)
- [AWS Best Practices](../.kiro/steering/Buenas%20practicas%20de%20AWS.md)
- [Project Structure](../.kiro/steering/structure.md)
- [Deployment Guide](../DEPLOYMENT_NOTES.md)
- [Multi-AZ Expansion Guide](../MULTI_AZ_EXPANSION.md)

## Support

For questions or issues:
- **Infrastructure Team**: [Add contact]
- **Security Team**: [Add contact]
- **Documentation**: See `terraform/README.md`
- **Emergency**: Follow escalation procedures in production tfvars
