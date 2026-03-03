# Tagging Module Changelog

## [2.0.0] - 2026-01-28

### 🎯 Major Update: Corporate AWS Tagging Policy Alignment

This release aligns the tagging module with the Corporate AWS Tagging Policy, introducing breaking changes to the mandatory tags structure.

### ✨ Added

- **New Mandatory Tags** (Corporate Policy):
  - `BusinessUnit` - Business unit identification
  - `Country` - Country code (e.g., CL, PE)
  - `Criticality` - Criticality level (high, medium, low)

- **Enhanced Validations**:
  - `Environment` now validates against: `prod`, `qa`, `dev`, `uat`, `sandbox`
  - `Criticality` validates against: `high`, `medium`, `low`
  - All mandatory tags validated for non-empty values

### 🔄 Changed

- **BREAKING**: `mandatory_tags` structure updated:
  - `Project` → `Application` (renamed for corporate alignment)
  - `Component` → Moved to `optional_tags` (no longer mandatory)
  - Added `BusinessUnit`, `Country`, `Criticality` as mandatory

- **Environment Values** (BREAKING):
  - Old: `development`, `staging`, `production`
  - New: `prod`, `qa`, `dev`, `uat`, `sandbox`

### 📚 Documentation

- Updated README.md with:
  - Corporate Policy compliance table
  - New mandatory tags (7 total)
  - Updated usage examples
  - Corporate-aligned best practices
  - References to policy documentation

### 🔧 Migration Guide

#### Before (v1.x):
```hcl
mandatory_tags = {
  Project     = "janis-cencosud-integration"
  Environment = "production"
  Component   = "vpc"
  Owner       = "cencosud-data-team"
  CostCenter  = "data-integration"
}
```

#### After (v2.0):
```hcl
mandatory_tags = {
  Application  = "janis-cencosud-integration"
  Environment  = "prod"
  Owner        = "data-engineering-team"
  CostCenter   = "CC-DATA-001"
  BusinessUnit = "Data-Analytics"
  Country      = "CL"
  Criticality  = "high"
}

optional_tags = {
  Component = "vpc"  # Moved from mandatory
}
```

### ⚠️ Breaking Changes

1. **Mandatory Tags Structure**: All code using this module must update the `mandatory_tags` object structure
2. **Environment Values**: Update all environment values to new format
3. **Component Tag**: Now optional - add to `optional_tags` if needed

### 📋 Validation Rules

The module now enforces:
- 7 mandatory tags (up from 5)
- Strict environment value validation
- Criticality level validation
- All mandatory tags must be non-empty

### 🔗 References

- Corporate Policy: `Politica_Etiquetado_AWS.md`
- Implementation Guide: `terraform/CORPORATE_TAGGING_IMPLEMENTATION.md`
- Update Summary: `terraform/TAGGING_UPDATE_SUMMARY.md`

---

## [1.0.0] - 2026-01-26

### Initial Release

- Basic tagging module with 5 mandatory tags
- Tag validation for keys and values
- Auto-generated CreatedDate
- Optional tags support
