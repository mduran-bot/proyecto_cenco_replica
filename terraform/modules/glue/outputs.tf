# ============================================================================
# AWS Glue Module Outputs
# ============================================================================

output "glue_role_arn" {
  description = "ARN of Glue IAM role"
  value       = aws_iam_role.glue_role.arn
}

output "glue_role_name" {
  description = "Name of Glue IAM role"
  value       = aws_iam_role.glue_role.name
}

output "bronze_database_name" {
  description = "Name of Bronze Glue catalog database"
  value       = aws_glue_catalog_database.bronze.name
}

output "silver_database_name" {
  description = "Name of Silver Glue catalog database"
  value       = aws_glue_catalog_database.silver.name
}

output "gold_database_name" {
  description = "Name of Gold Glue catalog database"
  value       = aws_glue_catalog_database.gold.name
}

output "bronze_to_silver_job_name" {
  description = "Name of Bronze to Silver Glue job"
  value       = var.create_bronze_to_silver_job ? aws_glue_job.bronze_to_silver[0].name : ""
}

output "silver_to_gold_job_name" {
  description = "Name of Silver to Gold Glue job"
  value       = var.create_silver_to_gold_job ? aws_glue_job.silver_to_gold[0].name : ""
}

output "all_job_names" {
  description = "Map of all Glue job names"
  value = {
    bronze_to_silver = var.create_bronze_to_silver_job ? aws_glue_job.bronze_to_silver[0].name : ""
    silver_to_gold   = var.create_silver_to_gold_job ? aws_glue_job.silver_to_gold[0].name : ""
  }
}
