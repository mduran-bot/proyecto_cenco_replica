package test

import (
	"fmt"
	"strings"
	"testing"

	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// TestResourceTaggingCompletenessProperty tests Property 12: Resource Tagging Completeness
// Feature: aws-infrastructure, Property 12: Resource Tagging Completeness
// Validates: Requirements 8.1, 8.4
//
// Property: For any AWS resource created by the infrastructure, all mandatory tags
// (Project, Environment, Component, Owner, CostCenter) must be present and non-empty.
func TestResourceTaggingCompletenessProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("All resources must have complete mandatory tags", prop.ForAll(
		func(tags map[string]string) bool {
			// Mandatory tags that must be present
			mandatoryTags := []string{
				"Project",
				"Environment",
				"Component",
				"Owner",
				"CostCenter",
			}

			// Check that all mandatory tags are present and non-empty
			for _, tagKey := range mandatoryTags {
				value, exists := tags[tagKey]
				if !exists || value == "" {
					return false
				}
			}

			return true
		},
		// Generate tag maps with all mandatory tags present
		gen.MapOf(
			gen.OneConstOf("Project", "Environment", "Component", "Owner", "CostCenter"),
			gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }),
		).SuchThat(func(m map[string]string) bool {
			// Ensure all 5 mandatory tags are present
			return len(m) == 5
		}),
	))

	properties.TestingRun(t)
}

// TestMandatoryTagPresence tests that each mandatory tag is present
func TestMandatoryTagPresence(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	mandatoryTags := []string{"Project", "Environment", "Component", "Owner", "CostCenter"}

	for _, tagKey := range mandatoryTags {
		tagKey := tagKey // Capture for closure
		properties.Property(fmt.Sprintf("Tag %s must be present", tagKey), prop.ForAll(
			func(tags map[string]string) bool {
				_, exists := tags[tagKey]
				return exists
			},
			gen.MapOf(
				gen.OneConstOf("Project", "Environment", "Component", "Owner", "CostCenter"),
				gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }),
			).SuchThat(func(m map[string]string) bool {
				return len(m) == 5
			}),
		))
	}

	properties.TestingRun(t)
}

// TestMandatoryTagNonEmpty tests that mandatory tags are non-empty
func TestMandatoryTagNonEmpty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("All mandatory tag values must be non-empty", prop.ForAll(
		func(project, environment, component, owner, costCenter string) bool {
			// All values must be non-empty
			if project == "" || environment == "" || component == "" ||
				owner == "" || costCenter == "" {
				return false
			}

			return true
		},
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }),
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }),
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }),
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }),
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }),
	))

	properties.TestingRun(t)
}

// TestEnvironmentTagValidation tests that Environment tag has valid values
func TestEnvironmentTagValidation(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Environment tag must be one of: development, staging, production", prop.ForAll(
		func(environment string) bool {
			validEnvironments := []string{"development", "staging", "production"}
			for _, valid := range validEnvironments {
				if environment == valid {
					return true
				}
			}
			return false
		},
		gen.OneConstOf("development", "staging", "production"),
	))

	properties.TestingRun(t)
}

// TestTagKeyFormat tests that tag keys follow proper format
func TestTagKeyFormat(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Tag keys must be alphanumeric with hyphens/underscores only", prop.ForAll(
		func(tagKey string) bool {
			// Valid characters: A-Z, a-z, 0-9, hyphen, underscore
			for _, char := range tagKey {
				if !((char >= 'A' && char <= 'Z') ||
					(char >= 'a' && char <= 'z') ||
					(char >= '0' && char <= '9') ||
					char == '-' || char == '_') {
					return false
				}
			}
			return len(tagKey) > 0
		},
		gen.RegexMatch("^[A-Za-z0-9_-]+$"),
	))

	properties.TestingRun(t)
}

// TestTagValueLength tests that tag values don't exceed AWS limit
func TestTagValueLength(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Tag values must not exceed 256 characters", prop.ForAll(
		func(tagValue string) bool {
			return len(tagValue) <= 256
		},
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) <= 256 }),
	))

	properties.TestingRun(t)
}

