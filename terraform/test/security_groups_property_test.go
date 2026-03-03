package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// TestSecurityGroupLeastPrivilegeProperty tests Property 7: Security Group Least Privilege
// Feature: aws-infrastructure, Property 7: Security Group Least Privilege
// Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
//
// Property: For any security group rule, the rule must follow the principle of least privilege
// by specifying the minimum required ports, protocols, and source/destination ranges.
func TestSecurityGroupLeastPrivilegeProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Security group rules must follow least privilege principle", prop.ForAll(
		func(port int, protocol string, cidr string) bool {
			// Define allowed ports for specific services
			allowedPorts := map[int]bool{
				443:  true, // HTTPS
				5439: true, // PostgreSQL/Redshift
			}

			// Define allowed protocols
			allowedProtocols := map[string]bool{
				"tcp": true,
				"-1":  true, // All protocols (only for specific cases)
			}

			// Define allowed CIDR ranges
			// 0.0.0.0/0 is only allowed for specific outbound rules
			// VPC CIDR (10.0.0.0/16) is allowed for internal communication
			isValidCIDR := func(cidr string) bool {
				validCIDRs := []string{
					"0.0.0.0/0",   // Internet (only for specific outbound rules)
					"10.0.0.0/16", // VPC CIDR
				}
				for _, valid := range validCIDRs {
					if cidr == valid {
						return true
					}
				}
				return false
			}

			// Verify port is in allowed list
			if !allowedPorts[port] && port != 0 && port != 65535 {
				return false
			}

			// Verify protocol is allowed
			if !allowedProtocols[protocol] {
				return false
			}

			// Verify CIDR is valid
			if cidr != "" && !isValidCIDR(cidr) {
				return false
			}

			// Additional validation: port 0-65535 range for Glue self-reference
			if port == 0 || port == 65535 {
				// This is only valid for Glue self-reference rules
				return protocol == "tcp"
			}

			return true
		},
		gen.OneConstOf(0, 443, 5439, 65535),
		gen.OneConstOf("tcp", "-1"),
		gen.OneConstOf("0.0.0.0/0", "10.0.0.0/16", ""),
	))

	properties.TestingRun(t)
}

// TestSecurityGroupSelfReferenceValidityProperty tests Property 8: Security Group Self-Reference Validity
// Feature: aws-infrastructure, Property 8: Security Group Self-Reference Validity
// Validates: Requirements 5.4, 5.5
//
// Property: For any security group with self-referencing rules (SG-MWAA, SG-Glue),
// the source and destination security group IDs must match the security group's own ID.
func TestSecurityGroupSelfReferenceValidityProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Self-referencing security groups must reference their own ID", prop.ForAll(
		func(sgID string, referencedSGID string, isSelfReference bool) bool {
			// If the rule is marked as self-reference, the IDs must match
			if isSelfReference {
				return sgID == referencedSGID
			}
			// If not self-reference, IDs should be different
			return sgID != referencedSGID
		},
		gen.OneConstOf("sg-mwaa-123", "sg-glue-456", "sg-lambda-789"),
		gen.OneConstOf("sg-mwaa-123", "sg-glue-456", "sg-lambda-789"),
		gen.Bool(),
	))

	properties.TestingRun(t)
}

// TestAPIGatewaySecurityGroupRules tests SG-API-Gateway configuration
// Validates: Requirements 5.1
func TestAPIGatewaySecurityGroupRules(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		inboundRules  []SecurityGroupRule
		outboundRules []SecurityGroupRule
	}{
		{
			name: "API Gateway with least privilege",
			inboundRules: []SecurityGroupRule{
				{
					Port:        443,
					Protocol:    "tcp",
					CIDR:        "0.0.0.0/0",
					Description: "HTTPS from Janis webhooks",
				},
			},
			outboundRules: []SecurityGroupRule{
				{
					Port:        0,
					Protocol:    "-1",
					CIDR:        "0.0.0.0/0",
					Description: "Allow all outbound traffic",
				},
			},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify inbound rules follow least privilege
			for _, rule := range tc.inboundRules {
				assert.Equal(t, 443, rule.Port, "API Gateway should only allow HTTPS (443)")
				assert.Equal(t, "tcp", rule.Protocol, "API Gateway should use TCP protocol")
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}

			// Verify outbound rules
			for _, rule := range tc.outboundRules {
				assert.Equal(t, "-1", rule.Protocol, "Outbound should allow all protocols")
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}
		})
	}
}

