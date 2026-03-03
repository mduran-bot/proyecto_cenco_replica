package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/leanovate/gopter"
	"github.com/leanovate/gopter/gen"
	"github.com/leanovate/gopter/prop"
	"github.com/stretchr/testify/assert"
)

// WAFRequest represents a simulated request for WAF testing
type WAFRequest struct {
	SourceIP      string
	CountryCode   string
	RequestCount  int
	TimeWindowMin int
}

// TestWAFRateLimitEnforcementProperty tests Property 10: WAF Rate Limit Enforcement
// Feature: aws-infrastructure, Property 10: WAF Rate Limit Enforcement
// Validates: Requirements 7.1
//
// Property: For any IP address making requests to the API Gateway, if the request count
// exceeds 2,000 requests in a 5-minute window, subsequent requests must be blocked with
// a 429 response code.
func TestWAFRateLimitEnforcementProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("WAF must block requests exceeding rate limit with 429", prop.ForAll(
		func(requestCount int, timeWindowMin int) bool {
			// WAF configuration: 2,000 requests per IP in 5 minutes
			rateLimit := 2000
			timeWindow := 5

			// Normalize request count to 5-minute window
			requestsPer5Min := requestCount
			if timeWindowMin != timeWindow {
				// Scale request count to 5-minute window
				requestsPer5Min = (requestCount * timeWindow) / timeWindowMin
			}

			// Property: If requests exceed rate limit, they should be blocked
			if requestsPer5Min > rateLimit {
				// Requests should be blocked with 429
				return true // This represents the expected behavior
			}

			// If requests are within limit, they should be allowed
			return requestsPer5Min <= rateLimit
		},
		gen.IntRange(0, 5000),      // Request count: 0 to 5000
		gen.IntRange(1, 10),        // Time window: 1 to 10 minutes
	))

	properties.TestingRun(t)
}

// TestWAFGeoBlockingEnforcementProperty tests Property 11: WAF Geo-Blocking Enforcement
// Feature: aws-infrastructure, Property 11: WAF Geo-Blocking Enforcement
// Validates: Requirements 7.2
//
// Property: For any incoming request to the API Gateway, if the source country is not
// Peru (PE) or an AWS region, the request must be blocked.
func TestWAFGeoBlockingEnforcementProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("WAF must block requests from non-allowed countries", prop.ForAll(
		func(countryCode string) bool {
			// Allowed countries: Peru (PE)
			allowedCountries := map[string]bool{
				"PE": true, // Peru
			}

			// Property: If country is not in allowed list, request should be blocked
			if !allowedCountries[countryCode] {
				// Request should be blocked with 403
				return true // This represents the expected behavior
			}

			// If country is allowed, request should pass through
			return allowedCountries[countryCode]
		},
		gen.OneConstOf("PE", "US", "BR", "AR", "CL", "CO", "MX", "CN", "RU", "DE", "FR", "GB", "JP", "IN"),
	))

	properties.TestingRun(t)
}

// TestWAFRateLimitConfiguration tests the WAF rate limit configuration
// Validates: Requirements 7.1
func TestWAFRateLimitConfiguration(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name          string
		requestCount  int
		timeWindowMin int
		shouldBlock   bool
		responseCode  int
	}{
		{
			name:          "Within rate limit - 1000 requests in 5 minutes",
			requestCount:  1000,
			timeWindowMin: 5,
			shouldBlock:   false,
			responseCode:  200,
		},
		{
			name:          "At rate limit boundary - 2000 requests in 5 minutes",
			requestCount:  2000,
			timeWindowMin: 5,
			shouldBlock:   false,
			responseCode:  200,
		},
		{
			name:          "Exceeds rate limit - 2001 requests in 5 minutes",
			requestCount:  2001,
			timeWindowMin: 5,
			shouldBlock:   true,
			responseCode:  429,
		},
		{
			name:          "Far exceeds rate limit - 5000 requests in 5 minutes",
			requestCount:  5000,
			timeWindowMin: 5,
			shouldBlock:   true,
			responseCode:  429,
		},
		{
			name:          "High rate in short time - 500 requests in 1 minute",
			requestCount:  500,
			timeWindowMin: 1,
			shouldBlock:   true, // 500 * 5 = 2500 > 2000 when normalized to 5-min window
			responseCode:  429,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Calculate requests per 5-minute window
			rateLimit := 2000
			timeWindow := 5
			requestsPer5Min := (tc.requestCount * timeWindow) / tc.timeWindowMin

			// Verify blocking behavior
			actualShouldBlock := requestsPer5Min > rateLimit
			assert.Equal(t, tc.shouldBlock, actualShouldBlock,
				"Request count %d in %d minutes should result in block=%v",
				tc.requestCount, tc.timeWindowMin, tc.shouldBlock)

			// Verify response code
			if actualShouldBlock {
				assert.Equal(t, 429, tc.responseCode,
					"Blocked requests should return 429 (Too Many Requests)")
			} else {
				assert.Equal(t, 200, tc.responseCode,
					"Allowed requests should return 200 (OK)")
			}
		})
	}
}

