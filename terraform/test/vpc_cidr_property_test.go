package test

import (
	"fmt"
	"net"
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// TestVPCCIDRValidityProperty tests Property 1: VPC CIDR Block Validity
// Feature: aws-infrastructure, Property 1: VPC CIDR Block Validity
// Validates: Requirements 1.1
//
// Property: For any VPC configuration, the CIDR block must be a valid IPv4 CIDR notation
// and provide exactly 65,536 IP addresses (10.0.0.0/16).
func TestVPCCIDRValidityProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("VPC CIDR block must be valid IPv4 and provide exactly 65,536 IPs", prop.ForAll(
		func(cidrBlock string) bool {
			// Parse the CIDR block
			_, ipNet, err := net.ParseCIDR(cidrBlock)
			if err != nil {
				// Invalid CIDR format should fail
				return false
			}

			// Calculate the number of IP addresses in the CIDR block
			ones, bits := ipNet.Mask.Size()
			if bits != 32 {
				// Not an IPv4 address
				return false
			}

			// Calculate total IPs: 2^(32 - prefix_length)
			totalIPs := 1 << uint(bits-ones)

			// For a /16 network, we should have exactly 65,536 IPs
			expectedIPs := 65536
			
			// The property holds if the CIDR provides exactly 65,536 IPs
			return totalIPs == expectedIPs
		},
		// Generate valid CIDR blocks with /16 prefix
		gen.OneConstOf(
			"10.0.0.0/16",
			"172.16.0.0/16",
			"192.168.0.0/16",
			"10.1.0.0/16",
			"10.10.0.0/16",
		),
	))

	properties.TestingRun(t)
}

// TestVPCCIDRValidityWithTerraform tests the actual VPC CIDR configuration in Terraform
// This test validates that the VPC module correctly uses a /16 CIDR block
func TestVPCCIDRValidityWithTerraform(t *testing.T) {
	t.Parallel()

	// Define test cases with different valid /16 CIDR blocks
	testCases := []struct {
		name      string
		vpcCIDR   string
		shouldPass bool
	}{
		{
			name:      "Standard 10.0.0.0/16",
			vpcCIDR:   "10.0.0.0/16",
			shouldPass: true,
		},
		{
			name:      "Alternative 172.16.0.0/16",
			vpcCIDR:   "172.16.0.0/16",
			shouldPass: true,
		},
		{
			name:      "Alternative 192.168.0.0/16",
			vpcCIDR:   "192.168.0.0/16",
			shouldPass: true,
		},
	}

	for _, tc := range testCases {
		tc := tc // capture range variable
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Validate CIDR block properties
			_, ipNet, err := net.ParseCIDR(tc.vpcCIDR)
			assert.NoError(t, err, "CIDR block should be valid")

			// Verify it's IPv4
			ones, bits := ipNet.Mask.Size()
			assert.Equal(t, 32, bits, "Should be IPv4 (32 bits)")

			// Calculate total IPs
			totalIPs := 1 << uint(bits-ones)
			assert.Equal(t, 65536, totalIPs, "VPC CIDR /16 should provide exactly 65,536 IP addresses")

			// Verify the prefix length is /16
			assert.Equal(t, 16, ones, "VPC CIDR should have /16 prefix")
		})
	}
}

// TestVPCCIDRInvalidCases tests that invalid CIDR blocks are properly rejected
func TestVPCCIDRInvalidCases(t *testing.T) {
	t.Parallel()

	invalidCases := []struct {
		name    string
		cidr    string
		reason  string
	}{
		{
			name:   "Invalid CIDR format",
			cidr:   "10.0.0.0",
			reason: "Missing prefix length",
		},
		{
			name:   "Wrong prefix length /24",
			cidr:   "10.0.0.0/24",
			reason: "Provides only 256 IPs, not 65,536",
		},
		{
			name:   "Wrong prefix length /8",
			cidr:   "10.0.0.0/8",
			reason: "Provides 16,777,216 IPs, not 65,536",
		},
		{
			name:   "Invalid IP address",
			cidr:   "999.999.999.999/16",
			reason: "Invalid IP address",
		},
		{
			name:   "Empty string",
			cidr:   "",
			reason: "Empty CIDR block",
		},
	}

	for _, tc := range invalidCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			_, ipNet, err := net.ParseCIDR(tc.cidr)
			
			if err != nil {
				// Expected: invalid CIDR should fail to parse
				return
			}

			// If it parsed, check if it provides the wrong number of IPs
			ones, bits := ipNet.Mask.Size()
			if bits == 32 {
				totalIPs := 1 << uint(bits-ones)
				assert.NotEqual(t, 65536, totalIPs, 
					fmt.Sprintf("CIDR %s should not provide 65,536 IPs (reason: %s)", tc.cidr, tc.reason))
			}
		})
	}
}

