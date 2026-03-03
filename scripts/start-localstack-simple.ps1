# ============================================================================
# Script: Simple LocalStack Initialization
# Purpose: Simplified version without complex error handling
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LocalStack Simple Initialization" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker
Write-Host "Step 1: Checking Docker..." -ForegroundColor Yellow
docker info | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Docker is not running" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK: Docker is running" -ForegroundColor Green
Write-Host ""

# Step 2: Start LocalStack
Write-Host "Step 2: Starting LocalStack..." -ForegroundColor Yellow
docker-compose -f docker-compose.localstack.yml up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to start LocalStack" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: LocalStack started" -ForegroundColor Green
Write-Host ""

# Step 3: Wait for LocalStack
Write-Host "Step 3: Waiting for LocalStack (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
Write-Host "  OK: Wait complete" -ForegroundColor Green
Write-Host ""

# Step 4: Initialize Terraform
Write-Host "Step 4: Initializing Terraform..." -ForegroundColor Yellow
Set-Location terraform
terraform init
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Terraform init failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Write-Host "  OK: Terraform initialized" -ForegroundColor Green
Write-Host ""

# Step 5: Validate
Write-Host "Step 5: Validating configuration..." -ForegroundColor Yellow
terraform validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Terraform validation failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Write-Host "  OK: Configuration valid" -ForegroundColor Green
Write-Host ""

# Step 6: Plan
Write-Host "Step 6: Planning deployment..." -ForegroundColor Yellow
terraform plan -var-file="terraform.tfvars" -out="localstack.tfplan"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Terraform plan failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Write-Host "  OK: Plan created" -ForegroundColor Green
Write-Host ""

# Step 7: Apply
Write-Host "Step 7: Applying configuration..." -ForegroundColor Yellow
Write-Host "  This may take 2-5 minutes..." -ForegroundColor Gray
terraform apply "localstack.tfplan"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Terraform apply failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Remove-Item "localstack.tfplan" -ErrorAction SilentlyContinue
Write-Host "  OK: Infrastructure deployed" -ForegroundColor Green
Write-Host ""

# Step 8: Show results
Write-Host "Step 8: Deployment summary..." -ForegroundColor Yellow
$resourceCount = (terraform state list | Measure-Object -Line).Lines
Write-Host "  Resources created: $resourceCount" -ForegroundColor Cyan
Write-Host ""

Set-Location ..

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUCCESS!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "LocalStack is running on http://localhost:4566" -ForegroundColor Green
Write-Host "Infrastructure deployed: $resourceCount resources" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  View outputs:   cd terraform; terraform output" -ForegroundColor White
Write-Host "  List resources: cd terraform; terraform state list" -ForegroundColor White
Write-Host "  View VPC:       aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs" -ForegroundColor White
Write-Host ""
Write-Host "To destroy:" -ForegroundColor Yellow
Write-Host "  cd terraform" -ForegroundColor White
Write-Host "  terraform destroy -var-file=`"terraform.tfvars`" -auto-approve" -ForegroundColor White
Write-Host "  cd .." -ForegroundColor White
Write-Host "  docker-compose -f docker-compose.localstack.yml down" -ForegroundColor White
Write-Host ""
