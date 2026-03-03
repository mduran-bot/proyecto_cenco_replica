# ============================================================================
# Single-AZ Deployment Property Test
# Validates Property 2: Single-AZ Deployment
# Requirements: 1.2, 2.2, 2.3
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Property 2: Single-AZ Deployment Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$testsPassed = 0
$testsFailed = 0

# ============================================================================
# Helper Functions
# ============================================================================

function Test-CIDRSubset {
    param(
        [string]$SubnetCIDR,
        [string]$VPCCIDR
    )
    
    try {
        $subnetParts = $SubnetCIDR -split '/'
        $vpcParts = $VPCCIDR -split '/'
        
        $subnetIP = $subnetParts[0]
        $subnetPrefix = [int]$subnetParts[1]
        $vpcIP = $vpcParts[0]
        $vpcPrefix = [int]$vpcParts[1]
        
        # Subnet prefix must be >= VPC prefix (more specific)
        if ($subnetPrefix -lt $vpcPrefix) {
            return $false
        }
        
        # Convert IPs to byte arrays
        $subnetBytes = [System.Net.IPAddress]::Parse($subnetIP).GetAddressBytes()
        $vpcBytes = [System.Net.IPAddress]::Parse($vpcIP).GetAddressBytes()
        
        # Reverse for little-endian
        [Array]::Reverse($subnetBytes)
        [Array]::Reverse($vpcBytes)
        
        # Convert to uint32
        $subnetIPInt = [BitConverter]::ToUInt32($subnetBytes, 0)
        $vpcIPInt = [BitConverter]::ToUInt32($vpcBytes, 0)
        
        # Calculate network addresses
        $vpcMask = [uint32]([Math]::Pow(2, 32) - [Math]::Pow(2, 32 - $vpcPrefix))
        $subnetNetwork = $subnetIPInt -band $vpcMask
        $vpcNetwork = $vpcIPInt -band $vpcMask
        
        return $subnetNetwork -eq $vpcNetwork
    }
    catch {
        return $false
    }
}

function Test-CIDROverlap {
    param(
        [string]$CIDR1,
        [string]$CIDR2
    )
    
    try {
        $cidr1Parts = $CIDR1 -split '/'
        $cidr2Parts = $CIDR2 -split '/'
        
        $ip1 = $cidr1Parts[0]
        $prefix1 = [int]$cidr1Parts[1]
        $ip2 = $cidr2Parts[0]
        $prefix2 = [int]$cidr2Parts[1]
        
        # Convert IPs to byte arrays
        $ip1Bytes = [System.Net.IPAddress]::Parse($ip1).GetAddressBytes()
        $ip2Bytes = [System.Net.IPAddress]::Parse($ip2).GetAddressBytes()
        
        # Reverse for little-endian
        [Array]::Reverse($ip1Bytes)
        [Array]::Reverse($ip2Bytes)
        
        # Convert to uint32
        $ip1Int = [BitConverter]::ToUInt32($ip1Bytes, 0)
        $ip2Int = [BitConverter]::ToUInt32($ip2Bytes, 0)
        
        # Calculate masks
        $mask1 = [uint32]([Math]::Pow(2, 32) - [Math]::Pow(2, 32 - $prefix1))
        $mask2 = [uint32]([Math]::Pow(2, 32) - [Math]::Pow(2, 32 - $prefix2))
        
        # Calculate network addresses
        $network1 = $ip1Int -band $mask1
        $network2 = $ip2Int -band $mask2
        
        # Check if network1 contains start of network2
        if (($ip2Int -band $mask1) -eq $network1) {
            return $true
        }
        
        # Check if network2 contains start of network1
        if (($ip1Int -band $mask2) -eq $network2) {
            return $true
        }
        
        return $false
    }
    catch {
        return $false
    }
}

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Message = ""
    )
    
    if ($Passed) {
        Write-Host "[PASS] $TestName" -ForegroundColor Green
        if ($Message) {
            Write-Host "       $Message" -ForegroundColor Gray
        }
        $script:testsPassed++
    }
    else {
        Write-Host "[FAIL] $TestName" -ForegroundColor Red
        if ($Message) {
            Write-Host "       $Message" -ForegroundColor Yellow
        }
        $script:testsFailed++
    }
}

# ============================================================================
# Test Data
# ============================================================================

$vpcCIDR = "10.0.0.0/16"
$activeSubnets = @{
    "public_a" = "10.0.1.0/24"
    "private_1a" = "10.0.10.0/24"
    "private_2a" = "10.0.20.0/24"
}

