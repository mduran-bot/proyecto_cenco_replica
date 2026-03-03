#!/bin/bash
# init-environment.sh
# Script to initialize Terraform for a specific environment
# Usage: ./init-environment.sh <environment>

set -e

ENVIRONMENT=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="$TERRAFORM_ROOT/environments/$ENVIRONMENT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate input
if [ -z "$ENVIRONMENT" ]; then
    print_error "Usage: ./init-environment.sh <environment>"
    echo "Available environments: dev, staging, prod"
    exit 1
fi

# Validate environment name
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    echo "Valid environments are: dev, staging, prod"
    exit 1
fi

print_info "Initializing Terraform for environment: $ENVIRONMENT"

# Create environment directory if it doesn't exist
if [ ! -d "$ENV_DIR" ]; then
    print_info "Creating environment directory: $ENV_DIR"
    mkdir -p "$ENV_DIR"
else
    print_warning "Environment directory already exists: $ENV_DIR"
fi

# Create symbolic links to shared configuration
print_info "Setting up shared configuration links..."

cd "$ENV_DIR"

# Create symlinks to shared files if they don't exist
if [ ! -L "backend.tf" ] && [ ! -f "backend.tf" ]; then
    ln -s ../../shared/backend.tf backend.tf
    print_info "Created symlink: backend.tf -> ../../shared/backend.tf"
fi

if [ ! -L "providers.tf" ] && [ ! -f "providers.tf" ]; then
    ln -s ../../shared/providers.tf providers.tf
    print_info "Created symlink: providers.tf -> ../../shared/providers.tf"
fi

if [ ! -L "variables.tf" ] && [ ! -f "variables.tf" ]; then
    ln -s ../../shared/variables.tf variables.tf
    print_info "Created symlink: variables.tf -> ../../shared/variables.tf"
fi

# Create main.tf if it doesn't exist
if [ ! -f "main.tf" ]; then
    print_info "Creating main.tf..."
    cat > main.tf << 'EOF'
# Main Terraform configuration for environment
# This file imports and configures all infrastructure modules

# VPC Module
module "vpc" {
  source = "../../modules/vpc"
  
  environment   = var.environment
  project_name  = var.project_name
  vpc_cidr      = var.vpc_cidr
  
  common_tags = local.common_tags
}

# Security Groups Module
module "security_groups" {
  source = "../../modules/security-groups"
  
  environment  = var.environment
  project_name = var.project_name
  vpc_id       = module.vpc.vpc_id
  
  common_tags = local.common_tags
}

# VPC Endpoints Module
module "vpc_endpoints" {
  source = "../../modules/vpc-endpoints"
  
  environment         = var.environment
  project_name        = var.project_name
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  route_table_ids     = module.vpc.route_table_ids
  security_group_ids  = [module.security_groups.vpc_endpoint_sg_id]
  
  common_tags = local.common_tags
}

# NACLs Module
module "nacls" {
  source = "../../modules/nacls"
  
  environment        = var.environment
  project_name       = var.project_name
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  
  common_tags = local.common_tags
}

# EventBridge Module
module "eventbridge" {
  source = "../../modules/eventbridge"
  
  environment  = var.environment
  project_name = var.project_name
  
  common_tags = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"
  
  environment  = var.environment
  project_name = var.project_name
  vpc_id       = module.vpc.vpc_id
  
  common_tags = local.common_tags
}

# Local variables
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "infrastructure"
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "terraform"
    CreatedDate = formatdate("YYYY-MM-DD", timestamp())
  }
}
EOF
    print_info "Created main.tf"
fi

# Create outputs.tf if it doesn't exist
if [ ! -f "outputs.tf" ]; then
    print_info "Creating outputs.tf..."
    cat > outputs.tf << 'EOF'
# Output values for the infrastructure

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway"
  value       = module.vpc.nat_gateway_id
}

output "security_group_ids" {
  description = "Map of security group IDs"
  value       = module.security_groups.security_group_ids
}

output "eventbridge_bus_arn" {
  description = "ARN of the EventBridge custom event bus"
  value       = module.eventbridge.event_bus_arn
}
EOF
    print_info "Created outputs.tf"
fi

# Create environment-specific tfvars file if it doesn't exist
if [ ! -f "$ENVIRONMENT.tfvars" ]; then
    print_info "Creating $ENVIRONMENT.tfvars..."
    cat > "$ENVIRONMENT.tfvars" << EOF
# Terraform variables for $ENVIRONMENT environment
# DO NOT commit credentials to version control

environment  = "$ENVIRONMENT"
aws_region   = "us-east-1"
project_name = "janis-cencosud"
owner        = "cencosud-data-team"
cost_center  = "data-engineering"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"

# AWS Credentials (pass via environment variables or command line)
# aws_access_key_id     = ""  # Set via -var or environment variable
# aws_secret_access_key = ""  # Set via -var or environment variable
# aws_session_token     = ""  # Optional, for STS temporary credentials
EOF
    print_info "Created $ENVIRONMENT.tfvars"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    print_info "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Terraform
*.tfstate
*.tfstate.*
*.tfplan
*.tfplan.*
.terraform/
.terraform.lock.hcl

# Credentials (NEVER commit)
credentials.tfvars
**/credentials.tfvars
*.pem
*.key

# Logs
terraform.log
*.log

# Backups
backups/
*.backup
EOF
    print_info "Created .gitignore"
fi

# Initialize Terraform
print_info "Running terraform init..."
terraform init

# Validate configuration
print_info "Running terraform validate..."
terraform validate

print_info "Environment $ENVIRONMENT initialized successfully!"
echo ""
print_info "Next steps:"
echo "  1. Review and update $ENVIRONMENT.tfvars with your configuration"
echo "  2. Set AWS credentials via environment variables:"
echo "     export AWS_ACCESS_KEY_ID=\"your-access-key\""
echo "     export AWS_SECRET_ACCESS_KEY=\"your-secret-key\""
echo "  3. Run terraform plan:"
echo "     terraform plan -var-file=\"$ENVIRONMENT.tfvars\""
echo "  4. Apply changes:"
echo "     terraform apply -var-file=\"$ENVIRONMENT.tfvars\""
echo ""
print_warning "Remember: Never commit credentials to version control!"
