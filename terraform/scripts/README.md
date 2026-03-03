# Terraform Utility Scripts

This directory contains utility scripts for managing Terraform infrastructure deployments.

## Available Scripts

### 1. init-environment.sh

Initializes a new Terraform environment with proper directory structure and configuration.

**Usage:**
```bash
./init-environment.sh <environment>
```

**Arguments:**
- `environment` - Required: dev, staging, or prod

**What it does:**
- Creates environment directory structure
- Sets up symbolic links to shared configuration files
- Creates main.tf, outputs.tf, and environment-specific tfvars
- Initializes Terraform and validates configuration
- Creates .gitignore to prevent committing sensitive files

**Example:**
```bash
./init-environment.sh dev
```

### 2. deploy.sh

Automated deployment script with credential management, validation, and manual confirmation.

**Usage:**
```bash
./deploy.sh <environment> [aws_access_key_id] [aws_secret_access_key] [aws_session_token]
```

**Arguments:**
- `environment` - Required: dev, staging, or prod
- `aws_access_key_id` - Optional: AWS Access Key ID (can use env var AWS_ACCESS_KEY_ID)
- `aws_secret_access_key` - Optional: AWS Secret Access Key (can use env var AWS_SECRET_ACCESS_KEY)
- `aws_session_token` - Optional: AWS Session Token for temporary credentials (can use env var AWS_SESSION_TOKEN)

**What it does:**
1. Backs up existing Terraform state
2. Checks Terraform formatting
3. Validates Terraform configuration
4. Runs security scan (if tfsec is installed)
5. Creates Terraform plan
6. Requires manual confirmation before applying
7. Applies changes and shows outputs
8. Saves deployment metadata

**Examples:**
```bash
# Using environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
./deploy.sh dev

# Passing credentials as arguments
./deploy.sh dev AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# With temporary credentials (STS)
./deploy.sh prod $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY $AWS_SESSION_TOKEN
```

### 3. backup-state.sh

Automates Terraform state file backups with management features.

**Usage:**
```bash
./backup-state.sh [environment] [options]
```

**Arguments:**
- `environment` - Specific environment to backup (dev, staging, prod)
- `--all` - Backup all environments

**Options:**
- `--list` - List all backups for the environment
- `--clean [N]` - Clean old backups, keeping last N (default: 10)
- `--restore FILE` - Restore state from a specific backup file

**What it does:**
- Creates timestamped backups of Terraform state files
- Lists existing backups with file sizes
- Cleans old backups to save disk space
- Restores state from previous backups (with safety backup)

**Examples:**
```bash
# Backup single environment
./backup-state.sh dev

# Backup all environments
./backup-state.sh --all

# List backups for dev
./backup-state.sh dev --list

# Clean old backups (keep last 5)
./backup-state.sh dev --clean 5

# Restore from backup
./backup-state.sh dev --restore environments/dev/backups/terraform.tfstate.backup.20240126_143000
```

## Prerequisites

### Required Tools
- **Terraform** >= 1.0
- **Bash** shell (Linux/macOS/WSL)
- **AWS CLI** (optional, for additional validation)

### Optional Tools
- **tfsec** - Security scanning for Terraform code
  - Install: https://github.com/aquasecurity/tfsec

## Making Scripts Executable

Before using the scripts, make them executable:

```bash
chmod +x init-environment.sh
chmod +x deploy.sh
chmod +x backup-state.sh
```

## Workflow

### Initial Setup

1. Initialize a new environment:
```bash
./init-environment.sh dev
```

2. Review and update the generated tfvars file:
```bash
cd ../environments/dev
nano dev.tfvars
```

3. Set AWS credentials:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### Regular Deployment

1. Create a backup before deployment:
```bash
./backup-state.sh dev
```

2. Deploy changes:
```bash
./deploy.sh dev
```

3. Verify deployment in AWS Console

### Maintenance

1. List backups periodically:
```bash
./backup-state.sh dev --list
```

2. Clean old backups:
```bash
./backup-state.sh dev --clean 10
```

3. Restore from backup if needed:
```bash
./backup-state.sh dev --restore <backup-file>
```

## Security Best Practices

### Credential Management

1. **Never commit credentials** to version control
2. **Use environment variables** for credentials when possible
3. **Rotate credentials** regularly
4. **Use temporary credentials** (STS) for production deployments
5. **Limit credential scope** to minimum required permissions

### State File Security

1. **Backup state files** before any changes
2. **Store backups securely** with appropriate access controls
3. **Never commit state files** to version control
4. **Clean old backups** to reduce exposure window
5. **Encrypt backups** if storing in shared locations

### Deployment Safety

1. **Always review plan** before applying
2. **Use manual confirmation** for production deployments
3. **Test in dev/staging** before production
4. **Monitor deployments** in CloudWatch
5. **Have rollback plan** ready

## Troubleshooting

### Script Permission Denied

```bash
chmod +x <script-name>.sh
```

### Terraform Not Found

Install Terraform: https://www.terraform.io/downloads

### AWS Credentials Not Working

1. Verify credentials are set:
```bash
echo $AWS_ACCESS_KEY_ID
```

2. Test AWS CLI access:
```bash
aws sts get-caller-identity
```

3. Check credential expiration (for temporary credentials)

### State Lock Errors

With local state, coordinate with team members to avoid concurrent modifications.

### Backup Restore Issues

1. Verify backup file exists and is readable
2. Check backup file integrity
3. Ensure you have write permissions to state file location

## Directory Structure

```
terraform/
├── scripts/
│   ├── init-environment.sh    # Initialize new environment
│   ├── deploy.sh              # Deploy infrastructure
│   ├── backup-state.sh        # Manage state backups
│   └── README.md              # This file
├── environments/
│   ├── dev/
│   │   ├── backups/           # State backups
│   │   ├── terraform.tfstate  # Current state
│   │   └── dev.tfvars         # Environment config
│   ├── staging/
│   └── prod/
├── modules/                   # Reusable modules
└── shared/                    # Shared configuration
```

## Support

For issues or questions:
1. Check this README
2. Review Terraform documentation
3. Check AWS documentation
4. Contact the infrastructure team

## Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
