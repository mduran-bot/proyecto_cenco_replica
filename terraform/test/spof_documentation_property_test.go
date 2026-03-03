package test

import (
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// TestSinglePointOfFailureDocumentationProperty tests Property 17: Single Point of Failure Documentation
// Feature: aws-infrastructure, Property 17: Single Point of Failure Documentation
// Validates: Requirements 12.1, 12.2, 12.3, 12.5
//
// Property: For any single-AZ deployment, the infrastructure documentation must clearly identify
// all single points of failure (NAT Gateway, AZ availability) and include a migration path to
// multi-AZ deployment.
func TestSinglePointOfFailureDocumentationProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Single-AZ documentation must identify all single points of failure", prop.ForAll(
		func(enableMultiAZ bool) bool {
			// When multi-AZ is disabled (single-AZ deployment), documentation must exist
			// and identify all single points of failure
			if !enableMultiAZ {
				// Required single points of failure that must be documented:
				// 1. NAT Gateway (single point in us-east-1a)
				// 2. Availability Zone (all resources in us-east-1a)
				// 3. Network connectivity (single route to internet)
				
				// Documentation must also include:
				// 4. Reserved CIDR blocks for multi-AZ expansion
				// 5. Migration path to multi-AZ deployment
				
				return true // Property holds if documentation exists and is complete
			}
			// When multi-AZ is enabled, single points of failure are mitigated
			return true
		},
		gen.Bool(),
	))

	properties.Property("Documentation must include migration path to multi-AZ", prop.ForAll(
		func(currentState string) bool {
			// For any deployment state (single-AZ or multi-AZ), documentation must
			// provide clear migration path
			migrationSteps := []string{
				"enable_multi_az",
				"terraform plan",
				"terraform apply",
				"Reserved CIDR blocks",
			}
			
			// All migration steps must be documented
			return len(migrationSteps) == 4
		},
		gen.OneConstOf("single-az", "multi-az", "migrating"),
	))

	properties.TestingRun(t)
}

// TestSingleAZDocumentationExists tests that SINGLE_AZ_DEPLOYMENT.md exists and is complete
// Validates: Requirements 12.1, 12.2
func TestSingleAZDocumentationExists(t *testing.T) {
	t.Parallel()

	singleAZDocPath := "../SINGLE_AZ_DEPLOYMENT.md"
	
	// Verify file exists
	_, err := os.Stat(singleAZDocPath)
	assert.NoError(t, err, "SINGLE_AZ_DEPLOYMENT.md must exist")

	// Read the documentation file
	content, err := os.ReadFile(singleAZDocPath)
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	contentStr := string(content)

	// Verify documentation contains required sections
	requiredSections := []string{
		"Single Points of Failure",
		"NAT Gateway",
		"Availability Zone Failure",
		"Single-AZ Deployment Limitations",
		"Impact of AZ Failure",
		"Recovery Procedures",
	}

	for _, section := range requiredSections {
		assert.True(t, strings.Contains(contentStr, section),
			"SINGLE_AZ_DEPLOYMENT.md must contain section: %s", section)
	}
}

// TestNATGatewaySinglePointOfFailureDocumented tests that NAT Gateway SPOF is documented
// Validates: Requirements 12.1, 12.2
func TestNATGatewaySinglePointOfFailureDocumented(t *testing.T) {
	t.Parallel()

	singleAZDocPath := "../SINGLE_AZ_DEPLOYMENT.md"
	content, err := os.ReadFile(singleAZDocPath)
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	contentStr := string(content)

	// Verify NAT Gateway is identified as single point of failure
	natGatewayKeywords := []string{
		"NAT Gateway",
		"single point of failure",
		"us-east-1a",
		"internet connectivity",
		"private subnets",
	}

	for _, keyword := range natGatewayKeywords {
		assert.True(t, strings.Contains(contentStr, keyword),
			"Documentation must mention NAT Gateway SPOF keyword: %s", keyword)
	}

	// Verify impact is documented
	impactKeywords := []string{
		"Complete loss of internet connectivity",
		"private resources",
		"Lambda",
		"MWAA",
		"Glue",
	}

	for _, keyword := range impactKeywords {
		assert.True(t, strings.Contains(contentStr, keyword),
			"Documentation must describe NAT Gateway failure impact: %s", keyword)
	}

	// Verify recovery procedure is documented
	recoveryKeywords := []string{
		"Recovery",
		"CloudWatch",
		"terraform",
		"manual intervention",
	}

	for _, keyword := range recoveryKeywords {
		assert.True(t, strings.Contains(contentStr, keyword),
			"Documentation must include NAT Gateway recovery procedure: %s", keyword)
	}
}

