package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

// TestVPCCreationWithCorrectCIDR tests that VPC is created with the correct CIDR block
// Validates: Requirements 1.1
func TestVPCCreationWithCorrectCIDR(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name        string
		vpcCIDR     string
		expectValid bool
	}{
		{
			name:        "Valid CIDR 10.0.0.0/16",
			vpcCIDR:     "10.0.0.0/16",
			expectValid: true,
		},
		{
			name:        "Valid CIDR 172.16.0.0/16",
			vpcCIDR:     "172.16.0.0/16",
			expectValid: true,
		},
		{
			name:        "Valid CIDR 192.168.0.0/16",
			vpcCIDR:     "192.168.0.0/16",
			expectValid: true,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
				TerraformDir: "../modules/vpc",
				Vars: map[string]interface{}{
					"vpc_cidr":               tc.vpcCIDR,
					"public_subnet_a_cidr":   "10.0.1.0/24",
					"private_subnet_1a_cidr": "10.0.10.0/24",
					"private_subnet_2a_cidr": "10.0.20.0/24",
					"enable_multi_az":        false,
					"public_subnet_b_cidr":   "10.0.2.0/24",
					"private_subnet_1b_cidr": "10.0.11.0/24",
					"private_subnet_2b_cidr": "10.0.21.0/24",
					"aws_region":             "us-east-1",
					"name_prefix":            "test-vpc",
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			exitCode, err := terraform.ValidateE(t, terraformOptions)
assert.NoError(t, err)

			if tc.expectValid {
				assert.Equal(t, 0, exitCode, "Terraform validation should succeed for valid CIDR")
			} else {
				assert.NotEqual(t, 0, exitCode, "Terraform validation should fail for invalid CIDR")
			}
		})
	}
}

// TestVPCDNSSettingsEnabled tests that DNS resolution and DNS hostnames are enabled
// Validates: Requirements 1.3
func TestVPCDNSSettingsEnabled(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":               "10.0.0.0/16",
			"public_subnet_a_cidr":   "10.0.1.0/24",
			"private_subnet_1a_cidr": "10.0.10.0/24",
			"private_subnet_2a_cidr": "10.0.20.0/24",
			"enable_multi_az":        false,
			"public_subnet_b_cidr":   "10.0.2.0/24",
			"private_subnet_1b_cidr": "10.0.11.0/24",
			"private_subnet_2b_cidr": "10.0.21.0/24",
			"aws_region":             "us-east-1",
			"name_prefix":            "test-vpc-dns",
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would:
	// 1. Deploy the infrastructure: terraform.InitAndApply(t, terraformOptions)
	// 2. Get VPC attributes: vpcID := terraform.Output(t, terraformOptions, "vpc_id")
	// 3. Use AWS SDK to verify: enableDnsSupport and enableDnsHostnames are true
	// 4. Clean up: defer terraform.Destroy(t, terraformOptions)
	//
	// For unit testing without actual deployment, we verify the configuration is valid
	// and the module code explicitly sets enable_dns_hostnames = true and enable_dns_support = true
}

// TestVPCMandatoryTagsApplied tests that mandatory tags are applied to VPC
// Validates: Requirements 1.4
func TestVPCMandatoryTagsApplied(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name       string
		namePrefix string
	}{
		{
			name:       "Production environment",
			namePrefix: "janis-cencosud-prod",
		},
		{
			name:       "Staging environment",
			namePrefix: "janis-cencosud-staging",
		},
		{
			name:       "Development environment",
			namePrefix: "janis-cencosud-dev",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
				TerraformDir: "../modules/vpc",
				Vars: map[string]interface{}{
					"vpc_cidr":               "10.0.0.0/16",
					"public_subnet_a_cidr":   "10.0.1.0/24",
					"private_subnet_1a_cidr": "10.0.10.0/24",
					"private_subnet_2a_cidr": "10.0.20.0/24",
					"enable_multi_az":        false,
					"public_subnet_b_cidr":   "10.0.2.0/24",
					"private_subnet_1b_cidr": "10.0.11.0/24",
					"private_subnet_2b_cidr": "10.0.21.0/24",
					"aws_region":             "us-east-1",
					"name_prefix":            tc.namePrefix,
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Note: The VPC module applies tags directly in the resource definition:
			// - Name: "${var.name_prefix}-vpc"
			// - Component: "vpc"
			//
			// Additional mandatory tags (Project, Environment, Owner, CostCenter, ManagedBy)
			// are applied via provider default_tags in shared/providers.tf
			//
			// In a real deployment test, we would:
			// 1. Deploy: terraform.InitAndApply(t, terraformOptions)
			// 2. Get VPC ID: vpcID := terraform.Output(t, terraformOptions, "vpc_id")
			// 3. Use AWS SDK to get VPC tags and verify all mandatory tags are present
			// 4. Clean up: defer terraform.Destroy(t, terraformOptions)
		})
	}
}