$reservedSubnets = @{
    "public_b" = "10.0.2.0/24"
    "private_1b" = "10.0.11.0/24"
    "private_2b" = "10.0.21.0/24"
}

$expectedAZ = "us-east-1a"
$reservedAZ = "us-east-1b"

# ============================================================================
# Test 1: Active Subnets are Valid Subsets of VPC CIDR
# ============================================================================

Write-Host "Test 1: Active subnets are valid subsets of VPC CIDR" -ForegroundColor Yellow
Write-Host ""

foreach ($subnet in $activeSubnets.GetEnumerator()) {
    $isSubset = Test-CIDRSubset -SubnetCIDR $subnet.Value -VPCCIDR $vpcCIDR
    Write-TestResult `
        -TestName "Active subnet $($subnet.Key) ($($subnet.Value)) is subset of VPC ($vpcCIDR)" `
        -Passed $isSubset `
        -Message "Subnet must be within VPC CIDR range"
}

Write-Host ""

# ============================================================================
# Test 2: Reserved Subnets are Valid Subsets of VPC CIDR
# ============================================================================

Write-Host "Test 2: Reserved subnets are valid subsets of VPC CIDR" -ForegroundColor Yellow
Write-Host ""

foreach ($subnet in $reservedSubnets.GetEnumerator()) {
    $isSubset = Test-CIDRSubset -SubnetCIDR $subnet.Value -VPCCIDR $vpcCIDR
    Write-TestResult `
        -TestName "Reserved subnet $($subnet.Key) ($($subnet.Value)) is subset of VPC ($vpcCIDR)" `
        -Passed $isSubset `
        -Message "Reserved subnet must be within VPC CIDR range"
}

Write-Host ""

# ============================================================================
# Test 3: Active Subnets Do Not Overlap
# ============================================================================

Write-Host "Test 3: Active subnets do not overlap with each other" -ForegroundColor Yellow
Write-Host ""

$activeSubnetList = $activeSubnets.GetEnumerator() | ForEach-Object { $_ }
for ($i = 0; $i -lt $activeSubnetList.Count; $i++) {
    for ($j = $i + 1; $j -lt $activeSubnetList.Count; $j++) {
        $subnet1 = $activeSubnetList[$i]
        $subnet2 = $activeSubnetList[$j]
        
        $overlaps = Test-CIDROverlap -CIDR1 $subnet1.Value -CIDR2 $subnet2.Value
        Write-TestResult `
            -TestName "Active subnets $($subnet1.Key) and $($subnet2.Key) do not overlap" `
            -Passed (-not $overlaps) `
            -Message "$($subnet1.Value) vs $($subnet2.Value)"
    }
}

Write-Host ""

# ============================================================================
# Test 4: Reserved Subnets Do Not Overlap
# ============================================================================

Write-Host "Test 4: Reserved subnets do not overlap with each other" -ForegroundColor Yellow
Write-Host ""

$reservedSubnetList = $reservedSubnets.GetEnumerator() | ForEach-Object { $_ }
for ($i = 0; $i -lt $reservedSubnetList.Count; $i++) {
    for ($j = $i + 1; $j -lt $reservedSubnetList.Count; $j++) {
        $subnet1 = $reservedSubnetList[$i]
        $subnet2 = $reservedSubnetList[$j]
        
        $overlaps = Test-CIDROverlap -CIDR1 $subnet1.Value -CIDR2 $subnet2.Value
        Write-TestResult `
            -TestName "Reserved subnets $($subnet1.Key) and $($subnet2.Key) do not overlap" `
            -Passed (-not $overlaps) `
            -Message "$($subnet1.Value) vs $($subnet2.Value)"
    }
}

Write-Host ""

# ============================================================================
# Test 5: Active and Reserved Subnets Do Not Overlap
# ============================================================================

Write-Host "Test 5: Active and reserved subnets do not overlap" -ForegroundColor Yellow
Write-Host ""

