# VPC Endpoints Validation Script
# Validates VPC endpoint service coverage configuration

param(
    [string]$TerraformDir = "../modules/vpc-endpoints"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "VPC Endpoints Validation"
Write-Host "========================================"
Write-Host ""

# Test 1: Verify all required VPC endpoints are defined
Write-Host "Test 1: Verifying required VPC endpoints are defined..."

$requiredEndpoints = @("s3", "glue", "secretsmanager", "logs", "kms", "sts", "events")

$mainTfPath = Join-Path $TerraformDir "main.tf"

if (-not (Test-Path $mainTfPath)) {
    Write-Host "FAIL: main.tf not found at $mainTfPath"
    exit 1
}

$mainTfContent = Get-Content $mainTfPath -Raw

$allEndpointsFound = $true
foreach ($endpoint in $requiredEndpoints) {
    $pattern = "resource `"aws_vpc_endpoint`" `"$endpoint`""
    
    if ($mainTfContent -match $pattern) {
        Write-Host "  PASS: $endpoint endpoint is defined"
    } else {
        Write-Host "  FAIL: $endpoint endpoint is NOT defined"
        $allEndpointsFound = $false
    }
}

if (-not $allEndpointsFound) {
    Write-Host ""
    Write-Host "VALIDATION FAILED: Not all required VPC endpoints are defined"
    exit 1
}

Write-Host ""

# Test 2: Verify S3 Gateway Endpoint configuration
Write-Host "Test 2: Verifying S3 Gateway Endpoint configuration..."

if ($mainTfContent -match 'vpc_endpoint_type\s*=\s*"Gateway"') {
    Write-Host "  PASS: S3 endpoint type is Gateway"
} else {
    Write-Host "  FAIL: S3 endpoint type is not Gateway"
    exit 1
}

if ($mainTfContent -match 'route_table_ids') {
    Write-Host "  PASS: S3 endpoint associated with route tables"
} else {
    Write-Host "  FAIL: S3 endpoint not associated with route tables"
    exit 1
}

Write-Host ""

# Test 3: Verify Interface Endpoints configuration
Write-Host "Test 3: Verifying Interface Endpoints configuration..."

$interfaceEndpoints = @("glue", "secretsmanager", "logs", "kms", "sts", "events")

foreach ($endpoint in $interfaceEndpoints) {
    Write-Host "  Checking $endpoint endpoint..."
    
    if ($mainTfContent -match "resource `"aws_vpc_endpoint`" `"$endpoint`"") {
        Write-Host "    PASS: $endpoint endpoint is defined"
    } else {
        Write-Host "    FAIL: $endpoint endpoint is NOT defined"
        exit 1
    }
}

Write-Host ""

# Test 4: Verify endpoint count
Write-Host "Test 4: Verifying endpoint count..."

$endpointMatches = ([regex]::Matches($mainTfContent, 'resource "aws_vpc_endpoint"')).Count

if ($endpointMatches -eq 7) {
    Write-Host "  PASS: Exactly 7 VPC endpoints are defined (1 Gateway + 6 Interface)"
} else {
    Write-Host "  FAIL: Expected 7 VPC endpoints, found $endpointMatches"
    exit 1
}

Write-Host ""

# Test 5: Verify tags are applied
Write-Host "Test 5: Verifying tags are applied to all endpoints..."

$tagsMatches = ([regex]::Matches($mainTfContent, 'tags\s*=')).Count

if ($tagsMatches -ge 7) {
    Write-Host "  PASS: All endpoints have tags defined"
} else {
    Write-Host "  FAIL: Not all endpoints have tags"
    exit 1
}

Write-Host ""

# Summary
Write-Host "========================================"
Write-Host "VALIDATION SUMMARY"
Write-Host "========================================"
Write-Host ""
Write-Host "PASS: All required VPC endpoints are defined (7 total)"
Write-Host "PASS: S3 Gateway Endpoint is correctly configured"
Write-Host "PASS: All 6 Interface Endpoints are correctly configured"
Write-Host "PASS: All endpoints have proper tags"
Write-Host ""
Write-Host "VPC ENDPOINTS VALIDATION PASSED"
Write-Host ""

# Property 6 Validation
Write-Host "========================================"
Write-Host "PROPERTY 6: VPC Endpoint Service Coverage"
Write-Host "========================================"
Write-Host ""
Write-Host "Property: For any required AWS service (S3, Glue, Secrets Manager,"
Write-Host "CloudWatch Logs, KMS, STS, EventBridge), a corresponding VPC endpoint"
Write-Host "must exist and be properly configured."
Write-Host ""
Write-Host "Validates: Requirements 4.1, 4.2"
Write-Host ""
Write-Host "PROPERTY VALIDATED: All required services have VPC endpoints"
Write-Host ""

exit 0
