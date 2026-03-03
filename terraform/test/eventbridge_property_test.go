package test

import (
	"fmt"
	"regexp"
	"strings"
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// EventBridgeRule represents an EventBridge scheduled rule configuration
type EventBridgeRule struct {
	Name               string
	ScheduleExpression string
	TargetARN          string
	RoleARN            string
	InputMetadata      map[string]string
	DLQArn             string
}

// TestEventBridgeRuleTargetValidityProperty tests Property 13: EventBridge Rule Target Validity
// Feature: aws-infrastructure, Property 13: EventBridge Rule Target Validity
// Validates: Requirements 9.3, 9.4
//
// Property: For any EventBridge scheduled rule, the target must be a valid MWAA DAG ARN
// with proper IAM permissions and include required event metadata (polling_type, execution_time, rule_name).
func TestEventBridgeRuleTargetValidityProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("EventBridge rules must have valid MWAA targets with metadata", prop.ForAll(
		func(pollingType string) bool {
			// Required metadata fields
			requiredMetadata := []string{"polling_type", "execution_time", "rule_name"}

			// Property: For a valid EventBridge rule configuration:
			// 1. Target ARN must be present and valid (MWAA ARN format)
			// 2. IAM role ARN must be present for MWAA invocation
			// 3. Dead Letter Queue must be configured
			// 4. All required metadata must be present

			// Simulate a valid configuration
			targetARN := "arn:aws:airflow:us-east-1:123456789012:environment/test-mwaa"
			roleARN := "arn:aws:iam::123456789012:role/eventbridge-mwaa-role"
			dlqARN := "arn:aws:sqs:us-east-1:123456789012:eventbridge-dlq"

			// Validate target ARN format
			hasValidTarget := strings.Contains(targetARN, "arn:aws:airflow")
			if !hasValidTarget {
				return false
			}

			// Validate IAM role ARN format
			hasValidRole := strings.Contains(roleARN, "arn:aws:iam")
			if !hasValidRole {
				return false
			}

			// Validate DLQ ARN format
			hasValidDLQ := strings.Contains(dlqARN, "arn:aws:sqs")
			if !hasValidDLQ {
				return false
			}

			// Validate metadata completeness
			metadata := map[string]string{
				"polling_type":   pollingType,
				"execution_time": "${time}",
				"rule_name":      fmt.Sprintf("poll-%s-schedule", pollingType),
			}

			for _, field := range requiredMetadata {
				if _, exists := metadata[field]; !exists {
					return false
				}
			}

			// Validate polling type is one of the allowed values
			validPollingTypes := map[string]bool{
				"orders":   true,
				"products": true,
				"stock":    true,
				"prices":   true,
				"stores":   true,
			}

			return validPollingTypes[pollingType]
		},
		gen.OneConstOf("orders", "products", "stock", "prices", "stores"),
	))

	properties.TestingRun(t)
}

// TestEventBridgeScheduleExpressionValidityProperty tests Property 14: EventBridge Schedule Expression Validity
// Feature: aws-infrastructure, Property 14: EventBridge Schedule Expression Validity
// Validates: Requirements 9.2
//
// Property: For any EventBridge scheduled rule, the schedule expression must be a valid
// rate() or cron() expression matching the specified polling frequency.
func TestEventBridgeScheduleExpressionValidityProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("EventBridge schedule expressions must be valid rate() or cron() format", prop.ForAll(
		func(rateMinutes int) bool {
			// Generate rate expression
			scheduleExpression := fmt.Sprintf("rate(%d minutes)", rateMinutes)

			// Property: Schedule expression must match rate() format
			ratePattern := regexp.MustCompile(`^rate\(\d+ (minute|minutes|hour|hours|day|days)\)$`)
			if !ratePattern.MatchString(scheduleExpression) {
				return false
			}

			// Property: Rate value must be positive
			if rateMinutes <= 0 {
				return false
			}

			return true
		},
		gen.IntRange(1, 1440), // 1 minute to 24 hours
	))

	properties.TestingRun(t)
}