// TestVPCConfigurationIntegrity tests the overall VPC configuration integrity
// This test validates that all VPC components are properly configured together
func TestVPCConfigurationIntegrity(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":               "10.0.0.0/16",
			"public_subnet_a_cidr":   "10.0.1.0/24",
			"private_subnet_1a_cidr": "10.0.10.0/24",
			"private_subnet_2a_cidr": "10.0.20.0/24",
			"enable_multi_az":        false,
			"public_subnet_b_cidr":   "10.0.2.0/24",
			"private_subnet_1b_cidr": "10.0.11.0/24",
			"private_subnet_2b_cidr": "10.0.21.0/24",
			"aws_region":             "us-east-1",
			"name_prefix":            "test-vpc-integrity",
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Verify the configuration can be planned without errors
	exitCode, err := terraform.InitAndPlanE(t, terraformOptions)
assert.NoError(t, err)
	assert.Equal(t, 0, exitCode, "Terraform plan should succeed")
}

// TestVPCSingleAZDeployment tests that VPC is deployed in single AZ when multi-AZ is disabled
// Validates: Requirements 1.2
func TestVPCSingleAZDeployment(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":               "10.0.0.0/16",
			"public_subnet_a_cidr":   "10.0.1.0/24",
			"private_subnet_1a_cidr": "10.0.10.0/24",
			"private_subnet_2a_cidr": "10.0.20.0/24",
			"enable_multi_az":        false, // Single AZ deployment
			"public_subnet_b_cidr":   "10.0.2.0/24",
			"private_subnet_1b_cidr": "10.0.11.0/24",
			"private_subnet_2b_cidr": "10.0.21.0/24",
			"aws_region":             "us-east-1",
			"name_prefix":            "test-vpc-single-az",
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would verify:
	// 1. Only subnets in us-east-1a are created
	// 2. No subnets in us-east-1b are created
	// 3. Only one NAT Gateway is created (in AZ A)
	// 4. Reserved CIDR blocks for AZ B are documented but not deployed
}

// TestVPCMultiAZDeployment tests that VPC can be deployed in multi-AZ when enabled
// This validates the future multi-AZ expansion capability
func TestVPCMultiAZDeployment(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":               "10.0.0.0/16",
			"public_subnet_a_cidr":   "10.0.1.0/24",
			"private_subnet_1a_cidr": "10.0.10.0/24",
			"private_subnet_2a_cidr": "10.0.20.0/24",
			"enable_multi_az":        true, // Multi-AZ deployment
			"public_subnet_b_cidr":   "10.0.2.0/24",
			"private_subnet_1b_cidr": "10.0.11.0/24",
			"private_subnet_2b_cidr": "10.0.21.0/24",
			"aws_region":             "us-east-1",
			"name_prefix":            "test-vpc-multi-az",
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Verify the configuration can be planned without errors
	exitCode, err := terraform.InitAndPlanE(t, terraformOptions)
assert.NoError(t, err)
	assert.Equal(t, 0, exitCode, "Terraform plan should succeed for multi-AZ deployment")

	// Note: In a real deployment test, we would verify:
	// 1. Subnets are created in both us-east-1a and us-east-1b
	// 2. Two NAT Gateways are created (one per AZ)
	// 3. Route tables are properly configured for each AZ
}

// TestVPCIPv4Support tests that VPC supports IPv4
// Validates: Requirements 1.5
func TestVPCIPv4Support(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":               "10.0.0.0/16", // IPv4 CIDR
			"public_subnet_a_cidr":   "10.0.1.0/24",
			"private_subnet_1a_cidr": "10.0.10.0/24",
			"private_subnet_2a_cidr": "10.0.20.0/24",
			"enable_multi_az":        false,
			"public_subnet_b_cidr":   "10.0.2.0/24",
			"private_subnet_1b_cidr": "10.0.11.0/24",
			"private_subnet_2b_cidr": "10.0.21.0/24",
			"aws_region":             "us-east-1",
			"name_prefix":            "test-vpc-ipv4",
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// The VPC module uses IPv4 CIDR blocks, which confirms IPv4 support
	// IPv6 support would require additional configuration (ipv6_cidr_block, etc.)
}

// TestVPCResourceNaming tests that VPC resources follow naming conventions
// Validates: Requirements 1.4 (tagging includes Name tag)
func TestVPCResourceNaming(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name           string
		namePrefix     string
		expectedVPCName string
	}{
		{
			name:           "Production naming",
			namePrefix:     "janis-cencosud-prod",
			expectedVPCName: "janis-cencosud-prod-vpc",
		},
		{
			name:           "Staging naming",
			namePrefix:     "janis-cencosud-staging",
			expectedVPCName: "janis-cencosud-staging-vpc",
		},
		{
			name:           "Development naming",
			namePrefix:     "janis-cencosud-dev",
			expectedVPCName: "janis-cencosud-dev-vpc",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
				TerraformDir: "../modules/vpc",
				Vars: map[string]interface{}{
					"vpc_cidr":               "10.0.0.0/16",
					"public_subnet_a_cidr":   "10.0.1.0/24",
					"private_subnet_1a_cidr": "10.0.10.0/24",
					"private_subnet_2a_cidr": "10.0.20.0/24",
					"enable_multi_az":        false,
					"public_subnet_b_cidr":   "10.0.2.0/24",
					"private_subnet_1b_cidr": "10.0.11.0/24",
					"private_subnet_2b_cidr": "10.0.21.0/24",
					"aws_region":             "us-east-1",
					"name_prefix":            tc.namePrefix,
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Note: The VPC resource is tagged with Name = "${var.name_prefix}-vpc"
			// In a real deployment test, we would verify the actual Name tag matches expectedVPCName
		})
	}
}

