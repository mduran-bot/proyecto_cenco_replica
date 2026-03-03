# Testing Guide for AWS Infrastructure

## Overview

This directory contains property-based tests and validation scripts for the AWS infrastructure. The tests validate correctness properties defined in the design document.

## Test Implementations

### Property 1: VPC CIDR Block Validity

**Validates: Requirements 1.1**

**Property Statement**: For any VPC configuration, the CIDR block must be a valid IPv4 CIDR notation and provide exactly 65,536 IP addresses (10.0.0.0/16).

**Test Files**:
- `vpc_cidr_property_test.go` - Go-based property tests using Terratest and Gopter
- `validate_vpc_cidr.ps1` - PowerShell validation script (no Go required)

### Property 2: Single-AZ Deployment

**Validates: Requirements 1.2, 2.2, 2.3**

**Property Statement**: For any infrastructure deployment, all resources must be deployed in exactly one Availability Zone (us-east-1a) with reserved CIDR blocks documented for future multi-AZ expansion.

**Test Files**:
- `single_az_property_test.go` - Go-based property tests using Terratest and Gopter
- `validate_single_az_deployment.ps1` - PowerShell validation script (no Go required)

## Running Tests

### Test Maintenance

#### fix_go_tests.py - Terratest API Compatibility Fixer

Before running Go tests, you may need to fix API compatibility issues:

```bash
cd terraform/test
python fix_go_tests.py
```

**What it does**:
- Automatically updates Go test files for Terratest API changes
- Adds error handling (`assert.NoError(t, err)`) where needed
- Maintains proper code indentation
- Processes multiple test files in batch

**When to use**:
- After updating Terratest to a newer version
- When tests fail with signature mismatch errors
- Before running Go tests for the first time

**Files processed**:
- routing_property_test.go
- security_groups_unit_test.go
- single_az_property_test.go
- vpc_unit_test.go
- vpc_cidr_property_test.go

### Option 1: PowerShell Validation Script (Recommended for Windows)

This script requires no additional dependencies and runs natively on Windows:

```powershell
cd terraform/test

# Run Property 1: VPC CIDR Block Validity
powershell -ExecutionPolicy Bypass -File validate_vpc_cidr.ps1

# Run Property 2: Single-AZ Deployment
powershell -ExecutionPolicy Bypass -File validate_single_az_deployment.ps1
```

**Property 1 Test Results**:
- Tests 5 valid /16 CIDR blocks
- Tests 5 invalid CIDR blocks (wrong prefix, invalid format, etc.)
- Validates that each CIDR provides exactly 65,536 IP addresses
- All 10 test cases passed ✓

**Property 2 Test Results**:
- Tests 40 validation checks across 10 test categories
- Validates active subnets are in us-east-1a only
- Validates reserved CIDR blocks for multi-AZ expansion
- Validates no overlaps between active and reserved subnets
- Validates documentation exists for single points of failure
- Validates VPC module configuration supports multi-AZ expansion
- Runs 100 property-based test iterations
- All 40 test cases passed ✓

### Option 2: Go-based Property Tests

Requires Go 1.21+ to be installed:

```bash
# Setup (first time only)
cd terraform/test
go mod download

# Run all tests
go test -v

# Run Property 1 test
go test -v -run TestVPCCIDRValidityProperty

# Run Property 2 test
go test -v -run TestSingleAZDeploymentProperty

# Run with 100 iterations (property-based testing)
go test -v -run TestVPCCIDRValidityProperty
go test -v -run TestSingleAZDeploymentProperty
```

### Option 3: Docker Container

Run tests in a containerized environment:

```bash
cd terraform/test
docker build -t terraform-tests .
docker run --rm terraform-tests
```

## Test Coverage

### Valid CIDR Blocks Tested
- `10.0.0.0/16` - Standard private network
- `172.16.0.0/16` - Alternative private network
- `192.168.0.0/16` - Common private network
- `10.1.0.0/16` - Alternative configuration
- `10.10.0.0/16` - Alternative configuration

### Invalid CIDR Blocks Tested
- `10.0.0.0/24` - Wrong prefix (only 256 IPs)
- `10.0.0.0/8` - Wrong prefix (16M IPs)
- `10.0.0.0` - Missing prefix length
- `999.999.999.999/16` - Invalid IP address
- `10.0.0.0/33` - Invalid prefix length

## Test Results

**Status**: ✓ PASSED

**Property 1 Summary**:
- Total Tests: 10
- Passed: 10
- Failed: 0

All property tests validate that:
1. VPC CIDR blocks use valid IPv4 CIDR notation
2. VPC CIDR blocks provide exactly 65,536 IP addresses
3. VPC CIDR blocks use /16 prefix length
4. Invalid CIDR blocks are correctly rejected

**Property 2 Summary**:
- Total Tests: 40
- Passed: 40
- Failed: 0

All property tests validate that:
1. Active subnets (public_a, private_1a, private_2a) are valid subsets of VPC CIDR
2. Reserved subnets (public_b, private_1b, private_2b) are valid subsets of VPC CIDR
3. No overlaps exist between active subnets
4. No overlaps exist between reserved subnets
5. No overlaps exist between active and reserved subnets
6. Single-AZ deployment has exactly 3 active subnets
7. Exactly 3 CIDR blocks are reserved for multi-AZ expansion
8. MULTI_AZ_EXPANSION.md documentation exists and contains required sections
9. VPC module configuration supports conditional multi-AZ deployment
10. Property holds across 100 iterations of property-based testing

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Terraform Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Property 1 - VPC CIDR Validity Tests
        run: |
          cd terraform/test
          powershell -ExecutionPolicy Bypass -File validate_vpc_cidr.ps1
      
      - name: Run Property 2 - Single-AZ Deployment Tests
        run: |
          cd terraform/test
          powershell -ExecutionPolicy Bypass -File validate_single_az_deployment.ps1
```

### Local Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd terraform/test

# Run Property 1 tests
powershell -ExecutionPolicy Bypass -File validate_vpc_cidr.ps1
if [ $? -ne 0 ]; then
    echo "Property 1 tests failed. Commit aborted."
    exit 1
fi

# Run Property 2 tests
powershell -ExecutionPolicy Bypass -File validate_single_az_deployment.ps1
if [ $? -ne 0 ]; then
    echo "Property 2 tests failed. Commit aborted."
    exit 1
fi
```

## Troubleshooting

### PowerShell Execution Policy

If you get an execution policy error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Go Not Installed

If Go is not installed and you want to run Go tests:

1. Download Go from https://go.dev/dl/
2. Install Go 1.21 or higher
3. Run `go version` to verify
4. Run `go mod download` in terraform/test directory

### Docker Alternative

If you don't want to install Go locally, use Docker:

```bash
docker run --rm -v ${PWD}:/workspace -w /workspace/terraform/test golang:1.21 go test -v
```

## Next Steps

After Property 1 and Property 2 tests pass, implement:
- Property 3: Subnet CIDR Non-Overlap (COMPLETED - see validate_subnet_cidr_overlap.ps1)
- Property 4: Public Subnet Internet Routing
- Property 5: Private Subnet NAT Routing
- Property 6: VPC Endpoint Service Coverage
- Property 7-17: Additional correctness properties

See `.kiro/specs/01-aws-infrastructure/design.md` for complete list of correctness properties.
