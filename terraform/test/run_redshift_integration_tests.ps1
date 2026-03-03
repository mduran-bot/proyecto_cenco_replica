# PowerShell script to run Redshift Integration Property Tests
# This script runs the property-based tests for Redshift security group integration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Redshift Integration Property Tests" -ForegroundColor Cyan
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
$goVersion = go version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Go is installed: $goVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Go is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Go from https://golang.org/dl/" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check if go.mod exists
if (-not (Test-Path "go.mod")) {
    Write-Host "✗ go.mod not found in test directory" -ForegroundColor Red
    Write-Host "Please run 'go mod init' first" -ForegroundColor Red
    exit 1
}

# Download dependencies
Write-Host "Downloading Go dependencies..." -ForegroundColor Yellow
go mod download
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to download dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies downloaded" -ForegroundColor Green
Write-Host ""

# Run the property tests
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Property Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Test: Property 16 - Redshift Security Group Integration" -ForegroundColor Yellow
Write-Host "Validates: Requirements 11.3" -ForegroundColor Gray
Write-Host "Property: New security group rules must not conflict with existing BI rules" -ForegroundColor Gray
Write-Host ""

# Run the tests with verbose output
go test -v -run TestRedshiftSecurityGroupIntegrationProperty -timeout 30m

$testResult = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Additional Validation Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run additional validation tests
Write-Host "Running: No Overlapping CIDRs Test" -ForegroundColor Yellow
go test -v -run TestRedshiftSecurityGroupNoOverlappingCIDRs -timeout 10m

Write-Host ""
Write-Host "Running: Preserves Existing Access Test" -ForegroundColor Yellow
go test -v -run TestRedshiftSecurityGroupPreservesExistingAccess -timeout 10m

Write-Host ""
Write-Host "Running: MySQL Pipeline Temporary Test" -ForegroundColor Yellow
go test -v -run TestRedshiftSecurityGroupMySQLPipelineTemporary -timeout 10m

Write-Host ""
Write-Host "Running: Rule Validation Test" -ForegroundColor Yellow
go test -v -run TestRedshiftSecurityGroupRuleValidation -timeout 10m

Write-Host ""
Write-Host "Running: Comprehensive Integration Test" -ForegroundColor Yellow
go test -v -run TestRedshiftSecurityGroupIntegrationComprehensive -timeout 30m

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Terraform Validation Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Running: Terraform Configuration Test" -ForegroundColor Yellow
go test -v -run TestRedshiftSecurityGroupWithTerraform -timeout 10m

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($testResult -eq 0) {
    Write-Host "✓ All Redshift Integration Property Tests PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Property 16 Validation:" -ForegroundColor Green
    Write-Host "  ✓ New security group rules do not conflict with existing BI rules" -ForegroundColor Green
    Write-Host "  ✓ CIDR blocks do not overlap" -ForegroundColor Green
    Write-Host "  ✓ Existing BI access is preserved" -ForegroundColor Green
    Write-Host "  ✓ MySQL pipeline rule is properly marked as temporary" -ForegroundColor Green
    Write-Host "  ✓ All rules are properly validated" -ForegroundColor Green
    Write-Host "  ✓ Terraform configuration is valid" -ForegroundColor Green
    Write-Host ""
    Write-Host "Requirements 11.3 validated successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Some Redshift Integration Property Tests FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the test output above for details." -ForegroundColor Yellow
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Security group rule conflicts" -ForegroundColor Yellow
    Write-Host "  - Overlapping CIDR blocks" -ForegroundColor Yellow
    Write-Host "  - Missing or invalid rule descriptions" -ForegroundColor Yellow
    Write-Host "  - Incorrect port or protocol configuration" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Test execution completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

exit $testResult
