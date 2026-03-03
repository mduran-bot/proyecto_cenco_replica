# ============================================================================
# Property Test: Subnet CIDR Non-Overlap
# Feature: aws-infrastructure, Property 3: Subnet CIDR Non-Overlap
# Validates: Requirements 2.1, 2.2
#
# Property: For any pair of subnets within the VPC, their CIDR blocks must not
# overlap and must be valid subsets of the VPC CIDR block (10.0.0.0/16).
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Property Test: Subnet CIDR Non-Overlap" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to convert CIDR to IP range
function Get-IPRange {
    param (
        [string]$CIDR
    )
    
    try {
        $parts = $CIDR -split '/'
        if ($parts.Count -ne 2) {
            return $null
        }
        
        $ip = $parts[0]
        $prefix = [int]$parts[1]
        
        # Validate IP address
        $ipBytes = [System.Net.IPAddress]::Parse($ip).GetAddressBytes()
        if ($ipBytes.Count -ne 4) {
            return $null
        }
        
        # Calculate network address
        $ipInt = [BitConverter]::ToUInt32($ipBytes[3..0], 0)
        $maskInt = [UInt32]([Math]::Pow(2, 32) - [Math]::Pow(2, 32 - $prefix))
        $networkInt = $ipInt -band $maskInt
        
        # Calculate broadcast address
        $broadcastInt = $networkInt -bor (-bnot $maskInt)
        
        # Calculate total IPs
        $totalIPs = [Math]::Pow(2, 32 - $prefix)
        
        return @{
            CIDR = $CIDR
            NetworkInt = $networkInt
            BroadcastInt = $broadcastInt
            Prefix = $prefix
            TotalIPs = $totalIPs
            Valid = $true
        }
    }
    catch {
        return @{
            CIDR = $CIDR
            Valid = $false
        }
    }
}

# Function to check if two CIDR blocks overlap
function Test-CIDROverlap {
    param (
        [hashtable]$Range1,
        [hashtable]$Range2
    )
    
    if (-not $Range1.Valid -or -not $Range2.Valid) {
        return $false
    }
    
    # Check if Range1 contains the start of Range2
    if ($Range1.NetworkInt -le $Range2.NetworkInt -and $Range2.NetworkInt -le $Range1.BroadcastInt) {
        return $true
    }
    
    # Check if Range2 contains the start of Range1
    if ($Range2.NetworkInt -le $Range1.NetworkInt -and $Range1.NetworkInt -le $Range2.BroadcastInt) {
        return $true
    }
    
    return $false
}

# Function to check if subnet is a valid subset of VPC
function Test-SubnetIsSubsetOfVPC {
    param (
        [hashtable]$Subnet,
        [hashtable]$VPC
    )
    
    if (-not $Subnet.Valid -or -not $VPC.Valid) {
        return $false
    }
    
    # Subnet must have more specific mask (larger prefix) than VPC
    if ($Subnet.Prefix -lt $VPC.Prefix) {
        return $false
    }
    
    # Subnet network address must be within VPC range
    if ($Subnet.NetworkInt -lt $VPC.NetworkInt -or $Subnet.NetworkInt -gt $VPC.BroadcastInt) {
        return $false
    }
    
    # Subnet broadcast address must be within VPC range
    if ($Subnet.BroadcastInt -lt $VPC.NetworkInt -or $Subnet.BroadcastInt -gt $VPC.BroadcastInt) {
        return $false
    }
    
    return $true
}

# Test counter
$testsPassed = 0
$testsFailed = 0

# ============================================================================
# Test Case 1: Single-AZ Configuration (Current Deployment)
# ============================================================================

Write-Host "Test Case 1: Single-AZ Configuration (Current Deployment)" -ForegroundColor Yellow
Write-Host "Testing: VPC 10.0.0.0/16 with 3 non-overlapping subnets" -ForegroundColor Gray

$vpcCIDR = "10.0.0.0/16"
$subnets = @(
    "10.0.1.0/24",   # Public Subnet A
    "10.0.10.0/24",  # Private Subnet 1A
    "10.0.20.0/24"   # Private Subnet 2A
)

$vpcRange = Get-IPRange -CIDR $vpcCIDR
$subnetRanges = @()

# Validate VPC CIDR
if ($vpcRange.Valid -and $vpcRange.Prefix -eq 16) {
    Write-Host "  [PASS] VPC CIDR $vpcCIDR is valid /16" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] VPC CIDR $vpcCIDR is invalid" -ForegroundColor Red
    $testsFailed++
}

# Validate each subnet is a subset of VPC
foreach ($subnet in $subnets) {
    $subnetRange = Get-IPRange -CIDR $subnet
    $subnetRanges += $subnetRange
    
    if (Test-SubnetIsSubsetOfVPC -Subnet $subnetRange -VPC $vpcRange) {
        Write-Host "  [PASS] Subnet $subnet is a valid subset of VPC" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  [FAIL] Subnet $subnet is NOT a valid subset of VPC" -ForegroundColor Red
        $testsFailed++
    }
}