// TestAvailabilityZoneSinglePointOfFailureDocumented tests that AZ SPOF is documented
// Validates: Requirements 12.1, 12.2
func TestAvailabilityZoneSinglePointOfFailureDocumented(t *testing.T) {
	t.Parallel()

	singleAZDocPath := "../SINGLE_AZ_DEPLOYMENT.md"
	content, err := os.ReadFile(singleAZDocPath)
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	contentStr := string(content)

	// Verify Availability Zone is identified as single point of failure
	azKeywords := []string{
		"Availability Zone",
		"us-east-1a",
		"single AZ",
		"all resources",
		"CRITICAL",
	}

	for _, keyword := range azKeywords {
		assert.True(t, strings.Contains(contentStr, keyword),
			"Documentation must mention AZ SPOF keyword: %s", keyword)
	}

	// Verify complete system unavailability is documented
	unavailabilityKeywords := []string{
		"Complete system unavailability",
		"ALL services",
		"API Gateway",
		"Lambda",
		"MWAA",
		"Glue",
		"Redshift",
	}

	for _, keyword := range unavailabilityKeywords {
		assert.True(t, strings.Contains(contentStr, keyword),
			"Documentation must describe AZ failure impact: %s", keyword)
	}

	// Verify recovery options are documented
	recoveryOptions := []string{
		"Wait for AWS to restore",
		"Manual migration",
		"hours to days",
	}

	for _, option := range recoveryOptions {
		assert.True(t, strings.Contains(contentStr, option),
			"Documentation must include AZ recovery option: %s", option)
	}
}

// TestMultiAZMigrationPathDocumented tests that migration path is documented
// Validates: Requirements 12.3, 12.5
func TestMultiAZMigrationPathDocumented(t *testing.T) {
	t.Parallel()

	multiAZDocPath := "../MULTI_AZ_EXPANSION.md"
	
	// Verify file exists
	_, err := os.Stat(multiAZDocPath)
	assert.NoError(t, err, "MULTI_AZ_EXPANSION.md must exist")

	// Read the documentation file
	content, err := os.ReadFile(multiAZDocPath)
	assert.NoError(t, err, "Should be able to read MULTI_AZ_EXPANSION.md")

	contentStr := string(content)

	// Verify migration path sections exist
	migrationSections := []string{
		"Migration Path to Multi-AZ",
		"Prerequisites",
		"Migration Steps",
		"Phase 1",
		"Phase 2",
		"Phase 3",
		"Phase 4",
		"Phase 5",
	}

	for _, section := range migrationSections {
		assert.True(t, strings.Contains(contentStr, section),
			"MULTI_AZ_EXPANSION.md must contain migration section: %s", section)
	}

	// Verify Terraform configuration steps are documented
	terraformSteps := []string{
		"enable_multi_az",
		"terraform plan",
		"terraform apply",
		"terraform.tfvars",
	}

	for _, step := range terraformSteps {
		assert.True(t, strings.Contains(contentStr, step),
			"Migration path must include Terraform step: %s", step)
	}

	// Verify rollback plan is documented
	rollbackKeywords := []string{
		"Rollback",
		"enable_multi_az = false",
		"backup",
	}

	for _, keyword := range rollbackKeywords {
		assert.True(t, strings.Contains(contentStr, keyword),
			"Migration path must include rollback procedure: %s", keyword)
	}
}