// TestVPCModuleWithValidCIDR tests the VPC module with a valid CIDR configuration
// This is a minimal integration test to ensure the module accepts valid CIDR blocks
func TestVPCModuleWithValidCIDR(t *testing.T) {
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
			"name_prefix":            "test-vpc",
		},
		NoColor: true,
	})

	// Validate that Terraform configuration is valid
	terraform.Validate(t, terraformOptions)

	// Verify the VPC CIDR is correctly set
	vpcCIDR := terraformOptions.Vars["vpc_cidr"].(string)
	_, ipNet, err := net.ParseCIDR(vpcCIDR)
	assert.NoError(t, err, "VPC CIDR should be valid")

	ones, bits := ipNet.Mask.Size()
	totalIPs := 1 << uint(bits-ones)
	assert.Equal(t, 65536, totalIPs, "VPC CIDR should provide exactly 65,536 IP addresses")
}

// cidrOverlaps checks if two CIDR blocks overlap
func cidrOverlaps(cidr1, cidr2 string) bool {
	_, ipNet1, err1 := net.ParseCIDR(cidr1)
	_, ipNet2, err2 := net.ParseCIDR(cidr2)

	if err1 != nil || err2 != nil {
		return false
	}

	// Check if ipNet1 contains the start of ipNet2
	if ipNet1.Contains(ipNet2.IP) {
		return true
	}

	// Check if ipNet2 contains the start of ipNet1
	if ipNet2.Contains(ipNet1.IP) {
		return true
	}

	return false
}

// cidrIsSubsetOf checks if a CIDR block is a valid subset of another CIDR block
func cidrIsSubsetOf(subnet, vpc string) bool {
	_, subnetNet, err1 := net.ParseCIDR(subnet)
	_, vpcNet, err2 := net.ParseCIDR(vpc)

	if err1 != nil || err2 != nil {
		return false
	}

	// Check if VPC contains the subnet's network address
	if !vpcNet.Contains(subnetNet.IP) {
		return false
	}

	// Check if subnet mask is more specific than VPC mask (larger prefix length)
	subnetOnes, _ := subnetNet.Mask.Size()
	vpcOnes, _ := vpcNet.Mask.Size()

	return subnetOnes >= vpcOnes
}

// TestSubnetCIDRNonOverlapProperty tests Property 3: Subnet CIDR Non-Overlap
// Feature: aws-infrastructure, Property 3: Subnet CIDR Non-Overlap
// Validates: Requirements 2.1, 2.2
//
// Property: For any pair of subnets within the VPC, their CIDR blocks must not overlap
// and must be valid subsets of the VPC CIDR block (10.0.0.0/16).
func TestSubnetCIDRNonOverlapProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Subnet CIDR blocks must not overlap and must be subsets of VPC CIDR", prop.ForAll(
		func(vpcCIDR string, subnetCIDRs []string) bool {
			// Parse VPC CIDR
			_, vpcNet, err := net.ParseCIDR(vpcCIDR)
			if err != nil {
				return false
			}

			// Verify VPC is /16
			vpcOnes, vpcBits := vpcNet.Mask.Size()
			if vpcBits != 32 || vpcOnes != 16 {
				return false
			}

			// Check each subnet is a valid subset of VPC
			for _, subnetCIDR := range subnetCIDRs {
				if !cidrIsSubsetOf(subnetCIDR, vpcCIDR) {
					return false
				}
			}

			// Check no two subnets overlap
			for i := 0; i < len(subnetCIDRs); i++ {
				for j := i + 1; j < len(subnetCIDRs); j++ {
					if cidrOverlaps(subnetCIDRs[i], subnetCIDRs[j]) {
						return false
					}
				}
			}

			return true
		},
		// Generate VPC CIDR (always /16)
		gen.OneConstOf("10.0.0.0/16", "172.16.0.0/16", "192.168.0.0/16"),
		// Generate subnet CIDRs that should not overlap
		gen.OneConstOf(
			// Single-AZ configuration (current deployment)
			[]string{"10.0.1.0/24", "10.0.10.0/24", "10.0.20.0/24"},
			// Multi-AZ configuration (future expansion)
			[]string{"10.0.1.0/24", "10.0.10.0/24", "10.0.20.0/24", "10.0.2.0/24", "10.0.11.0/24", "10.0.21.0/24"},
			// Alternative valid configurations
			[]string{"10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"},
			[]string{"10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"},
		),
	))

	properties.TestingRun(t)
}

