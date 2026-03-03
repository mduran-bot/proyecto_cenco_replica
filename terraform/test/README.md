# Terraform Infrastructure Tests

This directory contains property-based tests and unit tests for the AWS infrastructure using Terratest and Go.

## Quick Start

**📖 New to validation?** Start with [VALIDATION_GUIDE.md](./VALIDATION_GUIDE.md) for a comprehensive guide on:
- Validating infrastructure without deploying to AWS
- Using `terraform plan` to verify configuration
- Understanding what to validate in each component
- Troubleshooting common validation errors

## Prerequisites

- Go 1.21 or higher
- Terraform >= 1.0
- AWS credentials configured (for integration tests)
- Python 3.x (for test maintenance scripts)

## Installation

Install Go dependencies:

```bash
cd terraform/test
go mod download
```

## Test Maintenance Scripts

### fix_go_tests.py

**Purpose**: Automatically fixes Terratest API compatibility issues in Go test files.

**What it does**:
- Detects calls to `terraform.InitAndPlanE` and `terraform.ValidateE` that return `(exitCode, err)`
- Adds `assert.NoError(t, err)` after each call if not already present
- Maintains correct code indentation
- Processes multiple test files in batch

**Files processed**:
- routing_property_test.go
- security_groups_unit_test.go
- single_az_property_test.go
- vpc_unit_test.go
- vpc_cidr_property_test.go

**Usage**:
```bash
cd terraform/test
python fix_go_tests.py
```

**When to use**:
- After updating Terratest to a newer version
- When tests fail due to API changes in Terratest
- When adding new test files that use Terratest functions

**Background**: Terratest changed its API to return both `exitCode` and `err` from functions like `InitAndPlanE`. This script automatically updates test files to handle the new return signature.

## Running Tests

### Go-Based Tests

#### Run All Tests

```bash
go test -v -timeout 30m
```

#### Run Specific Test

```bash
# Run VPC CIDR property test
go test -v -run TestVPCCIDRValidityProperty

# Run VPC CIDR with Terraform validation
go test -v -run TestVPCCIDRValidityWithTerraform

# Run invalid CIDR cases
go test -v -run TestVPCCIDRInvalidCases

# Run Security Groups tests
go test -v -run TestSG

# Run NACL tests
go test -v -run TestNACL

# Run Routing tests
go test -v -run TestRouting
```

#### Run Tests in Parallel

```bash
go test -v -parallel 4
```

### PowerShell Validation Scripts

Alternative validation scripts that don't require Go installation:

**📖 For detailed validation guide, see [VALIDATION_GUIDE.md](./VALIDATION_GUIDE.md)**

#### Security Groups Validation

```powershell
# Unit tests for Security Groups configuration
.\validate_security_groups_unit_tests.ps1

# Property tests for Security Groups (28 validation tests)
.\validate_security_groups.ps1
```

#### Network ACLs Validation

```powershell
# Validate NACL configuration
.\validate_nacl.ps1
```

#### Routing Configuration Validation

```powershell
# Validate routing tables and internet connectivity
.\validate_routing_configuration.ps1
```

#### Infrastructure Validation (All Components)

```powershell
# Automated validation of all modules
.\validate_infrastructure.ps1
```

**Benefits of PowerShell scripts**:
- No Go installation required
- Fast execution (seconds vs minutes)
- Easy to read and modify
- Validates Terraform configuration files directly
- Ideal for quick checks during development

**See [VALIDATION_GUIDE.md](./VALIDATION_GUIDE.md) for**:
- Step-by-step validation instructions
- What to validate in each component (VPC, Security Groups, WAF, EventBridge, etc.)
- Using `terraform plan` for comprehensive validation
- Troubleshooting common errors

## Test Structure

### Property-Based Tests

Property-based tests use the `gopter` library to generate random test cases and verify that properties hold across all inputs.

- **TestVPCCIDRValidityProperty**: Validates that VPC CIDR blocks are valid IPv4 CIDR notation and provide exactly 65,536 IP addresses (Requirements 1.1)

### Unit Tests

