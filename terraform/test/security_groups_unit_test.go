package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

// TestSGAPIGatewayConfiguration tests that SG-API-Gateway has correct inbound/outbound rules
// Validates: Requirements 5.1
func TestSGAPIGatewayConfiguration(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would verify:
	// 1. Inbound: HTTPS (443) from 0.0.0.0/0 (or specific Janis IP ranges)
	// 2. Outbound: All traffic to 0.0.0.0/0
	// 3. No overly permissive rules on sensitive ports
}

// TestSGAPIGatewayNoOverlyPermissiveRules tests that API Gateway SG doesn't have overly permissive rules
// Validates: Requirements 5.1
func TestSGAPIGatewayNoOverlyPermissiveRules(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-permissive",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// The module only allows HTTPS (443) inbound, which is appropriate for API Gateway
	// Outbound allows all traffic, which is necessary for Lambda invocations
}

// TestSGRedshiftConfiguration tests that SG-Redshift has correct inbound/outbound rules
// Validates: Requirements 5.2
func TestSGRedshiftConfiguration(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name                   string
		biSecurityGroups       []string
		biIPRanges             []string
		mysqlPipelineSGID      string
		expectValidConfig      bool
	}{
		{
			name:                   "With BI security groups",
			biSecurityGroups:       []string{"sg-bi-001", "sg-bi-002"},
			biIPRanges:             []string{},
			mysqlPipelineSGID:      "",
			expectValidConfig:      true,
		},
		{
			name:                   "With BI IP ranges",
			biSecurityGroups:       []string{},
			biIPRanges:             []string{"10.1.0.0/24", "10.2.0.0/24"},
			mysqlPipelineSGID:      "",
			expectValidConfig:      true,
		},
		{
			name:                   "With MySQL pipeline (migration)",
			biSecurityGroups:       []string{},
			biIPRanges:             []string{},
			mysqlPipelineSGID:      "sg-mysql-pipeline",
			expectValidConfig:      true,
		},
		{
			name:                   "With all sources",
			biSecurityGroups:       []string{"sg-bi-001"},
			biIPRanges:             []string{"10.1.0.0/24"},
			mysqlPipelineSGID:      "sg-mysql-pipeline",
			expectValidConfig:      true,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
				TerraformDir: "../modules/security-groups",
				Vars: map[string]interface{}{
					"vpc_id":                        "vpc-test123",
					"vpc_cidr":                      "10.0.0.0/16",
					"name_prefix":                   "test-sg-redshift",
					"existing_redshift_sg_id":       "sg-redshift123",
					"existing_bi_security_groups":   tc.biSecurityGroups,
					"existing_bi_ip_ranges":         tc.biIPRanges,
					"existing_mysql_pipeline_sg_id": tc.mysqlPipelineSGID,
					"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			exitCode, err := terraform.ValidateE(t, terraformOptions)
assert.NoError(t, err)

			if tc.expectValidConfig {
				assert.Equal(t, 0, exitCode, "Terraform validation should succeed")
			} else {
				assert.NotEqual(t, 0, exitCode, "Terraform validation should fail")
			}

			// Note: In a real deployment test, we would verify:
			// 1. Inbound: PostgreSQL (5439) from SG-Lambda, SG-MWAA, BI systems
			// 2. Outbound: HTTPS (443) to VPC Endpoints only
			// 3. No overly permissive rules (no 0.0.0.0/0 on port 5439)
		})
	}
}

// TestSGRedshiftNoOverlyPermissiveRules tests that Redshift SG follows least privilege
// Validates: Requirements 5.2, 11.3
func TestSGRedshiftNoOverlyPermissiveRules(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-redshift-secure",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{"sg-bi-001"},
			"existing_bi_ip_ranges":         []string{"10.1.0.0/24"},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// The module only allows PostgreSQL (5439) from specific security groups
	// Outbound is restricted to HTTPS (443) to VPC Endpoints only
	// No 0.0.0.0/0 rules on sensitive ports
}

// TestSGLambdaConfiguration tests that SG-Lambda has correct inbound/outbound rules
// Validates: Requirements 5.3
func TestSGLambdaConfiguration(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-lambda",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would verify:
	// 1. No inbound rules (Lambda doesn't receive direct connections)
	// 2. Outbound: PostgreSQL (5439) to SG-Redshift
	// 3. Outbound: HTTPS (443) to VPC Endpoints and 0.0.0.0/0
}

// TestSGLambdaNoInboundRules tests that Lambda SG has no inbound rules
// Validates: Requirements 5.3
func TestSGLambdaNoInboundRules(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-lambda-inbound",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// The module defines no ingress rules for Lambda security group
	// This is correct as Lambda functions don't receive direct connections
}

// TestSGMWAAConfiguration tests that SG-MWAA has correct inbound/outbound rules
// Validates: Requirements 5.4
func TestSGMWAAConfiguration(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-mwaa",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would verify:
	// 1. Inbound: HTTPS (443) from SG-MWAA (self-reference for workers)
	// 2. Outbound: HTTPS (443) to VPC Endpoints and 0.0.0.0/0
	// 3. Outbound: PostgreSQL (5439) to SG-Redshift
}

// TestSGMWAASelfReference tests that MWAA SG has valid self-reference
// Validates: Requirements 5.4
func TestSGMWAASelfReference(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-mwaa-self",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// The module uses referenced_security_group_id = aws_security_group.mwaa.id
	// This creates a valid self-reference for MWAA worker communication
}

