# Setup script for Terraform tests
# This script checks for Go installation and sets up the test environment

Write-Host "Checking for Go installation..." -ForegroundColor Cyan

# Check if Go is installed
$goVersion = $null
try {
    $goVersion = go version 2>$null
} catch {
    $goVersion = $null
}

if ($null -eq $goVersion) {
    Write-Host "Go is not installed on this system." -ForegroundColor Red
    Write-Host ""
    Write-Host "To run property-based tests, you need to install Go:" -ForegroundColor Yellow
    Write-Host "1. Download Go from: https://go.dev/dl/" -ForegroundColor White
    Write-Host "2. Install Go 1.21 or higher" -ForegroundColor White
    Write-Host "3. Verify installation: go version" -ForegroundColor White
    Write-Host "4. Run this script again" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative: Run tests in a Docker container with Go installed" -ForegroundColor Yellow
    exit 1
}

Write-Host "Go is installed: $goVersion" -ForegroundColor Green

# Download Go modules
Write-Host "Downloading Go dependencies..." -ForegroundColor Cyan
go mod download

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies downloaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run tests with:" -ForegroundColor Cyan
    Write-Host "  go test -v" -ForegroundColor White
    Write-Host "  go test -v -run TestVPCCIDRValidityProperty" -ForegroundColor White
} else {
    Write-Host "Failed to download dependencies" -ForegroundColor Red
    exit 1
}
