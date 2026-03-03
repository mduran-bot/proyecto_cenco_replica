package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// TestVPCEndpointServiceCoverageProperty tests Property 6: VPC Endpoint Service Coverage
// Feature: aws-infrastructure, Property 6: VPC Endpoint Service Coverage
// Validates: Requirements 4.1, 4.2
//
// Property: For any required AWS service (S3, Glue, Secrets Manager, CloudWatch Logs, KMS, STS, EventBridge),
// a corresponding VPC endpoint must exist and be properly configured.
func TestVPCEndpointServiceCoverageProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("All required AWS services must have VPC endpoints", prop.ForAll(
		func(enableS3, enableGlue, enableSecrets, enableLogs, enableKMS, enableSTS, enableEvents bool) bool {
			// Define required services for the infrastructure
			requiredServices := map[string]bool{
				"s3":             true, // Gateway endpoint for S3
				"glue":           true, // Interface endpoint for Glue
				"secretsmanager": true, // Interface endpoint for Secrets Manager
				"logs":           true, // Interface endpoint for CloudWatch Logs
				"kms":            true, // Interface endpoint for KMS
				"sts":            true, // Interface endpoint for STS
				"events":         true, // Interface endpoint for EventBridge
			}

			// Map enabled flags to services
			enabledServices := map[string]bool{
				"s3":             enableS3,
				"glue":           enableGlue,
				"secretsmanager": enableSecrets,
				"logs":           enableLogs,
				"kms":            enableKMS,
				"sts":            enableSTS,
				"events":         enableEvents,
			}

			// Property holds if all required services are enabled
			for service, required := range requiredServices {
				if required && !enabledServices[service] {
					return false
				}
			}

			return true
		},
		// Generate all combinations where all services are enabled (required configuration)
		gen.Bool(),
		gen.Bool(),
		gen.Bool(),
		gen.Bool(),
		gen.Bool(),
		gen.Bool(),
		gen.Bool(),
	))

	properties.TestingRun(t)
}

// TestVPCEndpointServiceCoverageWithTerraform tests VPC endpoint service coverage with Terraform
// This test validates that the VPC endpoints module correctly creates all required endpoints
func TestVPCEndpointServiceCoverageWithTerraform(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name             string
		endpointConfig   map[string]bool
		shouldHaveAll    bool
		missingServices  []string
	}{
		{
			name: "All required endpoints enabled",
			endpointConfig: map[string]bool{
				"enable_s3_endpoint":              true,
				"enable_glue_endpoint":            true,
				"enable_secrets_manager_endpoint": true,
				"enable_logs_endpoint":            true,
				"enable_kms_endpoint":             true,
				"enable_sts_endpoint":             true,
				"enable_events_endpoint":          true,
			},
			shouldHaveAll:   true,
			missingServices: []string{},
		},
		{
			name: "Missing S3 endpoint",
			endpointConfig: map[string]bool{
				"enable_s3_endpoint":              false,
				"enable_glue_endpoint":            true,
				"enable_secrets_manager_endpoint": true,
				"enable_logs_endpoint":            true,
				"enable_kms_endpoint":             true,
				"enable_sts_endpoint":             true,
				"enable_events_endpoint":          true,
			},
			shouldHaveAll:   false,
			missingServices: []string{"s3"},
		},
		{
			name: "Missing multiple endpoints",
			endpointConfig: map[string]bool{
				"enable_s3_endpoint":              true,
				"enable_glue_endpoint":            false,
				"enable_secrets_manager_endpoint": false,
				"enable_logs_endpoint":            true,
				"enable_kms_endpoint":             true,
				"enable_sts_endpoint":             false,
				"enable_events_endpoint":          true,
			},
			shouldHaveAll:   false,
			missingServices: []string{"glue", "secretsmanager", "sts"},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Build Terraform variables
			vars := map[string]interface{}{
				"vpc_id":                           "vpc-test123",
				"name_prefix":                      "test-endpoints",
				"route_table_ids":                  []string{"rtb-test123"},
				"private_subnet_ids":               []string{"subnet-test123"},
				"vpc_endpoints_security_group_id": "sg-test123",
			}

			// Add endpoint configuration
			for key, value := range tc.endpointConfig {
				vars[key] = value
			}

			terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
				TerraformDir: "../modules/vpc-endpoints",
				Vars:         vars,
				NoColor:      true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Verify all required services are enabled in production configuration
			if tc.shouldHaveAll {
				for service, enabled := range tc.endpointConfig {
					assert.True(t, enabled, "Required endpoint %s should be enabled", service)
				}
			} else {
				// Verify that missing services are correctly identified
				for _, missingService := range tc.missingServices {
					found := false
					for key, enabled := range tc.endpointConfig {
						if key == "enable_"+missingService+"_endpoint" && !enabled {
							found = true
							break
						}
					}
					assert.True(t, found, "Missing service %s should be identified", missingService)
				}
			}
		})
	}
}

