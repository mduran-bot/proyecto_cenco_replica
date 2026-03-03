# ============================================================================
# Monitoring Module
# Creates VPC Flow Logs, DNS Query Logging, and CloudWatch Alarms
# ============================================================================

# ============================================================================
# VPC Flow Logs
# ============================================================================

resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  name              = "/aws/vpc/flow-logs/${var.name_prefix}"
  retention_in_days = var.vpc_flow_logs_retention_days

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-vpc-flow-logs"
    Component = "monitoring"
    Purpose   = "vpc-flow-logs"
  })
}

resource "aws_iam_role" "vpc_flow_logs" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  name = "${var.name_prefix}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-vpc-flow-logs-role"
    Component = "monitoring"
  })
}

resource "aws_iam_role_policy" "vpc_flow_logs" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  name = "${var.name_prefix}-vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_flow_log" "main" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  vpc_id               = var.vpc_id
  traffic_type         = "ALL"
  iam_role_arn         = aws_iam_role.vpc_flow_logs[0].arn
  log_destination      = aws_cloudwatch_log_group.vpc_flow_logs[0].arn
  log_destination_type = "cloud-watch-logs"

  # Explicit log format to capture all required metadata
  # Includes: source/destination IPs, ports, protocols, packet/byte counts, action
  log_format = "$${version} $${account-id} $${interface-id} $${srcaddr} $${dstaddr} $${srcport} $${dstport} $${protocol} $${packets} $${bytes} $${start} $${end} $${action} $${log-status}"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-vpc-flow-log"
    Component = "monitoring"
    Purpose   = "capture-all-vpc-traffic"
  })
}

# ============================================================================
# DNS Query Logging
# ============================================================================

resource "aws_cloudwatch_log_group" "dns_query_logs" {
  count = var.enable_dns_query_logging ? 1 : 0

  name              = "/aws/route53/resolver/${var.name_prefix}-dns-queries"
  retention_in_days = var.dns_logs_retention_days

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-dns-query-logs"
    Component = "monitoring"
    Purpose   = "dns-query-logs"
  })
}

# IAM role for Route53 Resolver Query Logging
resource "aws_iam_role" "dns_query_logs" {
  count = var.enable_dns_query_logging ? 1 : 0

  name = "${var.name_prefix}-dns-query-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "route53resolver.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-dns-query-logs-role"
    Component = "monitoring"
  })
}

resource "aws_iam_role_policy" "dns_query_logs" {
  count = var.enable_dns_query_logging ? 1 : 0

  name = "${var.name_prefix}-dns-query-logs-policy"
  role = aws_iam_role.dns_query_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.dns_query_logs[0].arn}:*"
      }
    ]
  })
}

# Route53 Resolver Query Log Config
resource "aws_route53_resolver_query_log_config" "main" {
  count = var.enable_dns_query_logging ? 1 : 0

  name            = "${var.name_prefix}-dns-query-log-config"
  destination_arn = aws_cloudwatch_log_group.dns_query_logs[0].arn

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-dns-query-log-config"
    Component = "monitoring"
    Purpose   = "security-monitoring"
  })

  depends_on = [aws_iam_role_policy.dns_query_logs]
}

# Associate Query Log Config with VPC
resource "aws_route53_resolver_query_log_config_association" "main" {
  count = var.enable_dns_query_logging ? 1 : 0

  resolver_query_log_config_id = aws_route53_resolver_query_log_config.main[0].id
  resource_id                  = var.vpc_id

  depends_on = [aws_route53_resolver_query_log_config.main]
}

# ============================================================================
# CloudWatch Alarms
# ============================================================================

# NAT Gateway Connection Errors
resource "aws_cloudwatch_metric_alarm" "nat_gateway_errors" {
  alarm_name          = "${var.name_prefix}-nat-gateway-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorPortAllocation"
  namespace           = "AWS/NATGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when NAT Gateway has port allocation errors"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    NatGatewayId = var.nat_gateway_id
  }

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-nat-gateway-errors"
    Component = "monitoring"
  })
}

# NAT Gateway Packet Drops
resource "aws_cloudwatch_metric_alarm" "nat_gateway_packet_drops" {
  alarm_name          = "${var.name_prefix}-nat-gateway-packet-drops"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "PacketsDropCount"
  namespace           = "AWS/NATGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 1000
  alarm_description   = "Alert when NAT Gateway drops packets"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    NatGatewayId = var.nat_gateway_id
  }

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-nat-gateway-packet-drops"
    Component = "monitoring"
  })
}