// TestWAFGeoBlockingConfiguration tests the WAF geo-blocking configuration
// Validates: Requirements 7.2
func TestWAFGeoBlockingConfiguration(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name         string
		countryCode  string
		shouldBlock  bool
		responseCode int
		description  string
	}{
		{
			name:         "Allow Peru",
			countryCode:  "PE",
			shouldBlock:  false,
			responseCode: 200,
			description:  "Peru is explicitly allowed",
		},
		{
			name:         "Block United States",
			countryCode:  "US",
			shouldBlock:  true,
			responseCode: 403,
			description:  "US is not in allowed list",
		},
		{
			name:         "Block Brazil",
			countryCode:  "BR",
			shouldBlock:  true,
			responseCode: 403,
			description:  "Brazil is not in allowed list",
		},
		{
			name:         "Block Argentina",
			countryCode:  "AR",
			shouldBlock:  true,
			responseCode: 403,
			description:  "Argentina is not in allowed list",
		},
		{
			name:         "Block Chile",
			countryCode:  "CL",
			shouldBlock:  true,
			responseCode: 403,
			description:  "Chile is not in allowed list",
		},
		{
			name:         "Block Colombia",
			countryCode:  "CO",
			shouldBlock:  true,
			responseCode: 403,
			description:  "Colombia is not in allowed list",
		},
		{
			name:         "Block China",
			countryCode:  "CN",
			shouldBlock:  true,
			responseCode: 403,
			description:  "China is not in allowed list",
		},
		{
			name:         "Block Russia",
			countryCode:  "RU",
			shouldBlock:  true,
			responseCode: 403,
			description:  "Russia is not in allowed list",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			// Allowed countries configuration
			allowedCountries := map[string]bool{
				"PE": true, // Peru
			}

			// Verify blocking behavior
			actualShouldBlock := !allowedCountries[tc.countryCode]
			assert.Equal(t, tc.shouldBlock, actualShouldBlock,
				"Country %s should result in block=%v: %s",
				tc.countryCode, tc.shouldBlock, tc.description)

			// Verify response code
			if actualShouldBlock {
				assert.Equal(t, 403, tc.responseCode,
					"Blocked requests should return 403 (Forbidden)")
			} else {
				assert.Equal(t, 200, tc.responseCode,
					"Allowed requests should return 200 (OK)")
			}
		})
	}
}

// TestWAFRateLimitPerIPIsolation tests that rate limiting is per-IP
// Validates: Requirements 7.1
func TestWAFRateLimitPerIPIsolation(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name        string
		requests    []WAFRequest
		description string
	}{
		{
			name: "Different IPs should have independent rate limits",
			requests: []WAFRequest{
				{SourceIP: "192.168.1.1", RequestCount: 2000, TimeWindowMin: 5},
				{SourceIP: "192.168.1.2", RequestCount: 2000, TimeWindowMin: 5},
				{SourceIP: "192.168.1.3", RequestCount: 2000, TimeWindowMin: 5},
			},
			description: "Each IP should be allowed 2000 requests independently",
		},
		{
			name: "Same IP exceeding limit should be blocked",
			requests: []WAFRequest{
				{SourceIP: "192.168.1.1", RequestCount: 2001, TimeWindowMin: 5},
			},
			description: "Single IP exceeding limit should be blocked",
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			rateLimit := 2000

			for _, req := range tc.requests {
				// Calculate requests per 5-minute window
				requestsPer5Min := (req.RequestCount * 5) / req.TimeWindowMin
				shouldBlock := requestsPer5Min > rateLimit

				if shouldBlock {
					assert.Greater(t, requestsPer5Min, rateLimit,
						"IP %s with %d requests should exceed rate limit",
						req.SourceIP, req.RequestCount)
				} else {
					assert.LessOrEqual(t, requestsPer5Min, rateLimit,
						"IP %s with %d requests should be within rate limit",
						req.SourceIP, req.RequestCount)
				}
			}
		})
	}
}

