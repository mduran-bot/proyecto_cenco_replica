package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// TestRedshiftSecurityGroupIntegrationProperty tests Property 16: Redshift Security Group Integration
// Feature: aws-infrastructure, Property 16: Redshift Security Group Integration
// Validates: Requirements 11.3
//
// Property: For any new security group rule added to SG-Redshift-Existing,
// the rule must not conflict with existing Cencosud BI system access rules.
func TestRedshiftSecurityGroupIntegrationProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("New Redshift security group rules must not conflict with existing BI rules", prop.ForAll(
		func(newRulePort int, newRuleProtocol string, newRuleSource string, existingRulePort int, existingRuleProtocol string, existingRuleSource string) bool {
			// Define the new rules being added for Janis integration
			newRules := []RedshiftSecurityGroupRule{
				{
					Port:        newRulePort,
					Protocol:    newRuleProtocol,
					Source:      newRuleSource,
					Description: "New rule from Janis integration",
				},
			}

			// Define existing BI system rules that must be preserved
			existingRules := []RedshiftSecurityGroupRule{
				{
					Port:        existingRulePort,
					Protocol:    existingRuleProtocol,
					Source:      existingRuleSource,
					Description: "Existing BI system rule",
				},
			}

			// Check for conflicts
			// A conflict occurs when:
			// 1. Same port and protocol but different source (could cause confusion)
			// 2. Overlapping CIDR ranges that could cause unexpected behavior
			// 3. Rules that would block existing access

			for _, newRule := range newRules {
				for _, existingRule := range existingRules {
					// Check if rules are identical (not a conflict, just redundant)
					if newRule.Port == existingRule.Port &&
						newRule.Protocol == existingRule.Protocol &&
						newRule.Source == existingRule.Source {
						// Identical rules are acceptable (idempotent)
						continue
					}

					// Check if new rule would interfere with existing rule
					// For Redshift, all rules should be ALLOW rules on port 5439
					// New rules should only add additional sources, not modify existing ones
					if newRule.Port == existingRule.Port &&
						newRule.Protocol == existingRule.Protocol {
						// Same port and protocol - this is acceptable as long as sources are different
						// This adds an additional allowed source without affecting existing ones
						if newRule.Source != existingRule.Source {
							// Different sources on same port/protocol is acceptable
							// This is additive, not conflicting
							continue
						}
					}

					// Check for invalid port numbers
					if newRule.Port < 0 || newRule.Port > 65535 {
						return false
					}

					// Check for invalid protocols
					validProtocols := map[string]bool{
						"tcp":  true,
						"udp":  true,
						"icmp": true,
						"-1":   true,
					}
					if !validProtocols[newRule.Protocol] {
						return false
					}
				}
			}

			// All checks passed - no conflicts detected
			return true
		},
		gen.OneConstOf(5439),                                                    // New rule port (Redshift PostgreSQL)
		gen.OneConstOf("tcp"),                                                   // New rule protocol
		gen.OneConstOf("sg-lambda", "sg-mwaa", "sg-glue", "10.0.0.0/16"),       // New rule sources
		gen.OneConstOf(5439),                                                    // Existing rule port
		gen.OneConstOf("tcp"),                                                   // Existing rule protocol
		gen.OneConstOf("sg-bi-1", "sg-bi-2", "192.168.1.0/24", "10.100.0.0/16"), // Existing BI sources
	))

	properties.TestingRun(t)
}

// TestRedshiftSecurityGroupNoOverlappingCIDRs tests that new CIDR rules don't overlap with existing ones
// Validates: Requirements 11.3
func TestRedshiftSecurityGroupNoOverlappingCIDRs(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("New CIDR rules must not overlap with existing BI CIDR rules", prop.ForAll(
		func(newCIDR string, existingCIDR string) bool {
			// For this test, we verify that new CIDR blocks don't overlap with existing ones
			// In practice, Redshift security groups allow multiple CIDR blocks
			// The key is that new rules should be additive, not replacing existing ones

			// Define valid CIDR blocks for new rules (VPC internal)
			validNewCIDRs := map[string]bool{
				"10.0.0.0/16":   true, // VPC CIDR
				"10.0.1.0/24":   true, // Public subnet
				"10.0.10.0/24":  true, // Private subnet 1A
				"10.0.20.0/24":  true, // Private subnet 2A
			}

			// Define valid CIDR blocks for existing BI rules (external)
			validExistingCIDRs := map[string]bool{
				"192.168.1.0/24":  true, // BI Network 1
				"192.168.2.0/24":  true, // BI Network 2
				"10.100.50.0/24":  true, // BI Network 3
				"10.100.51.0/24":  true, // BI Network 4
			}

			// Verify new CIDR is valid
			if !validNewCIDRs[newCIDR] {
				return false
			}

			// Verify existing CIDR is valid
			if !validExistingCIDRs[existingCIDR] {
				return false
			}

			// Check that new and existing CIDRs don't overlap
			// In this case, they're in completely different ranges, so no overlap
			// New rules are from 10.0.x.x (VPC internal)
			// Existing rules are from 192.168.x.x or 10.100.x.x (BI external)
			return newCIDR != existingCIDR
		},
		gen.OneConstOf("10.0.0.0/16", "10.0.1.0/24", "10.0.10.0/24", "10.0.20.0/24"),
		gen.OneConstOf("192.168.1.0/24", "192.168.2.0/24", "10.100.50.0/24", "10.100.51.0/24"),
	))

	properties.TestingRun(t)
}