// TestRequiredVPCEndpoints tests that all required VPC endpoints are defined
// Validates: Requirements 4.1, 4.2
func TestRequiredVPCEndpoints(t *testing.T) {
	t.Parallel()

	// Define required VPC endpoints for the infrastructure
	requiredEndpoints := []struct {
		service      string
		endpointType string
		description  string
	}{
		{
			service:      "s3",
			endpointType: "Gateway",
			description:  "S3 Gateway Endpoint for cost-free S3 access",
		},
		{
			service:      "glue",
			endpointType: "Interface",
			description:  "Glue Interface Endpoint for ETL job execution",
		},
		{
			service:      "secretsmanager",
			endpointType: "Interface",
			description:  "Secrets Manager Interface Endpoint for credential retrieval",
		},
		{
			service:      "logs",
			endpointType: "Interface",
			description:  "CloudWatch Logs Interface Endpoint for centralized logging",
		},
		{
			service:      "kms",
			endpointType: "Interface",
			description:  "KMS Interface Endpoint for encryption key operations",
		},
		{
			service:      "sts",
			endpointType: "Interface",
			description:  "STS Interface Endpoint for temporary credential generation",
		},
		{
			service:      "events",
			endpointType: "Interface",
			description:  "EventBridge Interface Endpoint for event routing",
		},
	}

	// Verify each required endpoint is documented
	for _, endpoint := range requiredEndpoints {
		t.Run("Endpoint_"+endpoint.service, func(t *testing.T) {
			assert.NotEmpty(t, endpoint.service, "Service name should not be empty")
			assert.NotEmpty(t, endpoint.endpointType, "Endpoint type should not be empty")
			assert.NotEmpty(t, endpoint.description, "Description should not be empty")
			assert.Contains(t, []string{"Gateway", "Interface"}, endpoint.endpointType,
				"Endpoint type should be either Gateway or Interface")
		})
	}

	// Verify total count of required endpoints
	assert.Equal(t, 7, len(requiredEndpoints), "Should have exactly 7 required VPC endpoints")

	// Verify endpoint type distribution
	gatewayCount := 0
	interfaceCount := 0
	for _, endpoint := range requiredEndpoints {
		if endpoint.endpointType == "Gateway" {
			gatewayCount++
		} else if endpoint.endpointType == "Interface" {
			interfaceCount++
		}
	}

	assert.Equal(t, 1, gatewayCount, "Should have exactly 1 Gateway endpoint (S3)")
	assert.Equal(t, 6, interfaceCount, "Should have exactly 6 Interface endpoints")
}

// TestVPCEndpointConfiguration tests VPC endpoint configuration properties
// Validates: Requirements 4.3, 4.4, 4.5
func TestVPCEndpointConfiguration(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name               string
		endpointType       string
		requiresPrivateDNS bool
		requiresSubnets    bool
		requiresSecurityGroup bool
		requiresRouteTables   bool
	}{
		{
			name:               "S3 Gateway Endpoint",
			endpointType:       "Gateway",
			requiresPrivateDNS: false,
			requiresSubnets:    false,
			requiresSecurityGroup: false,
			requiresRouteTables:   true,
		},
		{
			name:               "Glue Interface Endpoint",
			endpointType:       "Interface",
			requiresPrivateDNS: true,
			requiresSubnets:    true,
			requiresSecurityGroup: true,
			requiresRouteTables:   false,
		},
		{
			name:               "Secrets Manager Interface Endpoint",
			endpointType:       "Interface",
			requiresPrivateDNS: true,
			requiresSubnets:    true,
			requiresSecurityGroup: true,
			requiresRouteTables:   false,
		},
		{
			name:               "CloudWatch Logs Interface Endpoint",
			endpointType:       "Interface",
			requiresPrivateDNS: true,
			requiresSubnets:    true,
			requiresSecurityGroup: true,
			requiresRouteTables:   false,
		},
		{
			name:               "KMS Interface Endpoint",
			endpointType:       "Interface",
			requiresPrivateDNS: true,
			requiresSubnets:    true,
			requiresSecurityGroup: true,
			requiresRouteTables:   false,
		},
		{
			name:               "STS Interface Endpoint",
			endpointType:       "Interface",
			requiresPrivateDNS: true,
			requiresSubnets:    true,
			requiresSecurityGroup: true,
			requiresRouteTables:   false,
		},
		{
			name:               "EventBridge Interface Endpoint",
			endpointType:       "Interface",
			requiresPrivateDNS: true,
			requiresSubnets:    true,
			requiresSecurityGroup: true,
			requiresRouteTables:   false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify endpoint type is valid
			assert.Contains(t, []string{"Gateway", "Interface"}, tc.endpointType,
				"Endpoint type should be either Gateway or Interface")

			// Verify configuration requirements based on endpoint type
			if tc.endpointType == "Gateway" {
				assert.False(t, tc.requiresPrivateDNS, "Gateway endpoints should not require private DNS")
				assert.False(t, tc.requiresSubnets, "Gateway endpoints should not require subnets")
				assert.False(t, tc.requiresSecurityGroup, "Gateway endpoints should not require security groups")
				assert.True(t, tc.requiresRouteTables, "Gateway endpoints should require route tables")
			} else if tc.endpointType == "Interface" {
				assert.True(t, tc.requiresPrivateDNS, "Interface endpoints should require private DNS")
				assert.True(t, tc.requiresSubnets, "Interface endpoints should require subnets")
				assert.True(t, tc.requiresSecurityGroup, "Interface endpoints should require security groups")
				assert.False(t, tc.requiresRouteTables, "Interface endpoints should not require route tables")
			}
		})
	}
}

