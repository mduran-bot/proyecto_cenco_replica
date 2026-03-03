output "web_acl_id" {
  description = "ID of WAF Web ACL"
  value       = aws_wafv2_web_acl.main.id
}

output "web_acl_arn" {
  description = "ARN of WAF Web ACL"
  value       = aws_wafv2_web_acl.main.arn
}

output "log_group_name" {
  description = "Name of CloudWatch Log Group for WAF"
  value       = aws_cloudwatch_log_group.waf.name
}