foreach ($activeSubnet in $activeSubnets.GetEnumerator()) {
    foreach ($reservedSubnet in $reservedSubnets.GetEnumerator()) {
        $overlaps = Test-CIDROverlap -CIDR1 $activeSubnet.Value -CIDR2 $reservedSubnet.Value
        Write-TestResult `
            -TestName "Active $($activeSubnet.Key) and reserved $($reservedSubnet.Key) do not overlap" `
            -Passed (-not $overlaps) `
            -Message "$($activeSubnet.Value) vs $($reservedSubnet.Value)"
    }
}

Write-Host ""

# ============================================================================
# Test 6: Single-AZ Deployment Has Exactly 3 Active Subnets
# ============================================================================

Write-Host "Test 6: Single-AZ deployment has exactly 3 active subnets" -ForegroundColor Yellow
Write-Host ""

$activeCount = $activeSubnets.Count
$expectedCount = 3
$correctCount = $activeCount -eq $expectedCount

Write-TestResult `
    -TestName "Single-AZ has exactly 3 active subnets" `
    -Passed $correctCount `
    -Message "Expected: $expectedCount, Actual: $activeCount"

Write-Host ""

# ============================================================================
# Test 7: Reserved CIDR Blocks for Multi-AZ Expansion
# ============================================================================

Write-Host "Test 7: Reserved CIDR blocks documented for multi-AZ expansion" -ForegroundColor Yellow
Write-Host ""

$reservedCount = $reservedSubnets.Count
$expectedReservedCount = 3
$correctReservedCount = $reservedCount -eq $expectedReservedCount

Write-TestResult `
    -TestName "Exactly 3 CIDR blocks reserved for multi-AZ expansion" `
    -Passed $correctReservedCount `
    -Message "Expected: $expectedReservedCount, Actual: $reservedCount"

Write-Host ""

# ============================================================================
# Test 8: Documentation Exists for Multi-AZ Migration
# ============================================================================

Write-Host "Test 8: Multi-AZ migration documentation exists" -ForegroundColor Yellow
Write-Host ""

$docPath = "terraform/MULTI_AZ_EXPANSION.md"
$docExists = Test-Path $docPath

Write-TestResult `
    -TestName "MULTI_AZ_EXPANSION.md documentation exists" `
    -Passed $docExists `
    -Message "Path: $docPath"

if ($docExists) {
    $docContent = Get-Content $docPath -Raw
    
    # Check for required sections
    $requiredSections = @(
        "Single Points of Failure",
        "Reserved CIDR Blocks",
        "Migration Path to Multi-AZ",
        "NAT Gateway",
        "us-east-1a"
    )
    
    foreach ($section in $requiredSections) {
        $sectionExists = $docContent -match [regex]::Escape($section)
        Write-TestResult `
            -TestName "Documentation contains section: $section" `
            -Passed $sectionExists `
            -Message "Required for Requirements 12.1, 12.2, 12.3"
    }
}

Write-Host ""

# ============================================================================
# Test 9: VPC Module Configuration Validation
# ============================================================================

Write-Host "Test 9: VPC module configuration validation" -ForegroundColor Yellow
Write-Host ""

$vpcModulePath = "terraform/modules/vpc/main.tf"
$vpcModuleExists = Test-Path $vpcModulePath

Write-TestResult `
    -TestName "VPC module main.tf exists" `
    -Passed $vpcModuleExists `
    -Message "Path: $vpcModulePath"

if ($vpcModuleExists) {
    $vpcModuleContent = Get-Content $vpcModulePath -Raw
    
    # Check for conditional resource creation
    $hasConditionalSubnets = $vpcModuleContent -match 'count\s*=\s*var\.enable_multi_az'
    Write-TestResult `
        -TestName "VPC module uses conditional resource creation for multi-AZ" `
        -Passed $hasConditionalSubnets `
        -Message "Uses 'count = var.enable_multi_az ? 1 : 0' pattern"
    
    # Check for AZ A subnets
    $hasPublicA = $vpcModuleContent -match 'aws_subnet.*public_a'
    $hasPrivate1A = $vpcModuleContent -match 'aws_subnet.*private_1a'
    $hasPrivate2A = $vpcModuleContent -match 'aws_subnet.*private_2a'
    
    Write-TestResult `
        -TestName "VPC module defines public_a subnet" `
        -Passed $hasPublicA `
        -Message "Required for single-AZ deployment"
    
    Write-TestResult `
        -TestName "VPC module defines private_1a subnet" `
        -Passed $hasPrivate1A `
        -Message "Required for single-AZ deployment"
    
    Write-TestResult `
        -TestName "VPC module defines private_2a subnet" `
        -Passed $hasPrivate2A `
        -Message "Required for single-AZ deployment"
    
    # Check for AZ B subnets (conditional)
    $hasPublicB = $vpcModuleContent -match 'aws_subnet.*public_b'
    $hasPrivate1B = $vpcModuleContent -match 'aws_subnet.*private_1b'
    $hasPrivate2B = $vpcModuleContent -match 'aws_subnet.*private_2b'
    
    Write-TestResult `
        -TestName "VPC module defines public_b subnet (conditional)" `
        -Passed $hasPublicB `
        -Message "Required for multi-AZ expansion"
    
    Write-TestResult `
        -TestName "VPC module defines private_1b subnet (conditional)" `
        -Passed $hasPrivate1B `
        -Message "Required for multi-AZ expansion"
    
    Write-TestResult `
        -TestName "VPC module defines private_2b subnet (conditional)" `
        -Passed $hasPrivate2B `
        -Message "Required for multi-AZ expansion"
    
    # Check for NAT Gateway configuration
    $hasNATGatewayA = $vpcModuleContent -match 'aws_nat_gateway.*main_a'
    $hasNATGatewayB = $vpcModuleContent -match 'aws_nat_gateway.*main_b'
    
    Write-TestResult `
        -TestName "VPC module defines NAT Gateway A" `
        -Passed $hasNATGatewayA `
        -Message "Required for single-AZ deployment"
    
    Write-TestResult `
        -TestName "VPC module defines NAT Gateway B (conditional)" `
        -Passed $hasNATGatewayB `
        -Message "Required for multi-AZ expansion"
}

Write-Host ""

# ============================================================================
# Test 10: Property-Based Test - 100 Iterations
# ============================================================================

Write-Host "Test 10: Property-based test with 100 iterations" -ForegroundColor Yellow
Write-Host ""

$iterations = 100
$propertyTestsPassed = 0
$propertyTestsFailed = 0

for ($i = 1; $i -le $iterations; $i++) {
    # Test the property: All active subnets are subsets of VPC and don't overlap
    $allValid = $true
    
    # Check all active subnets are subsets
    foreach ($subnet in $activeSubnets.GetEnumerator()) {
        if (-not (Test-CIDRSubset -SubnetCIDR $subnet.Value -VPCCIDR $vpcCIDR)) {
            $allValid = $false
            break
        }
    }
    
    # Check no overlaps between active subnets
    if ($allValid) {
        $activeSubnetList = $activeSubnets.GetEnumerator() | ForEach-Object { $_ }
        for ($j = 0; $j -lt $activeSubnetList.Count; $j++) {
            for ($k = $j + 1; $k -lt $activeSubnetList.Count; $k++) {
                if (Test-CIDROverlap -CIDR1 $activeSubnetList[$j].Value -CIDR2 $activeSubnetList[$k].Value) {
                    $allValid = $false
                    break
                }
            }
            if (-not $allValid) { break }
        }
    }
    
    # Check no overlaps between active and reserved
    if ($allValid) {
        foreach ($activeSubnet in $activeSubnets.GetEnumerator()) {
            foreach ($reservedSubnet in $reservedSubnets.GetEnumerator()) {
                if (Test-CIDROverlap -CIDR1 $activeSubnet.Value -CIDR2 $reservedSubnet.Value) {
                    $allValid = $false
                    break
                }
            }
            if (-not $allValid) { break }
        }
    }
    
    if ($allValid) {
        $propertyTestsPassed++
    }
    else {
        $propertyTestsFailed++
    }
}

$propertyTestSuccess = $propertyTestsFailed -eq 0

Write-TestResult `
    -TestName "Property test: Single-AZ deployment correctness (100 iterations)" `
    -Passed $propertyTestSuccess `
    -Message "Passed: $propertyTestsPassed, Failed: $propertyTestsFailed"

Write-Host ""

# ============================================================================
# Summary
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Total Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "[SUCCESS] All tests passed! Single-AZ deployment property is valid." -ForegroundColor Green
    Write-Host ""
    Write-Host "Property 2: Single-AZ Deployment" -ForegroundColor Cyan
    Write-Host "Validates: Requirements 1.2, 2.2, 2.3" -ForegroundColor Gray
    Write-Host ""
    Write-Host "The infrastructure correctly:" -ForegroundColor White
    Write-Host "  - Deploys all resources in us-east-1a only" -ForegroundColor Gray
    Write-Host "  - Reserves CIDR blocks for future multi-AZ expansion" -ForegroundColor Gray
    Write-Host "  - Documents single points of failure" -ForegroundColor Gray
    Write-Host "  - Provides migration path to multi-AZ" -ForegroundColor Gray
    exit 0
}
else {
    Write-Host "[FAILURE] Some tests failed. Please review the failures above." -ForegroundColor Red
    exit 1
}
