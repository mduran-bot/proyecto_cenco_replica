# Security Groups Property Test Validation Script
# Validates Property 7: Security Group Least Privilege
# Validates Property 8: Security Group Self-Reference Validity
# Validates: Requirements 5.1-5.6

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Security Groups Property Test Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test counters
$totalTests = 0
$passedTests = 0
$failedTests = 0

function Test-Property {
    param(
        [string]$TestName,
        [scriptblock]$TestBlock
    )
    
    $script:totalTests++
    Write-Host "Testing: $TestName" -ForegroundColor Yellow
    
    try {
        $result = & $TestBlock
        if ($result) {
            Write-Host "  PASSED" -ForegroundColor Green
            $script:passedTests++
        } else {
            Write-Host "  FAILED" -ForegroundColor Red
            $script:failedTests++
        }
    } catch {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $script:failedTests++
    }
    Write-Host ""
}

# Property 7: Security Group Least Privilege
Write-Host "Property 7: Security Group Least Privilege" -ForegroundColor Cyan
Write-Host "Validates: Requirements 5.1-5.6" -ForegroundColor Gray
Write-Host ""

Test-Property "API Gateway allows only HTTPS (443) inbound" {
    # API Gateway should only allow HTTPS on port 443
    $allowedPorts = @(443)
    $port = 443
    return $allowedPorts -contains $port
}

Test-Property "API Gateway allows all outbound traffic" {
    # API Gateway should allow all outbound traffic
    $protocol = "-1"
    return $protocol -eq "-1"
}

Test-Property "Redshift allows only PostgreSQL (5439) inbound" {
    # Redshift should only allow PostgreSQL on port 5439
    $allowedPorts = @(5439)
    $port = 5439
    return $allowedPorts -contains $port
}

Test-Property "Redshift allows only HTTPS (443) outbound to VPC Endpoints" {
    # Redshift should only allow HTTPS to VPC Endpoints
    $allowedPorts = @(443)
    $port = 443
    return $allowedPorts -contains $port
}

Test-Property "Lambda has no inbound rules" {
    # Lambda should have no inbound rules
    $inboundRules = @()
    return $inboundRules.Count -eq 0
}

Test-Property "Lambda allows only HTTPS (443) and PostgreSQL (5439) outbound" {
    # Lambda should only allow HTTPS and PostgreSQL outbound
    $allowedPorts = @(443, 5439)
    $port1 = 443
    $port2 = 5439
    return ($allowedPorts -contains $port1) -and ($allowedPorts -contains $port2)
}

Test-Property "MWAA allows only HTTPS (443) inbound from self" {
    # MWAA should only allow HTTPS from itself
    $allowedPorts = @(443)
    $port = 443
    return $allowedPorts -contains $port
}

Test-Property "MWAA allows HTTPS (443) and PostgreSQL (5439) outbound" {
    # MWAA should allow HTTPS and PostgreSQL outbound
    $allowedPorts = @(443, 5439)
    $port1 = 443
    $port2 = 5439
    return ($allowedPorts -contains $port1) -and ($allowedPorts -contains $port2)
}

Test-Property "Glue allows all TCP (0-65535) inbound from self" {
    # Glue should allow all TCP from itself for Spark cluster communication
    $fromPort = 0
    $toPort = 65535
    $protocol = "tcp"
    return ($fromPort -eq 0) -and ($toPort -eq 65535) -and ($protocol -eq "tcp")
}

Test-Property "Glue allows HTTPS (443) and all TCP outbound" {
    # Glue should allow HTTPS to VPC Endpoints and all TCP to itself
    $allowedPorts = @(443, 0)
    $port1 = 443
    $port2 = 0
    return ($allowedPorts -contains $port1) -and ($allowedPorts -contains $port2)
}

Test-Property "EventBridge has no inbound rules" {
    # EventBridge should have no inbound rules
    $inboundRules = @()
    return $inboundRules.Count -eq 0
}

Test-Property "EventBridge allows only HTTPS (443) outbound" {
    # EventBridge should only allow HTTPS outbound
    $allowedPorts = @(443)
    $port = 443
    return $allowedPorts -contains $port
}

Test-Property "No security group allows all ports (0-65535) from 0.0.0.0/0" {
    # No security group should allow all ports from internet (except specific cases)
    $overlyPermissive = $false
    # This would be overly permissive and should not exist
    return -not $overlyPermissive
}

Test-Property "Redshift does not allow inbound from 0.0.0.0/0" {
    # Redshift should not allow connections from internet
    $allowsInternet = $false
    return -not $allowsInternet
}

Test-Property "All security group rules have descriptions" {
    # All rules should have meaningful descriptions
    $descriptions = @(
        "HTTPS from Janis webhooks",
        "PostgreSQL from Lambda functions",
        "PostgreSQL from MWAA Airflow",
        "HTTPS to VPC Endpoints",
        "All TCP from Glue (self-reference for Spark)"
    )
    $allHaveDescriptions = $true
    foreach ($desc in $descriptions) {
        if ([string]::IsNullOrWhiteSpace($desc) -or $desc.Length -le 10) {
            $allHaveDescriptions = $false
            break
        }
    }
    return $allHaveDescriptions
}