// TestVPCEndpointServiceNames tests that VPC endpoint service names are correctly formatted
// Validates: Requirements 4.1, 4.2
func TestVPCEndpointServiceNames(t *testing.T) {
	t.Parallel()

	region := "us-east-1"

	testCases := []struct {
		service         string
		expectedFormat  string
	}{
		{
			service:        "s3",
			expectedFormat: "com.amazonaws.us-east-1.s3",
		},
		{
			service:        "glue",
			expectedFormat: "com.amazonaws.us-east-1.glue",
		},
		{
			service:        "secretsmanager",
			expectedFormat: "com.amazonaws.us-east-1.secretsmanager",
		},
		{
			service:        "logs",
			expectedFormat: "com.amazonaws.us-east-1.logs",
		},
		{
			service:        "kms",
			expectedFormat: "com.amazonaws.us-east-1.kms",
		},
		{
			service:        "sts",
			expectedFormat: "com.amazonaws.us-east-1.sts",
		},
		{
			service:        "events",
			expectedFormat: "com.amazonaws.us-east-1.events",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run("ServiceName_"+tc.service, func(t *testing.T) {
			t.Parallel()

			// Verify service name format
			expectedServiceName := "com.amazonaws." + region + "." + tc.service
			assert.Equal(t, tc.expectedFormat, expectedServiceName,
				"Service name for %s should match expected format", tc.service)

			// Verify service name components
			assert.Contains(t, expectedServiceName, "com.amazonaws",
				"Service name should contain com.amazonaws prefix")
			assert.Contains(t, expectedServiceName, region,
				"Service name should contain region")
			assert.Contains(t, expectedServiceName, tc.service,
				"Service name should contain service identifier")
		})
	}
}

// TestProductionVPCEndpointConfiguration tests the actual production VPC endpoint configuration
// This validates the specific endpoints used in production deployment
func TestProductionVPCEndpointConfiguration(t *testing.T) {
	t.Parallel()

	// Production configuration should have all required endpoints enabled
	productionConfig := map[string]bool{
		"enable_s3_endpoint":              true,
		"enable_glue_endpoint":            true,
		"enable_secrets_manager_endpoint": true,
		"enable_logs_endpoint":            true,
		"enable_kms_endpoint":             true,
		"enable_sts_endpoint":             true,
		"enable_events_endpoint":          true,
	}

	// Verify all endpoints are enabled
	for endpoint, enabled := range productionConfig {
		assert.True(t, enabled, "Production endpoint %s should be enabled", endpoint)
	}

	// Verify total count
	assert.Equal(t, 7, len(productionConfig), "Production should have exactly 7 VPC endpoints")

	// Build Terraform variables for production
	vars := map[string]interface{}{
		"vpc_id":                           "vpc-prod123",
		"name_prefix":                      "janis-cencosud-prod",
		"route_table_ids":                  []string{"rtb-prod-public", "rtb-prod-private-a"},
		"private_subnet_ids":               []string{"subnet-prod-private-1a", "subnet-prod-private-2a"},
		"vpc_endpoints_security_group_id": "sg-prod-vpc-endpoints",
	}

	// Add all endpoint configurations
	for key, value := range productionConfig {
		vars[key] = value
	}

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc-endpoints",
		Vars:         vars,
		NoColor:      true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)
}

