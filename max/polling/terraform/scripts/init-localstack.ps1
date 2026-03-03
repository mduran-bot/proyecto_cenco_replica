# ============================================================================
# Initialize LocalStack Infrastructure (PowerShell)
# ============================================================================
# This script initializes the API polling infrastructure in LocalStack
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "🚀 Initializing API Polling Infrastructure in LocalStack..." -ForegroundColor Cyan

# Check if LocalStack is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:4566/_localstack/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ LocalStack is running" -ForegroundColor Green
} catch {
    Write-Host "❌ LocalStack is not running. Please start it first:" -ForegroundColor Red
    Write-Host "   cd .. && docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# Initialize Terraform
Write-Host "📦 Initializing Terraform..." -ForegroundColor Cyan
terraform init

# Validate configuration
Write-Host "🔍 Validating Terraform configuration..." -ForegroundColor Cyan
terraform validate

# Plan infrastructure
Write-Host "📋 Planning infrastructure..." -ForegroundColor Cyan
terraform plan -var-file="localstack.tfvars" -out="localstack.tfplan"

# Apply infrastructure
Write-Host "🏗️  Applying infrastructure..." -ForegroundColor Cyan
terraform apply "localstack.tfplan"

# Clean up plan file
Remove-Item "localstack.tfplan" -ErrorAction SilentlyContinue

# Display outputs
Write-Host ""
Write-Host "✅ Infrastructure created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Outputs:" -ForegroundColor Cyan
terraform output

Write-Host ""
Write-Host "🔍 Verify resources:" -ForegroundColor Cyan
Write-Host "   DynamoDB: aws --endpoint-url=http://localhost:4566 dynamodb list-tables" -ForegroundColor Yellow
Write-Host "   S3:       aws --endpoint-url=http://localhost:4566 s3 ls" -ForegroundColor Yellow
Write-Host "   SNS:      aws --endpoint-url=http://localhost:4566 sns list-topics" -ForegroundColor Yellow
Write-Host "   IAM:      aws --endpoint-url=http://localhost:4566 iam list-roles" -ForegroundColor Yellow
