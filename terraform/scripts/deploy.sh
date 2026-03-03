#!/bin/bash
# deploy.sh
# Automated deployment script with credential management
# Usage: ./deploy.sh <environment> [aws_access_key_id] [aws_secret_access_key] [aws_session_token]

set -e

ENVIRONMENT=$1
AWS_ACCESS_KEY_ID=$2
AWS_SECRET_ACCESS_KEY=$3
AWS_SESSION_TOKEN=$4

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="$TERRAFORM_ROOT/environments/$ENVIRONMENT"
BACKUP_DIR="$ENV_DIR/backups"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validate prerequisites
if ! command_exists terraform; then
    print_error "Terraform is not installed. Please install Terraform first."
    exit 1
fi

if ! command_exists aws; then
    print_warning "AWS CLI is not installed. Some validation steps may be skipped."
fi

# Validate input
if [ -z "$ENVIRONMENT" ]; then
    print_error "Usage: ./deploy.sh <environment> [aws_access_key_id] [aws_secret_access_key] [aws_session_token]"
    echo ""
    echo "Arguments:"
    echo "  environment           - Required: dev, staging, or prod"
    echo "  aws_access_key_id     - Optional: AWS Access Key ID (can use env var AWS_ACCESS_KEY_ID)"
    echo "  aws_secret_access_key - Optional: AWS Secret Access Key (can use env var AWS_SECRET_ACCESS_KEY)"
    echo "  aws_session_token     - Optional: AWS Session Token (can use env var AWS_SESSION_TOKEN)"
    echo ""
    echo "Examples:"
    echo "  # Using environment variables"
    echo "  export AWS_ACCESS_KEY_ID=\"your-key\""
    echo "  export AWS_SECRET_ACCESS_KEY=\"your-secret\""
    echo "  ./deploy.sh dev"
    echo ""
    echo "  # Passing credentials as arguments"
    echo "  ./deploy.sh dev AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    exit 1
fi

# Validate environment name
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    echo "Valid environments are: dev, staging, prod"
    exit 1
fi

# Check if environment directory exists
if [ ! -d "$ENV_DIR" ]; then
    print_error "Environment directory does not exist: $ENV_DIR"
    echo "Run ./init-environment.sh $ENVIRONMENT first"
    exit 1
fi

# Set AWS credentials from arguments or environment variables
if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    export AWS_ACCESS_KEY_ID
fi

if [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    export AWS_SECRET_ACCESS_KEY
fi

if [ -n "$AWS_SESSION_TOKEN" ]; then
    export AWS_SESSION_TOKEN
fi

# Verify AWS credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    print_error "AWS credentials not provided"
    echo "Set credentials via environment variables or pass as arguments"
    exit 1
fi

print_info "Starting deployment for environment: $ENVIRONMENT"
echo ""

# Change to environment directory
cd "$ENV_DIR"

# Step 1: Backup existing state
print_step "Step 1/6: Backing up Terraform state"
if [ -f "terraform.tfstate" ]; then
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)"
    cp terraform.tfstate "$BACKUP_FILE"
    print_info "State backed up to: $BACKUP_FILE"
else
    print_warning "No existing state file found (this may be the first deployment)"
fi
echo ""

# Step 2: Format check
print_step "Step 2/6: Checking Terraform formatting"
if terraform fmt -check -recursive; then
    print_info "Terraform files are properly formatted"
else
    print_warning "Some files need formatting. Running terraform fmt..."
    terraform fmt -recursive
    print_info "Files formatted successfully"
fi
echo ""

# Step 3: Validate configuration
print_step "Step 3/6: Validating Terraform configuration"
if terraform validate; then
    print_info "Configuration is valid"
else
    print_error "Configuration validation failed"
    exit 1
fi
echo ""

# Step 4: Security scan (if tfsec is available)
print_step "Step 4/6: Running security scan"
if command_exists tfsec; then
    if tfsec "$TERRAFORM_ROOT" --minimum-severity MEDIUM; then
        print_info "Security scan passed"
    else
        print_warning "Security issues detected. Review the output above."
        read -p "Continue with deployment? (y/N): " continue_deploy
        if [[ ! "$continue_deploy" =~ ^[Yy]$ ]]; then
            print_error "Deployment cancelled by user"
            exit 1
        fi
    fi
