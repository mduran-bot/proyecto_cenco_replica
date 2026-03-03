#!/bin/bash

###############################################################################
# Deploy DAGs and Dependencies to MWAA
#
# This script uploads DAGs, source code, and requirements to the MWAA S3 bucket
# for the Janis-Cencosud API Polling System.
#
# Usage:
#   ./deploy-dags.sh <environment> <mwaa-bucket-name>
#
# Example:
#   ./deploy-dags.sh prod cencosud-mwaa-prod
#
# Requirements:
#   - AWS CLI configured with appropriate credentials
#   - Access to MWAA S3 bucket
#   - Terraform outputs available (optional, for auto-detection)
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

###############################################################################
# Functions
###############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    log_info "AWS CLI found: $(aws --version)"
}

check_bucket_access() {
    local bucket=$1
    log_info "Checking access to S3 bucket: $bucket"
    
    if aws s3 ls "s3://$bucket" &> /dev/null; then
        log_info "✓ Access to bucket confirmed"
        return 0
    else
        log_error "✗ Cannot access bucket: $bucket"
        log_error "Please check your AWS credentials and bucket permissions"
        exit 1
    fi
}

create_deployment_package() {
    local temp_dir=$1
    
    log_info "Creating deployment package..."
    
    # Create directory structure
    mkdir -p "$temp_dir/dags"
    mkdir -p "$temp_dir/plugins"
    
    # Copy DAGs
    log_info "Copying DAG files..."
    cp -r "$PROJECT_ROOT/dags/"*.py "$temp_dir/dags/"
    
    # Copy source code as a plugin
    log_info "Copying source code..."
    cp -r "$PROJECT_ROOT/src" "$temp_dir/plugins/"
    
    # Copy requirements.txt
    log_info "Copying requirements.txt..."
    cp "$PROJECT_ROOT/requirements.txt" "$temp_dir/"
    
    log_info "✓ Deployment package created"
}

upload_to_s3() {
    local bucket=$1
    local temp_dir=$2
    
    log_info "Uploading files to S3..."
    
    # Upload DAGs
    log_info "Uploading DAGs..."
    aws s3 sync "$temp_dir/dags/" "s3://$bucket/dags/" \
        --delete \
        --exclude "*.pyc" \
        --exclude "__pycache__/*"
    
    # Upload plugins (source code)
    log_info "Uploading plugins..."
    aws s3 sync "$temp_dir/plugins/" "s3://$bucket/plugins/" \
        --delete \
        --exclude "*.pyc" \
        --exclude "__pycache__/*" \
        --exclude "*.pytest_cache/*"
    
    # Upload requirements.txt
    log_info "Uploading requirements.txt..."
    aws s3 cp "$temp_dir/requirements.txt" "s3://$bucket/requirements.txt"
    
    log_info "✓ Files uploaded successfully"
}

verify_deployment() {
    local bucket=$1
    
    log_info "Verifying deployment..."
    
    # Check DAGs
    local dag_count=$(aws s3 ls "s3://$bucket/dags/" | grep ".py$" | wc -l)
    log_info "DAGs uploaded: $dag_count"
    
    # Check requirements.txt
    if aws s3 ls "s3://$bucket/requirements.txt" &> /dev/null; then
        log_info "✓ requirements.txt uploaded"
    else
        log_warn "✗ requirements.txt not found"
    fi
    
    # List uploaded DAGs
    log_info "Uploaded DAGs:"
    aws s3 ls "s3://$bucket/dags/" | grep ".py$" | awk '{print "  - " $4}'
}

trigger_mwaa_update() {
    local environment_name=$1
    
    log_info "Triggering MWAA environment update..."
    log_warn "Note: MWAA will automatically detect changes in the S3 bucket"
    log_warn "It may take 5-10 minutes for DAGs to appear in the Airflow UI"
    
    # Optional: You can use AWS CLI to check MWAA environment status
    log_info "Checking MWAA environment status..."
    aws mwaa get-environment --name "$environment_name" \
        --query 'Environment.Status' \
        --output text || log_warn "Could not check MWAA status"
}

###############################################################################
# Main Script
###############################################################################

main() {
    # Parse arguments
    if [ $# -lt 2 ]; then
        log_error "Usage: $0 <environment> <mwaa-bucket-name> [mwaa-environment-name]"
        log_error "Example: $0 prod cencosud-mwaa-prod cencosud-mwaa-environment-prod"
        exit 1
    fi
    
    local environment=$1
    local mwaa_bucket=$2
    local mwaa_env_name=${3:-""}
    
    log_info "=========================================="
    log_info "MWAA Deployment Script"
    log_info "=========================================="
    log_info "Environment: $environment"
    log_info "MWAA Bucket: $mwaa_bucket"
    if [ -n "$mwaa_env_name" ]; then
        log_info "MWAA Environment: $mwaa_env_name"
    fi
    log_info "=========================================="
    echo
    
    # Pre-flight checks
    check_aws_cli
    check_bucket_access "$mwaa_bucket"
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT
    
    log_info "Using temporary directory: $temp_dir"
    echo
    
    # Create deployment package
    create_deployment_package "$temp_dir"
    echo
    
    # Upload to S3
    upload_to_s3 "$mwaa_bucket" "$temp_dir"
    echo
    
    # Verify deployment
    verify_deployment "$mwaa_bucket"
    echo
    
    # Trigger MWAA update (if environment name provided)
    if [ -n "$mwaa_env_name" ]; then
        trigger_mwaa_update "$mwaa_env_name"
        echo
    fi
    
    # Success message
    log_info "=========================================="
    log_info "✓ Deployment completed successfully!"
    log_info "=========================================="
    log_info "Next steps:"
    log_info "1. Wait 5-10 minutes for MWAA to detect changes"
    log_info "2. Check Airflow UI for new/updated DAGs"
    log_info "3. Verify DAGs are not paused"
    log_info "4. Test DAG execution manually if needed"
    log_info "5. Monitor CloudWatch logs for any errors"
    echo
    log_info "MWAA Airflow UI: https://console.aws.amazon.com/mwaa/home"
    log_info "CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home"
}

# Run main function
main "$@"
