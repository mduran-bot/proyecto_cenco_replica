# ============================================================================
# Tagging Module Outputs
# ============================================================================

output "tags" {
  description = "Complete set of validated tags to apply to resources"
  value       = local.tags
}

output "mandatory_tags" {
  description = "Mandatory tags only"
  value       = var.mandatory_tags
}

output "optional_tags" {
  description = "Optional tags only"
  value       = var.optional_tags
}

output "validation_passed" {
  description = "Indicates whether all tag validations passed"
  value = (
    local.validate_mandatory_tags &&
    local.validate_environment &&
    local.validate_tag_keys &&
    local.validate_tag_values
  )
}

output "tag_count" {
  description = "Total number of tags"
  value       = length(local.tags)
}

output "mandatory_tag_keys" {
  description = "List of mandatory tag keys"
  value       = local.mandatory_tag_keys
}