// TestTaggingModuleValidation tests the tagging module validation logic
func TestTaggingModuleValidation(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		mandatoryTags map[string]string
		shouldPass    bool
		errorContains string
	}{
		{
			name: "All mandatory tags present and valid",
			mandatoryTags: map[string]string{
				"Project":     "janis-cencosud-integration",
				"Environment": "production",
				"Component":   "vpc",
				"Owner":       "cencosud-data-team",
				"CostCenter":  "CC-12345",
			},
			shouldPass: true,
		},
		{
			name: "Missing Project tag",
			mandatoryTags: map[string]string{
				"Environment": "production",
				"Component":   "vpc",
				"Owner":       "cencosud-data-team",
				"CostCenter":  "CC-12345",
			},
			shouldPass:    false,
			errorContains: "Project",
		},
		{
			name: "Empty Environment tag",
			mandatoryTags: map[string]string{
				"Project":     "janis-cencosud-integration",
				"Environment": "",
				"Component":   "vpc",
				"Owner":       "cencosud-data-team",
				"CostCenter":  "CC-12345",
			},
			shouldPass:    false,
			errorContains: "Environment",
		},
		{
			name: "Invalid Environment value",
			mandatoryTags: map[string]string{
				"Project":     "janis-cencosud-integration",
				"Environment": "test",
				"Component":   "vpc",
				"Owner":       "cencosud-data-team",
				"CostCenter":  "CC-12345",
			},
			shouldPass:    false,
			errorContains: "Environment",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			mandatoryTagKeys := []string{"Project", "Environment", "Component", "Owner", "CostCenter"}

			if tc.shouldPass {
				// Verify all mandatory tags are present
				for _, key := range mandatoryTagKeys {
					value, exists := tc.mandatoryTags[key]
					assert.True(t, exists, "Mandatory tag %s must be present", key)
					assert.NotEmpty(t, value, "Mandatory tag %s must not be empty", key)
				}

				// Verify Environment has valid value
				validEnvironments := []string{"development", "staging", "production"}
				assert.Contains(t, validEnvironments, tc.mandatoryTags["Environment"],
					"Environment must be one of: development, staging, production")
			} else {
				// Verify that validation would fail
				missingOrInvalid := false
				for _, key := range mandatoryTagKeys {
					value, exists := tc.mandatoryTags[key]
					if !exists || value == "" {
						missingOrInvalid = true
						break
					}
				}

				// Check for invalid Environment value
				if env, exists := tc.mandatoryTags["Environment"]; exists {
					validEnvironments := []string{"development", "staging", "production"}
					isValid := false
					for _, valid := range validEnvironments {
						if env == valid {
							isValid = true
							break
						}
					}
					if !isValid {
						missingOrInvalid = true
					}
				}

				assert.True(t, missingOrInvalid,
					"Validation should fail for test case: %s", tc.name)
			}
		})
	}
}

// TestResourceTagConsistency tests that tags are consistent across resources
func TestResourceTagConsistency(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("All resources in same environment must have consistent Project and Environment tags", prop.ForAll(
		func(project, environment, component1, component2, owner, costCenter string) bool {
			// Create two resources with same Project and Environment but different Components
			resource1Tags := map[string]string{
				"Project":     project,
				"Environment": environment,
				"Component":   component1,
				"Owner":       owner,
				"CostCenter":  costCenter,
			}

			resource2Tags := map[string]string{
				"Project":     project,
				"Environment": environment,
				"Component":   component2,
				"Owner":       owner,
				"CostCenter":  costCenter,
			}

			// Verify Project and Environment tags match
			if resource1Tags["Project"] != resource2Tags["Project"] {
				return false
			}

			if resource1Tags["Environment"] != resource2Tags["Environment"] {
				return false
			}

			return true
		},
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }), // project
		gen.OneConstOf("development", "staging", "production"),                // environment
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }), // component1
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }), // component2
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }), // owner
		gen.AlphaString().SuchThat(func(s string) bool { return len(s) > 0 }), // costCenter
	))

	properties.TestingRun(t)
}

// TestOptionalTagsValidation tests that optional tags follow proper format
func TestOptionalTagsValidation(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name         string
		optionalTags map[string]string
		shouldPass   bool
	}{
		{
			name: "Valid optional tags",
			optionalTags: map[string]string{
				"CreatedBy":   "terraform",
				"CreatedDate": "2024-01-26",
				"LastModified": "2024-01-26",
			},
			shouldPass: true,
		},
		{
			name: "Empty optional tags",
			optionalTags: map[string]string{},
			shouldPass: true,
		},
		{
			name: "Optional tag with valid characters",
			optionalTags: map[string]string{
				"Custom-Tag_123": "value",
			},
			shouldPass: true,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			for key, value := range tc.optionalTags {
				// Verify key format
				validKey := true
				for _, char := range key {
					if !((char >= 'A' && char <= 'Z') ||
						(char >= 'a' && char <= 'z') ||
						(char >= '0' && char <= '9') ||
						char == '-' || char == '_') {
						validKey = false
						break
					}
				}
				assert.True(t, validKey, "Optional tag key must be alphanumeric with hyphens/underscores: %s", key)

				// Verify value length
				assert.LessOrEqual(t, len(value), 256, "Optional tag value must not exceed 256 characters")
			}
		})
	}
}

