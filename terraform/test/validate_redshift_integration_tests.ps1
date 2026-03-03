# PowerShell script to validate Redshift Integration Property Test files
# This script checks that all required files exist and have correct structure

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Redshift Integration Test Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$testDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$allChecksPass = $true

# Check test file exists
Write-Host "Checking test files..." -ForegroundColor Yellow
$testFile = Join-Path $testDir "redshift_integration_property_test.go"
if (Test-Path $testFile) {
    Write-Host "✓ redshift_integration_property_test.go exists" -ForegroundColor Green
    
    # Check file content
    $content = Get-Content $testFile -Raw
    
    # Check for required test functions
    $requiredTests = @(
        "TestRedshiftSecurityGroupIntegrationProperty",
        "TestRedshiftSecurityGroupNoOverlappingCIDRs",
        "TestRedshiftSecurityGroupPreservesExistingAccess",
        "TestRedshiftSecurityGroupMySQLPipelineTemporary",
        "TestRedshiftSecurityGroupRuleValidation",
        "TestRedshiftSecurityGroupIntegrationComprehensive",
        "TestRedshiftSecurityGroupWithTerraform"
    )
    
    foreach ($test in $requiredTests) {
        if ($content -match $test) {
            Write-Host "  ✓ $test found" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $test NOT found" -ForegroundColor Red
            $allChecksPass = $false
        }
    }
    
    # Check for Property 16 validation
    if ($content -match "Property 16") {
        Write-Host "  ✓ Property 16 validation found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Property 16 validation NOT found" -ForegroundColor Red
        $allChecksPass = $false
    }
    
    # Check for Requirements 11.3 validation
    if ($content -match "Requirements 11\.3") {
        Write-Host "  ✓ Requirements 11.3 validation found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Requirements 11.3 validation NOT found" -ForegroundColor Red
        $allChecksPass = $false
    }
    
} else {
    Write-Host "✗ redshift_integration_property_test.go NOT found" -ForegroundColor Red
    $allChecksPass = $false
}

Write-Host ""

# Check run script exists
Write-Host "Checking run script..." -ForegroundColor Yellow
$runScript = Join-Path $testDir "run_redshift_integration_tests.ps1"
if (Test-Path $runScript) {
    Write-Host "✓ run_redshift_integration_tests.ps1 exists" -ForegroundColor Green
} else {
    Write-Host "✗ run_redshift_integration_tests.ps1 NOT found" -ForegroundColor Red
    $allChecksPass = $false
}

Write-Host ""

# Check summary document exists
Write-Host "Checking summary document..." -ForegroundColor Yellow
$summaryDoc = Join-Path $testDir "REDSHIFT_INTEGRATION_PROPERTY_TEST_SUMMARY.md"
if (Test-Path $summaryDoc) {
    Write-Host "✓ REDSHIFT_INTEGRATION_PROPERTY_TEST_SUMMARY.md exists" -ForegroundColor Green
    
    # Check summary content
    $summaryContent = Get-Content $summaryDoc -Raw
    
    if ($summaryContent -match "Property 16") {
        Write-Host "  ✓ Property 16 documentation found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Property 16 documentation NOT found" -ForegroundColor Red
        $allChecksPass = $false
    }
    
    if ($summaryContent -match "Requirements 11\.3") {
        Write-Host "  ✓ Requirements 11.3 documentation found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Requirements 11.3 documentation NOT found" -ForegroundColor Red
        $allChecksPass = $false
    }
    
} else {
    Write-Host "✗ REDSHIFT_INTEGRATION_PROPERTY_TEST_SUMMARY.md NOT found" -ForegroundColor Red
    $allChecksPass = $false
}

Write-Host ""

# Check Go module files
Write-Host "Checking Go module files..." -ForegroundColor Yellow
$goMod = Join-Path $testDir "go.mod"
if (Test-Path $goMod) {
    Write-Host "✓ go.mod exists" -ForegroundColor Green
} else {
    Write-Host "✗ go.mod NOT found" -ForegroundColor Red
    $allChecksPass = $false
}

$goSum = Join-Path $testDir "go.sum"
if (Test-Path $goSum) {
    Write-Host "✓ go.sum exists" -ForegroundColor Green
} else {
    Write-Host "✗ go.sum NOT found" -ForegroundColor Red
    $allChecksPass = $false
}

Write-Host ""

# Check Go installation
Write-Host "Checking Go installation..." -ForegroundColor Yellow
try {
    $goVersion = go version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Go is installed: $goVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Go is not installed or not in PATH" -ForegroundColor Yellow
        Write-Host "  Note: Go is required to run the tests" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Go is not installed or not in PATH" -ForegroundColor Yellow
    Write-Host "  Note: Go is required to run the tests" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allChecksPass) {
    Write-Host "✓ All validation checks PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "The Redshift Integration Property Test is properly configured." -ForegroundColor Green
    Write-Host ""
    Write-Host "To run the tests:" -ForegroundColor Yellow
    Write-Host "  1. Ensure Go is installed and in your PATH" -ForegroundColor Gray
    Write-Host "  2. Navigate to the terraform/test directory" -ForegroundColor Gray
    Write-Host "  3. Run: .\run_redshift_integration_tests.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or run individual tests:" -ForegroundColor Yellow
    Write-Host "  go test -v -run TestRedshiftSecurityGroupIntegrationProperty" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "✗ Some validation checks FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the errors above and ensure all required files exist." -ForegroundColor Yellow
    exit 1
}