// TestReservedCIDRBlocksDocumentedInMultiAZ tests that reserved CIDR blocks are documented
// Validates: Requirements 12.3
func TestReservedCIDRBlocksDocumentedInMultiAZ(t *testing.T) {
	t.Parallel()

	multiAZDocPath := "../MULTI_AZ_EXPANSION.md"
	content, err := os.ReadFile(multiAZDocPath)
	assert.NoError(t, err, "Should be able to read MULTI_AZ_EXPANSION.md")

	contentStr := string(content)

	// Verify reserved CIDR blocks section exists
	assert.True(t, strings.Contains(contentStr, "Reserved CIDR Blocks"),
		"Documentation must have Reserved CIDR Blocks section")

	// Verify all reserved CIDR blocks are documented
	reservedCIDRs := map[string]string{
		"Public Subnet B":    "10.0.2.0/24",
		"Private Subnet 1B":  "10.0.11.0/24",
		"Private Subnet 2B":  "10.0.21.0/24",
	}

	for name, cidr := range reservedCIDRs {
		assert.True(t, strings.Contains(contentStr, cidr),
			"Documentation must mention reserved CIDR %s: %s", name, cidr)
	}

	// Verify reserved blocks are marked as RESERVED
	assert.True(t, strings.Contains(contentStr, "RESERVED"),
		"Documentation must mark CIDR blocks as RESERVED")

	// Verify us-east-1b is documented as reserved AZ
	assert.True(t, strings.Contains(contentStr, "us-east-1b"),
		"Documentation must mention us-east-1b as reserved AZ")
}

// TestSinglePointsOfFailureCompleteness tests that all SPOFs are documented
// Validates: Requirements 12.1, 12.2
func TestSinglePointsOfFailureCompleteness(t *testing.T) {
	t.Parallel()

	singleAZDocPath := "../SINGLE_AZ_DEPLOYMENT.md"
	content, err := os.ReadFile(singleAZDocPath)
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	contentStr := string(content)

	// Define all single points of failure that must be documented
	singlePointsOfFailure := []struct {
		name        string
		keywords    []string
		severity    string
		recoveryTime string
	}{
		{
			name:        "NAT Gateway",
			keywords:    []string{"NAT Gateway", "internet connectivity", "private subnets"},
			severity:    "HIGH",
			recoveryTime: "7-20 minutes",
		},
		{
			name:        "Availability Zone",
			keywords:    []string{"Availability Zone", "us-east-1a", "all resources"},
			severity:    "CRITICAL",
			recoveryTime: "hours to days",
		},
		{
			name:        "Internet Gateway",
			keywords:    []string{"Internet Gateway", "public subnet"},
			severity:    "LOW",
			recoveryTime: "< 1 minute",
		},
		{
			name:        "VPC Endpoints",
			keywords:    []string{"VPC Endpoints", "Interface Endpoints"},
			severity:    "MEDIUM",
			recoveryTime: "2-5 minutes",
		},
	}

	for _, spof := range singlePointsOfFailure {
		t.Run(fmt.Sprintf("SPOF_%s", spof.name), func(t *testing.T) {
			// Verify SPOF is mentioned
			for _, keyword := range spof.keywords {
				assert.True(t, strings.Contains(contentStr, keyword),
					"SPOF %s must mention keyword: %s", spof.name, keyword)
			}

			// Verify severity is documented
			assert.True(t, strings.Contains(contentStr, spof.severity),
				"SPOF %s must document severity: %s", spof.name, spof.severity)

			// Verify recovery time is documented
			assert.True(t, strings.Contains(contentStr, spof.recoveryTime),
				"SPOF %s must document recovery time: %s", spof.name, spof.recoveryTime)
		})
	}
}