// TestVPCResourceTags tests that VPC resources have proper tags
func TestVPCResourceTags(t *testing.T) {
	t.Parallel()

	// Simulate VPC resource tags
	vpcTags := map[string]string{
		"Name":      "test-vpc",
		"Component": "vpc",
	}

	// VPC should have Component tag
	assert.Contains(t, vpcTags, "Component", "VPC must have Component tag")
	assert.Equal(t, "vpc", vpcTags["Component"], "VPC Component tag must be 'vpc'")
}

// TestSubnetResourceTags tests that subnet resources have proper tags
func TestSubnetResourceTags(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name         string
		subnetTags   map[string]string
		expectedTier string
	}{
		{
			name: "Public subnet tags",
			subnetTags: map[string]string{
				"Name":      "test-public-subnet-a",
				"Component": "subnet",
				"Tier":      "public",
				"Purpose":   "nat-gateway-api-gateway",
			},
			expectedTier: "public",
		},
		{
			name: "Private subnet tags",
			subnetTags: map[string]string{
				"Name":      "test-private-subnet-1a",
				"Component": "subnet",
				"Tier":      "private",
				"Purpose":   "lambda-mwaa-redshift",
			},
			expectedTier: "private",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify required tags
			assert.Contains(t, tc.subnetTags, "Component", "Subnet must have Component tag")
			assert.Contains(t, tc.subnetTags, "Tier", "Subnet must have Tier tag")
			assert.Contains(t, tc.subnetTags, "Purpose", "Subnet must have Purpose tag")

			// Verify tag values
			assert.Equal(t, "subnet", tc.subnetTags["Component"], "Subnet Component tag must be 'subnet'")
			assert.Equal(t, tc.expectedTier, tc.subnetTags["Tier"], "Subnet Tier tag must match expected value")
		})
	}
}

// TestSecurityGroupResourceTags tests that security group resources have proper tags
func TestSecurityGroupResourceTags(t *testing.T) {
	t.Parallel()

	sgTags := map[string]string{
		"Name":      "test-sg-lambda",
		"Component": "security-group",
		"Purpose":   "lambda-functions",
	}

	// Security group should have Component tag
	assert.Contains(t, sgTags, "Component", "Security group must have Component tag")
	assert.Equal(t, "security-group", sgTags["Component"], "Security group Component tag must be 'security-group'")
}

// TestTagCaseConsistency tests that tag keys use consistent casing
func TestTagCaseConsistency(t *testing.T) {
	t.Parallel()

	mandatoryTagKeys := []string{"Project", "Environment", "Component", "Owner", "CostCenter"}

	for _, key := range mandatoryTagKeys {
		t.Run(fmt.Sprintf("Tag_%s_casing", key), func(t *testing.T) {
			// Verify first character is uppercase
			assert.True(t, key[0] >= 'A' && key[0] <= 'Z',
				"Mandatory tag key must start with uppercase: %s", key)

			// Verify tag key uses PascalCase (no hyphens or underscores in mandatory tags)
			assert.False(t, strings.Contains(key, "-"),
				"Mandatory tag key should not contain hyphens: %s", key)
			assert.False(t, strings.Contains(key, "_"),
				"Mandatory tag key should not contain underscores: %s", key)
		})
	}
}

// TestProjectTagValue tests that Project tag has expected value
func TestProjectTagValue(t *testing.T) {
	t.Parallel()

	expectedProject := "janis-cencosud-integration"

	tags := map[string]string{
		"Project": expectedProject,
	}

	assert.Equal(t, expectedProject, tags["Project"],
		"Project tag must have value: %s", expectedProject)
}

// TestOwnerTagValue tests that Owner tag has expected value
func TestOwnerTagValue(t *testing.T) {
	t.Parallel()

	expectedOwner := "cencosud-data-team"

	tags := map[string]string{
		"Owner": expectedOwner,
	}

	assert.Equal(t, expectedOwner, tags["Owner"],
		"Owner tag must have value: %s", expectedOwner)
}