Unit tests verify specific configurations and edge cases:

**VPC CIDR Tests (vpc_cidr_property_test.go)**:
- **TestVPCCIDRValidityWithTerraform**: Tests the VPC module with different valid /16 CIDR blocks
- **TestVPCCIDRInvalidCases**: Verifies that invalid CIDR blocks are properly rejected
- **TestVPCModuleWithValidCIDR**: Integration test that validates the VPC module accepts valid CIDR configurations

**VPC Configuration Tests (vpc_unit_test.go)**:
- **TestVPCCreationWithCorrectCIDR**: Tests VPC creation with correct CIDR block (Requirements 1.1)
- **TestVPCDNSSettingsEnabled**: Tests that DNS resolution and DNS hostnames are enabled (Requirements 1.3)
- **TestVPCMandatoryTagsApplied**: Tests that mandatory tags are applied to VPC (Requirements 1.4)
- **TestVPCConfigurationIntegrity**: Tests overall VPC configuration integrity
- **TestVPCSingleAZDeployment**: Tests single AZ deployment when multi-AZ is disabled (Requirements 1.2)
- **TestVPCMultiAZDeployment**: Tests multi-AZ deployment capability for future expansion
- **TestVPCIPv4Support**: Tests that VPC supports IPv4 (Requirements 1.5)
- **TestVPCResourceNaming**: Tests that VPC resources follow naming conventions (Requirements 1.4)

## Test Coverage

### Property 1: VPC CIDR Block Validity

**Validates: Requirements 1.1**

**Property**: For any VPC configuration, the CIDR block must be a valid IPv4 CIDR notation and provide exactly 65,536 IP addresses (10.0.0.0/16).

**Test Implementation**:
- Generates 100 test cases with valid /16 CIDR blocks
- Validates CIDR format using Go's `net.ParseCIDR`
- Calculates total IP addresses: 2^(32 - prefix_length)
- Asserts that total IPs equals exactly 65,536

**Test Cases**:
- Valid CIDR blocks: 10.0.0.0/16, 172.16.0.0/16, 192.168.0.0/16
- Invalid CIDR blocks: wrong prefix lengths (/8, /24), invalid formats, empty strings

### Unit Test Coverage

**VPC Creation with Correct CIDR Block (Requirements 1.1)**:
- Tests VPC creation with valid /16 CIDR blocks (10.0.0.0/16, 172.16.0.0/16, 192.168.0.0/16)
- Validates Terraform configuration accepts correct CIDR notation
- Verifies configuration can be planned without errors

**DNS Settings Enabled (Requirements 1.3)**:
- Tests that VPC module explicitly sets `enable_dns_hostnames = true`
- Tests that VPC module explicitly sets `enable_dns_support = true`
- Validates Terraform configuration is valid with DNS settings

**Mandatory Tags Applied (Requirements 1.4)**:
- Tests that VPC resources include Name tag with correct naming convention
- Tests that VPC resources include Component tag
- Validates that provider default_tags apply mandatory tags (Project, Environment, Owner, CostCenter, ManagedBy)
- Tests tag application across different environments (dev, staging, prod)

**Additional Coverage**:
- Single-AZ deployment validation (Requirements 1.2)
- Multi-AZ deployment capability for future expansion
- IPv4 support validation (Requirements 1.5)
- Resource naming conventions (Requirements 1.4)

## Continuous Integration

These tests should be run as part of the CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run Terraform Tests
  run: |
    cd terraform/test
    go test -v -timeout 30m
```

## Troubleshooting

### Test Timeout

If tests timeout, increase the timeout value:

```bash
go test -v -timeout 60m
```

### AWS Credentials

For integration tests that deploy actual infrastructure, ensure AWS credentials are configured:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

### Parallel Test Failures

If parallel tests fail due to resource conflicts, reduce parallelism:

```bash
go test -v -parallel 1
```

## References

- [Terratest Documentation](https://terratest.gruntwork.io/)
- [Gopter Property-Based Testing](https://github.com/leanovate/gopter)
- [AWS VPC CIDR Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html)