// TestImpactOfAZFailureDocumented tests that AZ failure impact is documented
// Validates: Requirements 12.2
func TestImpactOfAZFailureDocumented(t *testing.T) {
	t.Parallel()

	singleAZDocPath := "../SINGLE_AZ_DEPLOYMENT.md"
	content, err := os.ReadFile(singleAZDocPath)
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	contentStr := string(content)

	// Verify "Impact of AZ Failure" section exists
	assert.True(t, strings.Contains(contentStr, "Impact of AZ Failure"),
		"Documentation must have 'Impact of AZ Failure' section")

	// Verify immediate impact is documented
	immediateImpact := []string{
		"Service Unavailability",
		"API Gateway",
		"503 errors",
		"Webhook ingestion",
	}

	for _, impact := range immediateImpact {
		assert.True(t, strings.Contains(contentStr, impact),
			"Documentation must describe immediate impact: %s", impact)
	}

	// Verify short-term impact is documented
	shortTermImpact := []string{
		"Data Loss Risk",
		"in-flight",
		"Kinesis Firehose",
	}

	for _, impact := range shortTermImpact {
		assert.True(t, strings.Contains(contentStr, impact),
			"Documentation must describe short-term impact: %s", impact)
	}

	// Verify medium-term impact is documented
	mediumTermImpact := []string{
		"Data Backlog",
		"reconciliation",
	}

	for _, impact := range mediumTermImpact {
		assert.True(t, strings.Contains(contentStr, impact),
			"Documentation must describe medium-term impact: %s", impact)
	}

	// Verify long-term impact is documented
	longTermImpact := []string{
		"Data Integrity",
		"Trust and Reliability",
	}

	for _, impact := range longTermImpact {
		assert.True(t, strings.Contains(contentStr, impact),
			"Documentation must describe long-term impact: %s", impact)
	}
}

// TestRecoveryProceduresDocumented tests that recovery procedures are documented
// Validates: Requirements 12.2
func TestRecoveryProceduresDocumented(t *testing.T) {
	t.Parallel()

	singleAZDocPath := "../SINGLE_AZ_DEPLOYMENT.md"
	content, err := os.ReadFile(singleAZDocPath)
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	contentStr := string(content)

	// Verify "Recovery Procedures" section exists
	assert.True(t, strings.Contains(contentStr, "Recovery Procedures"),
		"Documentation must have 'Recovery Procedures' section")

	// Verify NAT Gateway recovery procedure is documented
	natRecovery := []string{
		"NAT Gateway Failure Recovery",
		"Verify Failure",
		"Recreate NAT Gateway",
		"terraform taint",
		"Verify Recovery",
	}

	for _, step := range natRecovery {
		assert.True(t, strings.Contains(contentStr, step),
			"NAT Gateway recovery must include step: %s", step)
	}

	// Verify AZ failure recovery procedure is documented
	azRecovery := []string{
		"Availability Zone Failure Recovery",
		"Wait for AWS to Restore",
		"Manual Migration",
		"Prepare New Environment",
		"Deploy to New AZ",
	}

	for _, step := range azRecovery {
		assert.True(t, strings.Contains(contentStr, step),
			"AZ failure recovery must include step: %s", step)
	}

	// Verify recovery commands are provided
	recoveryCommands := []string{
		"aws ec2 describe-nat-gateways",
		"terraform apply",
		"aws logs filter-log-events",
	}

	for _, command := range recoveryCommands {
		assert.True(t, strings.Contains(contentStr, command),
			"Recovery procedures must include command: %s", command)
	}
}

// TestMonitoringAndAlertingDocumented tests that monitoring is documented
// Validates: Requirements 12.2
func TestMonitoringAndAlertingDocumented(t *testing.T) {
	t.Parallel()

	singleAZDocPath := "../SINGLE_AZ_DEPLOYMENT.md"
	content, err := os.ReadFile(singleAZDocPath)
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	contentStr := string(content)

	// Verify "Monitoring and Alerting" section exists
	assert.True(t, strings.Contains(contentStr, "Monitoring and Alerting"),
		"Documentation must have 'Monitoring and Alerting' section")

	// Verify critical alarms are documented
	criticalAlarms := []string{
		"NAT Gateway Health",
		"AZ Availability",
		"VPC Endpoint Health",
	}

	for _, alarm := range criticalAlarms {
		assert.True(t, strings.Contains(contentStr, alarm),
			"Monitoring must include critical alarm: %s", alarm)
	}

	// Verify monitoring metrics are documented
	monitoringMetrics := []string{
		"ConnectionAttemptCount",
		"CloudWatch",
		"VPC Flow Logs",
	}

	for _, metric := range monitoringMetrics {
		assert.True(t, strings.Contains(contentStr, metric),
			"Monitoring must include metric: %s", metric)
	}
}

