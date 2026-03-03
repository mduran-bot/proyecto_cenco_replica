# Guide: Running SPOF Documentation Property Tests

## Overview

This guide explains how to run the Single Point of Failure (SPOF) Documentation Property Tests for the AWS infrastructure.

## Prerequisites

1. **Go installed**: Version 1.21 or higher
   ```bash
   go version
   ```

2. **Working directory**: Navigate to the test directory
   ```bash
   cd terraform/test
   ```

3. **Go modules**: Ensure go.mod and go.sum are present
   ```bash
   ls go.mod go.sum
   ```

## Running the Tests

### Option 1: Using PowerShell Script (Recommended)

```powershell
cd terraform/test
.\run_spof_documentation_tests.ps1
```

This script will:
- Check Go installation
- Download dependencies
- Run all SPOF documentation property tests
- Display detailed results

### Option 2: Using Go Directly

```bash
cd terraform/test
go test -v -timeout 30m -run "TestSinglePointOfFailureDocumentation" .
```

### Option 3: Run Specific Tests

Run individual test functions:

```bash
# Test documentation existence
go test -v -run "TestSingleAZDocumentationExists" .

# Test NAT Gateway SPOF documentation
go test -v -run "TestNATGatewaySinglePointOfFailureDocumented" .

# Test AZ SPOF documentation
go test -v -run "TestAvailabilityZoneSinglePointOfFailureDocumented" .

# Test migration path documentation
go test -v -run "TestMultiAZMigrationPathDocumented" .

# Test reserved CIDR blocks documentation
go test -v -run "TestReservedCIDRBlocksDocumented" .

# Run comprehensive property test
go test -v -run "TestSinglePointOfFailureDocumentationProperty_Comprehensive" .
```

## Validating Documentation Before Testing

Before running the property tests, validate that the documentation is complete:

```powershell
cd terraform/test
.\validate_spof_documentation.ps1
```

This validation script checks:
- SINGLE_AZ_DEPLOYMENT.md exists and contains all required sections
- MULTI_AZ_EXPANSION.md exists with migration path
- All single points of failure are documented
- Reserved CIDR blocks are documented
- Documentation cross-references are valid

## Expected Test Output

### Successful Test Run

```
=== RUN   TestSinglePointOfFailureDocumentationProperty
--- PASS: TestSinglePointOfFailureDocumentationProperty (X.XXs)

=== RUN   TestSingleAZDocumentationExists
--- PASS: TestSingleAZDocumentationExists (X.XXs)

=== RUN   TestNATGatewaySinglePointOfFailureDocumented
--- PASS: TestNATGatewaySinglePointOfFailureDocumented (X.XXs)

=== RUN   TestAvailabilityZoneSinglePointOfFailureDocumented
--- PASS: TestAvailabilityZoneSinglePointOfFailureDocumented (X.XXs)

=== RUN   TestMultiAZMigrationPathDocumented
--- PASS: TestMultiAZMigrationPathDocumented (X.XXs)

=== RUN   TestReservedCIDRBlocksDocumented
--- PASS: TestReservedCIDRBlocksDocumented (X.XXs)

=== RUN   TestSinglePointsOfFailureCompleteness
--- PASS: TestSinglePointsOfFailureCompleteness (X.XXs)

=== RUN   TestImpactOfAZFailureDocumented
--- PASS: TestImpactOfAZFailureDocumented (X.XXs)

=== RUN   TestRecoveryProceduresDocumented
--- PASS: TestRecoveryProceduresDocumented (X.XXs)

=== RUN   TestMonitoringAndAlertingDocumented
--- PASS: TestMonitoringAndAlertingDocumented (X.XXs)

=== RUN   TestArchitecturalChangesForMultiAZDocumented
--- PASS: TestArchitecturalChangesForMultiAZDocumented (X.XXs)

=== RUN   TestSingleAZDeploymentLimitationsDocumented
--- PASS: TestSingleAZDeploymentLimitationsDocumented (X.XXs)

=== RUN   TestDocumentationCrossReferences
--- PASS: TestDocumentationCrossReferences (X.XXs)

=== RUN   TestTerraformConfigurationSupportsDocumentedMigration
--- PASS: TestTerraformConfigurationSupportsDocumentedMigration (X.XXs)

=== RUN   TestSinglePointOfFailureDocumentationProperty_Comprehensive
--- PASS: TestSinglePointOfFailureDocumentationProperty_Comprehensive (X.XXs)

PASS
ok      github.com/cencosud/janis-integration/terraform/test    XX.XXXs
```

