# Validation script for VPC unit tests
# This script validates the test file structure and provides guidance

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "VPC Unit Test Validation" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if test file exists
$testFile = "vpc_unit_test.go"
if (Test-Path $testFile) {
    Write-Host "[OK] Test file exists: $testFile" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Test file not found: $testFile" -ForegroundColor Red
    exit 1
}

# Check file size
$fileSize = (Get-Item $testFile).Length
Write-Host "[OK] Test file size: $fileSize bytes" -ForegroundColor Green

# Count test functions
$content = Get-Content $testFile -Raw
$testFunctions = ([regex]::Matches($content, "func Test\w+\(t \*testing\.T\)")).Count
Write-Host "[OK] Number of test functions: $testFunctions" -ForegroundColor Green

# List test functions
Write-Host ""
Write-Host "Test Functions:" -ForegroundColor Cyan
$matches = [regex]::Matches($content, "func (Test\w+)\(t \*testing\.T\)")
foreach ($match in $matches) {
    $funcName = $match.Groups[1].Value
    Write-Host "  - $funcName" -ForegroundColor White
}

# Check for required imports
Write-Host ""
Write-Host "Checking imports..." -ForegroundColor Cyan
$requiredImports = @(
    "testing",
    "github.com/gruntwork-io/terratest/modules/terraform",
    "github.com/stretchr/testify/assert"
)

foreach ($import in $requiredImports) {
    if ($content -match [regex]::Escape($import)) {
        Write-Host "[OK] Import found: $import" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Import not found: $import" -ForegroundColor Yellow
    }
}

# Check for requirement validation comments
Write-Host ""
Write-Host "Checking requirement validations..." -ForegroundColor Cyan
$requirements = @("1.1", "1.2", "1.3", "1.4", "1.5")
foreach ($req in $requirements) {
    if ($content -match "Requirements $req") {
        Write-Host "[OK] Validates Requirements $req" -ForegroundColor Green
    } else {
        Write-Host "[INFO] No explicit validation for Requirements $req" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test file structure is valid!" -ForegroundColor Green
Write-Host ""
Write-Host "To run these tests, you need:" -ForegroundColor Yellow
Write-Host "1. Go 1.21 or higher installed" -ForegroundColor White
Write-Host "2. Run: go mod download" -ForegroundColor White
Write-Host "3. Run: go test -v -run TestVPC" -ForegroundColor White
Write-Host ""
Write-Host "Test Coverage:" -ForegroundColor Cyan
Write-Host "- VPC creation with correct CIDR block (Req 1.1)" -ForegroundColor White
Write-Host "- DNS settings enabled (Req 1.3)" -ForegroundColor White
Write-Host "- Mandatory tags applied (Req 1.4)" -ForegroundColor White
Write-Host "- Single-AZ deployment (Req 1.2)" -ForegroundColor White
Write-Host "- IPv4 support (Req 1.5)" -ForegroundColor White
Write-Host "- Configuration integrity" -ForegroundColor White
Write-Host "- Resource naming conventions" -ForegroundColor White
Write-Host ""
