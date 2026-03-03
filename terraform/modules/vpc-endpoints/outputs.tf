output "s3_endpoint_id" {
  description = "ID of S3 Gateway Endpoint"
  value       = var.enable_s3_endpoint ? aws_vpc_endpoint.s3[0].id : null
}

output "interface_endpoint_ids" {
  description = "IDs of Interface Endpoints"
  value = {
    glue           = var.enable_glue_endpoint ? aws_vpc_endpoint.glue[0].id : null
    secretsmanager = var.enable_secrets_manager_endpoint ? aws_vpc_endpoint.secretsmanager[0].id : null
    logs           = var.enable_logs_endpoint ? aws_vpc_endpoint.logs[0].id : null
    kms            = var.enable_kms_endpoint ? aws_vpc_endpoint.kms[0].id : null
    sts            = var.enable_sts_endpoint ? aws_vpc_endpoint.sts[0].id : null
    events         = var.enable_events_endpoint ? aws_vpc_endpoint.events[0].id : null
  }
}
