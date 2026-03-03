#!/usr/bin/env pwsh
# ============================================================================
# Security Groups Unit Tests Runner
# Runs unit tests for security group configurations
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Security Groups Unit Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to test directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if Go is installed
$goVersion = & go version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Go is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Go 1.21 or higher from https://go.dev/dl/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Go version: $goVersion" -ForegroundColor Green
Write-Host ""

# Download dependencies if needed
Write-Host "Downloading Go dependencies..." -ForegroundColor Yellow
& go mod download
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to download Go dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies downloaded successfully" -ForegroundColor Green
Write-Host ""

# Run unit tests
Write-Host "Running Security Groups Unit Tests..." -ForegroundColor Yellow
Write-Host ""

$testResults = @()

# Test 1: SG-API-Gateway Configuration
Write-Host "[1/15] Testing SG-API-Gateway Configuration..." -ForegroundColor Cyan
& go test -v -run TestSGAPIGatewayConfiguration -timeout 10m
$testResults += @{ Name = "SG-API-Gateway Configuration"; Success = ($LASTEXITCODE -eq 0) }

# Test 2: SG-API-Gateway No Overly Permissive Rules
Write-Host "[2/15] Testing SG-API-Gateway No Overly Permissive Rules..." -ForegroundColor Cyan
& go test -v -run TestSGAPIGatewayNoOverlyPermissiveRules -timeout 10m
$testResults += @{ Name = "SG-API-Gateway No Overly Permissive Rules"; Success = ($LASTEXITCODE -eq 0) }

# Test 3: SG-Redshift Configuration
Write-Host "[3/15] Testing SG-Redshift Configuration..." -ForegroundColor Cyan
& go test -v -run TestSGRedshiftConfiguration -timeout 10m
$testResults += @{ Name = "SG-Redshift Configuration"; Success = ($LASTEXITCODE -eq 0) }

# Test 4: SG-Redshift No Overly Permissive Rules
Write-Host "[4/15] Testing SG-Redshift No Overly Permissive Rules..." -ForegroundColor Cyan
& go test -v -run TestSGRedshiftNoOverlyPermissiveRules -timeout 10m
$testResults += @{ Name = "SG-Redshift No Overly Permissive Rules"; Success = ($LASTEXITCODE -eq 0) }

# Test 5: SG-Lambda Configuration
Write-Host "[5/15] Testing SG-Lambda Configuration..." -ForegroundColor Cyan
& go test -v -run TestSGLambdaConfiguration -timeout 10m
$testResults += @{ Name = "SG-Lambda Configuration"; Success = ($LASTEXITCODE -eq 0) }

# Test 6: SG-Lambda No Inbound Rules
Write-Host "[6/15] Testing SG-Lambda No Inbound Rules..." -ForegroundColor Cyan
& go test -v -run TestSGLambdaNoInboundRules -timeout 10m
$testResults += @{ Name = "SG-Lambda No Inbound Rules"; Success = ($LASTEXITCODE -eq 0) }

# Test 7: SG-MWAA Configuration
Write-Host "[7/15] Testing SG-MWAA Configuration..." -ForegroundColor Cyan
& go test -v -run TestSGMWAAConfiguration -timeout 10m
$testResults += @{ Name = "SG-MWAA Configuration"; Success = ($LASTEXITCODE -eq 0) }

# Test 8: SG-MWAA Self Reference
Write-Host "[8/15] Testing SG-MWAA Self Reference..." -ForegroundColor Cyan
& go test -v -run TestSGMWAASelfReference -timeout 10m
$testResults += @{ Name = "SG-MWAA Self Reference"; Success = ($LASTEXITCODE -eq 0) }

# Test 9: SG-Glue Configuration
Write-Host "[9/15] Testing SG-Glue Configuration..." -ForegroundColor Cyan
& go test -v -run TestSGGlueConfiguration -timeout 10m
$testResults += @{ Name = "SG-Glue Configuration"; Success = ($LASTEXITCODE -eq 0) }

# Test 10: SG-Glue Self Reference
Write-Host "[10/15] Testing SG-Glue Self Reference..." -ForegroundColor Cyan
& go test -v -run TestSGGlueSelfReference -timeout 10m
$testResults += @{ Name = "SG-Glue Self Reference"; Success = ($LASTEXITCODE -eq 0) }

# Test 11: SG-EventBridge Configuration
Write-Host "[11/15] Testing SG-EventBridge Configuration..." -ForegroundColor Cyan
& go test -v -run TestSGEventBridgeConfiguration -timeout 10m
$testResults += @{ Name = "SG-EventBridge Configuration"; Success = ($LASTEXITCODE -eq 0) }

# Test 12: SG-VPC-Endpoints Configuration
Write-Host "[12/15] Testing SG-VPC-Endpoints Configuration..." -ForegroundColor Cyan
& go test -v -run TestSGVPCEndpointsConfiguration -timeout 10m
$testResults += @{ Name = "SG-VPC-Endpoints Configuration"; Success = ($LASTEXITCODE -eq 0) }

# Test 13: All Security Groups Integrity
Write-Host "[13/15] Testing All Security Groups Integrity..." -ForegroundColor Cyan
& go test -v -run TestAllSecurityGroupsIntegrity -timeout 10m
$testResults += @{ Name = "All Security Groups Integrity"; Success = ($LASTEXITCODE -eq 0) }

# Test 14: Multiple Janis IP Ranges
Write-Host "[14/15] Testing Multiple Janis IP Ranges..." -ForegroundColor Cyan
& go test -v -run TestSecurityGroupsWithMultipleJanisIPRanges -timeout 10m
$testResults += @{ Name = "Multiple Janis IP Ranges"; Success = ($LASTEXITCODE -eq 0) }

# Test 15: Least Privilege Principle
Write-Host "[15/15] Testing Least Privilege Principle..." -ForegroundColor Cyan
& go test -v -run TestSecurityGroupsLeastPrivilege -timeout 10m
$testResults += @{ Name = "Least Privilege Principle"; Success = ($LASTEXITCODE -eq 0) }

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$passedTests = ($testResults | Where-Object { $_.Success }).Count
$failedTests = ($testResults | Where-Object { -not $_.Success }).Count
$totalTests = $testResults.Count

Write-Host ""
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor $(if ($failedTests -eq 0) { "Green" } else { "Red" })
Write-Host ""

# Display failed tests
if ($failedTests -gt 0) {
    Write-Host "Failed Tests:" -ForegroundColor Red
    foreach ($test in $testResults) {
        if (-not $test.Success) {
            Write-Host "  - $($test.Name)" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# Exit with appropriate code
if ($failedTests -eq 0) {
    Write-Host "All tests passed! ✓" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed! ✗" -ForegroundColor Red
    exit 1
}
