#!/bin/bash
# ============================================================================
# Deployment Script for Janis-Cencosud AWS Infrastructure
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_error "terraform.tfvars not found!"
    print_info "Please copy terraform.tfvars.example to terraform.tfvars and configure it."
    print_info "  cp terraform.tfvars.example terraform.tfvars"
    exit 1
fi

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_PROFILE" ]; then
    print_warning "No AWS credentials found in environment variables."
    print_info "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, or AWS_PROFILE."
    read -p "Continue anyway? (y/N): " continue
    if [ "$continue" != "y" ] && [ "$continue" != "Y" ]; then
        exit 1
    fi
fi

# Backup existing state if it exists
if [ -f "terraform.tfstate" ]; then
    BACKUP_FILE="terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)"
    print_info "Backing up existing state to $BACKUP_FILE"
    cp terraform.tfstate "$BACKUP_FILE"
fi

# Initialize Terraform
print_info "Initializing Terraform..."
terraform init

# Format check
print_info "Checking Terraform formatting..."
terraform fmt -check -recursive || {
    print_warning "Terraform files are not properly formatted."
    print_info "Running terraform fmt to fix formatting..."
    terraform fmt -recursive
}

# Validate
print_info "Validating Terraform configuration..."
terraform validate

# Plan
print_info "Creating Terraform plan..."
terraform plan -var-file="terraform.tfvars" -out="deployment.tfplan"

# Review plan
print_warning "Please review the plan above carefully."
read -p "Do you want to apply this plan? (yes/no): " apply_confirm

if [ "$apply_confirm" != "yes" ]; then
    print_info "Deployment cancelled."
    rm -f deployment.tfplan
    exit 0
fi

# Apply
print_info "Applying Terraform plan..."
terraform apply "deployment.tfplan"

# Cleanup
rm -f deployment.tfplan

print_info "Deployment completed successfully!"
print_info "Run 'terraform output' to see the created resources."