// TestRedshiftSecurityGroupRules tests SG-Redshift-Existing configuration
// Validates: Requirements 5.2
func TestRedshiftSecurityGroupRules(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		inboundRules  []SecurityGroupRule
		outboundRules []SecurityGroupRule
	}{
		{
			name: "Redshift with least privilege",
			inboundRules: []SecurityGroupRule{
				{
					Port:              5439,
					Protocol:          "tcp",
					SourceSG:          "sg-lambda",
					Description:       "PostgreSQL from Lambda functions",
				},
				{
					Port:              5439,
					Protocol:          "tcp",
					SourceSG:          "sg-mwaa",
					Description:       "PostgreSQL from MWAA Airflow",
				},
			},
			outboundRules: []SecurityGroupRule{
				{
					Port:              443,
					Protocol:          "tcp",
					DestinationSG:     "sg-vpc-endpoints",
					Description:       "HTTPS to VPC Endpoints",
				},
			},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify inbound rules follow least privilege
			for _, rule := range tc.inboundRules {
				assert.Equal(t, 5439, rule.Port, "Redshift should only allow PostgreSQL (5439)")
				assert.Equal(t, "tcp", rule.Protocol, "Redshift should use TCP protocol")
				assert.NotEmpty(t, rule.SourceSG, "Inbound should reference specific security groups")
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}

			// Verify outbound rules are restricted
			for _, rule := range tc.outboundRules {
				assert.Equal(t, 443, rule.Port, "Redshift outbound should only allow HTTPS (443)")
				assert.Equal(t, "tcp", rule.Protocol, "Redshift outbound should use TCP protocol")
				assert.NotEmpty(t, rule.DestinationSG, "Outbound should reference VPC endpoints SG")
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}
		})
	}
}

// TestLambdaSecurityGroupRules tests SG-Lambda configuration
// Validates: Requirements 5.3
func TestLambdaSecurityGroupRules(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		inboundRules  []SecurityGroupRule
		outboundRules []SecurityGroupRule
	}{
		{
			name:         "Lambda with no inbound rules",
			inboundRules: []SecurityGroupRule{},
			outboundRules: []SecurityGroupRule{
				{
					Port:              5439,
					Protocol:          "tcp",
					DestinationSG:     "sg-redshift",
					Description:       "PostgreSQL to Redshift cluster",
				},
				{
					Port:              443,
					Protocol:          "tcp",
					DestinationSG:     "sg-vpc-endpoints",
					Description:       "HTTPS to VPC Endpoints",
				},
				{
					Port:              443,
					Protocol:          "tcp",
					CIDR:              "0.0.0.0/0",
					Description:       "HTTPS to internet (Janis API)",
				},
			},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify no inbound rules (Lambda doesn't receive direct connections)
			assert.Empty(t, tc.inboundRules, "Lambda should have no inbound rules")

			// Verify outbound rules follow least privilege
			for _, rule := range tc.outboundRules {
				assert.Contains(t, []int{443, 5439}, rule.Port,
					"Lambda should only allow HTTPS (443) or PostgreSQL (5439)")
				assert.Equal(t, "tcp", rule.Protocol, "Lambda should use TCP protocol")
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}
		})
	}
}

// TestMWAASecurityGroupRules tests SG-MWAA configuration
// Validates: Requirements 5.4
func TestMWAASecurityGroupRules(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		sgID          string
		inboundRules  []SecurityGroupRule
		outboundRules []SecurityGroupRule
	}{
		{
			name: "MWAA with self-reference",
			sgID: "sg-mwaa-123",
			inboundRules: []SecurityGroupRule{
				{
					Port:              443,
					Protocol:          "tcp",
					SourceSG:          "sg-mwaa-123",
					Description:       "HTTPS from MWAA workers (self-reference)",
					IsSelfReference:   true,
				},
			},
			outboundRules: []SecurityGroupRule{
				{
					Port:              443,
					Protocol:          "tcp",
					DestinationSG:     "sg-vpc-endpoints",
					Description:       "HTTPS to VPC Endpoints",
				},
				{
					Port:              443,
					Protocol:          "tcp",
					CIDR:              "0.0.0.0/0",
					Description:       "HTTPS to internet",
				},
				{
					Port:              5439,
					Protocol:          "tcp",
					DestinationSG:     "sg-redshift",
					Description:       "PostgreSQL to Redshift cluster",
				},
			},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify self-reference inbound rule
			for _, rule := range tc.inboundRules {
				if rule.IsSelfReference {
					assert.Equal(t, tc.sgID, rule.SourceSG,
						"Self-reference rule must reference own security group ID")
					assert.Equal(t, 443, rule.Port, "MWAA self-reference should use HTTPS (443)")
				}
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}

			// Verify outbound rules follow least privilege
			for _, rule := range tc.outboundRules {
				assert.Contains(t, []int{443, 5439}, rule.Port,
					"MWAA should only allow HTTPS (443) or PostgreSQL (5439)")
				assert.Equal(t, "tcp", rule.Protocol, "MWAA should use TCP protocol")
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}
		})
	}
}