# Check for overlaps between subnets
$overlapFound = $false
for ($i = 0; $i -lt $subnetRanges.Count; $i++) {
    for ($j = $i + 1; $j -lt $subnetRanges.Count; $j++) {
        if (Test-CIDROverlap -Range1 $subnetRanges[$i] -Range2 $subnetRanges[$j]) {
            Write-Host "  [FAIL] Overlap detected: $($subnetRanges[$i].CIDR) and $($subnetRanges[$j].CIDR)" -ForegroundColor Red
            $testsFailed++
            $overlapFound = $true
        }
    }
}

if (-not $overlapFound) {
    Write-Host "  [PASS] No overlaps detected between subnets" -ForegroundColor Green
    $testsPassed++
}

Write-Host ""

# ============================================================================
# Test Case 2: Multi-AZ Configuration (Future Expansion)
# ============================================================================

Write-Host "Test Case 2: Multi-AZ Configuration (Future Expansion)" -ForegroundColor Yellow
Write-Host "Testing: VPC 10.0.0.0/16 with 6 non-overlapping subnets" -ForegroundColor Gray

$vpcCIDR = "10.0.0.0/16"
$subnets = @(
    "10.0.1.0/24",   # Public Subnet A
    "10.0.10.0/24",  # Private Subnet 1A
    "10.0.20.0/24",  # Private Subnet 2A
    "10.0.2.0/24",   # Public Subnet B (reserved)
    "10.0.11.0/24",  # Private Subnet 1B (reserved)
    "10.0.21.0/24"   # Private Subnet 2B (reserved)
)

$vpcRange = Get-IPRange -CIDR $vpcCIDR
$subnetRanges = @()

# Validate VPC CIDR
if ($vpcRange.Valid -and $vpcRange.Prefix -eq 16) {
    Write-Host "  [PASS] VPC CIDR $vpcCIDR is valid /16" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] VPC CIDR $vpcCIDR is invalid" -ForegroundColor Red
    $testsFailed++
}

# Validate each subnet is a subset of VPC
foreach ($subnet in $subnets) {
    $subnetRange = Get-IPRange -CIDR $subnet
    $subnetRanges += $subnetRange
    
    if (Test-SubnetIsSubsetOfVPC -Subnet $subnetRange -VPC $vpcRange) {
        Write-Host "  [PASS] Subnet $subnet is a valid subset of VPC" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  [FAIL] Subnet $subnet is NOT a valid subset of VPC" -ForegroundColor Red
        $testsFailed++
    }
}

# Check for overlaps between subnets
$overlapFound = $false
for ($i = 0; $i -lt $subnetRanges.Count; $i++) {
    for ($j = $i + 1; $j -lt $subnetRanges.Count; $j++) {
        if (Test-CIDROverlap -Range1 $subnetRanges[$i] -Range2 $subnetRanges[$j]) {
            Write-Host "  [FAIL] Overlap detected: $($subnetRanges[$i].CIDR) and $($subnetRanges[$j].CIDR)" -ForegroundColor Red
            $testsFailed++
            $overlapFound = $true
        }
    }
}

if (-not $overlapFound) {
    Write-Host "  [PASS] No overlaps detected between subnets" -ForegroundColor Green
    $testsPassed++
}

Write-Host ""

# ============================================================================
# Test Case 3: Alternative VPC CIDR with Non-Overlapping Subnets
# ============================================================================

Write-Host "Test Case 3: Alternative VPC CIDR (172.16.0.0/16)" -ForegroundColor Yellow
Write-Host "Testing: Alternative VPC with non-overlapping subnets" -ForegroundColor Gray

$vpcCIDR = "172.16.0.0/16"
$subnets = @(
    "172.16.1.0/24",
    "172.16.10.0/24",
    "172.16.20.0/24"
)

$vpcRange = Get-IPRange -CIDR $vpcCIDR
$subnetRanges = @()

# Validate VPC CIDR
if ($vpcRange.Valid -and $vpcRange.Prefix -eq 16) {
    Write-Host "  [PASS] VPC CIDR $vpcCIDR is valid /16" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] VPC CIDR $vpcCIDR is invalid" -ForegroundColor Red
    $testsFailed++
}

# Validate each subnet is a subset of VPC
foreach ($subnet in $subnets) {
    $subnetRange = Get-IPRange -CIDR $subnet
    $subnetRanges += $subnetRange
    
    if (Test-SubnetIsSubsetOfVPC -Subnet $subnetRange -VPC $vpcRange) {
        Write-Host "  [PASS] Subnet $subnet is a valid subset of VPC" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  [FAIL] Subnet $subnet is NOT a valid subset of VPC" -ForegroundColor Red
        $testsFailed++
    }
}

# Check for overlaps between subnets
$overlapFound = $false
for ($i = 0; $i -lt $subnetRanges.Count; $i++) {
    for ($j = $i + 1; $j -lt $subnetRanges.Count; $j++) {
        if (Test-CIDROverlap -Range1 $subnetRanges[$i] -Range2 $subnetRanges[$j]) {
            Write-Host "  [FAIL] Overlap detected: $($subnetRanges[$i].CIDR) and $($subnetRanges[$j].CIDR)" -ForegroundColor Red
            $testsFailed++
            $overlapFound = $true
        }
    }
}

