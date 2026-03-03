#!/usr/bin/env pwsh
# Script to run EventBridge property tests

Write-Host "Running EventBridge Property Tests..." -ForegroundColor Cyan

# Change to test directory
Push-Location $PSScriptRoot

try {
    # Run Property 13: EventBridge Rule Target Validity
    Write-Host "`nRunning Property 13: EventBridge Rule Target Validity..." -ForegroundColor Yellow
    go test -v -run TestEventBridgeRuleTargetValidityProperty
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Property 13 test failed!" -ForegroundColor Red
        exit 1
    }
    
    # Run Property 14: EventBridge Schedule Expression Validity
    Write-Host "`nRunning Property 14: EventBridge Schedule Expression Validity..." -ForegroundColor Yellow
    go test -v -run TestEventBridgeScheduleExpressionValidityProperty
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Property 14 test failed!" -ForegroundColor Red
        exit 1
    }
    
    # Run all EventBridge tests
    Write-Host "`nRunning all EventBridge tests..." -ForegroundColor Yellow
    go test -v -run TestEventBridge
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Some EventBridge tests failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`nAll EventBridge tests passed!" -ForegroundColor Green
    
} finally {
    Pop-Location
}