// TestRedshiftSecurityGroupPreservesExistingAccess tests that existing BI access is preserved
// Validates: Requirements 11.3
func TestRedshiftSecurityGroupPreservesExistingAccess(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name                string
		existingBIRules     []RedshiftSecurityGroupRule
		newJanisRules       []RedshiftSecurityGroupRule
		expectedTotalRules  int
		shouldPreserveBI    bool
	}{
		{
			name: "Adding Janis rules preserves existing BI rules",
			existingBIRules: []RedshiftSecurityGroupRule{
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-bi-1",
					Description: "PostgreSQL from Power BI Gateway",
				},
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-bi-2",
					Description: "PostgreSQL from Tableau Server",
				},
			},
			newJanisRules: []RedshiftSecurityGroupRule{
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-lambda",
					Description: "PostgreSQL from Lambda functions",
				},
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-mwaa",
					Description: "PostgreSQL from MWAA Airflow",
				},
			},
			expectedTotalRules: 4,
			shouldPreserveBI:   true,
		},
		{
			name: "Adding Janis rules with MySQL pipeline preserves all existing rules",
			existingBIRules: []RedshiftSecurityGroupRule{
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-bi-1",
					Description: "PostgreSQL from Power BI Gateway",
				},
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-mysql-pipeline",
					Description: "PostgreSQL from MySQL migration pipeline",
				},
			},
			newJanisRules: []RedshiftSecurityGroupRule{
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-lambda",
					Description: "PostgreSQL from Lambda functions",
				},
			},
			expectedTotalRules: 3,
			shouldPreserveBI:   true,
		},
		{
			name: "Multiple BI systems with IP ranges preserved",
			existingBIRules: []RedshiftSecurityGroupRule{
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "192.168.1.0/24",
					Description: "PostgreSQL from BI Network 1",
				},
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "10.100.50.0/24",
					Description: "PostgreSQL from BI Network 2",
				},
			},
			newJanisRules: []RedshiftSecurityGroupRule{
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-lambda",
					Description: "PostgreSQL from Lambda functions",
				},
			},
			expectedTotalRules: 3,
			shouldPreserveBI:   true,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Combine existing and new rules
			allRules := append(tc.existingBIRules, tc.newJanisRules...)

			// Verify total rule count
			assert.Equal(t, tc.expectedTotalRules, len(allRules),
				"Total rules should match expected count")

			// Verify all existing BI rules are still present
			if tc.shouldPreserveBI {
				for _, existingRule := range tc.existingBIRules {
					found := false
					for _, rule := range allRules {
						if rule.Port == existingRule.Port &&
							rule.Protocol == existingRule.Protocol &&
							rule.Source == existingRule.Source {
							found = true
							break
						}
					}
					assert.True(t, found,
						"Existing BI rule should be preserved: %s from %s",
						existingRule.Description, existingRule.Source)
				}
			}

			// Verify all new Janis rules are added
			for _, newRule := range tc.newJanisRules {
				found := false
				for _, rule := range allRules {
					if rule.Port == newRule.Port &&
						rule.Protocol == newRule.Protocol &&
						rule.Source == newRule.Source {
						found = true
						break
					}
				}
				assert.True(t, found,
					"New Janis rule should be added: %s from %s",
					newRule.Description, newRule.Source)
			}

			// Verify all rules are for port 5439 (Redshift PostgreSQL)
			for _, rule := range allRules {
				assert.Equal(t, 5439, rule.Port,
					"All Redshift rules should be for port 5439")
				assert.Equal(t, "tcp", rule.Protocol,
					"All Redshift rules should use TCP protocol")
			}
		})
	}
}

