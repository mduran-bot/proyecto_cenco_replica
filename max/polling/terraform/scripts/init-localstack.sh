#!/bin/bash
# ============================================================================
# Initialize LocalStack Infrastructure
# ============================================================================
# This script initializes the API polling infrastructure in LocalStack
# ============================================================================

set -e

echo "🚀 Initializing API Polling Infrastructure in LocalStack..."

# Check if LocalStack is running
if ! curl -s http://localhost:4566/_localstack/health > /dev/null; then
    echo "❌ LocalStack is not running. Please start it first:"
    echo "   cd .. && docker-compose up -d"
    exit 1
fi

echo "✅ LocalStack is running"

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

# Validate configuration
echo "🔍 Validating Terraform configuration..."
terraform validate

# Plan infrastructure
echo "📋 Planning infrastructure..."
terraform plan -var-file="localstack.tfvars" -out=localstack.tfplan

# Apply infrastructure
echo "🏗️  Applying infrastructure..."
terraform apply localstack.tfplan

# Clean up plan file
rm localstack.tfplan

# Display outputs
echo ""
echo "✅ Infrastructure created successfully!"
echo ""
echo "📊 Outputs:"
terraform output

echo ""
echo "🔍 Verify resources:"
echo "   DynamoDB: aws --endpoint-url=http://localhost:4566 dynamodb list-tables"
echo "   S3:       aws --endpoint-url=http://localhost:4566 s3 ls"
echo "   SNS:      aws --endpoint-url=http://localhost:4566 sns list-topics"
echo "   IAM:      aws --endpoint-url=http://localhost:4566 iam list-roles"
