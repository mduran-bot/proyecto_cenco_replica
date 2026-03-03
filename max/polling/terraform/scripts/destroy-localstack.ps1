# ============================================================================
# Destroy LocalStack Infrastructure (PowerShell)
# ============================================================================
# This script destroys the API polling infrastructure in LocalStack
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "🗑️  Destroying API Polling Infrastructure in LocalStack..." -ForegroundColor Cyan

# Check if LocalStack is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:4566/_localstack/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ LocalStack is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  LocalStack is not running. Resources may not be destroyed properly." -ForegroundColor Yellow
}

# Destroy infrastructure
Write-Host "🔥 Destroying infrastructure..." -ForegroundColor Cyan
terraform destroy -var-file="localstack.tfvars" -auto-approve

Write-Host ""
Write-Host "✅ Infrastructure destroyed successfully!" -ForegroundColor Green
