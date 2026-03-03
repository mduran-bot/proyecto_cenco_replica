# PowerShell script to validate VPC CIDR configuration
# This script validates Property 1: VPC CIDR Block Validity
# Validates: Requirements 1.1

param(
    [string]$VpcCidr = "10.0.0.0/16"
)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "VPC CIDR Validation Test" -ForegroundColor Cyan
Write-Host "Property 1: VPC CIDR Block Validity" -ForegroundColor Cyan
Write-Host "Validates: Requirements 1.1" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

function Test-VpcCidr {
    param([string]$Cidr)
    
    Write-Host "Testing CIDR: $Cidr" -ForegroundColor Yellow
    
    # Parse CIDR block
    if ($Cidr -notmatch '^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$') {
        Write-Host "  [FAIL] Invalid CIDR format" -ForegroundColor Red
        return $false
    }
    
    $parts = $Cidr -split '/'
    $ipAddress = $parts[0]
    $prefixLength = [int]$parts[1]
    
    # Validate IP address octets
    $octets = $ipAddress -split '\.'
    foreach ($octet in $octets) {
        $octetInt = [int]$octet
        if ($octetInt -lt 0 -or $octetInt -gt 255) {
            Write-Host "  [FAIL] Invalid IP address octet: $octet" -ForegroundColor Red
            return $false
        }
    }
    
    Write-Host "  [PASS] Valid IPv4 CIDR format" -ForegroundColor Green
    
    # Validate prefix length
    if ($prefixLength -lt 0 -or $prefixLength -gt 32) {
        Write-Host "  [FAIL] Invalid prefix length: $prefixLength (must be 0-32)" -ForegroundColor Red
        return $false
    }
    
    Write-Host "  [PASS] Valid prefix length: /$prefixLength" -ForegroundColor Green
    
    # Calculate total IP addresses
    $totalIps = [Math]::Pow(2, (32 - $prefixLength))
    Write-Host "  [INFO] Total IP addresses: $totalIps" -ForegroundColor Cyan
    
    # Verify exactly 65,536 IPs (requirement for /16)
    $expectedIps = 65536
    if ($totalIps -ne $expectedIps) {
        Write-Host "  [FAIL] Expected $expectedIps IPs, got $totalIps" -ForegroundColor Red
        Write-Host "  [INFO] For 65,536 IPs, use /16 prefix" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "  [PASS] Provides exactly 65,536 IP addresses" -ForegroundColor Green
    
    # Verify it's a /16 network
    if ($prefixLength -ne 16) {
        Write-Host "  [FAIL] Expected /16 prefix, got /$prefixLength" -ForegroundColor Red
        return $false
    }
    
    Write-Host "  [PASS] Correct /16 prefix length" -ForegroundColor Green
    
    return $true
}

# Test valid CIDR blocks
Write-Host "Testing Valid CIDR Blocks:" -ForegroundColor Cyan
Write-Host "----------------------------" -ForegroundColor Cyan

$validCidrs = @(
    "10.0.0.0/16",
    "172.16.0.0/16",
    "192.168.0.0/16",
    "10.1.0.0/16",
    "10.10.0.0/16"
)

$passCount = 0
$failCount = 0

foreach ($cidr in $validCidrs) {
    if (Test-VpcCidr -Cidr $cidr) {
        $passCount++
    } else {
        $failCount++
    }
    Write-Host ""
}

# Test invalid CIDR blocks
Write-Host "Testing Invalid CIDR Blocks:" -ForegroundColor Cyan
Write-Host "-----------------------------" -ForegroundColor Cyan

$invalidCidrs = @(
    @{Cidr="10.0.0.0/24"; Reason="Wrong prefix (256 IPs)"},
    @{Cidr="10.0.0.0/8"; Reason="Wrong prefix (16M IPs)"},
    @{Cidr="10.0.0.0"; Reason="Missing prefix"},
    @{Cidr="999.999.999.999/16"; Reason="Invalid IP"},
    @{Cidr="10.0.0.0/33"; Reason="Invalid prefix"}
)

foreach ($testCase in $invalidCidrs) {
    Write-Host "Testing: $($testCase.Cidr) - Expected to fail ($($testCase.Reason))" -ForegroundColor Yellow
    $result = Test-VpcCidr -Cidr $testCase.Cidr
    if (-not $result) {
        Write-Host "  [EXPECTED] Correctly rejected invalid CIDR" -ForegroundColor Green
        $passCount++
    } else {
        Write-Host "  [UNEXPECTED] Invalid CIDR was accepted!" -ForegroundColor Red
        $failCount++
    }
    Write-Host ""
}

# Summary
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Total Tests: $($passCount + $failCount)" -ForegroundColor White
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed!" -ForegroundColor Red
    exit 1
}
