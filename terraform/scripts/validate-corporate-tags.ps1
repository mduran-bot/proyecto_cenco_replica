# ============================================================================
# Script: Validate Corporate Tags
# Purpose: Verify all Terraform resources comply with Corporate Tagging Policy
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Corporate Tagging Policy Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host ""

# Mandatory tags per Corporate Policy
$mandatoryTags = @(
    "Application",
    "Environment",
    "Owner",
    "CostCenter",
    "BusinessUnit",
    "Country",
    "Criticality"
)

# Valid values per Corporate Policy
$validEnvironments = @("prod", "qa", "dev", "uat", "sandbox")
$validCriticality = @("high", "medium", "low")

# Change to terraform directory
$scriptPath = Split-Path -Parent $PSScriptRoot
Set-Location $scriptPath

Write-Host "Step 1: Validating Terraform configuration..." -ForegroundColor Cyan
Write-Host ""

# Run terraform validate
$validateResult = terraform validate 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Terraform validation failed:" -ForegroundColor Red
    Write-Host $validateResult -ForegroundColor Red
    exit 1
} else {
    Write-Host "✓ Terraform validation passed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 2: Checking tfvars file..." -ForegroundColor Cyan
Write-Host ""

$tfvarsPath = "environments/$Environment/$Environment.tfvars"
if (-not (Test-Path $tfvarsPath)) {
    Write-Host "✗ tfvars file not found: $tfvarsPath" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Found tfvars file: $tfvarsPath" -ForegroundColor Green

# Read tfvars content
$tfvarsContent = Get-Content $tfvarsPath -Raw

Write-Host ""
Write-Host "Step 3: Validating mandatory tags..." -ForegroundColor Cyan
Write-Host ""

$missingTags = @()
foreach ($tag in $mandatoryTags) {
    $tagPattern = "$tag\s*=\s*`"[^`"]+`""
    if ($tfvarsContent -match $tagPattern) {
        Write-Host "  ✓ $tag" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $tag - MISSING" -ForegroundColor Red
        $missingTags += $tag
    }
}

if ($missingTags.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR: Missing mandatory tags:" -ForegroundColor Red
    $missingTags | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

Write-Host ""
Write-Host "Step 4: Validating tag values..." -ForegroundColor Cyan
Write-Host ""

# Validate Environment value
if ($tfvarsContent -match 'environment\s*=\s*"([^"]+)"') {
    $envValue = $matches[1]
    if ($validEnvironments -contains $envValue) {
        Write-Host "  ✓ Environment value '$envValue' is valid" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Environment value '$envValue' is invalid" -ForegroundColor Red
        Write-Host "    Valid values: $($validEnvironments -join ', ')" -ForegroundColor Yellow
        exit 1
    }
}

# Validate Criticality value
if ($tfvarsContent -match 'criticality\s*=\s*"([^"]+)"') {
    $critValue = $matches[1]
    if ($validCriticality -contains $critValue) {
        Write-Host "  ✓ Criticality value '$critValue' is valid" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Criticality value '$critValue' is invalid" -ForegroundColor Red
        Write-Host "    Valid values: $($validCriticality -join ', ')" -ForegroundColor Yellow
        exit 1
    }
}

# Validate CostCenter is not empty
if ($tfvarsContent -match 'cost_center\s*=\s*"([^"]*)"') {
    $costCenter = $matches[1]
    if ($costCenter -and $costCenter -ne "") {
        Write-Host "  ✓ CostCenter is set: '$costCenter'" -ForegroundColor Green
    } else {
        Write-Host "  ✗ CostCenter is empty - MUST be set before deployment" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Step 5: Running terraform plan..." -ForegroundColor Cyan
Write-Host ""

$planResult = terraform plan -var-file="$tfvarsPath" -detailed-exitcode 2>&1
$planExitCode = $LASTEXITCODE

if ($planExitCode -eq 0) {
    Write-Host "✓ No changes needed" -ForegroundColor Green
} elseif ($planExitCode -eq 2) {
    Write-Host "✓ Plan successful (changes detected)" -ForegroundColor Green
} else {
    Write-Host "✗ Plan failed" -ForegroundColor Red
    Write-Host $planResult -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ All mandatory tags present" -ForegroundColor Green
Write-Host "✓ All tag values valid" -ForegroundColor Green
Write-Host "✓ Terraform configuration valid" -ForegroundColor Green
Write-Host ""
Write-Host "Environment '$Environment' is ready for deployment!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review the terraform plan output" -ForegroundColor White
Write-Host "2. Get approval from team lead" -ForegroundColor White
Write-Host "3. Run: terraform apply -var-file=`"$tfvarsPath`"" -ForegroundColor White
Write-Host ""