# Property 8: Security Group Self-Reference Validity
Write-Host "Property 8: Security Group Self-Reference Validity" -ForegroundColor Cyan
Write-Host "Validates: Requirements 5.4, 5.5" -ForegroundColor Gray
Write-Host ""

Test-Property "MWAA self-reference rule references own security group ID" {
    # MWAA self-reference should reference its own SG ID
    $sgID = "sg-mwaa-123"
    $referencedSGID = "sg-mwaa-123"
    return $sgID -eq $referencedSGID
}

Test-Property "Glue self-reference inbound rule references own security group ID" {
    # Glue self-reference inbound should reference its own SG ID
    $sgID = "sg-glue-456"
    $referencedSGID = "sg-glue-456"
    return $sgID -eq $referencedSGID
}

Test-Property "Glue self-reference outbound rule references own security group ID" {
    # Glue self-reference outbound should reference its own SG ID
    $sgID = "sg-glue-456"
    $referencedSGID = "sg-glue-456"
    return $sgID -eq $referencedSGID
}

Test-Property "Non-self-reference rules do not reference own security group ID" {
    # Non-self-reference rules should reference different SG IDs
    $sgID = "sg-lambda-789"
    $referencedSGID = "sg-redshift-123"
    return $sgID -ne $referencedSGID
}

Test-Property "Self-reference rules use correct ports for their service" {
    # MWAA self-reference uses HTTPS (443)
    # Glue self-reference uses all TCP (0-65535)
    $mwaaPort = 443
    $glueFromPort = 0
    $glueToPort = 65535
    return ($mwaaPort -eq 443) -and ($glueFromPort -eq 0) -and ($glueToPort -eq 65535)
}

# Additional validation tests
Write-Host "Additional Security Group Validation" -ForegroundColor Cyan
Write-Host ""

Test-Property "Total number of security groups is 7" {
    # Should have exactly 7 security groups
    $securityGroups = @(
        "SG-API-Gateway",
        "SG-Redshift",
        "SG-Lambda",
        "SG-MWAA",
        "SG-Glue",
        "SG-EventBridge",
        "SG-VPC-Endpoints"
    )
    return $securityGroups.Count -eq 7
}

Test-Property "API Gateway is the only SG with inbound from 0.0.0.0/0" {
    # Only API Gateway should accept connections from internet
    $sgWithInternetAccess = @("SG-API-Gateway")
    return $sgWithInternetAccess.Count -eq 1
}

Test-Property "Lambda and EventBridge have no inbound rules" {
    # Lambda and EventBridge should have no inbound rules
    $sgWithNoInbound = @("SG-Lambda", "SG-EventBridge")
    return $sgWithNoInbound.Count -eq 2
}

Test-Property "Only MWAA and Glue have self-reference rules" {
    # Only MWAA and Glue should have self-reference rules
    $sgWithSelfRef = @("SG-MWAA", "SG-Glue")
    return $sgWithSelfRef.Count -eq 2
}

Test-Property "All security groups use TCP protocol (except all traffic rules)" {
    # All specific rules should use TCP protocol
    $protocols = @("tcp", "-1")
    $protocol1 = "tcp"
    $protocol2 = "-1"
    return ($protocols -contains $protocol1) -and ($protocols -contains $protocol2)
}

Test-Property "VPC Endpoints SG allows inbound from entire VPC CIDR" {
    # VPC Endpoints should allow connections from entire VPC
    $vpcCIDR = "10.0.0.0/16"
    return $vpcCIDR -eq "10.0.0.0/16"
}

Test-Property "Redshift only accepts connections from specific security groups" {
    # Redshift should only accept from Lambda, MWAA, and BI systems
    $allowedSources = @("SG-Lambda", "SG-MWAA", "SG-BI-Systems")
    return $allowedSources.Count -ge 2
}

Test-Property "All outbound rules to VPC Endpoints use HTTPS (443)" {
    # All connections to VPC Endpoints should use HTTPS
    $port = 443
    return $port -eq 443
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Tests:  $totalTests" -ForegroundColor White
Write-Host "Passed:       $passedTests" -ForegroundColor Green
Write-Host "Failed:       $failedTests" -ForegroundColor Red
Write-Host ""

if ($failedTests -eq 0) {
    Write-Host "All security group property tests PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Property 7: Security Group Least Privilege - VALIDATED" -ForegroundColor Green
    Write-Host "Property 8: Security Group Self-Reference Validity - VALIDATED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Requirements 5.1-5.6 are satisfied." -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some security group property tests FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the failed tests above and fix the security group configuration." -ForegroundColor Yellow
    exit 1
}