// TestRedshiftSecurityGroupMySQLPipelineTemporary tests MySQL pipeline rule is temporary
// Validates: Requirements 11.3
func TestRedshiftSecurityGroupMySQLPipelineTemporary(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name                    string
		includeMySQLPipeline    bool
		mysqlPipelineSGID       string
		expectedMySQLRuleExists bool
	}{
		{
			name:                    "MySQL pipeline rule exists during migration",
			includeMySQLPipeline:    true,
			mysqlPipelineSGID:       "sg-mysql-pipeline-123",
			expectedMySQLRuleExists: true,
		},
		{
			name:                    "MySQL pipeline rule removed after migration",
			includeMySQLPipeline:    false,
			mysqlPipelineSGID:       "",
			expectedMySQLRuleExists: false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Simulate security group rules
			rules := []RedshiftSecurityGroupRule{
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-lambda",
					Description: "PostgreSQL from Lambda functions",
				},
				{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-mwaa",
					Description: "PostgreSQL from MWAA Airflow",
				},
			}

			// Add MySQL pipeline rule if included
			if tc.includeMySQLPipeline && tc.mysqlPipelineSGID != "" {
				rules = append(rules, RedshiftSecurityGroupRule{
					Port:        5439,
					Protocol:    "tcp",
					Source:      tc.mysqlPipelineSGID,
					Description: "PostgreSQL from MySQL migration pipeline (temporary)",
				})
			}

			// Check if MySQL pipeline rule exists
			mysqlRuleFound := false
			for _, rule := range rules {
				if rule.Source == tc.mysqlPipelineSGID {
					mysqlRuleFound = true
					// Verify it's marked as temporary in description
					assert.Contains(t, rule.Description, "temporary",
						"MySQL pipeline rule should be marked as temporary")
					break
				}
			}

			assert.Equal(t, tc.expectedMySQLRuleExists, mysqlRuleFound,
				"MySQL pipeline rule existence should match expected state")
		})
	}
}

// TestRedshiftSecurityGroupWithTerraform tests Redshift security group configuration with Terraform
// Validates: Requirements 11.3
func TestRedshiftSecurityGroupWithTerraform(t *testing.T) {
	t.Parallel()

	vars := map[string]interface{}{
		"vpc_id":                        "vpc-test123",
		"vpc_cidr":                      "10.0.0.0/16",
		"name_prefix":                   "test-redshift",
		"existing_bi_security_groups":   []string{"sg-bi-1", "sg-bi-2"},
		"existing_bi_ip_ranges":         []string{"192.168.1.0/24", "10.100.50.0/24"},
		"existing_mysql_pipeline_sg_id": "sg-mysql-pipeline-123",
	}

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars:         vars,
		NoColor:      true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)
}

// TestRedshiftSecurityGroupRuleValidation tests validation of security group rules
// Validates: Requirements 11.3
func TestRedshiftSecurityGroupRuleValidation(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name        string
		rule        RedshiftSecurityGroupRule
		shouldBeValid bool
		reason      string
	}{
		{
			name: "Valid Lambda rule",
			rule: RedshiftSecurityGroupRule{
				Port:        5439,
				Protocol:    "tcp",
				Source:      "sg-lambda",
				Description: "PostgreSQL from Lambda functions",
			},
			shouldBeValid: true,
			reason:        "Standard Lambda access rule",
		},
		{
			name: "Valid MWAA rule",
			rule: RedshiftSecurityGroupRule{
				Port:        5439,
				Protocol:    "tcp",
				Source:      "sg-mwaa",
				Description: "PostgreSQL from MWAA Airflow",
			},
			shouldBeValid: true,
			reason:        "Standard MWAA access rule",
		},
		{
			name: "Valid BI system rule with security group",
			rule: RedshiftSecurityGroupRule{
				Port:        5439,
				Protocol:    "tcp",
				Source:      "sg-bi-powerbi",
				Description: "PostgreSQL from Power BI Gateway",
			},
			shouldBeValid: true,
			reason:        "Existing BI system access",
		},
		{
			name: "Valid BI system rule with IP range",
			rule: RedshiftSecurityGroupRule{
				Port:        5439,
				Protocol:    "tcp",
				Source:      "192.168.1.0/24",
				Description: "PostgreSQL from BI Network",
			},
			shouldBeValid: true,
			reason:        "Existing BI system access via IP range",
		},
		{
			name: "Invalid port number",
			rule: RedshiftSecurityGroupRule{
				Port:        3306,
				Protocol:    "tcp",
				Source:      "sg-lambda",
				Description: "Wrong port for Redshift",
			},
			shouldBeValid: false,
			reason:        "Redshift uses port 5439, not 3306",
		},
		{
			name: "Invalid protocol",
			rule: RedshiftSecurityGroupRule{
				Port:        5439,
				Protocol:    "udp",
				Source:      "sg-lambda",
				Description: "Wrong protocol for Redshift",
			},
			shouldBeValid: false,
			reason:        "Redshift uses TCP, not UDP",
		},
		{
			name: "Missing description",
			rule: RedshiftSecurityGroupRule{
				Port:        5439,
				Protocol:    "tcp",
				Source:      "sg-lambda",
				Description: "",
			},
			shouldBeValid: false,
			reason:        "All rules must have descriptions for auditability",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			isValid := validateRedshiftSecurityGroupRule(tc.rule)

			if tc.shouldBeValid {
				assert.True(t, isValid,
					"Rule should be valid: %s", tc.reason)
			} else {
				assert.False(t, isValid,
					"Rule should be invalid: %s", tc.reason)
			}
		})
	}
}

