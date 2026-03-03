# ============================================================================
# S3 Module Outputs
# ============================================================================

# Bronze Layer Outputs
output "bronze_bucket_id" {
  description = "ID of the Bronze layer bucket"
  value       = aws_s3_bucket.bronze.id
}

output "bronze_bucket_arn" {
  description = "ARN of the Bronze layer bucket"
  value       = aws_s3_bucket.bronze.arn
}

output "bronze_bucket_domain_name" {
  description = "Domain name of the Bronze layer bucket"
  value       = aws_s3_bucket.bronze.bucket_domain_name
}

# Silver Layer Outputs
output "silver_bucket_id" {
  description = "ID of the Silver layer bucket"
  value       = aws_s3_bucket.silver.id
}

output "silver_bucket_arn" {
  description = "ARN of the Silver layer bucket"
  value       = aws_s3_bucket.silver.arn
}

output "silver_bucket_domain_name" {
  description = "Domain name of the Silver layer bucket"
  value       = aws_s3_bucket.silver.bucket_domain_name
}

# Gold Layer Outputs
output "gold_bucket_id" {
  description = "ID of the Gold layer bucket"
  value       = aws_s3_bucket.gold.id
}

output "gold_bucket_arn" {
  description = "ARN of the Gold layer bucket"
  value       = aws_s3_bucket.gold.arn
}

output "gold_bucket_domain_name" {
  description = "Domain name of the Gold layer bucket"
  value       = aws_s3_bucket.gold.bucket_domain_name
}

# Scripts Bucket Outputs
output "scripts_bucket_id" {
  description = "ID of the scripts bucket"
  value       = aws_s3_bucket.scripts.id
}

output "scripts_bucket_arn" {
  description = "ARN of the scripts bucket"
  value       = aws_s3_bucket.scripts.arn
}

output "scripts_bucket_domain_name" {
  description = "Domain name of the scripts bucket"
  value       = aws_s3_bucket.scripts.bucket_domain_name
}

# Logs Bucket Outputs
output "logs_bucket_id" {
  description = "ID of the logs bucket"
  value       = aws_s3_bucket.logs.id
}

output "logs_bucket_arn" {
  description = "ARN of the logs bucket"
  value       = aws_s3_bucket.logs.arn
}

output "logs_bucket_domain_name" {
  description = "Domain name of the logs bucket"
  value       = aws_s3_bucket.logs.bucket_domain_name
}

# All Bucket Names (for convenience)
output "all_bucket_names" {
  description = "Map of all bucket names by layer"
  value = {
    bronze  = aws_s3_bucket.bronze.id
    silver  = aws_s3_bucket.silver.id
    gold    = aws_s3_bucket.gold.id
    scripts = aws_s3_bucket.scripts.id
    logs    = aws_s3_bucket.logs.id
  }
}

# All Bucket ARNs (for IAM policies)
output "all_bucket_arns" {
  description = "Map of all bucket ARNs by layer"
  value = {
    bronze  = aws_s3_bucket.bronze.arn
    silver  = aws_s3_bucket.silver.arn
    gold    = aws_s3_bucket.gold.arn
    scripts = aws_s3_bucket.scripts.arn
    logs    = aws_s3_bucket.logs.arn
  }
}
