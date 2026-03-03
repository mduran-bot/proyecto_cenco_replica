# ============================================================================
# Tagging Module - Validation Test Examples
# ============================================================================
# This file demonstrates various validation scenarios for the tagging module

# ============================================================================
# Test 1: Valid Configuration (Should Pass)
# ============================================================================

module "valid_tags" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "production"
    Component   = "test-resource"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  optional_tags = {
    CreatedBy    = "terraform"
    Purpose      = "validation-testing"
    LastModified = "2024-01-15"
  }
}

output "valid_tags_output" {
  value = module.valid_tags.tags
}

# ============================================================================
# Test 2: Invalid Environment (Should Fail)
# ============================================================================
# Uncomment to test validation failure

# module "invalid_environment" {
#   source = "../"
#
#   mandatory_tags = {
#     Project     = "janis-cencosud-integration"
#     Environment = "dev"  # Invalid: must be "development", "staging", or "production"
#     Component   = "test-resource"
#     Owner       = "cencosud-data-team"
#     CostCenter  = "data-integration"
#   }
# }

# ============================================================================
# Test 3: Empty Mandatory Tag (Should Fail)
# ============================================================================
# Uncomment to test validation failure

# module "empty_component" {
#   source = "../"
#
#   mandatory_tags = {
#     Project     = "janis-cencosud-integration"
#     Environment = "production"
#     Component   = ""  # Invalid: cannot be empty
#     Owner       = "cencosud-data-team"
#     CostCenter  = "data-integration"
#   }
# }

# ============================================================================
# Test 4: Invalid Tag Key Format (Should Fail)
# ============================================================================
# Uncomment to test validation failure

# module "invalid_tag_key" {
#   source = "../"
#
#   mandatory_tags = {
#     Project     = "janis-cencosud-integration"
#     Environment = "production"
#     Component   = "test-resource"
#     Owner       = "cencosud-data-team"
#     CostCenter  = "data-integration"
#   }
#
#   optional_tags = {
#     "Invalid Key!" = "value"  # Invalid: contains special characters
#   }
# }

# ============================================================================
# Test 5: Tag Value Too Long (Should Fail)
# ============================================================================
# Uncomment to test validation failure

# module "long_tag_value" {
#   source = "../"
#
#   mandatory_tags = {
#     Project     = "janis-cencosud-integration"
#     Environment = "production"
#     Component   = "test-resource"
#     Owner       = "cencosud-data-team"
#     CostCenter  = "data-integration"
#   }
#
#   optional_tags = {
#     Description = "This is a very long description that exceeds the AWS tag value limit of 256 characters. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
#   }
# }

# ============================================================================
# Test 6: Auto-Generated CreatedDate
# ============================================================================

module "auto_created_date" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "staging"
    Component   = "test-resource"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  include_created_date = true # CreatedDate will be auto-generated
}

output "auto_created_date_tags" {
  value = module.auto_created_date.tags
}

# ============================================================================
# Test 7: Disable Auto-Generated CreatedDate
# ============================================================================

module "no_auto_date" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "development"
    Component   = "test-resource"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  include_created_date = false # No auto-generated date
}

output "no_auto_date_tags" {
  value = module.no_auto_date.tags
}

# ============================================================================
# Test 8: Validation Status Check
# ============================================================================

output "validation_results" {
  description = "Validation status for all test modules"
  value = {
    valid_tags_passed   = module.valid_tags.validation_passed
    auto_date_passed    = module.auto_created_date.validation_passed
    no_auto_date_passed = module.no_auto_date.validation_passed
    valid_tags_count    = module.valid_tags.tag_count
    mandatory_tag_keys  = module.valid_tags.mandatory_tag_keys
  }
}