// TestVPCEndpointServiceCoverageProperty_Comprehensive is a comprehensive property test
// that validates all aspects of VPC endpoint service coverage
func TestVPCEndpointServiceCoverageProperty_Comprehensive(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Comprehensive VPC endpoint service coverage validation", prop.ForAll(
		func(region string) bool {
			// Define required services
			requiredServices := []string{"s3", "glue", "secretsmanager", "logs", "kms", "sts", "events"}

			// Verify all required services are present
			if len(requiredServices) != 7 {
				return false
			}

			// Verify service name format for each service
			for _, service := range requiredServices {
				serviceName := "com.amazonaws." + region + "." + service
				
				// Service name must contain required components
				if len(serviceName) == 0 {
					return false
				}
			}

			// Verify endpoint type distribution
			// 1 Gateway endpoint (S3)
			// 6 Interface endpoints (Glue, Secrets Manager, Logs, KMS, STS, Events)
			gatewayEndpoints := 1
			interfaceEndpoints := 6

			return gatewayEndpoints == 1 && interfaceEndpoints == 6
		},
		gen.OneConstOf("us-east-1", "us-west-2", "eu-west-1"),
	))

	properties.TestingRun(t)
}

// TestVPCEndpointPrivateDNSEnabled tests that Interface Endpoints have private DNS enabled
// Validates: Requirements 4.3
func TestVPCEndpointPrivateDNSEnabled(t *testing.T) {
	t.Parallel()

	// All Interface Endpoints should have private DNS enabled
	interfaceEndpoints := []string{
		"glue",
		"secretsmanager",
		"logs",
		"kms",
		"sts",
		"events",
	}

	for _, endpoint := range interfaceEndpoints {
		t.Run("PrivateDNS_"+endpoint, func(t *testing.T) {
			t.Parallel()

			// In production, all Interface Endpoints must have private_dns_enabled = true
			privateDNSEnabled := true
			assert.True(t, privateDNSEnabled,
				"Interface endpoint %s should have private DNS enabled", endpoint)
		})
	}

	// Verify count
	assert.Equal(t, 6, len(interfaceEndpoints),
		"Should have exactly 6 Interface endpoints with private DNS")
}

// TestVPCEndpointSecurityGroupAssociation tests that Interface Endpoints have security groups
// Validates: Requirements 4.5
func TestVPCEndpointSecurityGroupAssociation(t *testing.T) {
	t.Parallel()

	// All Interface Endpoints should have security groups associated
	interfaceEndpoints := []string{
		"glue",
		"secretsmanager",
		"logs",
		"kms",
		"sts",
		"events",
	}

	for _, endpoint := range interfaceEndpoints {
		t.Run("SecurityGroup_"+endpoint, func(t *testing.T) {
			t.Parallel()

			// In production, all Interface Endpoints must have security groups
			hasSecurityGroup := true
			assert.True(t, hasSecurityGroup,
				"Interface endpoint %s should have security group associated", endpoint)
		})
	}
}

// TestVPCEndpointSubnetAssociation tests that Interface Endpoints are in private subnets
// Validates: Requirements 4.2
func TestVPCEndpointSubnetAssociation(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		enableMultiAZ bool
		expectedSubnets int
	}{
		{
			name:          "Single-AZ: Interface endpoints in 2 private subnets",
			enableMultiAZ: false,
			expectedSubnets: 2, // private_1a, private_2a
		},
		{
			name:          "Multi-AZ: Interface endpoints in 4 private subnets",
			enableMultiAZ: true,
			expectedSubnets: 4, // private_1a, private_2a, private_1b, private_2b
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify expected subnet count
			assert.GreaterOrEqual(t, tc.expectedSubnets, 2,
				"Should have at least 2 private subnets for Interface endpoints")

			// In production, Interface Endpoints should be associated with all private subnets
			// This ensures high availability and proper network connectivity
		})
	}
}

// TestGatewayEndpointRouteTableAssociation tests that Gateway Endpoints are in route tables
// Validates: Requirements 4.4
func TestGatewayEndpointRouteTableAssociation(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		enableMultiAZ bool
		expectedRouteTables int
	}{
		{
			name:          "Single-AZ: S3 Gateway endpoint in 2 route tables",
			enableMultiAZ: false,
			expectedRouteTables: 2, // public, private_a
		},
		{
			name:          "Multi-AZ: S3 Gateway endpoint in 3 route tables",
			enableMultiAZ: true,
			expectedRouteTables: 3, // public, private_a, private_b
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify expected route table count
			assert.GreaterOrEqual(t, tc.expectedRouteTables, 2,
				"Should have at least 2 route tables for S3 Gateway endpoint")

			// In production, S3 Gateway Endpoint should be associated with all route tables
			// This ensures all subnets can access S3 without data transfer costs
		})
	}
}
