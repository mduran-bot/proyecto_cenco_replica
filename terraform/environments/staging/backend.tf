# Backend Configuration for Local State Management
# 
# This configuration uses local state storage (default behavior).
# State files will be stored in the environment-specific directories.
# 
# For free tier usage, we avoid remote backends like S3 + DynamoDB.
# Each environment (dev/staging/prod) will have its own terraform.tfstate file.
#
# IMPORTANT: 
# - Add terraform.tfstate* to .gitignore
# - Create manual backups before major changes
# - Coordinate with team to avoid concurrent modifications

terraform {
  # No backend configuration = local state (default)
  # State will be stored in terraform.tfstate in the working directory
}