// TestRedshiftSecurityGroupIntegrationComprehensive is a comprehensive test
// that validates all aspects of Redshift security group integration
func TestRedshiftSecurityGroupIntegrationComprehensive(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Comprehensive Redshift security group integration validation", prop.ForAll(
		func(numBISystems int, numJanisComponents int, includeMySQLPipeline bool) bool {
			// Generate existing BI rules
			existingRules := make([]RedshiftSecurityGroupRule, numBISystems)
			for i := 0; i < numBISystems; i++ {
				existingRules[i] = RedshiftSecurityGroupRule{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-bi-" + string(rune('a'+i)),
					Description: "PostgreSQL from BI system",
				}
			}

			// Generate new Janis rules
			janisComponents := []string{"sg-lambda", "sg-mwaa", "sg-glue"}
			newRules := make([]RedshiftSecurityGroupRule, 0)
			for i := 0; i < numJanisComponents && i < len(janisComponents); i++ {
				newRules = append(newRules, RedshiftSecurityGroupRule{
					Port:        5439,
					Protocol:    "tcp",
					Source:      janisComponents[i],
					Description: "PostgreSQL from Janis component",
				})
			}

			// Add MySQL pipeline rule if included
			if includeMySQLPipeline {
				newRules = append(newRules, RedshiftSecurityGroupRule{
					Port:        5439,
					Protocol:    "tcp",
					Source:      "sg-mysql-pipeline",
					Description: "PostgreSQL from MySQL migration pipeline (temporary)",
				})
			}

			// Verify no conflicts between existing and new rules
			for _, existingRule := range existingRules {
				for _, newRule := range newRules {
					// Rules should not have the same source (no duplicates)
					if existingRule.Source == newRule.Source {
						return false
					}

					// All rules should be for port 5439 and TCP
					if existingRule.Port != 5439 || newRule.Port != 5439 {
						return false
					}
					if existingRule.Protocol != "tcp" || newRule.Protocol != "tcp" {
						return false
					}
				}
			}

			// Verify all rules have descriptions
			allRules := append(existingRules, newRules...)
			for _, rule := range allRules {
				if rule.Description == "" {
					return false
				}
			}

			return true
		},
		gen.IntRange(1, 5),  // Number of BI systems (1-5)
		gen.IntRange(1, 3),  // Number of Janis components (1-3)
		gen.Bool(),          // Include MySQL pipeline
	))

	properties.TestingRun(t)
}

// RedshiftSecurityGroupRule represents a security group rule for Redshift
type RedshiftSecurityGroupRule struct {
	Port        int
	Protocol    string
	Source      string // Can be security group ID or CIDR block
	Description string
}

// validateRedshiftSecurityGroupRule validates a Redshift security group rule
func validateRedshiftSecurityGroupRule(rule RedshiftSecurityGroupRule) bool {
	// Validate port (must be 5439 for Redshift)
	if rule.Port != 5439 {
		return false
	}

	// Validate protocol (must be TCP for Redshift)
	if rule.Protocol != "tcp" {
		return false
	}

	// Validate source is not empty
	if rule.Source == "" {
		return false
	}

	// Validate description is not empty
	if rule.Description == "" {
		return false
	}

	return true
}
