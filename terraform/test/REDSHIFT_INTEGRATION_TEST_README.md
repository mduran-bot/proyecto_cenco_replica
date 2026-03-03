# Redshift Integration Property Test - Quick Start

## Overview

This directory contains the property-based tests for Redshift Security Group Integration (Property 16).

## Files Created

1. **redshift_integration_property_test.go** - Main test file with all property tests
2. **run_redshift_integration_tests.ps1** - PowerShell script to run all tests
3. **validate_redshift_integration_tests.ps1** - Validation script to check file structure
4. **REDSHIFT_INTEGRATION_PROPERTY_TEST_SUMMARY.md** - Comprehensive documentation

## Quick Start

### Prerequisites

- Go 1.21 or later installed
- PowerShell (for running scripts)
- Terraform (for Terraform validation tests)

### Running the Tests

#### Option 1: Run All Tests (Recommended)

```powershell
cd terraform/test
.\run_redshift_integration_tests.ps1
```

#### Option 2: Run Individual Tests

```bash
cd terraform/test

# Main property test
go test -v -run TestRedshiftSecurityGroupIntegrationProperty -timeout 30m

# No overlapping CIDRs test
go test -v -run TestRedshiftSecurityGroupNoOverlappingCIDRs -timeout 10m

# Preserves existing access test
go test -v -run TestRedshiftSecurityGroupPreservesExistingAccess -timeout 10m

# MySQL pipeline temporary test
go test -v -run TestRedshiftSecurityGroupMySQLPipelineTemporary -timeout 10m

# Rule validation test
go test -v -run TestRedshiftSecurityGroupRuleValidation -timeout 10m

# Comprehensive integration test
go test -v -run TestRedshiftSecurityGroupIntegrationComprehensive -timeout 30m

# Terraform configuration test
go test -v -run TestRedshiftSecurityGroupWithTerraform -timeout 10m
```

#### Option 3: Run All Redshift Tests

```bash
cd terraform/test
go test -v -run TestRedshiftSecurityGroup -timeout 60m
```

### Validating Test Files

To check that all required files exist and are properly structured:

```powershell
cd terraform/test
.\validate_redshift_integration_tests.ps1
```

## Test Coverage

The test suite validates:

✅ **Property 16**: New security group rules do not conflict with existing BI rules  
✅ **Requirements 11.3**: Integration with existing Cencosud infrastructure

### Specific Validations

1. **No Conflicts**: New Janis rules don't interfere with existing BI system rules
2. **No CIDR Overlaps**: New VPC internal CIDRs don't overlap with BI external CIDRs
3. **Preserves Access**: Existing BI system access is maintained after adding Janis rules
4. **Temporary Rules**: MySQL pipeline rules are properly marked as temporary
5. **Rule Validation**: All rules follow proper format (port 5439, TCP, descriptions)
6. **Terraform Config**: Module configuration is valid

## Expected Results

When all tests pass, you should see:

```
✓ All Redshift Integration Property Tests PASSED

Property 16 Validation:
  ✓ New security group rules do not conflict with existing BI rules
  ✓ CIDR blocks do not overlap
  ✓ Existing BI access is preserved
  ✓ MySQL pipeline rule is properly marked as temporary
  ✓ All rules are properly validated
  ✓ Terraform configuration is valid

Requirements 11.3 validated successfully!
```

## Troubleshooting

### Go Module Errors

If you see "go.mod file not found" errors:

```bash
cd terraform/test
go mod download
```

### Test Timeout

If tests timeout, increase the timeout value:

```bash
go test -v -run TestRedshiftSecurityGroup -timeout 120m
```

### PowerShell Execution Policy

If PowerShell scripts won't run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Documentation

For detailed documentation, see:

- **REDSHIFT_INTEGRATION_PROPERTY_TEST_SUMMARY.md** - Complete test documentation
- **terraform/REDSHIFT_INTEGRATION.md** - Redshift integration guide
- **.kiro/specs/01-aws-infrastructure/requirements.md** - Requirements (11.3)
- **.kiro/specs/01-aws-infrastructure/design.md** - Design (Property 16)

## Support

For questions or issues:

1. Check the REDSHIFT_INTEGRATION_PROPERTY_TEST_SUMMARY.md for detailed information
2. Review the test output for specific error messages
3. Verify all prerequisites are installed
4. Check that go.mod and go.sum are present in the test directory

## Status

✅ **Task 16.2 Completed**: Property test for Redshift security group integration  
📝 **Property 16**: Redshift Security Group Integration  
✅ **Requirements 11.3**: Validated

**Date**: January 26, 2026
