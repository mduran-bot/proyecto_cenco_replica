# Run All Unit Tests
# This script executes all unit tests for the AWS infrastructure
# Validates: All Requirements

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AWS Infrastructure - Unit Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to test directory if not already there
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($scriptPath) {
    Set-Location $scriptPath
}

$ErrorActionPreference = "Stop"
$testsPassed = 0
$testsFailed = 0
$testsSkipped = 0

# Check if Go is installed
Write-Host "Checking Go installation..." -ForegroundColor Yellow
try {
    $goVersion = go version
    Write-Host "OK Go is installed: $goVersion" -ForegroundColor Green
} catch {
    Write-Host "X Go is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Go 1.21+ from https://go.dev/dl/" -ForegroundColor Yellow
    Write-Host "Or use Docker: docker run --rm -v PWD:/workspace -w /workspace golang:1.21 go test -v" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check if go.mod exists
if (-not (Test-Path "go.mod")) {
    Write-Host "X go.mod not found. Please run 'go mod init' first." -ForegroundColor Red
    exit 1
}

# Download dependencies
Write-Host "Downloading Go dependencies..." -ForegroundColor Yellow
try {
    go mod download
    Write-Host "OK Dependencies downloaded" -ForegroundColor Green
} catch {
    Write-Host "X Failed to download dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Unit Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to run a specific test file
function Run-UnitTest {
    param(
        [string]$TestFile,
        [string]$Description
    )
    
    Write-Host "Running: $Description" -ForegroundColor Yellow
    Write-Host "File: $TestFile" -ForegroundColor Gray
    Write-Host ""
    
    try {
        # Run the specific test file
        $output = go test -v -run "^Test.*" "./$TestFile" 2>&1
        
        # Check if tests passed
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK $Description - PASSED" -ForegroundColor Green
            
            # Count passed tests
            $passedCount = ($output | Select-String -Pattern "--- PASS:" | Measure-Object).Count
            $script:testsPassed += $passedCount
            
            Write-Host "  Tests passed: $passedCount" -ForegroundColor Gray
        } else {
            Write-Host "X $Description - FAILED" -ForegroundColor Red
            
            # Count failed tests
            $failedCount = ($output | Select-String -Pattern "--- FAIL:" | Measure-Object).Count
            $script:testsFailed += $failedCount
            
            Write-Host "  Tests failed: $failedCount" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Error output:" -ForegroundColor Red
            Write-Host $output -ForegroundColor Red
        }
    } catch {
        Write-Host "X $Description - ERROR" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        $script:testsFailed++
    }
    
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host ""
}

# Run VPC Unit Tests
Run-UnitTest -TestFile "vpc_unit_test.go" -Description "VPC Configuration Unit Tests"

# Run Security Groups Unit Tests
Run-UnitTest -TestFile "security_groups_unit_test.go" -Description "Security Groups Unit Tests"

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Unit Test Suite Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Total Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host "Total Tests Skipped: $testsSkipped" -ForegroundColor Yellow
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "OK ALL UNIT TESTS PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "The infrastructure unit tests validate:" -ForegroundColor Cyan
    Write-Host "  - VPC configuration with correct CIDR blocks" -ForegroundColor Gray
    Write-Host "  - DNS settings are properly enabled" -ForegroundColor Gray
    Write-Host "  - Mandatory tags are applied to all resources" -ForegroundColor Gray
    Write-Host "  - Single-AZ and Multi-AZ deployment configurations" -ForegroundColor Gray
    Write-Host "  - IPv4 support and resource naming conventions" -ForegroundColor Gray
    Write-Host "  - Security group configurations for all services" -ForegroundColor Gray
    Write-Host "  - Least privilege principle in security rules" -ForegroundColor Gray
    Write-Host "  - Self-referencing security groups (MWAA, Glue)" -ForegroundColor Gray
    Write-Host "  - No overly permissive rules on sensitive ports" -ForegroundColor Gray
    Write-Host ""
    exit 0
} else {
    Write-Host "X SOME UNIT TESTS FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the error output above and fix the failing tests." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