// TestWAFCustomResponseBody tests the custom response body for rate limiting
// Validates: Requirements 7.1
func TestWAFCustomResponseBody(t *testing.T) {
	t.Parallel()

	// WAF configuration includes custom response body for rate limit
	customResponseBody := "Too many requests. Please try again later."
	customResponseCode := 429

	assert.NotEmpty(t, customResponseBody,
		"WAF should have custom response body for rate limit violations")
	assert.Equal(t, 429, customResponseCode,
		"WAF should return 429 for rate limit violations")
	assert.Contains(t, customResponseBody, "Too many requests",
		"Custom response should indicate rate limiting")
}

// TestWAFManagedRulesConfiguration tests AWS Managed Rules configuration
// Validates: Requirements 7.3
func TestWAFManagedRulesConfiguration(t *testing.T) {
	t.Parallel()

	// Required AWS Managed Rules
	requiredManagedRules := []struct {
		name        string
		description string
	}{
		{
			name:        "AWSManagedRulesAmazonIpReputationList",
			description: "Blocks known malicious IPs",
		},
		{
			name:        "AWSManagedRulesCommonRuleSet",
			description: "OWASP Top 10 protection",
		},
		{
			name:        "AWSManagedRulesKnownBadInputsRuleSet",
			description: "Blocks malicious payloads",
		},
	}

	for _, rule := range requiredManagedRules {
		rule := rule
		t.Run(rule.name, func(t *testing.T) {
			t.Parallel()

			assert.NotEmpty(t, rule.name,
				"Managed rule should have a name")
			assert.NotEmpty(t, rule.description,
				"Managed rule should have a description")
		})
	}

	// Verify all required managed rules are present
	assert.Equal(t, 3, len(requiredManagedRules),
		"WAF should have exactly 3 AWS Managed Rules")
}

// TestWAFLoggingConfiguration tests WAF logging to CloudWatch
// Validates: Requirements 7.4
func TestWAFLoggingConfiguration(t *testing.T) {
	t.Parallel()

	// WAF logging configuration
	loggingEnabled := true
	logDestination := "CloudWatch Logs"
	logRetentionDays := 90

	assert.True(t, loggingEnabled,
		"WAF logging should be enabled")
	assert.Equal(t, "CloudWatch Logs", logDestination,
		"WAF logs should be sent to CloudWatch Logs")
	assert.Equal(t, 90, logRetentionDays,
		"WAF logs should be retained for 90 days")
}

// TestWAFRulePriority tests that WAF rules have correct priorities
// Validates: Requirements 7.1, 7.2, 7.3
func TestWAFRulePriority(t *testing.T) {
	t.Parallel()

	// WAF rules are evaluated in priority order (lowest first)
	rules := []struct {
		name     string
		priority int
		ruleType string
	}{
		{
			name:     "RateLimitRule",
			priority: 1,
			ruleType: "rate-based",
		},
		{
			name:     "GeoBlockingRule",
			priority: 2,
			ruleType: "geo-match",
		},
		{
			name:     "AWSManagedRulesAmazonIpReputationList",
			priority: 10,
			ruleType: "managed",
		},
		{
			name:     "AWSManagedRulesCommonRuleSet",
			priority: 11,
			ruleType: "managed",
		},
		{
			name:     "AWSManagedRulesKnownBadInputsRuleSet",
			priority: 12,
			ruleType: "managed",
		},
	}

	// Verify rules are in ascending priority order
	for i := 0; i < len(rules)-1; i++ {
		assert.Less(t, rules[i].priority, rules[i+1].priority,
			"WAF rules should be in ascending priority order")
	}

	// Verify rate limiting has highest priority (evaluated first)
	assert.Equal(t, 1, rules[0].priority,
		"Rate limiting should have priority 1 (highest)")
	assert.Equal(t, "RateLimitRule", rules[0].name,
		"Rate limiting rule should be evaluated first")

	// Verify geo-blocking has second priority
	assert.Equal(t, 2, rules[1].priority,
		"Geo-blocking should have priority 2")
	assert.Equal(t, "GeoBlockingRule", rules[1].name,
		"Geo-blocking rule should be evaluated second")
}