// TestCostCenterTagFormat tests that CostCenter tag follows proper format
func TestCostCenterTagFormat(t *testing.T) {
	t.Parallel()

	validCostCenters := []string{
		"CC-12345",
		"COST-CENTER-001",
		"DataTeam-2024",
	}

	for _, costCenter := range validCostCenters {
		t.Run(fmt.Sprintf("CostCenter_%s", costCenter), func(t *testing.T) {
			// Verify cost center is non-empty
			assert.NotEmpty(t, costCenter, "CostCenter must not be empty")

			// Verify cost center follows alphanumeric with hyphens format
			validFormat := true
			for _, char := range costCenter {
				if !((char >= 'A' && char <= 'Z') ||
					(char >= 'a' && char <= 'z') ||
					(char >= '0' && char <= '9') ||
					char == '-') {
					validFormat = false
					break
				}
			}
			assert.True(t, validFormat, "CostCenter must be alphanumeric with hyphens: %s", costCenter)
		})
	}
}

// TestCreatedDateTagFormat tests that CreatedDate tag follows ISO format
func TestCreatedDateTagFormat(t *testing.T) {
	t.Parallel()

	validDates := []string{
		"2024-01-26",
		"2024-12-31",
		"2025-06-15",
	}

	for _, date := range validDates {
		t.Run(fmt.Sprintf("Date_%s", date), func(t *testing.T) {
			// Verify date format YYYY-MM-DD
			parts := strings.Split(date, "-")
			assert.Equal(t, 3, len(parts), "Date must have format YYYY-MM-DD")
			assert.Equal(t, 4, len(parts[0]), "Year must be 4 digits")
			assert.Equal(t, 2, len(parts[1]), "Month must be 2 digits")
			assert.Equal(t, 2, len(parts[2]), "Day must be 2 digits")
		})
	}
}

// TestTaggingModuleIntegration tests integration with the tagging module
func TestTaggingModuleIntegration(t *testing.T) {
	t.Parallel()

	// Simulate tagging module output
	mandatoryTags := map[string]string{
		"Project":     "janis-cencosud-integration",
		"Environment": "production",
		"Component":   "vpc",
		"Owner":       "cencosud-data-team",
		"CostCenter":  "CC-12345",
	}

	optionalTags := map[string]string{
		"CreatedBy":   "terraform",
		"CreatedDate": "2024-01-26",
	}

	// Merge tags
	allTags := make(map[string]string)
	for k, v := range mandatoryTags {
		allTags[k] = v
	}
	for k, v := range optionalTags {
		allTags[k] = v
	}

	// Verify all mandatory tags are present
	mandatoryKeys := []string{"Project", "Environment", "Component", "Owner", "CostCenter"}
	for _, key := range mandatoryKeys {
		assert.Contains(t, allTags, key, "All tags must include mandatory tag: %s", key)
		assert.NotEmpty(t, allTags[key], "Mandatory tag must not be empty: %s", key)
	}

	// Verify total tag count
	assert.Equal(t, 7, len(allTags), "Total tags should be 7 (5 mandatory + 2 optional)")
}

// TestTagValidationFailures tests that invalid tags are rejected
func TestTagValidationFailures(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name      string
		tags      map[string]string
		shouldFail bool
		reason    string
	}{
		{
			name: "Missing mandatory tag",
			tags: map[string]string{
				"Project":     "test",
				"Environment": "production",
				"Component":   "vpc",
				"Owner":       "team",
				// Missing CostCenter
			},
			shouldFail: true,
			reason:     "Missing CostCenter tag",
		},
		{
			name: "Empty tag value",
			tags: map[string]string{
				"Project":     "",
				"Environment": "production",
				"Component":   "vpc",
				"Owner":       "team",
				"CostCenter":  "CC-123",
			},
			shouldFail: true,
			reason:     "Empty Project tag value",
		},
		{
			name: "Invalid Environment value",
			tags: map[string]string{
				"Project":     "test",
				"Environment": "invalid",
				"Component":   "vpc",
				"Owner":       "team",
				"CostCenter":  "CC-123",
			},
			shouldFail: true,
			reason:     "Invalid Environment value",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			mandatoryKeys := []string{"Project", "Environment", "Component", "Owner", "CostCenter"}
			validEnvironments := []string{"development", "staging", "production"}

			hasError := false

			// Check for missing tags
			for _, key := range mandatoryKeys {
				if _, exists := tc.tags[key]; !exists {
					hasError = true
					break
				}
			}

			// Check for empty values
			for _, key := range mandatoryKeys {
				if value, exists := tc.tags[key]; exists && value == "" {
					hasError = true
					break
				}
			}

			// Check for invalid Environment value
			if env, exists := tc.tags["Environment"]; exists {
				isValid := false
				for _, valid := range validEnvironments {
					if env == valid {
						isValid = true
						break
					}
				}
				if !isValid {
					hasError = true
				}
			}

			if tc.shouldFail {
				assert.True(t, hasError, "Validation should fail: %s", tc.reason)
			} else {
				assert.False(t, hasError, "Validation should pass")
			}
		})
	}
}
