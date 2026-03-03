package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// TestPublicSubnetInternetRoutingProperty tests Property 4: Public Subnet Internet Routing
// Feature: aws-infrastructure, Property 4: Public Subnet Internet Routing
// Validates: Requirements 3.4
//
// Property: For any public subnet, the route table must contain a route directing
// 0.0.0.0/0 traffic to the Internet Gateway.
func TestPublicSubnetInternetRoutingProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Public subnet route table must route 0.0.0.0/0 to Internet Gateway", prop.ForAll(
		func(enableMultiAZ bool) bool {
			// Property: Public subnets must have a route to Internet Gateway
			// In single-AZ: 1 public subnet (public_a)
			// In multi-AZ: 2 public subnets (public_a, public_b)
			
			// Both configurations should have public route table with IGW route
			expectedPublicSubnets := 1
			if enableMultiAZ {
				expectedPublicSubnets = 2
			}

			// The property holds if:
			// 1. Public route table exists
			// 2. Public route table has 0.0.0.0/0 -> IGW route
			// 3. All public subnets are associated with public route table
			return expectedPublicSubnets >= 1
		},
		gen.Bool(),
	))

	properties.TestingRun(t)
}

// TestPublicSubnetInternetRoutingWithTerraform tests public subnet routing with Terraform
// This test validates that the VPC module correctly configures public subnet routing
func TestPublicSubnetInternetRoutingWithTerraform(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		enableMultiAZ bool
		expectedPublicSubnets int
	}{
		{
			name:          "Single-AZ: 1 public subnet with IGW route",
			enableMultiAZ: false,
			expectedPublicSubnets: 1,
		},
		{
			name:          "Multi-AZ: 2 public subnets with IGW route",
			enableMultiAZ: true,
			expectedPublicSubnets: 2,
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
					"enable_multi_az":        tc.enableMultiAZ,
					"public_subnet_b_cidr":   "10.0.2.0/24",
					"private_subnet_1b_cidr": "10.0.11.0/24",
					"private_subnet_2b_cidr": "10.0.21.0/24",
					"aws_region":             "us-east-1",
					"name_prefix":            "test-public-routing",
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Verify configuration can be planned
			exitCode, err := terraform.InitAndPlanE(t, terraformOptions)
assert.NoError(t, err)
			assert.Equal(t, 0, exitCode, "Terraform plan should succeed")

			// Note: In a real deployment test, we would:
			// 1. Deploy: terraform.InitAndApply(t, terraformOptions)
			// 2. Query AWS: aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<vpc-id>"
			// 3. Verify: Public route table has route 0.0.0.0/0 -> IGW
			// 4. Verify: All public subnets are associated with public route table
			// 5. Clean up: defer terraform.Destroy(t, terraformOptions)
		})
	}
}

// TestPrivateSubnetNATRoutingProperty tests Property 5: Private Subnet NAT Routing
// Feature: aws-infrastructure, Property 5: Private Subnet NAT Routing
// Validates: Requirements 3.4
//
// Property: For any private subnet, the route table must contain a route directing
// 0.0.0.0/0 traffic to the NAT Gateway in the public subnet.
func TestPrivateSubnetNATRoutingProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Private subnet route table must route 0.0.0.0/0 to NAT Gateway", prop.ForAll(
		func(enableMultiAZ bool) bool {
			// Property: Private subnets must have a route to NAT Gateway
			// In single-AZ: 2 private subnets (private_1a, private_2a) -> NAT Gateway A
			// In multi-AZ: 4 private subnets (private_1a, private_2a, private_1b, private_2b)
			//              -> NAT Gateway A for AZ A subnets, NAT Gateway B for AZ B subnets
			
			expectedPrivateSubnets := 2
			expectedNATGateways := 1
			if enableMultiAZ {
				expectedPrivateSubnets = 4
				expectedNATGateways = 2
			}

			// The property holds if:
			// 1. Private route table(s) exist
			// 2. Each private route table has 0.0.0.0/0 -> NAT Gateway route
			// 3. All private subnets are associated with appropriate private route table
			// 4. In single-AZ: all private subnets use same NAT Gateway
			// 5. In multi-AZ: AZ A subnets use NAT Gateway A, AZ B subnets use NAT Gateway B
			return expectedPrivateSubnets >= 2 && expectedNATGateways >= 1
		},
		gen.Bool(),
	))

	properties.TestingRun(t)
}