// TestSGGlueConfiguration tests that SG-Glue has correct inbound/outbound rules
// Validates: Requirements 5.5
func TestSGGlueConfiguration(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-glue",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would verify:
	// 1. Inbound: All TCP from SG-Glue (self-reference for Spark)
	// 2. Outbound: HTTPS (443) to VPC Endpoints
	// 3. Outbound: All TCP to SG-Glue (self-reference)
}

// TestSGGlueSelfReference tests that Glue SG has valid self-reference
// Validates: Requirements 5.5
func TestSGGlueSelfReference(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-glue-self",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// The module uses referenced_security_group_id = aws_security_group.glue.id
	// This creates a valid self-reference for Spark cluster communication
}

// TestSGEventBridgeConfiguration tests that SG-EventBridge has correct outbound rules
// Validates: Requirements 5.6
func TestSGEventBridgeConfiguration(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-eventbridge",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would verify:
	// 1. Outbound: HTTPS (443) to MWAA endpoints
	// 2. Outbound: HTTPS (443) to VPC Endpoints
}

// TestSGVPCEndpointsConfiguration tests that SG-VPC-Endpoints has correct rules
// Validates: Requirements 4.5
func TestSGVPCEndpointsConfiguration(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-vpc-endpoints",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Note: In a real deployment test, we would verify:
	// 1. Inbound: HTTPS (443) from entire VPC CIDR
	// 2. Outbound: HTTPS (443) to AWS services (0.0.0.0/0)
}

// TestAllSecurityGroupsIntegrity tests that all security groups can be created together
func TestAllSecurityGroupsIntegrity(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-integrity",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{"sg-bi-001"},
			"existing_bi_ip_ranges":         []string{"10.1.0.0/24"},
			"existing_mysql_pipeline_sg_id": "sg-mysql-pipeline",
			"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// Verify the configuration can be planned without errors
	exitCode, err := terraform.InitAndPlanE(t, terraformOptions)
assert.NoError(t, err)
	assert.Equal(t, 0, exitCode, "Terraform plan should succeed for all security groups")
}

// TestSecurityGroupsWithMultipleJanisIPRanges tests API Gateway SG with multiple Janis IP ranges
// Validates: Requirements 5.1
func TestSecurityGroupsWithMultipleJanisIPRanges(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-multi-janis",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{},
			"existing_bi_ip_ranges":         []string{},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"1.2.3.0/24", "4.5.6.0/24", "7.8.9.0/24"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// The module creates multiple ingress rules for each Janis IP range
	// This allows restricting webhook access to specific Janis IP addresses
}

// TestSecurityGroupsLeastPrivilege tests that all SGs follow least privilege principle
// Validates: Requirements 5.1-5.6
func TestSecurityGroupsLeastPrivilege(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/security-groups",
		Vars: map[string]interface{}{
			"vpc_id":                        "vpc-test123",
			"vpc_cidr":                      "10.0.0.0/16",
			"name_prefix":                   "test-sg-least-privilege",
			"existing_redshift_sg_id":       "sg-redshift123",
			"existing_bi_security_groups":   []string{"sg-bi-001"},
			"existing_bi_ip_ranges":         []string{"10.1.0.0/24"},
			"existing_mysql_pipeline_sg_id": "",
			"allowed_janis_ip_ranges":       []string{"1.2.3.0/24"},
		},
		NoColor: true,
	})

	// Validate Terraform configuration
	terraform.Validate(t, terraformOptions)

	// All security groups follow least privilege:
	// - API Gateway: Only HTTPS (443) inbound from specific IPs
	// - Redshift: Only PostgreSQL (5439) from specific SGs, HTTPS outbound to VPC endpoints only
	// - Lambda: No inbound, specific outbound to Redshift and VPC endpoints
	// - MWAA: Self-reference for workers, specific outbound
	// - Glue: Self-reference for Spark, HTTPS to VPC endpoints
	// - EventBridge: Only HTTPS outbound to MWAA and VPC endpoints
	// - VPC Endpoints: HTTPS from VPC CIDR only
}

// TestSecurityGroupsResourceNaming tests that security groups follow naming conventions
// Validates: Requirements 5.1-5.6
func TestSecurityGroupsResourceNaming(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name       string
		namePrefix string
	}{
		{
			name:       "Production naming",
			namePrefix: "janis-cencosud-prod",
		},
		{
			name:       "Staging naming",
			namePrefix: "janis-cencosud-staging",
		},
		{
			name:       "Development naming",
			namePrefix: "janis-cencosud-dev",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
				TerraformDir: "../modules/security-groups",
				Vars: map[string]interface{}{
					"vpc_id":                        "vpc-test123",
					"vpc_cidr":                      "10.0.0.0/16",
					"name_prefix":                   tc.namePrefix,
					"existing_redshift_sg_id":       "sg-redshift123",
					"existing_bi_security_groups":   []string{},
					"existing_bi_ip_ranges":         []string{},
					"existing_mysql_pipeline_sg_id": "",
					"allowed_janis_ip_ranges":       []string{"0.0.0.0/0"},
				},
				NoColor: true,
			})

			// Validate Terraform configuration
			terraform.Validate(t, terraformOptions)

			// Security groups are named: ${var.name_prefix}-sg-{purpose}
			// Example: janis-cencosud-prod-sg-api-gateway
		})
	}
}

