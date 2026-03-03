#!/usr/bin/env pwsh
# Validation script for EventBridge property tests

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "EventBridge Property Tests Validation" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $PSScriptRoot

try {
    Write-Host "Running Property 13: EventBridge Rule Target Validity..." -ForegroundColor Yellow
    $result13 = go test -v -run TestEventBridgeRuleTargetValidityProperty 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Property 13 PASSED" -ForegroundColor Green
        $prop13Pass = $true
    } else {
        Write-Host "❌ Property 13 FAILED" -ForegroundColor Red
        Write-Host $result13
        $prop13Pass = $false
    }
    
    Write-Host ""
    Write-Host "Running Property 14: EventBridge Schedule Expression Validity..." -ForegroundColor Yellow
    $result14 = go test -v -run TestEventBridgeScheduleExpressionValidityProperty 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Property 14 PASSED" -ForegroundColor Green
        $prop14Pass = $true
    } else {
        Write-Host "❌ Property 14 FAILED" -ForegroundColor Red
        Write-Host $result14
        $prop14Pass = $false
    }
    
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "Test Summary" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    
    if ($prop13Pass) {
        Write-Host "Property 13 (Rule Target Validity): ✅ PASSED" -ForegroundColor Green
    } else {
        Write-Host "Property 13 (Rule Target Validity): ❌ FAILED" -ForegroundColor Red
    }
    
    if ($prop14Pass) {
        Write-Host "Property 14 (Schedule Expression Validity): ✅ PASSED" -ForegroundColor Green
    } else {
        Write-Host "Property 14 (Schedule Expression Validity): ❌ FAILED" -ForegroundColor Red
    }
    
    Write-Host ""
    
    if ($prop13Pass -and $prop14Pass) {
        Write-Host "🎉 All EventBridge property tests PASSED!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Validated Requirements:" -ForegroundColor Cyan
        Write-Host "  - Requirement 9.2: Scheduled rules for polling" -ForegroundColor White
        Write-Host "  - Requirement 9.3: Rule targets with MWAA DAG ARNs" -ForegroundColor White
        Write-Host "  - Requirement 9.4: Event metadata in rule targets" -ForegroundColor White
        exit 0
    } else {
        Write-Host "⚠️  Some property tests failed" -ForegroundColor Red
        exit 1
    }
    
} finally {
    Pop-Location
}