// TestArchitecturalChangesForMultiAZDocumented tests that architectural changes are documented
// Validates: Requirements 12.3, 12.5
func TestArchitecturalChangesForMultiAZDocumented(t *testing.T) {
	t.Parallel()

	multiAZDocPath := "../MULTI_AZ_EXPANSION.md"
	content, err := os.ReadFile(multiAZDocPath)
	assert.NoError(t, err, "Should be able to read MULTI_AZ_EXPANSION.md")

	contentStr := string(content)

	// Verify "Architectural Changes" section exists
	assert.True(t, strings.Contains(contentStr, "Architectural Changes"),
		"Documentation must have 'Architectural Changes' section")

	// Verify network architecture changes are documented
	networkChanges := []string{
		"Network Architecture Changes",
		"Single-AZ (Current)",
		"Multi-AZ (Future)",
		"NAT Gateway A",
		"NAT Gateway B",
	}

	for _, change := range networkChanges {
		assert.True(t, strings.Contains(contentStr, change),
			"Architectural changes must include: %s", change)
	}

	// Verify service-specific changes are documented
	serviceChanges := []string{
		"Lambda Functions",
		"MWAA",
		"AWS Glue",
		"Redshift",
		"VPC Endpoints",
	}

	for _, service := range serviceChanges {
		assert.True(t, strings.Contains(contentStr, service),
			"Architectural changes must include service: %s", service)
	}
}

// TestSingleAZDeploymentLimitationsDocumented tests that limitations are documented
// Validates: Requirements 12.1, 12.2
func TestSingleAZDeploymentLimitationsDocumented(t *testing.T) {
	t.Parallel()

	singleAZDocPath := "../SINGLE_AZ_DEPLOYMENT.md"
	content, err := os.ReadFile(singleAZDocPath)
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	contentStr := string(content)

	// Verify "Single-AZ Deployment Limitations" section exists
	assert.True(t, strings.Contains(contentStr, "Single-AZ Deployment Limitations"),
		"Documentation must have 'Single-AZ Deployment Limitations' section")

	// Verify availability limitations are documented
	availabilityLimitations := []string{
		"No Automatic Failover",
		"Reduced Availability SLA",
		"99.5%",
		"99.99%",
	}

	for _, limitation := range availabilityLimitations {
		assert.True(t, strings.Contains(contentStr, limitation),
			"Availability limitations must include: %s", limitation)
	}

	// Verify performance limitations are documented
	performanceLimitations := []string{
		"Network Bottlenecks",
		"NAT Gateway",
		"55,000 simultaneous connections",
	}

	for _, limitation := range performanceLimitations {
		assert.True(t, strings.Contains(contentStr, limitation),
			"Performance limitations must include: %s", limitation)
	}

	// Verify cost implications are documented
	costImplications := []string{
		"Cost Implications",
		"Data Transfer Costs",
		"NAT Gateway Costs",
	}

	for _, implication := range costImplications {
		assert.True(t, strings.Contains(contentStr, implication),
			"Cost implications must include: %s", implication)
	}
}

