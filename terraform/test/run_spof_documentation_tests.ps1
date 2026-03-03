# PowerShell script to run Single Point of Failure Documentation Property Tests
# Feature: aws-infrastructure, Property 17: Single Point of Failure Documentation
# Validates: Requirements 12.1, 12.2, 12.3, 12.5

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Single Point of Failure Documentation Property Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set error action preference
$ErrorActionPreference = "Continue"

# Change to test directory
$testDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $testDir

Write-Host "Test Directory: $testDir" -ForegroundColor Yellow
Write-Host ""

# Check if Go is installed
Write-Host "Checking Go installation..." -ForegroundColor Yellow
$goVersion = go version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Go is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Go from https://golang.org/dl/" -ForegroundColor Red
    exit 1
}
Write-Host "Go version: $goVersion" -ForegroundColor Green
Write-Host ""

# Check if required Go modules are available
Write-Host "Checking Go modules..." -ForegroundColor Yellow
if (-not (Test-Path "go.mod")) {
    Write-Host "ERROR: go.mod not found" -ForegroundColor Red
    Write-Host "Please run 'go mod init' first" -ForegroundColor Red
    exit 1
}
Write-Host "Go modules found" -ForegroundColor Green
Write-Host ""

# Download dependencies
Write-Host "Downloading Go dependencies..." -ForegroundColor Yellow
go mod download
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Some dependencies may not have downloaded correctly" -ForegroundColor Yellow
}
Write-Host ""

# Run the property tests
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Property Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Test: Property 17 - Single Point of Failure Documentation" -ForegroundColor Yellow
Write-Host "Validates: Requirements 12.1, 12.2, 12.3, 12.5" -ForegroundColor Yellow
Write-Host ""

# Run all SPOF documentation tests
Write-Host "Running all SPOF documentation property tests..." -ForegroundColor Cyan
go test -v -timeout 30m -run "TestSinglePointOfFailureDocumentation" ./...

$testExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Execution Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($testExitCode -eq 0) {
    Write-Host "✓ All SPOF documentation property tests PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Documentation Validation Results:" -ForegroundColor Green
    Write-Host "  ✓ SINGLE_AZ_DEPLOYMENT.md exists and is complete" -ForegroundColor Green
    Write-Host "  ✓ NAT Gateway single point of failure documented" -ForegroundColor Green
    Write-Host "  ✓ Availability Zone single point of failure documented" -ForegroundColor Green
    Write-Host "  ✓ Impact of AZ failure documented" -ForegroundColor Green
    Write-Host "  ✓ Recovery procedures documented" -ForegroundColor Green
    Write-Host "  ✓ MULTI_AZ_EXPANSION.md exists with migration path" -ForegroundColor Green
    Write-Host "  ✓ Reserved CIDR blocks documented" -ForegroundColor Green
    Write-Host "  ✓ Architectural changes documented" -ForegroundColor Green
    Write-Host "  ✓ Monitoring and alerting documented" -ForegroundColor Green
    Write-Host "  ✓ Documentation cross-references validated" -ForegroundColor Green
    Write-Host ""
    Write-Host "Property 17 validation: PASSED ✓" -ForegroundColor Green
} else {
    Write-Host "✗ Some SPOF documentation property tests FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the test output above for details." -ForegroundColor Yellow
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Missing documentation files (SINGLE_AZ_DEPLOYMENT.md or MULTI_AZ_EXPANSION.md)" -ForegroundColor Yellow
    Write-Host "  - Incomplete single point of failure documentation" -ForegroundColor Yellow
    Write-Host "  - Missing recovery procedures" -ForegroundColor Yellow
    Write-Host "  - Missing migration path to multi-AZ" -ForegroundColor Yellow
    Write-Host "  - Missing reserved CIDR block documentation" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Property 17 validation: FAILED ✗" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Documentation Requirements" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Required Documentation Elements:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Single Points of Failure Identification:" -ForegroundColor White
Write-Host "   - NAT Gateway (HIGH severity, 7-20 min recovery)" -ForegroundColor Gray
Write-Host "   - Availability Zone (CRITICAL severity, hours to days recovery)" -ForegroundColor Gray
Write-Host "   - Internet Gateway (LOW severity, < 1 min recovery)" -ForegroundColor Gray
Write-Host "   - VPC Endpoints (MEDIUM severity, 2-5 min recovery)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Impact Analysis:" -ForegroundColor White
Write-Host "   - Immediate impact (T+0 to T+5 minutes)" -ForegroundColor Gray
Write-Host "   - Short-term impact (T+5 minutes to T+1 hour)" -ForegroundColor Gray
Write-Host "   - Medium-term impact (T+1 hour to T+24 hours)" -ForegroundColor Gray
Write-Host "   - Long-term impact (T+24 hours+)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Recovery Procedures:" -ForegroundColor White
Write-Host "   - NAT Gateway failure recovery steps" -ForegroundColor Gray
Write-Host "   - Availability Zone failure recovery options" -ForegroundColor Gray
Write-Host "   - Automated detection mechanisms" -ForegroundColor Gray
Write-Host "   - Manual intervention procedures" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Migration Path to Multi-AZ:" -ForegroundColor White
Write-Host "   - Prerequisites and planning" -ForegroundColor Gray
Write-Host "   - Phase-by-phase migration steps" -ForegroundColor Gray
Write-Host "   - Terraform configuration changes" -ForegroundColor Gray
Write-Host "   - Rollback procedures" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Reserved CIDR Blocks:" -ForegroundColor White
Write-Host "   - Public Subnet B: 10.0.2.0/24 (us-east-1b)" -ForegroundColor Gray
Write-Host "   - Private Subnet 1B: 10.0.11.0/24 (us-east-1b)" -ForegroundColor Gray
Write-Host "   - Private Subnet 2B: 10.0.21.0/24 (us-east-1b)" -ForegroundColor Gray
Write-Host ""
Write-Host "6. Monitoring and Alerting:" -ForegroundColor White
Write-Host "   - Critical alarms configuration" -ForegroundColor Gray
Write-Host "   - Monitoring dashboard metrics" -ForegroundColor Gray
Write-Host "   - Alert escalation procedures" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

exit $testExitCode