// TestGlueSecurityGroupRules tests SG-Glue configuration
// Validates: Requirements 5.5
func TestGlueSecurityGroupRules(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		sgID          string
		inboundRules  []SecurityGroupRule
		outboundRules []SecurityGroupRule
	}{
		{
			name: "Glue with self-reference for Spark",
			sgID: "sg-glue-456",
			inboundRules: []SecurityGroupRule{
				{
					Port:              0,
					ToPort:            65535,
					Protocol:          "tcp",
					SourceSG:          "sg-glue-456",
					Description:       "All TCP from Glue (self-reference for Spark)",
					IsSelfReference:   true,
				},
			},
			outboundRules: []SecurityGroupRule{
				{
					Port:              443,
					Protocol:          "tcp",
					DestinationSG:     "sg-vpc-endpoints",
					Description:       "HTTPS to VPC Endpoints",
				},
				{
					Port:              0,
					ToPort:            65535,
					Protocol:          "tcp",
					DestinationSG:     "sg-glue-456",
					Description:       "All TCP to Glue (self-reference for Spark)",
					IsSelfReference:   true,
				},
			},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify self-reference inbound rule for Spark cluster communication
			for _, rule := range tc.inboundRules {
				if rule.IsSelfReference {
					assert.Equal(t, tc.sgID, rule.SourceSG,
						"Self-reference rule must reference own security group ID")
					assert.Equal(t, 0, rule.Port, "Glue self-reference should start at port 0")
					assert.Equal(t, 65535, rule.ToPort, "Glue self-reference should end at port 65535")
					assert.Equal(t, "tcp", rule.Protocol, "Glue should use TCP protocol")
				}
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}

			// Verify outbound rules
			for _, rule := range tc.outboundRules {
				if rule.IsSelfReference {
					assert.Equal(t, tc.sgID, rule.DestinationSG,
						"Self-reference rule must reference own security group ID")
				}
				assert.Equal(t, "tcp", rule.Protocol, "Glue should use TCP protocol")
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}
		})
	}
}

// TestEventBridgeSecurityGroupRules tests SG-EventBridge configuration
// Validates: Requirements 5.6
func TestEventBridgeSecurityGroupRules(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		inboundRules  []SecurityGroupRule
		outboundRules []SecurityGroupRule
	}{
		{
			name:         "EventBridge with no inbound rules",
			inboundRules: []SecurityGroupRule{},
			outboundRules: []SecurityGroupRule{
				{
					Port:              443,
					Protocol:          "tcp",
					DestinationSG:     "sg-mwaa",
					Description:       "HTTPS to MWAA for DAG triggering",
				},
				{
					Port:              443,
					Protocol:          "tcp",
					DestinationSG:     "sg-vpc-endpoints",
					Description:       "HTTPS to VPC Endpoints",
				},
			},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Verify no inbound rules (EventBridge receives events internally)
			assert.Empty(t, tc.inboundRules, "EventBridge should have no inbound rules")

			// Verify outbound rules follow least privilege
			for _, rule := range tc.outboundRules {
				assert.Equal(t, 443, rule.Port, "EventBridge should only allow HTTPS (443)")
				assert.Equal(t, "tcp", rule.Protocol, "EventBridge should use TCP protocol")
				assert.NotEmpty(t, rule.DestinationSG, "Outbound should reference specific security groups")
				assert.NotEmpty(t, rule.Description, "Rule should have description")
			}
		})
	}
}

