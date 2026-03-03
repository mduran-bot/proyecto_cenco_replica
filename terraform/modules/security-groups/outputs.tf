output "sg_api_gateway_id" {
  description = "ID of API Gateway Security Group"
  value       = aws_security_group.api_gateway.id
}

output "sg_redshift_id" {
  description = "ID of Redshift Security Group"
  value       = aws_security_group.redshift.id
}

output "sg_lambda_id" {
  description = "ID of Lambda Security Group"
  value       = aws_security_group.lambda.id
}

output "sg_mwaa_id" {
  description = "ID of MWAA Security Group"
  value       = aws_security_group.mwaa.id
}

output "sg_glue_id" {
  description = "ID of Glue Security Group"
  value       = aws_security_group.glue.id
}

output "sg_eventbridge_id" {
  description = "ID of EventBridge Security Group"
  value       = aws_security_group.eventbridge.id
}

output "sg_vpc_endpoints_id" {
  description = "ID of VPC Endpoints Security Group"
  value       = aws_security_group.vpc_endpoints.id
}
