# ============================================================================
# Script: Verify LocalStack Deployment
# Purpose: Check that LocalStack and infrastructure are working correctly
# ============================================================================

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LocalStack Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# ============================================================================
# Check 1: Docker
# ============================================================================

Write-Host "1. Checking Docker..." -ForegroundColor Yellow
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Docker is running" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Docker is not running" -ForegroundColor Red
        $allGood = $false
    }
} catch {
    Write-Host "   ✗ Docker not found" -ForegroundColor Red
    $allGood = $false
}

# ============================================================================
# Check 2: LocalStack Container
# ============================================================================

Write-Host "2. Checking LocalStack container..." -ForegroundColor Yellow
$container = docker ps --filter "name=localstack-janis-cencosud" --format "{{.Status}}" 2>$null
if ($container -match "Up") {
    Write-Host "   ✓ LocalStack container is running" -ForegroundColor Green
    Write-Host "     Status: $container" -ForegroundColor Gray
} else {
    Write-Host "   ✗ LocalStack container is not running" -ForegroundColor Red
    Write-Host "     Run: docker-compose -f docker-compose.localstack.yml up -d" -ForegroundColor Yellow
    $allGood = $false
}

# ============================================================================
# Check 3: LocalStack Health
# ============================================================================

Write-Host "3. Checking LocalStack health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:4566/_localstack/health" -TimeoutSec 5 -ErrorAction Stop
    $runningServices = ($response.services.PSObject.Properties | Where-Object { $_.Value -eq "running" }).Count
    $totalServices = $response.services.PSObject.Properties.Count
    
    Write-Host "   ✓ LocalStack is responding" -ForegroundColor Green
    Write-Host "     Services: $runningServices/$totalServices running" -ForegroundColor Gray
    
    # List running services
    $running = $response.services.PSObject.Properties | Where-Object { $_.Value -eq "running" } | Select-Object -ExpandProperty Name
    Write-Host "     Running: $($running -join ', ')" -ForegroundColor Gray
} catch {
    Write-Host "   ✗ LocalStack is not responding" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Yellow
    $allGood = $false
}

# ============================================================================
# Check 4: Terraform
# ============================================================================

Write-Host "4. Checking Terraform..." -ForegroundColor Yellow
try {
    $tfVersion = terraform --version 2>&1 | Select-Object -First 1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Terraform installed: $tfVersion" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Terraform not found" -ForegroundColor Red
        $allGood = $false
    }
} catch {
    Write-Host "   ✗ Terraform not found" -ForegroundColor Red
    $allGood = $false
}

# ============================================================================
# Check 5: Terraform State
# ============================================================================

Write-Host "5. Checking Terraform state..." -ForegroundColor Yellow
if (Test-Path "terraform/terraform.tfstate") {
    $stateContent = Get-Content "terraform/terraform.tfstate" -Raw | ConvertFrom-Json
    $resourceCount = $stateContent.resources.Count
    
    if ($resourceCount -gt 0) {
        Write-Host "   ✓ Terraform state exists" -ForegroundColor Green
        Write-Host "     Resources: $resourceCount" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠ Terraform state exists but no resources" -ForegroundColor Yellow
        Write-Host "     Run: cd terraform && terraform apply -var-file=`"terraform.tfvars`"" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠ No Terraform state found" -ForegroundColor Yellow
    Write-Host "     Infrastructure not deployed yet" -ForegroundColor Gray
    Write-Host "     Run: .\scripts\init-localstack.ps1" -ForegroundColor Yellow
}

# ============================================================================
# Check 6: AWS CLI (Optional)
# ============================================================================

Write-Host "6. Checking AWS CLI (optional)..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ AWS CLI installed: $awsVersion" -ForegroundColor Green
        
        # Try to query LocalStack
        try {
            $vpcs = aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs --query 'Vpcs[*].VpcId' --output text 2>$null
            if ($vpcs) {
                Write-Host "   ✓ Can query LocalStack with AWS CLI" -ForegroundColor Green
                Write-Host "     VPCs found: $vpcs" -ForegroundColor Gray
            } else {
                Write-Host "   ⚠ No VPCs found in LocalStack" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "   ⚠ Cannot query LocalStack" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ℹ AWS CLI not installed (optional)" -ForegroundColor Cyan
}

# ============================================================================
# Check 7: Terraform Resources (if deployed)
# ============================================================================

if (Test-Path "terraform/terraform.tfstate") {
    Write-Host "7. Checking deployed resources..." -ForegroundColor Yellow
    
    Push-Location terraform
    
    $resources = terraform state list 2>$null
    if ($resources) {
        $resourceCount = ($resources | Measure-Object -Line).Lines
        Write-Host "   ✓ $resourceCount resources in state" -ForegroundColor Green
        
        # Check key resources
        $hasVpc = $resources | Where-Object { $_ -match "aws_vpc" }
        $hasSubnets = $resources | Where-Object { $_ -match "aws_subnet" }
        $hasSG = $resources | Where-Object { $_ -match "aws_security_group" }
        
        if ($hasVpc) { Write-Host "     ✓ VPC" -ForegroundColor Green } else { Write-Host "     ✗ VPC missing" -ForegroundColor Red }
        if ($hasSubnets) { Write-Host "     ✓ Subnets" -ForegroundColor Green } else { Write-Host "     ✗ Subnets missing" -ForegroundColor Red }
        if ($hasSG) { Write-Host "     ✓ Security Groups" -ForegroundColor Green } else { Write-Host "     ✗ Security Groups missing" -ForegroundColor Red }
    }
    
    Pop-Location
}

Write-Host ""

# ============================================================================
# Summary
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allGood) {
    Write-Host "✓ All critical checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your LocalStack environment is ready to use." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  - View outputs:   cd terraform && terraform output" -ForegroundColor White
    Write-Host "  - List resources: cd terraform && terraform state list" -ForegroundColor White
    Write-Host "  - Query AWS:      aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs" -ForegroundColor White
} else {
    Write-Host "✗ Some checks failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the issues above and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Quick fixes:" -ForegroundColor Yellow
    Write-Host "  - Start Docker Desktop" -ForegroundColor White
    Write-Host "  - Start LocalStack: docker-compose -f docker-compose.localstack.yml up -d" -ForegroundColor White
    Write-Host "  - Deploy infrastructure: .\scripts\init-localstack.ps1" -ForegroundColor White
}

Write-Host ""