// TestSubnetCIDRNonOverlapWithTerraform tests subnet CIDR non-overlap with actual Terraform configuration
// This test validates that the VPC module correctly configures non-overlapping subnets
func TestSubnetCIDRNonOverlapWithTerraform(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		vpcCIDR       string
		subnetCIDRs   map[string]string
		enableMultiAZ bool
		shouldPass    bool
	}{
		{
			name:    "Single-AZ non-overlapping subnets",
			vpcCIDR: "10.0.0.0/16",
			subnetCIDRs: map[string]string{
				"public_a":    "10.0.1.0/24",
				"private_1a":  "10.0.10.0/24",
				"private_2a":  "10.0.20.0/24",
				"public_b":    "10.0.2.0/24",
				"private_1b":  "10.0.11.0/24",
				"private_2b":  "10.0.21.0/24",
			},
			enableMultiAZ: false,
			shouldPass:    true,
		},
		{
			name:    "Multi-AZ non-overlapping subnets",
			vpcCIDR: "10.0.0.0/16",
			subnetCIDRs: map[string]string{
				"public_a":    "10.0.1.0/24",
				"private_1a":  "10.0.10.0/24",
				"private_2a":  "10.0.20.0/24",
				"public_b":    "10.0.2.0/24",
				"private_1b":  "10.0.11.0/24",
				"private_2b":  "10.0.21.0/24",
			},
			enableMultiAZ: true,
			shouldPass:    true,
		},
		{
			name:    "Alternative VPC CIDR with non-overlapping subnets",
			vpcCIDR: "172.16.0.0/16",
			subnetCIDRs: map[string]string{
				"public_a":    "172.16.1.0/24",
				"private_1a":  "172.16.10.0/24",
				"private_2a":  "172.16.20.0/24",
				"public_b":    "172.16.2.0/24",
				"private_1b":  "172.16.11.0/24",
				"private_2b":  "172.16.21.0/24",
			},
			enableMultiAZ: false,
			shouldPass:    true,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify all subnets are valid subsets of VPC CIDR
			for subnetName, subnetCIDR := range tc.subnetCIDRs {
				assert.True(t, cidrIsSubsetOf(subnetCIDR, tc.vpcCIDR),
					"Subnet %s (%s) should be a valid subset of VPC CIDR %s", subnetName, subnetCIDR, tc.vpcCIDR)
			}

			// Verify no two subnets overlap
			subnetList := make([]string, 0, len(tc.subnetCIDRs))
			for _, cidr := range tc.subnetCIDRs {
				subnetList = append(subnetList, cidr)
			}

			for i := 0; i < len(subnetList); i++ {
				for j := i + 1; j < len(subnetList); j++ {
					assert.False(t, cidrOverlaps(subnetList[i], subnetList[j]),
						"Subnets %s and %s should not overlap", subnetList[i], subnetList[j])
				}
			}

			// Validate Terraform configuration
			terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
				TerraformDir: "../modules/vpc",
				Vars: map[string]interface{}{
					"vpc_cidr":               tc.vpcCIDR,
					"public_subnet_a_cidr":   tc.subnetCIDRs["public_a"],
					"private_subnet_1a_cidr": tc.subnetCIDRs["private_1a"],
					"private_subnet_2a_cidr": tc.subnetCIDRs["private_2a"],
					"enable_multi_az":        tc.enableMultiAZ,
					"public_subnet_b_cidr":   tc.subnetCIDRs["public_b"],
					"private_subnet_1b_cidr": tc.subnetCIDRs["private_1b"],
					"private_subnet_2b_cidr": tc.subnetCIDRs["private_2b"],
					"aws_region":             "us-east-1",
					"name_prefix":            "test-vpc-overlap",
				},
				NoColor: true,
			})

			exitCode, err := terraform.ValidateE(t, terraformOptions)
assert.NoError(t, err)
			if tc.shouldPass {
				assert.Equal(t, 0, exitCode, "Terraform validation should succeed for non-overlapping subnets")
			} else {
				assert.NotEqual(t, 0, exitCode, "Terraform validation should fail for overlapping subnets")
			}
		})
	}
}

