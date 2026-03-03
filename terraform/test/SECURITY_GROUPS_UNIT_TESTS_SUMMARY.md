# Security Groups Unit Tests Summary

## Overview

This document summarizes the unit tests implemented for security group configurations in task 8.8. The tests validate that each security group has correct inbound/outbound rules and follows the principle of least privilege.

## Test Files

### Go-based Unit Tests
- **File**: `security_groups_unit_test.go`
- **Framework**: Terratest with Go
- **Purpose**: Comprehensive unit tests for security group configurations
- **Requirements**: Go 1.21+ installed

### PowerShell Validation Script
- **File**: `validate_security_groups_unit_tests.ps1`
- **Framework**: Native PowerShell
- **Purpose**: Quick validation without Go installation
- **Requirements**: PowerShell (Windows native)

### PowerShell Test Runner
- **File**: `run_security_groups_unit_tests.ps1`
- **Framework**: PowerShell wrapper for Go tests
- **Purpose**: Automated test execution with detailed reporting
- **Requirements**: Go 1.21+ installed

## Test Coverage

### Test 1: SG-API-Gateway Configuration
**Validates: Requirements 5.1**

Tests that SG-API-Gateway has:
- Inbound: HTTPS (443) from allowed Janis IP ranges
- Outbound: All traffic to 0.0.0.0/0
- Proper naming convention
- Required tags

**Test Cases**:
- `TestSGAPIGatewayConfiguration`: Validates basic configuration
- `TestSGAPIGatewayNoOverlyPermissiveRules`: Ensures only HTTPS (443) is allowed inbound

### Test 2: SG-Redshift Configuration
**Validates: Requirements 5.2, 11.3**

Tests that SG-Redshift has:
- Inbound: PostgreSQL (5439) from SG-Lambda, SG-MWAA, existing BI systems
- Outbound: HTTPS (443) to VPC Endpoints only
- Support for existing BI security groups and IP ranges
- Support for MySQL pipeline during migration

**Test Cases**:
- `TestSGRedshiftConfiguration`: Validates configuration with different BI sources
  - With BI security groups
  - With BI IP ranges
  - With MySQL pipeline (migration)
  - With all sources combined
- `TestSGRedshiftNoOverlyPermissiveRules`: Ensures no 0.0.0.0/0 on port 5439

### Test 3: SG-Lambda Configuration
**Validates: Requirements 5.3**

