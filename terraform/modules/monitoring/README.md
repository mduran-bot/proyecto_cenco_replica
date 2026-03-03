# Monitoring Module

## Overview

This module creates comprehensive monitoring and logging infrastructure for the VPC, including VPC Flow Logs, DNS Query Logging, and CloudWatch Alarms for security and operational monitoring.

## Features

### VPC Flow Logs
- **Comprehensive Traffic Capture**: Logs all network traffic (ACCEPT and REJECT) in the VPC
- **Detailed Metadata**: Captures source/destination IPs, ports, protocols, packet/byte counts, and actions
- **CloudWatch Integration**: Logs stored in CloudWatch Logs with configurable retention
- **IAM Role Management**: Automatic creation of IAM roles and policies for Flow Logs

### DNS Query Logging
- **Route53 Resolver Integration**: Captures all DNS queries made within the VPC
- **Security Monitoring**: Helps detect DNS-based attacks and data exfiltration attempts
- **CloudWatch Storage**: Logs stored in CloudWatch Logs with configurable retention
- **VPC Association**: Automatically associates query logging with the VPC

### CloudWatch Alarms

#### Infrastructure Alarms
- **NAT Gateway Errors**: Alerts on port allocation errors
- **NAT Gateway Packet Drops**: Alerts on packet drops indicating network issues

#### Security Alarms
- **Rejected Connections Spike**: Detects unusual spikes in rejected connections (potential attacks)
- **Port Scanning Detection**: Identifies potential port scanning activity
- **Data Exfiltration Risk**: Alerts on unusually high outbound traffic
- **SSH/RDP Activity**: Monitors unusual SSH (port 22) and RDP (port 3389) connection attempts

#### Application Alarms
- **EventBridge Failed Invocations**: Monitors EventBridge rule execution failures

## Usage

```hcl
module "monitoring" {
  source = "./modules/monitoring"

  # Required Variables
  vpc_id         = module.vpc.vpc_id
  nat_gateway_id = module.vpc.nat_gateway_id
  name_prefix    = "janis-cencosud-prod"

  # Retention Configuration
  vpc_flow_logs_retention_days = 90
  dns_logs_retention_days      = 90

  # SNS Topic for Alerts
  alarm_sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:infrastructure-alerts"

  # Feature Toggles
  enable_vpc_flow_logs     = true
  enable_dns_query_logging = true

  # EventBridge Rules for Monitoring
  eventbridge_rule_names = [
    "order-polling-rule",
    "product-polling-rule",
    "stock-polling-rule",
    "price-polling-rule",
    "store-polling-rule"
  ]

  # Corporate Tags
  tags = {
    Application  = "janis-cencosud-integration"
    Environment  = "prod"
    Owner        = "data-engineering-team"
    CostCenter   = "CC-DATA-001"
    BusinessUnit = "Data-Analytics"
    Country      = "CL"
    Criticality  = "high"
    ManagedBy    = "terraform"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| vpc_id | ID of the VPC to monitor | string | - | yes |
| nat_gateway_id | ID of the NAT Gateway to monitor | string | - | yes |
| name_prefix | Prefix for resource names | string | - | yes |
| vpc_flow_logs_retention_days | Retention period for VPC Flow Logs in days | number | 90 | no |
| dns_logs_retention_days | Retention period for DNS Query Logs in days | number | 90 | no |
| alarm_sns_topic_arn | SNS topic ARN for alarm notifications | string | "" | no |
| enable_vpc_flow_logs | Enable VPC Flow Logs | bool | true | no |
| enable_dns_query_logging | Enable DNS Query Logging | bool | true | no |
| eventbridge_rule_names | List of EventBridge rule names to monitor | list(string) | [] | no |
| tags | Common tags to apply to all resources | map(string) | {} | no |

## Outputs

| Name | Description |
|------|-------------|
| vpc_flow_logs_log_group | CloudWatch Log Group name for VPC Flow Logs |
| dns_query_logs_log_group | CloudWatch Log Group name for DNS Query Logs |
| alarm_arns | Map of CloudWatch Alarm ARNs |
| metric_filter_names | List of CloudWatch Log Metric Filter names |

## Resources Created

### VPC Flow Logs (when enabled)
- `aws_cloudwatch_log_group.vpc_flow_logs` - Log group for VPC Flow Logs
- `aws_iam_role.vpc_flow_logs` - IAM role for VPC Flow Logs service
- `aws_iam_role_policy.vpc_flow_logs` - IAM policy for CloudWatch Logs access
- `aws_flow_log.main` - VPC Flow Log configuration

### DNS Query Logging (when enabled)
- `aws_cloudwatch_log_group.dns_query_logs` - Log group for DNS queries
- `aws_iam_role.dns_query_logs` - IAM role for Route53 Resolver
- `aws_iam_role_policy.dns_query_logs` - IAM policy for CloudWatch Logs access
- `aws_route53_resolver_query_log_config.main` - Query log configuration
- `aws_route53_resolver_query_log_config_association.main` - VPC association

### CloudWatch Alarms
- `aws_cloudwatch_metric_alarm.nat_gateway_errors` - NAT Gateway error alarm
- `aws_cloudwatch_metric_alarm.nat_gateway_packet_drops` - Packet drop alarm
- `aws_cloudwatch_metric_alarm.rejected_connections_spike` - Security alarm
- `aws_cloudwatch_metric_alarm.port_scanning_detected` - Security alarm
- `aws_cloudwatch_metric_alarm.data_exfiltration_risk` - Security alarm
- `aws_cloudwatch_metric_alarm.unusual_ssh_rdp_activity` - Security alarm
- `aws_cloudwatch_metric_alarm.eventbridge_failed_invocations` - Application alarm

### CloudWatch Log Metric Filters
- `aws_cloudwatch_log_metric_filter.rejected_connections` - Tracks rejected connections
- `aws_cloudwatch_log_metric_filter.port_scanning` - Detects port scanning
- `aws_cloudwatch_log_metric_filter.high_outbound_traffic` - Monitors data transfer
- `aws_cloudwatch_log_metric_filter.ssh_rdp_attempts` - Tracks SSH/RDP attempts

## Security Features

### Threat Detection
- **Port Scanning**: Detects multiple rejected connections from the same source
- **Data Exfiltration**: Alerts on unusually high outbound traffic (>100MB in 5 minutes)
- **Brute Force Attempts**: Monitors SSH/RDP connection attempts
- **Connection Anomalies**: Tracks spikes in rejected connections

### Compliance
- **Audit Trail**: Complete network traffic logs for compliance requirements
- **DNS Monitoring**: Tracks all DNS queries for security analysis
- **Retention Policies**: Configurable retention periods (7-90 days typical)
- **Encryption**: All logs encrypted at rest using AWS-managed keys

## Cost Considerations

### VPC Flow Logs
- **Data Ingestion**: ~$0.50 per GB ingested to CloudWatch Logs
- **Storage**: ~$0.03 per GB per month
- **Typical Cost**: $10-50/month depending on traffic volume

### DNS Query Logging
- **Data Ingestion**: ~$0.50 per GB ingested
- **Storage**: ~$0.03 per GB per month
- **Typical Cost**: $5-20/month depending on query volume

### CloudWatch Alarms
- **Standard Alarms**: $0.10 per alarm per month
- **High-Resolution Alarms**: $0.30 per alarm per month
- **Typical Cost**: $1-5/month for all alarms

### Cost Optimization Tips
- Reduce retention periods in non-production environments
- Disable DNS logging in development if not needed
- Use metric filters to focus on relevant events
- Consider S3 export for long-term log archival

## Monitoring Best Practices

### Alarm Configuration
1. **Set Appropriate Thresholds**: Adjust thresholds based on baseline traffic patterns
2. **Avoid Alert Fatigue**: Don't set thresholds too low
3. **Test Alarms**: Verify alarms trigger correctly
4. **Document Runbooks**: Create response procedures for each alarm

### Log Analysis
1. **Regular Review**: Periodically review logs for anomalies
2. **Automated Analysis**: Use CloudWatch Insights for pattern detection
3. **Integration**: Connect to SIEM tools for advanced analysis
4. **Retention**: Balance compliance needs with storage costs

### Security Monitoring
1. **Baseline Traffic**: Establish normal traffic patterns
2. **Anomaly Detection**: Look for deviations from baseline
3. **Incident Response**: Have procedures for security alerts
4. **Regular Updates**: Update detection rules as threats evolve

## Troubleshooting

### VPC Flow Logs Not Appearing
```bash
# Check IAM role permissions
aws iam get-role-policy --role-name <role-name> --policy-name <policy-name>