else
    print_warning "tfsec not installed. Skipping security scan."
    print_info "Install tfsec for security scanning: https://github.com/aquasecurity/tfsec"
fi
echo ""

# Step 5: Plan
print_step "Step 5/6: Creating Terraform plan"
PLAN_FILE="$ENVIRONMENT.tfplan"

# Build terraform plan command
PLAN_CMD="terraform plan -var-file=\"$ENVIRONMENT.tfvars\""

if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    PLAN_CMD="$PLAN_CMD -var=\"aws_access_key_id=$AWS_ACCESS_KEY_ID\""
fi

if [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    PLAN_CMD="$PLAN_CMD -var=\"aws_secret_access_key=$AWS_SECRET_ACCESS_KEY\""
fi

if [ -n "$AWS_SESSION_TOKEN" ]; then
    PLAN_CMD="$PLAN_CMD -var=\"aws_session_token=$AWS_SESSION_TOKEN\""
fi

PLAN_CMD="$PLAN_CMD -out=\"$PLAN_FILE\""

# Execute plan
eval "$PLAN_CMD"

if [ $? -eq 0 ]; then
    print_info "Plan created successfully: $PLAN_FILE"
else
    print_error "Plan creation failed"
    exit 1
fi
echo ""

# Step 6: Apply (with manual confirmation)
print_step "Step 6/6: Applying Terraform changes"
echo ""
print_warning "=== DEPLOYMENT CONFIRMATION ==="
echo "Environment: $ENVIRONMENT"
echo "Plan file: $PLAN_FILE"
echo "Backup location: $BACKUP_DIR"
echo ""
print_warning "This will make changes to your AWS infrastructure!"
echo ""

# Show plan summary
terraform show -no-color "$PLAN_FILE" | grep -E "Plan:|No changes"

echo ""
read -p "Do you want to apply these changes? (yes/NO): " confirm

if [ "$confirm" != "yes" ]; then
    print_warning "Deployment cancelled by user"
    rm -f "$PLAN_FILE"
    exit 0
fi

print_info "Applying changes..."
if terraform apply "$PLAN_FILE"; then
    print_info "Deployment completed successfully!"
    rm -f "$PLAN_FILE"
    
    # Show outputs
    echo ""
    print_info "Infrastructure outputs:"
    terraform output
    
    # Save deployment metadata
    cat > "$BACKUP_DIR/deployment.$(date +%Y%m%d_%H%M%S).log" << EOF
Deployment Information
======================
Environment: $ENVIRONMENT
Date: $(date)
User: $(whoami)
Terraform Version: $(terraform version -json | grep -o '"terraform_version":"[^"]*"' | cut -d'"' -f4)
Status: SUCCESS
EOF
    
else
    print_error "Deployment failed!"
    rm -f "$PLAN_FILE"
    
    # Save failure metadata
    cat > "$BACKUP_DIR/deployment.$(date +%Y%m%d_%H%M%S).log" << EOF
Deployment Information
======================
Environment: $ENVIRONMENT
Date: $(date)
User: $(whoami)
Terraform Version: $(terraform version -json | grep -o '"terraform_version":"[^"]*"' | cut -d'"' -f4)
Status: FAILED
EOF
    
    print_error "Check the error messages above for details"
    print_info "State backup available at: $BACKUP_DIR"
    exit 1
fi

echo ""
print_info "=== Deployment Summary ==="
echo "Environment: $ENVIRONMENT"
echo "Status: SUCCESS"
echo "Backup location: $BACKUP_DIR"
echo ""
print_info "Next steps:"
echo "  - Verify resources in AWS Console"
echo "  - Run smoke tests to validate deployment"
echo "  - Monitor CloudWatch for any issues"
echo ""
print_warning "Remember to clean up old backups periodically!"
