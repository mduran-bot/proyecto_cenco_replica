# ============================================================================
# Script: Initialize LocalStack and Deploy Infrastructure
# Purpose: Complete setup from zero to deployed infrastructure
# ============================================================================

param(
    [switch]$SkipDockerCheck,
    [switch]$DestroyFirst,
    [switch]$SkipWait
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LocalStack Initialization Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Step 1: Verify Prerequisites
# ============================================================================

Write-Host "Step 1: Verifying prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check Docker
if (-not $SkipDockerCheck) {
    Write-Host "  Checking Docker..." -ForegroundColor Gray
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Docker not found" -ForegroundColor Red
        Write-Host "  Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  OK: Docker installed: $dockerVersion" -ForegroundColor Green
    
    # Check if Docker is running
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Docker is not running" -ForegroundColor Red
        Write-Host "  Please start Docker Desktop and try again" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  OK: Docker is running" -ForegroundColor Green
}

# Check Terraform
Write-Host "  Checking Terraform..." -ForegroundColor Gray
$tfVersion = terraform --version 2>&1 | Select-Object -First 1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Terraform not found" -ForegroundColor Red
    Write-Host "  Install Terraform: https://www.terraform.io/downloads" -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK: Terraform installed: $tfVersion" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 2: Clean Up Previous Deployment (if requested)
# ============================================================================

if ($DestroyFirst) {
    Write-Host "Step 2: Cleaning up previous deployment..." -ForegroundColor Yellow
    Write-Host ""
    
    # Destroy Terraform resources
    if (Test-Path "terraform/terraform.tfstate") {
        Write-Host "  Destroying Terraform resources..." -ForegroundColor Gray
        Set-Location terraform
        terraform destroy -var-file="terraform.tfvars" -auto-approve 2>&1 | Out-Null
        Set-Location ..
        Write-Host "  OK: Terraform resources destroyed" -ForegroundColor Green
    }
    
    # Stop LocalStack
    Write-Host "  Stopping LocalStack..." -ForegroundColor Gray
    docker-compose -f docker-compose.localstack.yml down 2>&1 | Out-Null
    Write-Host "  OK: LocalStack stopped" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
# Step 3: Start LocalStack
# ============================================================================

Write-Host "Step 3: Starting LocalStack..." -ForegroundColor Yellow
Write-Host ""

# Check if LocalStack is already running
$existingContainer = docker ps --filter "name=localstack-janis-cencosud" --format "{{.Names}}" 2>$null
if ($existingContainer -eq "localstack-janis-cencosud") {
    Write-Host "  INFO: LocalStack is already running" -ForegroundColor Cyan
    Write-Host "  Restarting to ensure clean state..." -ForegroundColor Gray
    docker-compose -f docker-compose.localstack.yml restart 2>&1 | Out-Null
}
else {
    Write-Host "  Starting LocalStack container..." -ForegroundColor Gray
    docker-compose -f docker-compose.localstack.yml up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to start LocalStack" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  OK: LocalStack container started" -ForegroundColor Green
Write-Host ""

# Wait for LocalStack to be ready
if (-not $SkipWait) {
    Write-Host "  Waiting for LocalStack to initialize..." -ForegroundColor Gray
    Write-Host "  (This usually takes 30-60 seconds)" -ForegroundColor Gray
    
    $maxAttempts = 30
    $attempt = 0
    $ready = $false
    
    while (($attempt -lt $maxAttempts) -and (-not $ready)) {
        $attempt++
        Start-Sleep -Seconds 2
        
        $response = Invoke-WebRequest -Uri "http://localhost:4566/_localstack/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($null -ne $response -and $response.StatusCode -eq 200) {
            $ready = $true
            Write-Host "  OK: LocalStack is ready!" -ForegroundColor Green
        }
        else {
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    }
    
    if (-not $ready) {
        Write-Host ""
        Write-Host "  WARNING: LocalStack health check timeout" -ForegroundColor Yellow
        Write-Host "  Continuing anyway... (LocalStack might still be initializing)" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Show LocalStack status
Write-Host "  LocalStack Status:" -ForegroundColor Gray
$health = Invoke-RestMethod -Uri "http://localhost:4566/_localstack/health" -ErrorAction SilentlyContinue
if ($null -ne $health) {
    $runningServices = ($health.services.PSObject.Properties | Where-Object { $_.Value -eq "running" }).Count
    Write-Host "  OK: $runningServices services running" -ForegroundColor Green
}
else {
    Write-Host "  WARNING: Could not fetch health status" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Step 4: Initialize Terraform
# ============================================================================

Write-Host "Step 4: Initializing Terraform..." -ForegroundColor Yellow
Write-Host ""

Set-Location terraform

# Check if already initialized
if (Test-Path ".terraform") {
    Write-Host "  INFO: Terraform already initialized" -ForegroundColor Cyan
    Write-Host "  Re-initializing to ensure clean state..." -ForegroundColor Gray
}

terraform init -upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Terraform initialization failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "  OK: Terraform initialized successfully" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 5: Validate Configuration
# ============================================================================

Write-Host "Step 5: Validating Terraform configuration..." -ForegroundColor Yellow
Write-Host ""

terraform fmt -recursive | Out-Null
Write-Host "  OK: Code formatted" -ForegroundColor Green

terraform validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Terraform validation failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "  OK: Configuration is valid" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 6: Plan Deployment
# ============================================================================

Write-Host "Step 6: Planning deployment..." -ForegroundColor Yellow
Write-Host ""

Write-Host "  Running terraform plan..." -ForegroundColor Gray
terraform plan -var-file="terraform.tfvars" -out="localstack.tfplan"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Terraform plan failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host ""
Write-Host "  OK: Plan created successfully" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 7: Apply Configuration
# ============================================================================

Write-Host "Step 7: Deploying infrastructure to LocalStack..." -ForegroundColor Yellow
Write-Host ""

Write-Host "  Applying Terraform configuration..." -ForegroundColor Gray
Write-Host "  (This may take 2-5 minutes)" -ForegroundColor Gray
Write-Host ""

terraform apply "localstack.tfplan"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: Terraform apply failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Clean up plan file
Remove-Item "localstack.tfplan" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  OK: Infrastructure deployed successfully!" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 8: Verify Deployment
# ============================================================================

Write-Host "Step 8: Verifying deployment..." -ForegroundColor Yellow
Write-Host ""

# Count resources
$resourceCount = (terraform state list | Measure-Object -Line).Lines
Write-Host "  OK: $resourceCount resources created" -ForegroundColor Green

# Show key outputs
Write-Host ""
Write-Host "  Key Outputs:" -ForegroundColor Gray
$outputs = terraform output -json | ConvertFrom-Json
foreach ($prop in $outputs.PSObject.Properties) {
    if ($prop.Name -match "vpc_id|subnet|nat_gateway") {
        Write-Host "    $($prop.Name): $($prop.Value.value)" -ForegroundColor Cyan
    }
}

Write-Host ""

# Verify with AWS CLI (if available)
$awsVersion = aws --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Verifying with AWS CLI..." -ForegroundColor Gray
    
    $vpcs = aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs --query 'Vpcs[*].VpcId' --output text 2>$null
    if ($null -ne $vpcs -and $vpcs -ne "") {
        Write-Host "  OK: VPC verified in LocalStack: $vpcs" -ForegroundColor Green
    }
    
    $subnets = aws --endpoint-url=http://localhost:4566 ec2 describe-subnets --query 'Subnets[*].SubnetId' --output text 2>$null
    if ($null -ne $subnets -and $subnets -ne "") {
        $subnetArray = $subnets.Split()
        Write-Host "  OK: $($subnetArray.Count) subnets verified in LocalStack" -ForegroundColor Green
    }
}

Set-Location ..

Write-Host ""

# ============================================================================
# Summary
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "OK: LocalStack is running on http://localhost:4566" -ForegroundColor Green
Write-Host "OK: Infrastructure deployed successfully" -ForegroundColor Green
Write-Host "OK: $resourceCount Terraform resources created" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. View outputs:      cd terraform; terraform output" -ForegroundColor White
Write-Host "  2. List resources:    cd terraform; terraform state list" -ForegroundColor White
Write-Host "  3. View VPC:          aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs" -ForegroundColor White
Write-Host "  4. View logs:         docker logs localstack-janis-cencosud" -ForegroundColor White
Write-Host ""

Write-Host "To destroy everything:" -ForegroundColor Yellow
Write-Host "  cd terraform; terraform destroy -var-file=`"terraform.tfvars`" -auto-approve" -ForegroundColor White
Write-Host "  docker-compose -f docker-compose.localstack.yml down" -ForegroundColor White
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - GUIA_INICIO_LOCALSTACK.md" -ForegroundColor White
Write-Host "  - terraform/LOCALSTACK_CONFIG.md" -ForegroundColor White
Write-Host "  - README-LOCALSTACK.md" -ForegroundColor White
Write-Host ""

Write-Host "Happy testing! 🚀" -ForegroundColor Cyan
Write-Host ""
