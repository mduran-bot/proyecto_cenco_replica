#!/bin/bash
# ============================================================================
# Destroy Script for Janis-Cencosud AWS Infrastructure
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

# Warning
print_error "⚠️  WARNING: This will DESTROY all infrastructure resources! ⚠️"
print_warning "This action cannot be undone!"
echo ""

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_error "terraform.tfvars not found!"
    exit 1
fi

# Backup state
if [ -f "terraform.tfstate" ]; then
    BACKUP_FILE="terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)"
    print_info "Backing up state to $BACKUP_FILE"
    cp terraform.tfstate "$BACKUP_FILE"
fi

# Show what will be destroyed
print_info "Showing resources that will be destroyed..."
terraform plan -destroy -var-file="terraform.tfvars"

echo ""
print_warning "Are you absolutely sure you want to destroy all resources?"
read -p "Type 'destroy' to confirm: " confirm

if [ "$confirm" != "destroy" ]; then
    print_info "Destruction cancelled."
    exit 0
fi

# Final confirmation
print_error "FINAL WARNING: All resources will be permanently deleted!"
read -p "Type 'yes' to proceed: " final_confirm

if [ "$final_confirm" != "yes" ]; then
    print_info "Destruction cancelled."
    exit 0
fi

# Destroy
print_info "Destroying infrastructure..."
terraform destroy -var-file="terraform.tfvars"

print_info "Infrastructure destroyed."