### Failed Test Example

If documentation is incomplete, you'll see errors like:

```
=== RUN   TestNATGatewaySinglePointOfFailureDocumented
    spof_documentation_property_test.go:XXX: 
        Error Trace:    spof_documentation_property_test.go:XXX
        Error:          Should be true
        Test:           TestNATGatewaySinglePointOfFailureDocumented
        Messages:       Documentation must mention NAT Gateway SPOF keyword: single point of failure
--- FAIL: TestNATGatewaySinglePointOfFailureDocumented (X.XXs)
```

## Troubleshooting

### Issue: "go.mod file not found"

**Solution**: Ensure you're in the correct directory
```bash
cd terraform/test
ls go.mod  # Should exist
```

### Issue: "cannot find package"

**Solution**: Download Go dependencies
```bash
go mod download
go mod tidy
```

### Issue: "Documentation file not found"

**Solution**: Verify documentation files exist
```bash
ls ../SINGLE_AZ_DEPLOYMENT.md
ls ../MULTI_AZ_EXPANSION.md
```

### Issue: Tests fail due to missing sections

**Solution**: Review the documentation and add missing sections. See SPOF_DOCUMENTATION_PROPERTY_TEST_SUMMARY.md for required elements.

## What the Tests Validate

### Property 17: Single Point of Failure Documentation

The tests validate that:

1. **SINGLE_AZ_DEPLOYMENT.md exists** and contains:
   - Single Points of Failure section
   - NAT Gateway SPOF (HIGH severity, 7-20 min recovery)
   - Availability Zone SPOF (CRITICAL severity, hours to days recovery)
   - Internet Gateway SPOF (LOW severity, < 1 min recovery)
   - VPC Endpoints SPOF (MEDIUM severity, 2-5 min recovery)
   - Impact analysis (immediate, short-term, medium-term, long-term)
   - Recovery procedures with commands
   - Monitoring and alerting guidance
   - Single-AZ deployment limitations

2. **MULTI_AZ_EXPANSION.md exists** and contains:
   - Reserved CIDR blocks (10.0.2.0/24, 10.0.11.0/24, 10.0.21.0/24)
   - Migration path to multi-AZ (5 phases)
   - Terraform configuration steps (enable_multi_az, plan, apply)
   - Rollback procedures
   - Architectural changes for multi-AZ

3. **Documentation is actionable**:
   - Recovery procedures include specific commands
   - Migration steps are technically feasible
   - Terraform configuration supports documented migration

4. **Documentation is complete**:
   - All SPOFs are identified with severity and recovery times
   - Cross-references between documents are valid
   - Requirements 12.1, 12.2, 12.3, 12.5 are satisfied

## Integration with CI/CD

To integrate these tests into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run SPOF Documentation Tests
  run: |
    cd terraform/test
    go test -v -timeout 30m -run "TestSinglePointOfFailureDocumentation" .
```

## Next Steps

After running the tests:

1. **If tests pass**: Documentation is complete and accurate
2. **If tests fail**: Review error messages and update documentation
3. **Regular reviews**: Run tests quarterly to ensure documentation stays current
4. **Incident updates**: Update recovery times based on actual incidents
5. **Cost updates**: Update cost estimates as AWS pricing changes

## References

- Test Implementation: `spof_documentation_property_test.go`
- Test Summary: `SPOF_DOCUMENTATION_PROPERTY_TEST_SUMMARY.md`
- Single-AZ Documentation: `../SINGLE_AZ_DEPLOYMENT.md`
- Multi-AZ Documentation: `../MULTI_AZ_EXPANSION.md`
- Requirements: `../../.kiro/specs/01-aws-infrastructure/requirements.md`
- Design: `../../.kiro/specs/01-aws-infrastructure/design.md`

---

**Last Updated**: 2026-01-26  
**Property**: 17 - Single Point of Failure Documentation  
**Requirements**: 12.1, 12.2, 12.3, 12.5