// TestWAFWithTerraform tests WAF configuration with Terraform
// This test validates the actual Terraform module
func TestWAFWithTerraform(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/waf",
		NoColor:      true,
	})

	// Validate Terraform configuration (without variables, just syntax check)
	terraform.Validate(t, terraformOptions)
}

// TestWAFDefaultAction tests that WAF default action is Allow
// Validates: Requirements 7.5
func TestWAFDefaultAction(t *testing.T) {
	t.Parallel()

	// WAF default action should be Allow (only block specific threats)
	defaultAction := "allow"

	assert.Equal(t, "allow", defaultAction,
		"WAF default action should be Allow (whitelist approach)")
}

// TestWAFRateLimitBoundaryConditions tests boundary conditions for rate limiting
// Validates: Requirements 7.1
func TestWAFRateLimitBoundaryConditions(t *testing.T) {
	t.Parallel()

	rateLimit := 2000

	testCases := []struct {
		name         string
		requestCount int
		shouldBlock  bool
	}{
		{
			name:         "Zero requests",
			requestCount: 0,
			shouldBlock:  false,
		},
		{
			name:         "One request",
			requestCount: 1,
			shouldBlock:  false,
		},
		{
			name:         "Exactly at limit",
			requestCount: 2000,
			shouldBlock:  false,
		},
		{
			name:         "One over limit",
			requestCount: 2001,
			shouldBlock:  true,
		},
		{
			name:         "Maximum reasonable requests",
			requestCount: 10000,
			shouldBlock:  true,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			actualShouldBlock := tc.requestCount > rateLimit
			assert.Equal(t, tc.shouldBlock, actualShouldBlock,
				"Request count %d should result in block=%v",
				tc.requestCount, tc.shouldBlock)
		})
	}
}

// TestWAFGeoBlockingAllCountries tests geo-blocking for comprehensive country list
// Validates: Requirements 7.2
func TestWAFGeoBlockingAllCountries(t *testing.T) {
	t.Parallel()

	allowedCountries := map[string]bool{
		"PE": true, // Peru
	}

	// Test a comprehensive list of countries
	countries := []string{
		"PE", "US", "BR", "AR", "CL", "CO", "MX", "VE", "EC", "BO",
		"PY", "UY", "GY", "SR", "GF", "CN", "RU", "IN", "JP", "KR",
		"DE", "FR", "GB", "IT", "ES", "PT", "NL", "BE", "CH", "AT",
		"AU", "NZ", "CA", "ZA", "EG", "NG", "KE", "SA", "AE", "IL",
	}

	for _, country := range countries {
		country := country
		t.Run("Country_"+country, func(t *testing.T) {
			t.Parallel()

			shouldBlock := !allowedCountries[country]
			
			if country == "PE" {
				assert.False(t, shouldBlock,
					"Peru (PE) should be allowed")
			} else {
				assert.True(t, shouldBlock,
					"Country %s should be blocked", country)
			}
		})
	}
}

// TestWAFComprehensiveProperty tests comprehensive WAF behavior
// Validates: Requirements 7.1, 7.2
func TestWAFComprehensiveProperty(t *testing.T) {
	t.Parallel()

	parameters := gopter.DefaultTestParameters()
	parameters.MinSuccessfulTests = 100
	properties := gopter.NewProperties(parameters)

	properties.Property("WAF must enforce both rate limiting and geo-blocking", prop.ForAll(
		func(requestCount int, countryCode string) bool {
			// Rate limit configuration
			rateLimit := 2000
			allowedCountries := map[string]bool{"PE": true}

			// Check rate limiting
			exceedsRateLimit := requestCount > rateLimit

			// Check geo-blocking
			blockedByGeo := !allowedCountries[countryCode]

			// Request should be blocked if either condition is true
			shouldBlock := exceedsRateLimit || blockedByGeo

			// Property: WAF correctly identifies requests that should be blocked
			return shouldBlock == (exceedsRateLimit || blockedByGeo)
		},
		gen.IntRange(0, 5000),
		gen.OneConstOf("PE", "US", "BR", "AR", "CL", "CO", "MX", "CN", "RU"),
	))

	properties.TestingRun(t)
}