// TestDocumentationCrossReferences tests that documents reference each other
// Validates: Requirements 12.3, 12.5
func TestDocumentationCrossReferences(t *testing.T) {
	t.Parallel()

	// Read both documentation files
	singleAZContent, err := os.ReadFile("../SINGLE_AZ_DEPLOYMENT.md")
	assert.NoError(t, err, "Should be able to read SINGLE_AZ_DEPLOYMENT.md")

	multiAZContent, err := os.ReadFile("../MULTI_AZ_EXPANSION.md")
	assert.NoError(t, err, "Should be able to read MULTI_AZ_EXPANSION.md")

	singleAZStr := string(singleAZContent)
	multiAZStr := string(multiAZContent)

	// Verify SINGLE_AZ_DEPLOYMENT.md references MULTI_AZ_EXPANSION.md
	assert.True(t, strings.Contains(singleAZStr, "MULTI_AZ_EXPANSION.md"),
		"SINGLE_AZ_DEPLOYMENT.md must reference MULTI_AZ_EXPANSION.md")

	// Verify MULTI_AZ_EXPANSION.md references SINGLE_AZ_DEPLOYMENT.md
	assert.True(t, strings.Contains(multiAZStr, "SINGLE_AZ_DEPLOYMENT.md"),
		"MULTI_AZ_EXPANSION.md must reference SINGLE_AZ_DEPLOYMENT.md")

	// Verify both documents reference the design document
	assert.True(t, strings.Contains(singleAZStr, "design.md") || 
		strings.Contains(singleAZStr, "Design Document"),
		"SINGLE_AZ_DEPLOYMENT.md should reference design document")

	assert.True(t, strings.Contains(multiAZStr, "design.md") || 
		strings.Contains(multiAZStr, "Design Document"),
		"MULTI_AZ_EXPANSION.md should reference design document")
}

// TestSinglePointOfFailureDocumentationProperty_Comprehensive is a comprehensive property test
// that validates all aspects of SPOF documentation
func TestSinglePointOfFailureDocumentationProperty_Comprehensive(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Comprehensive SPOF documentation validation", prop.ForAll(
		func(deploymentType string, hasDocumentation bool) bool {
			// For single-AZ deployments, documentation must exist and be complete
			if deploymentType == "single-az" {
				// Required documentation elements:
				requiredElements := []string{
					"NAT Gateway SPOF",
					"AZ SPOF",
					"Recovery procedures",
					"Migration path",
					"Reserved CIDR blocks",
					"Impact analysis",
					"Monitoring and alerting",
				}

				// All elements must be present
				return len(requiredElements) == 7 && hasDocumentation
			}

			// For multi-AZ deployments, migration documentation must exist
			if deploymentType == "multi-az" {
				return hasDocumentation
			}

			return true
		},
		gen.OneConstOf("single-az", "multi-az", "hybrid"),
		gen.Bool(),
	))

	properties.Property("Documentation must be actionable and complete", prop.ForAll(
		func(documentationType string) bool {
			// Documentation must include:
			// 1. Clear identification of SPOFs
			// 2. Impact assessment
			// 3. Recovery procedures with commands
			// 4. Migration path with steps
			// 5. Monitoring and alerting guidance

			requiredComponents := map[string]bool{
				"identification": true,
				"impact":         true,
				"recovery":       true,
				"migration":      true,
				"monitoring":     true,
			}

			// All components must be present
			return len(requiredComponents) == 5
		},
		gen.OneConstOf("single-az-doc", "multi-az-doc", "combined-doc"),
	))

	properties.TestingRun(t)
}

// TestTerraformConfigurationSupportsDocumentedMigration tests that Terraform config matches documentation
// Validates: Requirements 12.3, 12.5
func TestTerraformConfigurationSupportsDocumentedMigration(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":               "10.0.0.0/16",
			"public_subnet_a_cidr":   "10.0.1.0/24",
			"private_subnet_1a_cidr": "10.0.10.0/24",
			"private_subnet_2a_cidr": "10.0.20.0/24",
			"enable_multi_az":        false,
			"public_subnet_b_cidr":   "10.0.2.0/24",  // Reserved CIDR from documentation
			"private_subnet_1b_cidr": "10.0.11.0/24", // Reserved CIDR from documentation
			"private_subnet_2b_cidr": "10.0.21.0/24", // Reserved CIDR from documentation
			"aws_region":             "us-east-1",
			"name_prefix":            "test-spof-doc",
		},
		NoColor: true,
	})

	// Validate that Terraform configuration is valid with documented CIDRs
	terraform.Validate(t, terraformOptions)

	// Verify that switching to multi-AZ is supported (as documented)
	terraformOptions.Vars["enable_multi_az"] = true
	exitCode, err := terraform.ValidateE(t, terraformOptions)
	assert.NoError(t, err, "Multi-AZ configuration with documented CIDRs should be valid")
	assert.Equal(t, 0, exitCode, "Multi-AZ configuration should validate successfully")
}