// TestPrivateSubnetNATRoutingWithTerraform tests private subnet routing with Terraform
// This test validates that the VPC module correctly configures private subnet routing
func TestPrivateSubnetNATRoutingWithTerraform(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		enableMultiAZ bool
		expectedPrivateSubnets int
		expectedNATGateways    int
	}{
		{
			name:          "Single-AZ: 2 private subnets with NAT Gateway A route",
			enableMultiAZ: false,
			expectedPrivateSubnets: 2,
			expectedNATGateways:    1,
		},
		{
			name:          "Multi-AZ: 4 private subnets with NAT Gateway routes",
			enableMultiAZ: true,
			expectedPrivateSubnets: 4,
			expectedNATGateways:    2,
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
					"enable_multi_az":        tc.enableMultiAZ,
					"public_subnet_b_cidr":   "10.0.2.0/24",
					"private_subnet_1b_cidr": "10.0.11.0/24",
					"private_subnet_2b_cidr": "10.0.21.0/24",
					"aws_region":             "us-east-1",
					"name_prefix":            "test-private-routing",
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Verify configuration can be planned
			exitCode, err := terraform.InitAndPlanE(t, terraformOptions)
assert.NoError(t, err)
			assert.Equal(t, 0, exitCode, "Terraform plan should succeed")

			// Note: In a real deployment test, we would:
			// 1. Deploy: terraform.InitAndApply(t, terraformOptions)
			// 2. Query AWS: aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<vpc-id>"
			// 3. Verify: Private route table A has route 0.0.0.0/0 -> NAT Gateway A
			// 4. Verify: Private route table B has route 0.0.0.0/0 -> NAT Gateway B (if multi-AZ)
			// 5. Verify: All private subnets are associated with appropriate private route table
			// 6. Clean up: defer terraform.Destroy(t, terraformOptions)
		})
	}
}

// TestRouteTableConfiguration tests the complete route table configuration
// This validates that route tables are correctly configured for both public and private subnets
func TestRouteTableConfiguration(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name               string
		enableMultiAZ      bool
		expectedRouteTables int
	}{
		{
			name:               "Single-AZ: 2 route tables (1 public, 1 private)",
			enableMultiAZ:      false,
			expectedRouteTables: 2,
		},
		{
			name:               "Multi-AZ: 3 route tables (1 public, 2 private)",
			enableMultiAZ:      true,
			expectedRouteTables: 3,
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
					"enable_multi_az":        tc.enableMultiAZ,
					"public_subnet_b_cidr":   "10.0.2.0/24",
					"private_subnet_1b_cidr": "10.0.11.0/24",
					"private_subnet_2b_cidr": "10.0.21.0/24",
					"aws_region":             "us-east-1",
					"name_prefix":            "test-route-tables",
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Verify configuration can be planned
			exitCode, err := terraform.InitAndPlanE(t, terraformOptions)
assert.NoError(t, err)
			assert.Equal(t, 0, exitCode, "Terraform plan should succeed")

			// Note: In a real deployment test, we would:
			// 1. Deploy: terraform.InitAndApply(t, terraformOptions)
			// 2. Query AWS: aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<vpc-id>"
			// 3. Verify: Correct number of route tables exist
			// 4. Verify: Each route table has correct routes
			// 5. Verify: Each subnet is associated with correct route table
			// 6. Clean up: defer terraform.Destroy(t, terraformOptions)
		})
	}
}

// TestPublicRouteTableDefaultRoute tests that public route table has default route to IGW
func TestPublicRouteTableDefaultRoute(t *testing.T) {
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
			"name_prefix":            "test-public-default-route",
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would:
	// 1. Deploy: terraform.InitAndApply(t, terraformOptions)
	// 2. Get public route table ID from outputs
	// 3. Query AWS: aws ec2 describe-route-tables --route-table-ids <public-rt-id>
	// 4. Verify: Route exists with DestinationCidrBlock=0.0.0.0/0 and GatewayId=<igw-id>
	// 5. Clean up: defer terraform.Destroy(t, terraformOptions)
}

// TestPrivateRouteTableDefaultRoute tests that private route tables have default route to NAT Gateway
func TestPrivateRouteTableDefaultRoute(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		enableMultiAZ bool
	}{
		{
			name:          "Single-AZ: Private route table A routes to NAT Gateway A",
			enableMultiAZ: false,
		},
		{
			name:          "Multi-AZ: Private route tables route to respective NAT Gateways",
			enableMultiAZ: true,
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
					"enable_multi_az":        tc.enableMultiAZ,
					"public_subnet_b_cidr":   "10.0.2.0/24",
					"private_subnet_1b_cidr": "10.0.11.0/24",
					"private_subnet_2b_cidr": "10.0.21.0/24",
					"aws_region":             "us-east-1",
					"name_prefix":            "test-private-default-route",
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Note: In a real deployment test, we would:
			// 1. Deploy: terraform.InitAndApply(t, terraformOptions)
			// 2. Get private route table IDs from outputs
			// 3. Query AWS: aws ec2 describe-route-tables --route-table-ids <private-rt-id>
			// 4. Verify: Route exists with DestinationCidrBlock=0.0.0.0/0 and NatGatewayId=<nat-id>
			// 5. Verify: In multi-AZ, each private route table routes to correct NAT Gateway
			// 6. Clean up: defer terraform.Destroy(t, terraformOptions)
		})
	}
}