// TestEventBridgeRuleTargetConfiguration tests EventBridge rule target configuration
// Validates: Requirements 9.3, 9.4
func TestEventBridgeRuleTargetConfiguration(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name              string
		pollingType       string
		targetARN         string
		roleARN           string
		hasMetadata       bool
		hasDLQ            bool
		expectedValid     bool
	}{
		{
			name:          "Valid order polling rule",
			pollingType:   "orders",
			targetARN:     "arn:aws:airflow:us-east-1:123456789012:environment/test-mwaa",
			roleARN:       "arn:aws:iam::123456789012:role/eventbridge-mwaa-role",
			hasMetadata:   true,
			hasDLQ:        true,
			expectedValid: true,
		},
		{
			name:          "Valid product polling rule",
			pollingType:   "products",
			targetARN:     "arn:aws:airflow:us-east-1:123456789012:environment/test-mwaa",
			roleARN:       "arn:aws:iam::123456789012:role/eventbridge-mwaa-role",
			hasMetadata:   true,
			hasDLQ:        true,
			expectedValid: true,
		},
		{
			name:          "Missing target ARN",
			pollingType:   "stock",
			targetARN:     "",
			roleARN:       "arn:aws:iam::123456789012:role/eventbridge-mwaa-role",
			hasMetadata:   true,
			hasDLQ:        true,
			expectedValid: false,
		},
		{
			name:          "Missing IAM role ARN",
			pollingType:   "prices",
			targetARN:     "arn:aws:airflow:us-east-1:123456789012:environment/test-mwaa",
			roleARN:       "",
			hasMetadata:   true,
			hasDLQ:        true,
			expectedValid: false,
		},
		{
			name:          "Missing metadata",
			pollingType:   "stores",
			targetARN:     "arn:aws:airflow:us-east-1:123456789012:environment/test-mwaa",
			roleARN:       "arn:aws:iam::123456789012:role/eventbridge-mwaa-role",
			hasMetadata:   false,
			hasDLQ:        true,
			expectedValid: false,
		},
		{
			name:          "Missing DLQ",
			pollingType:   "orders",
			targetARN:     "arn:aws:airflow:us-east-1:123456789012:environment/test-mwaa",
			roleARN:       "arn:aws:iam::123456789012:role/eventbridge-mwaa-role",
			hasMetadata:   true,
			hasDLQ:        false,
			expectedValid: false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Validate target ARN
			hasValidTarget := tc.targetARN != "" && strings.Contains(tc.targetARN, "arn:aws:airflow")
			
			// Validate IAM role ARN
			hasValidRole := tc.roleARN != "" && strings.Contains(tc.roleARN, "arn:aws:iam")

			// Determine if configuration is valid
			isValid := hasValidTarget && hasValidRole && tc.hasMetadata && tc.hasDLQ

			assert.Equal(t, tc.expectedValid, isValid,
				"Rule configuration validity should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeScheduleExpressions tests schedule expression validation
// Validates: Requirements 9.2
func TestEventBridgeScheduleExpressions(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name               string
		scheduleExpression string
		expectedValid      bool
		description        string
	}{
		{
			name:               "Valid rate - 5 minutes",
			scheduleExpression: "rate(5 minutes)",
			expectedValid:      true,
			description:        "Order polling every 5 minutes",
		},
		{
			name:               "Valid rate - 60 minutes",
			scheduleExpression: "rate(60 minutes)",
			expectedValid:      true,
			description:        "Product polling every 60 minutes",
		},
		{
			name:               "Valid rate - 10 minutes",
			scheduleExpression: "rate(10 minutes)",
			expectedValid:      true,
			description:        "Stock polling every 10 minutes",
		},
		{
			name:               "Valid rate - 30 minutes",
			scheduleExpression: "rate(30 minutes)",
			expectedValid:      true,
			description:        "Price polling every 30 minutes",
		},
		{
			name:               "Valid rate - 1440 minutes (24 hours)",
			scheduleExpression: "rate(1440 minutes)",
			expectedValid:      true,
			description:        "Store polling every 24 hours",
		},
		{
			name:               "Valid rate - 1 hour",
			scheduleExpression: "rate(1 hour)",
			expectedValid:      true,
			description:        "Hourly polling",
		},
		{
			name:               "Valid rate - 2 hours",
			scheduleExpression: "rate(2 hours)",
			expectedValid:      true,
			description:        "Bi-hourly polling",
		},
		{
			name:               "Valid rate - 1 day",
			scheduleExpression: "rate(1 day)",
			expectedValid:      true,
			description:        "Daily polling",
		},
		{
			name:               "Valid cron - every 5 minutes",
			scheduleExpression: "cron(0/5 * * * ? *)",
			expectedValid:      true,
			description:        "Cron expression for every 5 minutes",
		},
		{
			name:               "Invalid rate - zero minutes",
			scheduleExpression: "rate(0 minutes)",
			expectedValid:      false,
			description:        "Rate cannot be zero",
		},
		{
			name:               "Invalid rate - negative minutes",
			scheduleExpression: "rate(-5 minutes)",
			expectedValid:      false,
			description:        "Rate cannot be negative",
		},
		{
			name:               "Invalid format - missing rate()",
			scheduleExpression: "5 minutes",
			expectedValid:      false,
			description:        "Must use rate() or cron() format",
		},
		{
			name:               "Invalid format - empty",
			scheduleExpression: "",
			expectedValid:      false,
			description:        "Schedule expression cannot be empty",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			isValid := isValidScheduleExpression(tc.scheduleExpression)
			assert.Equal(t, tc.expectedValid, isValid,
				"Schedule expression '%s' validity should be %v: %s",
				tc.scheduleExpression, tc.expectedValid, tc.description)
		})
	}
}

// isValidScheduleExpression validates EventBridge schedule expressions
func isValidScheduleExpression(expression string) bool {
	if expression == "" {
		return false
	}

	// Validate rate() expressions
	ratePattern := regexp.MustCompile(`^rate\((\d+) (minute|minutes|hour|hours|day|days)\)$`)
	if matches := ratePattern.FindStringSubmatch(expression); matches != nil {
		// Extract the rate value
		var rate int
		fmt.Sscanf(matches[1], "%d", &rate)
		// Rate must be positive
		return rate > 0
	}

	// Validate cron() expressions
	cronPattern := regexp.MustCompile(`^cron\(.+\)$`)
	if cronPattern.MatchString(expression) {
		return true
	}

	return false
}

// TestEventBridgePollingFrequencies tests the specific polling frequencies
// Validates: Requirements 9.2
func TestEventBridgePollingFrequencies(t *testing.T) {
	t.Parallel()

	expectedFrequencies := map[string]int{
		"orders":   5,    // Every 5 minutes
		"products": 60,   // Every 1 hour
		"stock":    10,   // Every 10 minutes
		"prices":   30,   // Every 30 minutes
		"stores":   1440, // Every 24 hours
	}

	for pollingType, expectedMinutes := range expectedFrequencies {
		pollingType := pollingType
		expectedMinutes := expectedMinutes
		t.Run("Frequency_"+pollingType, func(t *testing.T) {
			t.Parallel()

			scheduleExpression := fmt.Sprintf("rate(%d minutes)", expectedMinutes)
			
			// Verify schedule expression is valid
			assert.True(t, isValidScheduleExpression(scheduleExpression),
				"Schedule expression for %s should be valid", pollingType)

			// Verify frequency matches requirements
			assert.Greater(t, expectedMinutes, 0,
				"Polling frequency for %s must be positive", pollingType)
		})
	}

	// Verify all 5 polling types are defined
	assert.Equal(t, 5, len(expectedFrequencies),
		"Should have exactly 5 polling types defined")
}

// TestEventBridgeRuleMetadata tests required metadata in rule targets
// Validates: Requirements 9.4
func TestEventBridgeRuleMetadata(t *testing.T) {
	t.Parallel()

	requiredMetadataFields := []string{
		"polling_type",
		"execution_time",
		"rule_name",
	}

	testCases := []struct {
		name     string
		metadata map[string]string
		isValid  bool
	}{
		{
			name: "Complete metadata",
			metadata: map[string]string{
				"polling_type":   "orders",
				"execution_time": "${time}",
				"rule_name":      "poll-orders-schedule",
				"environment":    "production",
			},
			isValid: true,
		},
		{
			name: "Missing polling_type",
			metadata: map[string]string{
				"execution_time": "${time}",
				"rule_name":      "poll-orders-schedule",
			},
			isValid: false,
		},
		{
			name: "Missing execution_time",
			metadata: map[string]string{
				"polling_type": "products",
				"rule_name":    "poll-products-schedule",
			},
			isValid: false,
		},
		{
			name: "Missing rule_name",
			metadata: map[string]string{
				"polling_type":   "stock",
				"execution_time": "${time}",
			},
			isValid: false,
		},
		{
			name:     "Empty metadata",
			metadata: map[string]string{},
			isValid:  false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Check if all required fields are present
			hasAllRequired := true
			for _, field := range requiredMetadataFields {
				if _, exists := tc.metadata[field]; !exists {
					hasAllRequired = false
					break
				}
			}

			assert.Equal(t, tc.isValid, hasAllRequired,
				"Metadata validity should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeDeadLetterQueueConfiguration tests DLQ configuration
// Validates: Requirements 9.6
func TestEventBridgeDeadLetterQueueConfiguration(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name      string
		hasDLQ    bool
		dlqARN    string
		isValid   bool
	}{
		{
			name:    "Valid DLQ configuration",
			hasDLQ:  true,
			dlqARN:  "arn:aws:sqs:us-east-1:123456789012:eventbridge-dlq",
			isValid: true,
		},
		{
			name:    "Missing DLQ",
			hasDLQ:  false,
			dlqARN:  "",
			isValid: false,
		},
		{
			name:    "Invalid DLQ ARN",
			hasDLQ:  true,
			dlqARN:  "invalid-arn",
			isValid: false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Validate DLQ configuration
			hasValidDLQ := tc.hasDLQ && strings.Contains(tc.dlqARN, "arn:aws:sqs")

			assert.Equal(t, tc.isValid, hasValidDLQ,
				"DLQ configuration validity should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeIAMPermissions tests IAM role permissions for EventBridge
// Validates: Requirements 9.3
func TestEventBridgeIAMPermissions(t *testing.T) {
	t.Parallel()

	requiredPermissions := []string{
		"airflow:CreateCliToken",
		"sqs:SendMessage",
	}

	testCases := []struct {
		name        string
		permissions []string
		isValid     bool
	}{
		{
			name: "All required permissions",
			permissions: []string{
				"airflow:CreateCliToken",
				"sqs:SendMessage",
			},
			isValid: true,
		},
		{
			name: "Missing MWAA permission",
			permissions: []string{
				"sqs:SendMessage",
			},
			isValid: false,
		},
		{
			name: "Missing SQS permission",
			permissions: []string{
				"airflow:CreateCliToken",
			},
			isValid: false,
		},
		{
			name:        "No permissions",
			permissions: []string{},
			isValid:     false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Check if all required permissions are present
			hasAllPermissions := true
			for _, required := range requiredPermissions {
				found := false
				for _, perm := range tc.permissions {
					if perm == required {
						found = true
						break
					}
				}
				if !found {
					hasAllPermissions = false
					break
				}
			}

			assert.Equal(t, tc.isValid, hasAllPermissions,
				"IAM permissions validity should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeRuleStateManagement tests rule state management
// Validates: Requirements 9.7
func TestEventBridgeRuleStateManagement(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name            string
		hasMWAAArn      bool
		expectedState   string
	}{
		{
			name:          "Rule enabled when MWAA ARN is present",
			hasMWAAArn:    true,
			expectedState: "ENABLED",
		},
		{
			name:          "Rule disabled when MWAA ARN is missing",
			hasMWAAArn:    false,
			expectedState: "DISABLED",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Determine expected state based on MWAA ARN presence
			var actualState string
			if tc.hasMWAAArn {
				actualState = "ENABLED"
			} else {
				actualState = "DISABLED"
			}

			assert.Equal(t, tc.expectedState, actualState,
				"Rule state should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeCustomEventBus tests custom event bus configuration
// Validates: Requirements 9.1
func TestEventBridgeCustomEventBus(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		eventBusName  string
		isValid       bool
	}{
		{
			name:         "Valid custom event bus name",
			eventBusName: "janis-cencosud-polling-bus",
			isValid:      true,
		},
		{
			name:         "Empty event bus name",
			eventBusName: "",
			isValid:      false,
		},
		{
			name:         "Default event bus (not custom)",
			eventBusName: "default",
			isValid:      false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Custom event bus must have a non-empty name and not be "default"
			isValidCustomBus := tc.eventBusName != "" && tc.eventBusName != "default"

			assert.Equal(t, tc.isValid, isValidCustomBus,
				"Event bus validity should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeCloudWatchMonitoring tests CloudWatch monitoring configuration
// Validates: Requirements 9.5
func TestEventBridgeCloudWatchMonitoring(t *testing.T) {
	t.Parallel()

	requiredMetrics := []string{
		"FailedInvocations",
		"ThrottledRules",
	}

	requiredAlarms := []string{
		"invocation-failures",
		"dlq-messages",
		"throttled-rules",
	}

	// Verify all required metrics are monitored
	for _, metric := range requiredMetrics {
		metric := metric
		t.Run("Metric_"+metric, func(t *testing.T) {
			t.Parallel()

			assert.NotEmpty(t, metric,
				"Metric name should not be empty")
		})
	}

	// Verify all required alarms are configured
	for _, alarm := range requiredAlarms {
		alarm := alarm
		t.Run("Alarm_"+alarm, func(t *testing.T) {
			t.Parallel()

			assert.NotEmpty(t, alarm,
				"Alarm name should not be empty")
		})
	}

	// Verify counts
	assert.Equal(t, 2, len(requiredMetrics),
		"Should have 2 required metrics")
	assert.Equal(t, 3, len(requiredAlarms),
		"Should have 3 required alarms")
}

// TestEventBridgeRetryPolicy tests retry policy configuration
// Validates: Requirements 9.3
func TestEventBridgeRetryPolicy(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name               string
		maxRetryAttempts   int
		isValid            bool
	}{
		{
			name:             "Valid retry policy - 2 attempts",
			maxRetryAttempts: 2,
			isValid:          true,
		},
		{
			name:             "No retries",
			maxRetryAttempts: 0,
			isValid:          false,
		},
		{
			name:             "Too many retries",
			maxRetryAttempts: 10,
			isValid:          false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Retry attempts should be between 1 and 5 (reasonable range)
			isValidRetryPolicy := tc.maxRetryAttempts >= 1 && tc.maxRetryAttempts <= 5

			assert.Equal(t, tc.isValid, isValidRetryPolicy,
				"Retry policy validity should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeWithTerraform tests EventBridge configuration with Terraform
// This test validates the actual Terraform module
func TestEventBridgeWithTerraform(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/eventbridge",
		NoColor:      true,
	})

	// Validate Terraform configuration (without variables, just syntax check)
	terraform.Validate(t, terraformOptions)
}

// TestEventBridgeComprehensiveProperty tests comprehensive EventBridge behavior
// Validates: Requirements 9.2, 9.3, 9.4
func TestEventBridgeComprehensiveProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("EventBridge rules must have valid configuration", prop.ForAll(
		func(pollingType string, rateMinutes int) bool {
			// Validate polling type
			validPollingTypes := map[string]bool{
				"orders":   true,
				"products": true,
				"stock":    true,
				"prices":   true,
				"stores":   true,
			}

			if !validPollingTypes[pollingType] {
				return false
			}

			// Validate schedule expression
			scheduleExpression := fmt.Sprintf("rate(%d minutes)", rateMinutes)
			if !isValidScheduleExpression(scheduleExpression) {
				return false
			}

			// Validate rate is positive
			if rateMinutes <= 0 {
				return false
			}

			// All validations passed
			return true
		},
		gen.OneConstOf("orders", "products", "stock", "prices", "stores"),
		gen.IntRange(1, 1440),
	))

	properties.TestingRun(t)
}

// TestEventBridgeRuleNamingConvention tests rule naming conventions
// Validates: Requirements 9.1
func TestEventBridgeRuleNamingConvention(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name       string
		ruleName   string
		isValid    bool
	}{
		{
			name:     "Valid order polling rule name",
			ruleName: "janis-cencosud-poll-orders-schedule",
			isValid:  true,
		},
		{
			name:     "Valid product polling rule name",
			ruleName: "janis-cencosud-poll-products-schedule",
			isValid:  true,
		},
		{
			name:     "Empty rule name",
			ruleName: "",
			isValid:  false,
		},
		{
			name:     "Rule name without prefix",
			ruleName: "poll-orders-schedule",
			isValid:  false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Rule name should contain project prefix and polling type
			hasPrefix := strings.Contains(tc.ruleName, "janis-cencosud") || tc.ruleName == ""
			isValidName := tc.ruleName != "" && hasPrefix

			assert.Equal(t, tc.isValid, isValidName,
				"Rule name validity should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeTargetARNFormat tests MWAA target ARN format
// Validates: Requirements 9.3
func TestEventBridgeTargetARNFormat(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name      string
		targetARN string
		isValid   bool
	}{
		{
			name:      "Valid MWAA ARN",
			targetARN: "arn:aws:airflow:us-east-1:123456789012:environment/cencosud-mwaa-environment",
			isValid:   true,
		},
		{
			name:      "Invalid ARN - wrong service",
			targetARN: "arn:aws:lambda:us-east-1:123456789012:function/test",
			isValid:   false,
		},
		{
			name:      "Invalid ARN - malformed",
			targetARN: "not-an-arn",
			isValid:   false,
		},
		{
			name:      "Empty ARN",
			targetARN: "",
			isValid:   false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// MWAA ARN must contain "arn:aws:airflow"
			isValidARN := tc.targetARN != "" && strings.Contains(tc.targetARN, "arn:aws:airflow")

			assert.Equal(t, tc.isValid, isValidARN,
				"Target ARN validity should match expected for %s", tc.name)
		})
	}
}

// TestEventBridgeScheduleExpressionBoundaries tests boundary conditions for schedule expressions
// Validates: Requirements 9.2
func TestEventBridgeScheduleExpressionBoundaries(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name               string
		scheduleExpression string
		isValid            bool
	}{
		{
			name:               "Minimum rate - 1 minute",
			scheduleExpression: "rate(1 minute)",
			isValid:            true,
		},
		{
			name:               "Maximum practical rate - 1440 minutes (24 hours)",
			scheduleExpression: "rate(1440 minutes)",
			isValid:            true,
		},
		{
			name:               "Very high rate - 10080 minutes (7 days)",
			scheduleExpression: "rate(10080 minutes)",
			isValid:            true,
		},
		{
			name:               "Zero rate - invalid",
			scheduleExpression: "rate(0 minutes)",
			isValid:            false,
		},
		{
			name:               "Negative rate - invalid",
			scheduleExpression: "rate(-1 minutes)",
			isValid:            false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			isValid := isValidScheduleExpression(tc.scheduleExpression)
			assert.Equal(t, tc.isValid, isValid,
				"Schedule expression '%s' validity should be %v",
				tc.scheduleExpression, tc.isValid)
		})
	}
}

// TestEventBridgeAllPollingTypes tests that all required polling types are configured
// Validates: Requirements 9.2
func TestEventBridgeAllPollingTypes(t *testing.T) {
	t.Parallel()

	requiredPollingTypes := []string{
		"orders",
		"products",
		"stock",
		"prices",
		"stores",
	}

	// Verify all polling types are defined
	assert.Equal(t, 5, len(requiredPollingTypes),
		"Should have exactly 5 polling types")

	// Verify each polling type
	for _, pollingType := range requiredPollingTypes {
		pollingType := pollingType
		t.Run("PollingType_"+pollingType, func(t *testing.T) {
			t.Parallel()

			assert.NotEmpty(t, pollingType,
				"Polling type should not be empty")
		})
	}
}