# VPC Flow Logs - Rejected Connections
resource "aws_cloudwatch_log_metric_filter" "rejected_connections" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  name           = "${var.name_prefix}-rejected-connections"
  log_group_name = aws_cloudwatch_log_group.vpc_flow_logs[0].name
  pattern        = "[version, account, eni, source, destination, srcport, dstport, protocol, packets, bytes, windowstart, windowend, action=REJECT, flowlogstatus]"

  metric_transformation {
    name      = "RejectedConnections"
    namespace = "${var.name_prefix}/VPC"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "rejected_connections_spike" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  alarm_name          = "${var.name_prefix}-rejected-connections-spike"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "RejectedConnections"
  namespace           = "${var.name_prefix}/VPC"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "Alert on spike in rejected connections (potential security threat)"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-rejected-connections-spike"
    Component = "monitoring"
    Purpose   = "security-anomaly-detection"
  })

  depends_on = [aws_cloudwatch_log_metric_filter.rejected_connections]
}

# Suspicious Port Scanning Activity
resource "aws_cloudwatch_log_metric_filter" "port_scanning" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  name           = "${var.name_prefix}-port-scanning"
  log_group_name = aws_cloudwatch_log_group.vpc_flow_logs[0].name
  # Detect multiple rejected connections from same source to different ports
  pattern = "[version, account, eni, source, destination, srcport, dstport, protocol, packets=1, bytes, windowstart, windowend, action=REJECT, flowlogstatus]"

  metric_transformation {
    name      = "PortScanningAttempts"
    namespace = "${var.name_prefix}/VPC"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "port_scanning_detected" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  alarm_name          = "${var.name_prefix}-port-scanning-detected"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "PortScanningAttempts"
  namespace           = "${var.name_prefix}/VPC"
  period              = 300
  statistic           = "Sum"
  threshold           = 50
  alarm_description   = "Alert on potential port scanning activity"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-port-scanning-detected"
    Component = "monitoring"
    Purpose   = "security-threat-detection"
  })

  depends_on = [aws_cloudwatch_log_metric_filter.port_scanning]
}

# High Volume of Outbound Traffic (potential data exfiltration)
resource "aws_cloudwatch_log_metric_filter" "high_outbound_traffic" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  name           = "${var.name_prefix}-high-outbound-traffic"
  log_group_name = aws_cloudwatch_log_group.vpc_flow_logs[0].name
  # Track large outbound transfers
  pattern = "[version, account, eni, source, destination, srcport, dstport, protocol, packets, bytes>10000000, windowstart, windowend, action=ACCEPT, flowlogstatus]"

  metric_transformation {
    name      = "HighOutboundTraffic"
    namespace = "${var.name_prefix}/VPC"
    value     = "$bytes"
  }
}

resource "aws_cloudwatch_metric_alarm" "data_exfiltration_risk" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  alarm_name          = "${var.name_prefix}-data-exfiltration-risk"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HighOutboundTraffic"
  namespace           = "${var.name_prefix}/VPC"
  period              = 300
  statistic           = "Sum"
  threshold           = 100000000 # 100 MB in 5 minutes
  alarm_description   = "Alert on unusually high outbound traffic (potential data exfiltration)"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-data-exfiltration-risk"
    Component = "monitoring"
    Purpose   = "security-anomaly-detection"
  })

  depends_on = [aws_cloudwatch_log_metric_filter.high_outbound_traffic]
}

# Unusual SSH/RDP Connection Attempts
resource "aws_cloudwatch_log_metric_filter" "ssh_rdp_attempts" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  name           = "${var.name_prefix}-ssh-rdp-attempts"
  log_group_name = aws_cloudwatch_log_group.vpc_flow_logs[0].name
  # Detect SSH (22) and RDP (3389) connection attempts
  pattern = "[version, account, eni, source, destination, srcport, dstport=22||dstport=3389, protocol=6, packets, bytes, windowstart, windowend, action, flowlogstatus]"

  metric_transformation {
    name      = "SSHRDPAttempts"
    namespace = "${var.name_prefix}/VPC"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "unusual_ssh_rdp_activity" {
  count = var.enable_vpc_flow_logs ? 1 : 0

  alarm_name          = "${var.name_prefix}-unusual-ssh-rdp-activity"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "SSHRDPAttempts"
  namespace           = "${var.name_prefix}/VPC"
  period              = 300
  statistic           = "Sum"
  threshold           = 20
  alarm_description   = "Alert on unusual SSH/RDP connection attempts"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-unusual-ssh-rdp-activity"
    Component = "monitoring"
    Purpose   = "security-threat-detection"
  })

  depends_on = [aws_cloudwatch_log_metric_filter.ssh_rdp_attempts]
}

# EventBridge Failed Invocations
resource "aws_cloudwatch_metric_alarm" "eventbridge_failed_invocations" {
  count = length(var.eventbridge_rule_names)

  alarm_name          = "${var.name_prefix}-eventbridge-failed-${var.eventbridge_rule_names[count.index]}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FailedInvocations"
  namespace           = "AWS/Events"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when EventBridge rule fails to invoke targets"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    RuleName = var.eventbridge_rule_names[count.index]
  }

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-eventbridge-failed-${var.eventbridge_rule_names[count.index]}"
    Component = "monitoring"
  })
}
