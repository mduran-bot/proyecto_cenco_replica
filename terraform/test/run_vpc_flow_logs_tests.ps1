# PowerShell script to run VPC Flow Logs property tests
# This script validates Property 15: VPC Flow Logs Capture Completeness

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VPC Flow Logs Property Tests" -ForegroundColor Cyan
Write-Host "Property 15: VPC Flow Logs Capture Completeness" -ForegroundColor Cyan
Write-Host "Validates: Requirements 10.2" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set error action preference
$ErrorActionPreference = "Continue"

# Change to test directory
Set-Location -Path $PSScriptRoot

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

# Check if go.mod exists
if (-not (Test-Path "go.mod")) {
    Write-Host "ERROR: go.mod not found in test directory" -ForegroundColor Red
    Write-Host "Please run 'go mod init' first" -ForegroundColor Red
    exit 1
}

# Download dependencies
Write-Host "Downloading Go dependencies..." -ForegroundColor Yellow
go mod download
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to download dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies downloaded successfully" -ForegroundColor Green
Write-Host ""

# Run VPC Flow Logs property tests
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running VPC Flow Logs Property Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Test 1: VPC Flow Logs Capture Completeness Property" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsCaptureCompletenessProperty -timeout 30m
$test1Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 2: VPC Flow Logs Metadata Completeness" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsMetadataCompleteness -timeout 30m
$test2Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 3: VPC Flow Logs with Terraform" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsWithTerraform -timeout 30m
$test3Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 4: VPC Flow Logs Module Configuration" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsModuleConfiguration -timeout 30m
$test4Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 5: VPC Flow Logs Traffic Type Validation" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsTrafficTypeValidation -timeout 30m
$test5Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 6: VPC Flow Logs Log Format Fields" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsLogFormatFields -timeout 30m
$test6Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 7: VPC Flow Logs Retention Policy" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsRetentionPolicy -timeout 30m
$test7Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 8: VPC Flow Logs Action Capture" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsActionCapture -timeout 30m
$test8Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 9: VPC Flow Logs CloudWatch Integration" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsCloudWatchIntegration -timeout 30m
$test9Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 10: VPC Flow Logs Comprehensive Capture" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsComprehensiveCapture -timeout 30m
$test10Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 11: Production VPC Flow Logs Configuration" -ForegroundColor Yellow
go test -v -run TestProductionVPCFlowLogsConfiguration -timeout 30m
$test11Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 12: VPC Flow Logs IAM Permissions" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsIAMPermissions -timeout 30m
$test12Result = $LASTEXITCODE
Write-Host ""

Write-Host "Test 13: VPC Flow Logs Security Monitoring" -ForegroundColor Yellow
go test -v -run TestVPCFlowLogsSecurityMonitoring -timeout 30m
$test13Result = $LASTEXITCODE
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$allTests = @(
    @{Name="VPC Flow Logs Capture Completeness Property"; Result=$test1Result},
    @{Name="VPC Flow Logs Metadata Completeness"; Result=$test2Result},
    @{Name="VPC Flow Logs with Terraform"; Result=$test3Result},
    @{Name="VPC Flow Logs Module Configuration"; Result=$test4Result},
    @{Name="VPC Flow Logs Traffic Type Validation"; Result=$test5Result},
    @{Name="VPC Flow Logs Log Format Fields"; Result=$test6Result},
    @{Name="VPC Flow Logs Retention Policy"; Result=$test7Result},
    @{Name="VPC Flow Logs Action Capture"; Result=$test8Result},
    @{Name="VPC Flow Logs CloudWatch Integration"; Result=$test9Result},
    @{Name="VPC Flow Logs Comprehensive Capture"; Result=$test10Result},
    @{Name="Production VPC Flow Logs Configuration"; Result=$test11Result},
    @{Name="VPC Flow Logs IAM Permissions"; Result=$test12Result},
    @{Name="VPC Flow Logs Security Monitoring"; Result=$test13Result}
)

$passedTests = 0
$failedTests = 0

foreach ($test in $allTests) {
    if ($test.Result -eq 0) {
        Write-Host "✓ $($test.Name)" -ForegroundColor Green
        $passedTests++
    } else {
        Write-Host "✗ $($test.Name)" -ForegroundColor Red
        $failedTests++
    }
}

Write-Host ""
Write-Host "Total Tests: $($allTests.Count)" -ForegroundColor Cyan
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor Red
Write-Host ""

if ($failedTests -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "All VPC Flow Logs Property Tests PASSED!" -ForegroundColor Green
    Write-Host "Property 15 is validated successfully" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Some VPC Flow Logs Property Tests FAILED" -ForegroundColor Red
    Write-Host "Please review the test output above" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
