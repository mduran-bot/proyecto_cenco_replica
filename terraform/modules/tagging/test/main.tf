# ============================================================================
# Tagging Module Test
# ============================================================================

module "test_tags" {
  source = "../"

  mandatory_tags = {
    Project     = "janis-cencosud-integration"
    Environment = "production"
    Component   = "test-component"
    Owner       = "cencosud-data-team"
    CostCenter  = "data-integration"
  }

  optional_tags = {
    CreatedBy = "terraform"
    Purpose   = "testing"
  }

  include_created_date = true
}

output "all_tags" {
  value = module.test_tags.tags
}

output "validation_passed" {
  value = module.test_tags.validation_passed
}

output "tag_count" {
  value = module.test_tags.tag_count
}

output "mandatory_tag_keys" {
  value = module.test_tags.mandatory_tag_keys
}
