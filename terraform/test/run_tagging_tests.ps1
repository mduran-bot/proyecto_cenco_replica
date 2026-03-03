# ============================================================================
# Run Tagging Property Tests
# Tests Property 12: Resource Tagging Completeness
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tagging Property Tests" -ForegroundColor Cyan
Write-Host "Property 12: Resource Tagging Completeness" -ForegroundColor Cyan
Write-Host "Validates: Requirements 8.1, 8.4" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

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

# Run the tagging property tests
Write-Host "Running Tagging Property Tests..." -ForegroundColor Yellow
Write-Host "Test file: tagging_property_test.go" -ForegroundColor Cyan
Write-Host "Minimum successful tests: 100 iterations per property" -ForegroundColor Cyan
Write-Host ""

go test -v -run TestResourceTaggingCompletenessProperty -timeout 30m

$testResult = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($testResult -eq 0) {
    Write-Host "✓ Tagging Property Tests PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Property 12 validated successfully:" -ForegroundColor Green
    Write-Host "- All mandatory tags (Project, Environment, Component, Owner, CostCenter) are present" -ForegroundColor Green
    Write-Host "- All mandatory tag values are non-empty" -ForegroundColor Green
    Write-Host "- Environment tag has valid values (development, staging, production)" -ForegroundColor Green
    Write-Host "- Tag keys follow proper format (alphanumeric with hyphens/underscores)" -ForegroundColor Green
    Write-Host "- Tag values do not exceed 256 characters" -ForegroundColor Green
} else {
    Write-Host "✗ Tagging Property Tests FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Property 12 validation failed. Please review the test output above." -ForegroundColor Red
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run additional tagging tests
Write-Host "Running Additional Tagging Tests..." -ForegroundColor Yellow
Write-Host ""

go test -v -run "TestMandatoryTag|TestEnvironmentTag|TestTagKey|TestTagValue|TestTagging" -timeout 30m

$additionalTestResult = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($additionalTestResult -eq 0) {
    Write-Host "✓ Additional Tagging Tests PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Additional Tagging Tests FAILED" -ForegroundColor Red
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Exit with appropriate code
if ($testResult -eq 0 -and $additionalTestResult -eq 0) {
    Write-Host "All tagging tests completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tagging tests failed. Please review the output above." -ForegroundColor Red
    exit 1
}
