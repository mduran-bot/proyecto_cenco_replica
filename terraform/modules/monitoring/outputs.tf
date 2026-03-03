output "vpc_flow_logs_log_group" {
  description = "CloudWatch Log Group for VPC Flow Logs"
  value       = var.enable_vpc_flow_logs ? aws_cloudwatch_log_group.vpc_flow_logs[0].name : null
}

output "dns_query_logs_log_group" {
  description = "CloudWatch Log Group for DNS Query Logs"
  value       = var.enable_dns_query_logging ? aws_cloudwatch_log_group.dns_query_logs[0].name : null
}

output "alarm_arns" {
  description = "ARNs of CloudWatch Alarms"
  value = concat(
    var.nat_gateway_id != "" ? [
      aws_cloudwatch_metric_alarm.nat_gateway_errors.arn,
      aws_cloudwatch_metric_alarm.nat_gateway_packet_drops.arn
    ] : [],
    var.enable_vpc_flow_logs ? [
      aws_cloudwatch_metric_alarm.rejected_connections_spike[0].arn,
      aws_cloudwatch_metric_alarm.port_scanning_detected[0].arn,
      aws_cloudwatch_metric_alarm.data_exfiltration_risk[0].arn,
      aws_cloudwatch_metric_alarm.unusual_ssh_rdp_activity[0].arn
    ] : [],
    aws_cloudwatch_metric_alarm.eventbridge_failed_invocations[*].arn
  )
}

output "metric_filter_names" {
  description = "Names of CloudWatch Log Metric Filters"
  value = var.enable_vpc_flow_logs ? [
    aws_cloudwatch_log_metric_filter.rejected_connections[0].name,
    aws_cloudwatch_log_metric_filter.port_scanning[0].name,
    aws_cloudwatch_log_metric_filter.high_outbound_traffic[0].name,
    aws_cloudwatch_log_metric_filter.ssh_rdp_attempts[0].name
  ] : []
}