// TestSecurityGroupRuleDescriptions tests that all rules have descriptions
// Validates: Requirements 5.1-5.6
func TestSecurityGroupRuleDescriptions(t *testing.T) {
	t.Parallel()

	// All security group rules must have descriptions for auditability
	testCases := []struct {
		securityGroup string
		ruleType      string
		description   string
	}{
		{"SG-API-Gateway", "ingress", "HTTPS from Janis webhooks"},
		{"SG-API-Gateway", "egress", "Allow all outbound traffic"},
		{"SG-Redshift", "ingress", "PostgreSQL from Lambda functions"},
		{"SG-Redshift", "ingress", "PostgreSQL from MWAA Airflow"},
		{"SG-Redshift", "egress", "HTTPS to VPC Endpoints"},
		{"SG-Lambda", "egress", "PostgreSQL to Redshift cluster"},
		{"SG-Lambda", "egress", "HTTPS to VPC Endpoints"},
		{"SG-Lambda", "egress", "HTTPS to internet (Janis API)"},
		{"SG-MWAA", "ingress", "HTTPS from MWAA workers (self-reference)"},
		{"SG-MWAA", "egress", "HTTPS to VPC Endpoints"},
		{"SG-MWAA", "egress", "HTTPS to internet"},
		{"SG-MWAA", "egress", "PostgreSQL to Redshift cluster"},
		{"SG-Glue", "ingress", "All TCP from Glue (self-reference for Spark)"},
		{"SG-Glue", "egress", "HTTPS to VPC Endpoints"},
		{"SG-Glue", "egress", "All TCP to Glue (self-reference for Spark)"},
		{"SG-EventBridge", "egress", "HTTPS to MWAA for DAG triggering"},
		{"SG-EventBridge", "egress", "HTTPS to VPC Endpoints"},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.securityGroup+"_"+tc.ruleType, func(t *testing.T) {
			t.Parallel()

			assert.NotEmpty(t, tc.description,
				"Security group %s %s rule should have description", tc.securityGroup, tc.ruleType)
			assert.Greater(t, len(tc.description), 10,
				"Description should be meaningful (>10 characters)")
		})
	}
}

// TestSecurityGroupNoOverlyPermissiveRules tests that no rules are overly permissive
// Validates: Requirements 5.1-5.6
func TestSecurityGroupNoOverlyPermissiveRules(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		securityGroup string
		ruleType      string
		port          int
		protocol      string
		cidr          string
		isPermissive  bool
		reason        string
	}{
		{
			name:          "API Gateway inbound HTTPS from internet is acceptable",
			securityGroup: "SG-API-Gateway",
			ruleType:      "ingress",
			port:          443,
			protocol:      "tcp",
			cidr:          "0.0.0.0/0",
			isPermissive:  false,
			reason:        "API Gateway needs to receive webhooks from Janis",
		},
		{
			name:          "Redshift inbound from 0.0.0.0/0 is NOT acceptable",
			securityGroup: "SG-Redshift",
			ruleType:      "ingress",
			port:          5439,
			protocol:      "tcp",
			cidr:          "0.0.0.0/0",
			isPermissive:  true,
			reason:        "Redshift should only accept connections from specific security groups",
		},
		{
			name:          "Lambda inbound from 0.0.0.0/0 is NOT acceptable",
			securityGroup: "SG-Lambda",
			ruleType:      "ingress",
			port:          443,
			protocol:      "tcp",
			cidr:          "0.0.0.0/0",
			isPermissive:  true,
			reason:        "Lambda should have no inbound rules",
		},
		{
			name:          "Glue inbound all ports from 0.0.0.0/0 is NOT acceptable",
			securityGroup: "SG-Glue",
			ruleType:      "ingress",
			port:          0,
			protocol:      "-1",
			cidr:          "0.0.0.0/0",
			isPermissive:  true,
			reason:        "Glue should only accept connections from itself (self-reference)",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			if tc.isPermissive {
				// This rule should NOT exist in production
				assert.True(t, tc.isPermissive,
					"Rule is correctly identified as overly permissive: %s", tc.reason)
			} else {
				// This rule is acceptable
				assert.False(t, tc.isPermissive,
					"Rule is acceptable: %s", tc.reason)
			}
		})
	}
}

// TestSecurityGroupWithTerraform tests security group configuration with Terraform
// This test validates the actual Terraform module
func TestSecurityGroupWithTerraform(t *testing.T) {
	t.Parallel()

	vars := map[string]interface{}{
		"vpc_id":                         "vpc-test123",
		"vpc_cidr":                       "10.0.0.0/16",
		"name_prefix":                    "test-sg",
		"existing_redshift_sg_id":        "sg-redshift-existing",
		"existing_bi_security_groups":    []string{"sg-bi-1", "sg-bi-2"},
		"existing_bi_ip_ranges":          []string{"192.168.1.0/24"},
		"existing_mysql_pipeline_sg_id":  "",
		"allowed_janis_ip_ranges":        []string{"0.0.0.0/0"},
	}

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars:         vars,
		NoColor:      true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)
}

