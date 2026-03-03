# PowerShell script to validate Single Point of Failure Documentation
# This script checks that all required documentation exists before running tests

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SPOF Documentation Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$validationPassed = $true

# Change to terraform directory
$terraformDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $terraformDir

Write-Host "Terraform Directory: $terraformDir" -ForegroundColor Yellow
Write-Host ""

# Check for SINGLE_AZ_DEPLOYMENT.md
Write-Host "Checking SINGLE_AZ_DEPLOYMENT.md..." -ForegroundColor Yellow
if (Test-Path "SINGLE_AZ_DEPLOYMENT.md") {
    Write-Host "  ✓ File exists" -ForegroundColor Green
    
    $content = Get-Content "SINGLE_AZ_DEPLOYMENT.md" -Raw
    
    # Check for required sections
    $requiredSections = @(
        "Single Points of Failure",
        "NAT Gateway",
        "Availability Zone Failure",
        "Single-AZ Deployment Limitations",
        "Impact of AZ Failure",
        "Recovery Procedures",
        "Monitoring and Alerting"
    )
    
    foreach ($section in $requiredSections) {
        if ($content -match [regex]::Escape($section)) {
            Write-Host "  ✓ Section found: $section" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Section missing: $section" -ForegroundColor Red
            $validationPassed = $false
        }
    }
    
    # Check for specific SPOFs
    $spofs = @(
        "NAT Gateway",
        "Availability Zone",
        "Internet Gateway",
        "VPC Endpoints"
    )
    
    Write-Host ""
    Write-Host "  Checking Single Points of Failure documentation:" -ForegroundColor Yellow
    foreach ($spof in $spofs) {
        if ($content -match [regex]::Escape($spof)) {
            Write-Host "    ✓ $spof documented" -ForegroundColor Green
        } else {
            Write-Host "    ✗ $spof not documented" -ForegroundColor Red
            $validationPassed = $false
        }
    }
    
    # Check for severity levels
    Write-Host ""
    Write-Host "  Checking severity levels:" -ForegroundColor Yellow
    $severities = @("HIGH", "CRITICAL", "LOW", "MEDIUM")
    foreach ($severity in $severities) {
        if ($content -match $severity) {
            Write-Host "    ✓ $severity severity documented" -ForegroundColor Green
        } else {
            Write-Host "    ✗ $severity severity not documented" -ForegroundColor Red
            $validationPassed = $false
        }
    }
    
    # Check for recovery times
    Write-Host ""
    Write-Host "  Checking recovery time estimates:" -ForegroundColor Yellow
    $recoveryTimes = @("7-20 minutes", "hours to days", "< 1 minute", "2-5 minutes")
    foreach ($time in $recoveryTimes) {
        if ($content -match [regex]::Escape($time)) {
            Write-Host "    ✓ Recovery time documented: $time" -ForegroundColor Green
        } else {
            Write-Host "    ✗ Recovery time not documented: $time" -ForegroundColor Red
            $validationPassed = $false
        }
    }
    
} else {
    Write-Host "  ✗ SINGLE_AZ_DEPLOYMENT.md not found" -ForegroundColor Red
    $validationPassed = $false
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Check for MULTI_AZ_EXPANSION.md
Write-Host ""
Write-Host "Checking MULTI_AZ_EXPANSION.md..." -ForegroundColor Yellow
if (Test-Path "MULTI_AZ_EXPANSION.md") {
    Write-Host "  ✓ File exists" -ForegroundColor Green
    
    $content = Get-Content "MULTI_AZ_EXPANSION.md" -Raw
    
    # Check for required sections
    $requiredSections = @(
        "Migration Path to Multi-AZ",
        "Reserved CIDR Blocks",
        "Prerequisites",
        "Migration Steps",
        "Architectural Changes",
        "Rollback Plan"
    )
    
    foreach ($section in $requiredSections) {
        if ($content -match [regex]::Escape($section)) {
            Write-Host "  ✓ Section found: $section" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Section missing: $section" -ForegroundColor Red
            $validationPassed = $false
        }
    }
    
    # Check for reserved CIDR blocks
    Write-Host ""
    Write-Host "  Checking reserved CIDR blocks:" -ForegroundColor Yellow
    $reservedCIDRs = @(
        "10.0.2.0/24",
        "10.0.11.0/24",
        "10.0.21.0/24"
    )
    
    foreach ($cidr in $reservedCIDRs) {
        if ($content -match [regex]::Escape($cidr)) {
            Write-Host "    ✓ Reserved CIDR documented: $cidr" -ForegroundColor Green
        } else {
            Write-Host "    ✗ Reserved CIDR not documented: $cidr" -ForegroundColor Red
            $validationPassed = $false
        }
    }
    
    # Check for Terraform configuration steps
    Write-Host ""
    Write-Host "  Checking Terraform migration steps:" -ForegroundColor Yellow
    $terraformSteps = @(
        "enable_multi_az",
        "terraform plan",
        "terraform apply",
        "terraform.tfvars"
    )
    
    foreach ($step in $terraformSteps) {
        if ($content -match [regex]::Escape($step)) {
            Write-Host "    ✓ Step documented: $step" -ForegroundColor Green
        } else {
            Write-Host "    ✗ Step not documented: $step" -ForegroundColor Red
            $validationPassed = $false
        }
    }
    
    # Check for migration phases
    Write-Host ""
    Write-Host "  Checking migration phases:" -ForegroundColor Yellow
    $phases = @("Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5")
    foreach ($phase in $phases) {
        if ($content -match [regex]::Escape($phase)) {
            Write-Host "    ✓ $phase documented" -ForegroundColor Green
        } else {
            Write-Host "    ✗ $phase not documented" -ForegroundColor Red
            $validationPassed = $false
        }
    }
    
} else {
    Write-Host "  ✗ MULTI_AZ_EXPANSION.md not found" -ForegroundColor Red
    $validationPassed = $false
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Check for cross-references
Write-Host ""
Write-Host "Checking documentation cross-references..." -ForegroundColor Yellow

if ((Test-Path "SINGLE_AZ_DEPLOYMENT.md") -and (Test-Path "MULTI_AZ_EXPANSION.md")) {
    $singleAZContent = Get-Content "SINGLE_AZ_DEPLOYMENT.md" -Raw
    $multiAZContent = Get-Content "MULTI_AZ_EXPANSION.md" -Raw
    
    if ($singleAZContent -match "MULTI_AZ_EXPANSION\.md") {
        Write-Host "  ✓ SINGLE_AZ_DEPLOYMENT.md references MULTI_AZ_EXPANSION.md" -ForegroundColor Green
    } else {
        Write-Host "  ✗ SINGLE_AZ_DEPLOYMENT.md does not reference MULTI_AZ_EXPANSION.md" -ForegroundColor Red
        $validationPassed = $false
    }
    
    if ($multiAZContent -match "SINGLE_AZ_DEPLOYMENT\.md") {
        Write-Host "  ✓ MULTI_AZ_EXPANSION.md references SINGLE_AZ_DEPLOYMENT.md" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MULTI_AZ_EXPANSION.md does not reference SINGLE_AZ_DEPLOYMENT.md" -ForegroundColor Red
        $validationPassed = $false
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($validationPassed) {
    Write-Host "✓ All documentation validation checks PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "The following documentation is complete:" -ForegroundColor Green
    Write-Host "  ✓ Single points of failure identified" -ForegroundColor Green
    Write-Host "  ✓ Impact analysis documented" -ForegroundColor Green
    Write-Host "  ✓ Recovery procedures documented" -ForegroundColor Green
    Write-Host "  ✓ Migration path to multi-AZ documented" -ForegroundColor Green
    Write-Host "  ✓ Reserved CIDR blocks documented" -ForegroundColor Green
    Write-Host "  ✓ Architectural changes documented" -ForegroundColor Green
    Write-Host "  ✓ Documentation cross-references validated" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run the property tests with:" -ForegroundColor Yellow
    Write-Host "  .\run_spof_documentation_tests.ps1" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "✗ Documentation validation FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please address the issues above before running property tests." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Required documentation:" -ForegroundColor Yellow
    Write-Host "  - SINGLE_AZ_DEPLOYMENT.md with complete SPOF documentation" -ForegroundColor White
    Write-Host "  - MULTI_AZ_EXPANSION.md with migration path" -ForegroundColor White
    Write-Host "  - Cross-references between documents" -ForegroundColor White
    Write-Host ""
    exit 1
}