if (-not $overlapFound) {
    Write-Host "  [PASS] No overlaps detected between subnets" -ForegroundColor Green
    $testsPassed++
}

Write-Host ""

# ============================================================================
# Test Case 4: Detect Overlapping Subnets (Negative Test)
# ============================================================================

Write-Host "Test Case 4: Overlapping Subnets Detection (Negative Test)" -ForegroundColor Yellow
Write-Host "Testing: Overlapping subnet detection" -ForegroundColor Gray

$testName1 = "Identical CIDRs"
$range1 = Get-IPRange -CIDR "10.0.1.0/24"
$range2 = Get-IPRange -CIDR "10.0.1.0/24"
$overlaps = Test-CIDROverlap -Range1 $range1 -Range2 $range2
if ($overlaps -eq $true) {
    Write-Host "  [PASS] $testName1 : Correctly detected overlap=True" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] $testName1 : Expected overlap=True, got False" -ForegroundColor Red
    $testsFailed++
}

$testName2 = "Subset CIDR"
$range1 = Get-IPRange -CIDR "10.0.0.0/16"
$range2 = Get-IPRange -CIDR "10.0.1.0/24"
$overlaps = Test-CIDROverlap -Range1 $range1 -Range2 $range2
if ($overlaps -eq $true) {
    Write-Host "  [PASS] $testName2 : Correctly detected overlap=True" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] $testName2 : Expected overlap=True, got False" -ForegroundColor Red
    $testsFailed++
}

$testName3 = "Non-overlapping adjacent"
$range1 = Get-IPRange -CIDR "10.0.1.0/24"
$range2 = Get-IPRange -CIDR "10.0.2.0/24"
$overlaps = Test-CIDROverlap -Range1 $range1 -Range2 $range2
if ($overlaps -eq $false) {
    Write-Host "  [PASS] $testName3 : Correctly detected overlap=False" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] $testName3 : Expected overlap=False, got True" -ForegroundColor Red
    $testsFailed++
}

$testName4 = "Non-overlapping distant"
$range1 = Get-IPRange -CIDR "10.0.1.0/24"
$range2 = Get-IPRange -CIDR "10.0.10.0/24"
$overlaps = Test-CIDROverlap -Range1 $range1 -Range2 $range2
if ($overlaps -eq $false) {
    Write-Host "  [PASS] $testName4 : Correctly detected overlap=False" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] $testName4 : Expected overlap=False, got True" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# ============================================================================
# Test Case 5: Subnet Outside VPC Range (Negative Test)
# ============================================================================

Write-Host "Test Case 5: Subnet Outside VPC Range (Negative Test)" -ForegroundColor Yellow
Write-Host "Testing: Subnet must be within VPC range" -ForegroundColor Gray

$vpcRange = Get-IPRange -CIDR "10.0.0.0/16"

$testName1 = "Outside VPC range"
$subnetRange = Get-IPRange -CIDR "10.1.0.0/24"
$isSubset = Test-SubnetIsSubsetOfVPC -Subnet $subnetRange -VPC $vpcRange
if (-not $isSubset) {
    Write-Host "  [PASS] Correctly rejected 10.1.0.0/24: $testName1" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] Incorrectly accepted 10.1.0.0/24: $testName1" -ForegroundColor Red
    $testsFailed++
}

$testName2 = "Different network"
$subnetRange = Get-IPRange -CIDR "192.168.1.0/24"
$isSubset = Test-SubnetIsSubsetOfVPC -Subnet $subnetRange -VPC $vpcRange
if (-not $isSubset) {
    Write-Host "  [PASS] Correctly rejected 192.168.1.0/24: $testName2" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] Incorrectly accepted 192.168.1.0/24: $testName2" -ForegroundColor Red
    $testsFailed++
}

$testName3 = "Less specific than VPC"
$subnetRange = Get-IPRange -CIDR "10.0.0.0/8"
$isSubset = Test-SubnetIsSubsetOfVPC -Subnet $subnetRange -VPC $vpcRange
if (-not $isSubset) {
    Write-Host "  [PASS] Correctly rejected 10.0.0.0/8: $testName3" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [FAIL] Incorrectly accepted 10.0.0.0/8: $testName3" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# ============================================================================
# Test Summary
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor White
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "[SUCCESS] All property tests PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Property 3 validated:" -ForegroundColor Cyan
    Write-Host "  - All subnets are valid subsets of VPC CIDR" -ForegroundColor Gray
    Write-Host "  - No subnet CIDR blocks overlap" -ForegroundColor Gray
    Write-Host "  - Both single-AZ and multi-AZ configurations are valid" -ForegroundColor Gray
    Write-Host "  - Overlap detection works correctly" -ForegroundColor Gray
    Write-Host "  - Invalid subnet configurations are properly rejected" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "[FAILURE] Some property tests FAILED" -ForegroundColor Red
    exit 1
}