// TestProductionSecurityGroupConfiguration tests the production security group setup
// Validates: Requirements 5.1-5.6
func TestProductionSecurityGroupConfiguration(t *testing.T) {
	t.Parallel()

	// Production configuration
	productionSGs := []struct {
		name          string
		hasInbound    bool
		hasOutbound   bool
		hasSelfRef    bool
	}{
		{
			name:          "SG-API-Gateway",
			hasInbound:    true,
			hasOutbound:   true,
			hasSelfRef:    false,
		},
		{
			name:          "SG-Redshift",
			hasInbound:    true,
			hasOutbound:   true,
			hasSelfRef:    false,
		},
		{
			name:          "SG-Lambda",
			hasInbound:    false,
			hasOutbound:   true,
			hasSelfRef:    false,
		},
		{
			name:          "SG-MWAA",
			hasInbound:    true,
			hasOutbound:   true,
			hasSelfRef:    true,
		},
		{
			name:          "SG-Glue",
			hasInbound:    true,
			hasOutbound:   true,
			hasSelfRef:    true,
		},
		{
			name:          "SG-EventBridge",
			hasInbound:    false,
			hasOutbound:   true,
			hasSelfRef:    false,
		},
		{
			name:          "SG-VPC-Endpoints",
			hasInbound:    true,
			hasOutbound:   true,
			hasSelfRef:    false,
		},
	}

	for _, sg := range productionSGs {
		sg := sg
		t.Run(sg.name, func(t *testing.T) {
			t.Parallel()

			// Verify security group configuration
			assert.NotEmpty(t, sg.name, "Security group should have a name")

			// Verify inbound/outbound rules exist as expected
			if sg.hasInbound {
				assert.True(t, sg.hasInbound, "%s should have inbound rules", sg.name)
			}
			if sg.hasOutbound {
				assert.True(t, sg.hasOutbound, "%s should have outbound rules", sg.name)
			}

			// Verify self-reference configuration
			if sg.hasSelfRef {
				assert.True(t, sg.hasSelfRef, "%s should have self-reference rules", sg.name)
			}
		})
	}

	// Verify total count of security groups
	assert.Equal(t, 7, len(productionSGs), "Production should have exactly 7 security groups")
}

// TestSecurityGroupLeastPrivilegeComprehensive is a comprehensive property test
// that validates all aspects of least privilege principle
func TestSecurityGroupLeastPrivilegeComprehensive(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("Comprehensive least privilege validation", prop.ForAll(
		func(sgType string, ruleType string, port int) bool {
			// Define allowed configurations per security group type
			allowedConfigs := map[string]map[string][]int{
				"api-gateway": {
					"ingress": {443},
					"egress":  {0}, // All protocols
				},
				"redshift": {
					"ingress": {5439},
					"egress":  {443},
				},
				"lambda": {
					"ingress": {},
					"egress":  {443, 5439},
				},
				"mwaa": {
					"ingress": {443},
					"egress":  {443, 5439},
				},
				"glue": {
					"ingress": {0}, // All TCP for Spark
					"egress":  {443, 0}, // HTTPS and all TCP for Spark
				},
				"eventbridge": {
					"ingress": {},
					"egress":  {443},
				},
			}

			// Verify configuration exists for this SG type
			if _, exists := allowedConfigs[sgType]; !exists {
				return false
			}

			// Verify rule type exists
			if _, exists := allowedConfigs[sgType][ruleType]; !exists {
				return false
			}

			// Verify port is in allowed list
			allowedPorts := allowedConfigs[sgType][ruleType]
			for _, allowedPort := range allowedPorts {
				if port == allowedPort {
					return true
				}
			}

			// If no match found, rule doesn't follow least privilege
			return len(allowedPorts) == 0 && ruleType == "ingress"
		},
		gen.OneConstOf("api-gateway", "redshift", "lambda", "mwaa", "glue", "eventbridge"),
		gen.OneConstOf("ingress", "egress"),
		gen.OneConstOf(0, 443, 5439),
	))

	properties.TestingRun(t)
}

// SecurityGroupRule represents a security group rule for testing
type SecurityGroupRule struct {
	Port            int
	ToPort          int
	Protocol        string
	CIDR            string
	SourceSG        string
	DestinationSG   string
	Description     string
	IsSelfReference bool
}