# Verify Flow Log status
aws ec2 describe-flow-logs --filter "Name=resource-id,Values=<vpc-id>"

# Check CloudWatch Log Group
aws logs describe-log-groups --log-group-name-prefix "/aws/vpc/flow-logs"
```

### DNS Query Logs Not Appearing
```bash
# Check Route53 Resolver Query Log Config
aws route53resolver list-resolver-query-log-configs

# Verify VPC association
aws route53resolver list-resolver-query-log-config-associations

# Check CloudWatch Log Group
aws logs describe-log-groups --log-group-name-prefix "/aws/route53/resolver"
```

### Alarms Not Triggering
```bash
# Check alarm state
aws cloudwatch describe-alarms --alarm-names <alarm-name>

# Verify SNS topic subscription
aws sns list-subscriptions-by-topic --topic-arn <topic-arn>

# Test alarm manually
aws cloudwatch set-alarm-state --alarm-name <alarm-name> --state-value ALARM --state-reason "Testing"
```

## Examples

### Development Environment
```hcl
module "monitoring" {
  source = "./modules/monitoring"

  vpc_id         = module.vpc.vpc_id
  nat_gateway_id = module.vpc.nat_gateway_id
  name_prefix    = "janis-cencosud-dev"

  # Shorter retention for cost savings
  vpc_flow_logs_retention_days = 7
  dns_logs_retention_days      = 7

  # Optional: Disable DNS logging in dev
  enable_vpc_flow_logs     = true
  enable_dns_query_logging = false

  # No SNS alerts in dev
  alarm_sns_topic_arn = ""

  tags = local.common_tags
}
```

### Production Environment
```hcl
module "monitoring" {
  source = "./modules/monitoring"

  vpc_id         = module.vpc.vpc_id
  nat_gateway_id = module.vpc.nat_gateway_id
  name_prefix    = "janis-cencosud-prod"

  # Compliance retention periods
  vpc_flow_logs_retention_days = 90
  dns_logs_retention_days      = 90

  # Full monitoring enabled
  enable_vpc_flow_logs     = true
  enable_dns_query_logging = true

  # Production alerts
  alarm_sns_topic_arn = aws_sns_topic.prod_alerts.arn

  eventbridge_rule_names = module.eventbridge.rule_names

  tags = local.common_tags
}
```

## References

- [VPC Flow Logs Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html)
- [Route53 Resolver Query Logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-query-logs.html)
- [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)

## Version History

- **v1.0.0** (2026-01-28): Initial implementation with VPC Flow Logs, DNS Query Logging, and comprehensive CloudWatch Alarms
- Corporate tagging policy compliance
- Security threat detection alarms
- EventBridge monitoring integration

---

**Module Status**: ✅ Production Ready  
**Last Updated**: January 28, 2026  
**Maintained By**: Data Engineering Team
