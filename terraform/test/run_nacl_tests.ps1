# PowerShell script to run NACL property tests
# This script runs the property-based tests for NACL stateless bidirectionality

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NACL Property Tests" -ForegroundColor Cyan
Write-Host "Property 9: NACL Stateless Bidirectionality" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set working directory to test folder
$testDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $testDir

Write-Host "Running NACL property tests..." -ForegroundColor Yellow
Write-Host ""

# Run the property tests
go test -v -run TestNACL

# Capture exit code
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "NACL Property Tests: PASSED" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "NACL Property Tests: FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

exit $exitCode
