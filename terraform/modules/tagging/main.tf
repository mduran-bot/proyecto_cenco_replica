# ============================================================================
# Tagging Module
# Provides centralized tag management and validation for all AWS resources
# ============================================================================

# ============================================================================
# Tag Validation (Corporate AWS Tagging Policy)
# ============================================================================

# Validate that all mandatory tags are provided
locals {
  # Mandatory tags per Corporate Policy
  mandatory_tag_keys = [
    "Application",
    "Environment",
    "Owner",
    "CostCenter",
    "BusinessUnit",
    "Country",
    "Criticality"
  ]

  # Check if all mandatory tags are present
  missing_mandatory_tags = [
    for key in local.mandatory_tag_keys :
    key if !contains(keys(var.mandatory_tags), key)
  ]

  # Validation: Ensure no mandatory tags are missing
  validate_mandatory_tags = length(local.missing_mandatory_tags) == 0 ? true : tobool("Missing mandatory tags: ${join(", ", local.missing_mandatory_tags)}")

  # Validate Environment tag value (per Corporate Policy)
  valid_environments   = ["prod", "qa", "dev", "uat", "sandbox"]
  validate_environment = contains(local.valid_environments, var.mandatory_tags["Environment"]) ? true : tobool("Environment must be one of: ${join(", ", local.valid_environments)}")

  # Validate Criticality tag value (per Corporate Policy)
  valid_criticality_levels = ["high", "medium", "low"]
  validate_criticality     = contains(local.valid_criticality_levels, var.mandatory_tags["Criticality"]) ? true : tobool("Criticality must be one of: ${join(", ", local.valid_criticality_levels)}")

  # Validate tag key format (alphanumeric, hyphens, underscores only)
  invalid_tag_keys = [
    for key in concat(keys(var.mandatory_tags), keys(var.optional_tags)) :
    key if !can(regex("^[A-Za-z0-9_-]+$", key))
  ]
  validate_tag_keys = length(local.invalid_tag_keys) == 0 ? true : tobool("Invalid tag keys (must be alphanumeric with hyphens/underscores): ${join(", ", local.invalid_tag_keys)}")

  # Validate tag value length (AWS limit: 256 characters)
  invalid_tag_values = [
    for key, value in merge(var.mandatory_tags, var.optional_tags) :
    key if length(value) > 256
  ]
  validate_tag_values = length(local.invalid_tag_values) == 0 ? true : tobool("Tag values exceed 256 characters: ${join(", ", local.invalid_tag_values)}")
}

# ============================================================================
# Tag Composition
# ============================================================================

locals {
  # Merge mandatory and optional tags
  all_tags = merge(
    var.mandatory_tags,
    var.optional_tags
  )

  # Tags with automatic timestamp (if not provided)
  tags_with_timestamp = merge(
    local.all_tags,
    var.include_created_date && !contains(keys(local.all_tags), "CreatedDate") ? {
      CreatedDate = formatdate("YYYY-MM-DD", timestamp())
    } : {}
  )

  # Final tags output
  tags = local.tags_with_timestamp
}