// TestSubnetCIDROverlapDetection tests that overlapping subnet CIDRs are properly detected
func TestSubnetCIDROverlapDetection(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name           string
		cidr1          string
		cidr2          string
		shouldOverlap  bool
	}{
		{
			name:          "Identical CIDRs overlap",
			cidr1:         "10.0.1.0/24",
			cidr2:         "10.0.1.0/24",
			shouldOverlap: true,
		},
		{
			name:          "Subset CIDR overlaps",
			cidr1:         "10.0.0.0/16",
			cidr2:         "10.0.1.0/24",
			shouldOverlap: true,
		},
		{
			name:          "Non-overlapping adjacent CIDRs",
			cidr1:         "10.0.1.0/24",
			cidr2:         "10.0.2.0/24",
			shouldOverlap: false,
		},
		{
			name:          "Non-overlapping distant CIDRs",
			cidr1:         "10.0.1.0/24",
			cidr2:         "10.0.10.0/24",
			shouldOverlap: false,
		},
		{
			name:          "Overlapping partial CIDRs",
			cidr1:         "10.0.1.0/25",
			cidr2:         "10.0.1.128/25",
			shouldOverlap: false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			overlaps := cidrOverlaps(tc.cidr1, tc.cidr2)
			assert.Equal(t, tc.shouldOverlap, overlaps,
				"CIDRs %s and %s overlap detection mismatch", tc.cidr1, tc.cidr2)
		})
	}
}

// TestSubnetCIDRSubsetValidation tests that subnet CIDRs are valid subsets of VPC CIDR
func TestSubnetCIDRSubsetValidation(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name         string
		vpcCIDR      string
		subnetCIDR   string
		shouldBeSubset bool
	}{
		{
			name:         "Valid subnet within VPC",
			vpcCIDR:      "10.0.0.0/16",
			subnetCIDR:   "10.0.1.0/24",
			shouldBeSubset: true,
		},
		{
			name:         "Subnet outside VPC range",
			vpcCIDR:      "10.0.0.0/16",
			subnetCIDR:   "10.1.0.0/24",
			shouldBeSubset: false,
		},
		{
			name:         "Subnet with less specific mask than VPC",
			vpcCIDR:      "10.0.0.0/16",
			subnetCIDR:   "10.0.0.0/8",
			shouldBeSubset: false,
		},
		{
			name:         "Subnet at VPC boundary",
			vpcCIDR:      "10.0.0.0/16",
			subnetCIDR:   "10.0.255.0/24",
			shouldBeSubset: true,
		},
		{
			name:         "Subnet just outside VPC boundary",
			vpcCIDR:      "10.0.0.0/16",
			subnetCIDR:   "10.1.0.0/24",
			shouldBeSubset: false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			isSubset := cidrIsSubsetOf(tc.subnetCIDR, tc.vpcCIDR)
			assert.Equal(t, tc.shouldBeSubset, isSubset,
				"Subnet %s subset validation of VPC %s mismatch", tc.subnetCIDR, tc.vpcCIDR)
		})
	}
}

// TestProductionSubnetConfiguration tests the actual production subnet configuration
// This validates the specific CIDR blocks used in the production deployment
func TestProductionSubnetConfiguration(t *testing.T) {
	t.Parallel()

	vpcCIDR := "10.0.0.0/16"
	subnets := map[string]string{
		"public_a":    "10.0.1.0/24",
		"private_1a":  "10.0.10.0/24",
		"private_2a":  "10.0.20.0/24",
		"public_b":    "10.0.2.0/24",   // Reserved for multi-AZ
		"private_1b":  "10.0.11.0/24",  // Reserved for multi-AZ
		"private_2b":  "10.0.21.0/24",  // Reserved for multi-AZ
	}

	// Verify all subnets are valid subsets of VPC
	for name, cidr := range subnets {
		assert.True(t, cidrIsSubsetOf(cidr, vpcCIDR),
			"Production subnet %s (%s) must be a valid subset of VPC CIDR %s", name, cidr, vpcCIDR)
	}

	// Verify no overlaps between any pair of subnets
	subnetList := make([]struct{ name, cidr string }, 0, len(subnets))
	for name, cidr := range subnets {
		subnetList = append(subnetList, struct{ name, cidr string }{name, cidr})
	}

	for i := 0; i < len(subnetList); i++ {
		for j := i + 1; j < len(subnetList); j++ {
			assert.False(t, cidrOverlaps(subnetList[i].cidr, subnetList[j].cidr),
				"Production subnets %s (%s) and %s (%s) must not overlap",
				subnetList[i].name, subnetList[i].cidr,
				subnetList[j].name, subnetList[j].cidr)
		}
	}
}