Tests that SG-Lambda has:
- No inbound rules (Lambda doesn't receive direct connections)
- Outbound: PostgreSQL (5439) to SG-Redshift
- Outbound: HTTPS (443) to VPC Endpoints and 0.0.0.0/0

**Test Cases**:
- `TestSGLambdaConfiguration`: Validates outbound rules
- `TestSGLambdaNoInboundRules`: Ensures no inbound rules exist

### Test 4: SG-MWAA Configuration
**Validates: Requirements 5.4**

Tests that SG-MWAA has:
- Inbound: HTTPS (443) from SG-MWAA (self-reference for workers)
- Outbound: HTTPS (443) to VPC Endpoints and 0.0.0.0/0
- Outbound: PostgreSQL (5439) to SG-Redshift

**Test Cases**:
- `TestSGMWAAConfiguration`: Validates basic configuration
- `TestSGMWAASelfReference`: Validates self-reference is properly configured

### Test 5: SG-Glue Configuration
**Validates: Requirements 5.5**

Tests that SG-Glue has:
- Inbound: All TCP from SG-Glue (self-reference for Spark)
- Outbound: HTTPS (443) to VPC Endpoints
- Outbound: All TCP to SG-Glue (self-reference)

**Test Cases**:
- `TestSGGlueConfiguration`: Validates basic configuration
- `TestSGGlueSelfReference`: Validates self-reference is properly configured

### Test 6: SG-EventBridge Configuration
**Validates: Requirements 5.6**

Tests that SG-EventBridge has:
- Outbound: HTTPS (443) to MWAA endpoints
- Outbound: HTTPS (443) to VPC Endpoints

**Test Cases**:
- `TestSGEventBridgeConfiguration`: Validates outbound rules

### Test 7: SG-VPC-Endpoints Configuration
**Validates: Requirements 4.5**

Tests that SG-VPC-Endpoints has:
- Inbound: HTTPS (443) from entire VPC CIDR
- Outbound: HTTPS (443) to AWS services (0.0.0.0/0)

**Test Cases**:
- `TestSGVPCEndpointsConfiguration`: Validates configuration

### Test 8: Integration Tests

**Test Cases**:
- `TestAllSecurityGroupsIntegrity`: Validates all security groups can be created together
- `TestSecurityGroupsWithMultipleJanisIPRanges`: Tests API Gateway SG with multiple Janis IP ranges
- `TestSecurityGroupsLeastPrivilege`: Validates all SGs follow least privilege principle
- `TestSecurityGroupsResourceNaming`: Tests naming conventions across environments

## Running the Tests

### Option 1: PowerShell Validation Script (Recommended for Windows)

```powershell
cd terraform/test
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
.\validate_security_groups_unit_tests.ps1
```

**Tests Performed**:
1. SG-API-Gateway has correct configuration
2. SG-Redshift has correct configuration
3. SG-Lambda has correct configuration
4. SG-Lambda has no inbound rules
5. SG-MWAA has correct configuration
6. SG-MWAA has valid self-reference
7. SG-Glue has correct configuration
8. SG-Glue has valid self-reference
9. SG-EventBridge has correct configuration
10. SG-VPC-Endpoints has correct configuration
11. All required security groups are defined
12. Security groups follow naming convention
13. Security groups have proper tags
14. Redshift SG has no overly permissive rules
15. All security groups follow least privilege

### Option 2: Go-based Unit Tests

```bash
cd terraform/test

# Run all security group unit tests
go test -v -run TestSG

# Run specific test
go test -v -run TestSGAPIGatewayConfiguration

# Run with timeout
go test -v -run TestSG -timeout 10m
```

### Option 3: PowerShell Test Runner

```powershell
cd terraform/test
.\run_security_groups_unit_tests.ps1
```

This script runs all 15 Go-based unit tests sequentially and provides a detailed summary.

## Test Results

**Status**: ✓ READY FOR EXECUTION

All test files have been created and are ready to run. The tests validate:

1. **Correct Inbound/Outbound Rules**: Each security group has the appropriate rules defined
2. **No Overly Permissive Rules**: Security groups follow least privilege principle
3. **Self-References**: MWAA and Glue security groups have valid self-references
4. **Naming Conventions**: All security groups follow the naming pattern `${var.name_prefix}-sg-{purpose}`
5. **Tagging**: All security groups have required tags (Name, Component, Purpose)
6. **Integration**: All security groups can be created together without conflicts

## Security Group Summary

### SG-API-Gateway
- **Purpose**: Protect API Gateway webhook endpoints
- **Inbound**: HTTPS (443) from allowed Janis IP ranges
- **Outbound**: All traffic to 0.0.0.0/0
- **Least Privilege**: ✓ Only HTTPS inbound

### SG-Redshift
- **Purpose**: Control access to Redshift cluster
- **Inbound**: PostgreSQL (5439) from SG-Lambda, SG-MWAA, BI systems
- **Outbound**: HTTPS (443) to VPC Endpoints only
- **Least Privilege**: ✓ No 0.0.0.0/0 on port 5439

### SG-Lambda
- **Purpose**: Lambda function network security
- **Inbound**: None (Lambda doesn't receive direct connections)
- **Outbound**: PostgreSQL (5439) to SG-Redshift, HTTPS (443) to VPC Endpoints and internet
- **Least Privilege**: ✓ No inbound rules

### SG-MWAA
- **Purpose**: MWAA environment security
- **Inbound**: HTTPS (443) from SG-MWAA (self-reference)
- **Outbound**: HTTPS (443) to VPC Endpoints and internet, PostgreSQL (5439) to SG-Redshift
- **Least Privilege**: ✓ Self-reference for worker communication

### SG-Glue
- **Purpose**: Glue job network security
- **Inbound**: All TCP from SG-Glue (self-reference for Spark)
- **Outbound**: HTTPS (443) to VPC Endpoints, All TCP to SG-Glue (self-reference)
- **Least Privilege**: ✓ Self-reference for Spark cluster

### SG-EventBridge
- **Purpose**: EventBridge VPC endpoint security
- **Inbound**: None
- **Outbound**: HTTPS (443) to MWAA and VPC Endpoints
- **Least Privilege**: ✓ Specific outbound only

### SG-VPC-Endpoints
- **Purpose**: Common security group for VPC Interface Endpoints
- **Inbound**: HTTPS (443) from entire VPC CIDR
- **Outbound**: HTTPS (443) to AWS services
- **Least Privilege**: ✓ VPC CIDR only inbound

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Security Groups Unit Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Run Security Groups Unit Tests
        run: |
          cd terraform/test
          go test -v -run TestSG -timeout 10m
```

### Local Pre-commit Hook

```bash
#!/bin/bash
cd terraform/test
go test -v -run TestSG -timeout 10m
if [ $? -ne 0 ]; then
    echo "Security groups unit tests failed. Commit aborted."
    exit 1
fi
```

## Next Steps

1. **Run Tests**: Execute the validation script or Go tests to verify all tests pass
2. **Fix Failures**: If any tests fail, review the security group configuration and fix issues
3. **Document Results**: Update this summary with actual test results
4. **Integrate with CI/CD**: Add tests to the CI/CD pipeline for automated validation

## References

- **Requirements**: `.kiro/specs/01-aws-infrastructure/requirements.md` (Requirements 5.1-5.6, 11.3)
- **Design**: `.kiro/specs/01-aws-infrastructure/design.md` (Security Groups section)
- **Module**: `terraform/modules/security-groups/main.tf`
- **Property Tests**: `terraform/test/security_groups_property_test.go` (Task 8.7)
- **Terratest Documentation**: https://terratest.gruntwork.io/