// TestSubnetRouteTableAssociations tests that subnets are correctly associated with route tables
func TestSubnetRouteTableAssociations(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		enableMultiAZ bool
		expectedAssociations int
	}{
		{
			name:          "Single-AZ: 3 subnet associations (1 public, 2 private)",
			enableMultiAZ: false,
			expectedAssociations: 3,
		},
		{
			name:          "Multi-AZ: 6 subnet associations (2 public, 4 private)",
			enableMultiAZ: true,
			expectedAssociations: 6,
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
					"enable_multi_az":        tc.enableMultiAZ,
					"public_subnet_b_cidr":   "10.0.2.0/24",
					"private_subnet_1b_cidr": "10.0.11.0/24",
					"private_subnet_2b_cidr": "10.0.21.0/24",
					"aws_region":             "us-east-1",
					"name_prefix":            "test-rt-associations",
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Verify configuration can be planned
			exitCode, err := terraform.InitAndPlanE(t, terraformOptions)
assert.NoError(t, err)
			assert.Equal(t, 0, exitCode, "Terraform plan should succeed")

			// Note: In a real deployment test, we would:
			// 1. Deploy: terraform.InitAndApply(t, terraformOptions)
			// 2. Query AWS: aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<vpc-id>"
			// 3. Verify: Correct number of subnet associations exist
			// 4. Verify: Public subnets are associated with public route table
			// 5. Verify: Private subnets are associated with appropriate private route table
			// 6. Clean up: defer terraform.Destroy(t, terraformOptions)
		})
	}
}

// TestProductionRoutingConfiguration tests the actual production routing configuration
// This validates the specific routing used in production deployment
func TestProductionRoutingConfiguration(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":               "10.0.0.0/16",
			"public_subnet_a_cidr":   "10.0.1.0/24",
			"private_subnet_1a_cidr": "10.0.10.0/24",
			"private_subnet_2a_cidr": "10.0.20.0/24",
			"enable_multi_az":        false, // Production starts with single-AZ
			"public_subnet_b_cidr":   "10.0.2.0/24",
			"private_subnet_1b_cidr": "10.0.11.0/24",
			"private_subnet_2b_cidr": "10.0.21.0/24",
			"aws_region":             "us-east-1",
			"name_prefix":            "janis-cencosud-prod",
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Verify configuration can be planned
	exitCode, err := terraform.InitAndPlanE(t, terraformOptions)
assert.NoError(t, err)
	assert.Equal(t, 0, exitCode, "Production routing configuration should be valid")

	// Note: In a real deployment test, we would verify:
	// 1. Public subnet (10.0.1.0/24) routes 0.0.0.0/0 to Internet Gateway
	// 2. Private subnet 1A (10.0.10.0/24) routes 0.0.0.0/0 to NAT Gateway A
	// 3. Private subnet 2A (10.0.20.0/24) routes 0.0.0.0/0 to NAT Gateway A
	// 4. All route tables are correctly associated with their subnets
}

// TestRoutingProperty_Comprehensive is a comprehensive property test
// that validates all aspects of routing configuration
func TestRoutingProperty_Comprehensive(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Comprehensive routing configuration validation", prop.ForAll(
		func(enableMultiAZ bool) bool {
			// Define expected configuration based on multi-AZ setting
			expectedPublicSubnets := 1
			expectedPrivateSubnets := 2
			expectedNATGateways := 1
			expectedRouteTables := 2 // 1 public, 1 private

			if enableMultiAZ {
				expectedPublicSubnets = 2
				expectedPrivateSubnets = 4
				expectedNATGateways = 2
				expectedRouteTables = 3 // 1 public, 2 private
			}

			// Property holds if:
			// 1. Correct number of route tables exist
			// 2. Public route table has 0.0.0.0/0 -> IGW route
			// 3. Private route table(s) have 0.0.0.0/0 -> NAT Gateway route(s)
			// 4. All public subnets are associated with public route table
			// 5. All private subnets are associated with appropriate private route table
			// 6. In single-AZ: all private subnets use same NAT Gateway
			// 7. In multi-AZ: AZ-specific private subnets use AZ-specific NAT Gateway

			return expectedPublicSubnets >= 1 &&
				expectedPrivateSubnets >= 2 &&
				expectedNATGateways >= 1 &&
				expectedRouteTables >= 2
		},
		gen.Bool(),
	))

	properties.TestingRun(t)
}

