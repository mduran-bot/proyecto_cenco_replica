# Monitoring Module - Implementation Summary

**Date**: January 28, 2026  
**Status**: ✅ PRODUCTION READY  
**Module**: `terraform/modules/monitoring`

## Overview

The monitoring module provides comprehensive observability and security monitoring for the AWS infrastructure, including VPC Flow Logs, DNS Query Logging, and CloudWatch Alarms for threat detection and operational monitoring.

## Key Features Implemented

### 1. VPC Flow Logs ✅
- **Comprehensive Traffic Capture**: Logs ALL network traffic (ACCEPT and REJECT actions)
- **Detailed Metadata**: Captures source/destination IPs, ports, protocols, packet/byte counts
- **Custom Log Format**: Explicit format string for complete visibility
- **CloudWatch Integration**: Logs stored in CloudWatch Logs with configurable retention
- **IAM Automation**: Automatic creation of IAM roles and policies

**Resources Created**:
- `aws_cloudwatch_log_group.vpc_flow_logs` - Log group with configurable retention
- `aws_iam_role.vpc_flow_logs` - Service role for VPC Flow Logs
- `aws_iam_role_policy.vpc_flow_logs` - Policy for CloudWatch Logs access
- `aws_flow_log.main` - VPC Flow Log configuration

### 2. DNS Query Logging ✅
- **Route53 Resolver Integration**: Captures all DNS queries within the VPC
- **Security Monitoring**: Helps detect DNS-based attacks and data exfiltration
- **CloudWatch Storage**: Logs stored with configurable retention
- **Automatic VPC Association**: Seamless integration with VPC

**Resources Created**:
- `aws_cloudwatch_log_group.dns_query_logs` - Log group for DNS queries
- `aws_iam_role.dns_query_logs` - Service role for Route53 Resolver
- `aws_iam_role_policy.dns_query_logs` - Policy for CloudWatch Logs access
- `aws_route53_resolver_query_log_config.main` - Query log configuration
- `aws_route53_resolver_query_log_config_association.main` - VPC association

### 3. CloudWatch Alarms ✅

#### Infrastructure Alarms
- **NAT Gateway Errors**: Monitors port allocation errors
  - Threshold: >10 errors in 10 minutes
  - Metric: `ErrorPortAllocation`
  
- **NAT Gateway Packet Drops**: Detects packet drops
  - Threshold: >1000 packets in 10 minutes
  - Metric: `PacketsDropCount`

#### Security Alarms
- **Rejected Connections Spike**: Detects unusual spikes in rejected connections
  - Threshold: >100 rejected connections in 5 minutes
  - Purpose: Potential DDoS or attack detection
  
- **Port Scanning Detection**: Identifies port scanning activity
  - Threshold: >50 single-packet rejected connections in 5 minutes
  - Purpose: Detect reconnaissance attempts
  
- **Data Exfiltration Risk**: Alerts on high outbound traffic
  - Threshold: >100 MB in 5 minutes
  - Purpose: Detect potential data exfiltration
  
- **SSH/RDP Activity Monitoring**: Tracks SSH (22) and RDP (3389) attempts
  - Threshold: >20 attempts in 5 minutes
  - Purpose: Detect brute force attempts

#### Application Alarms
- **EventBridge Failed Invocations**: Monitors EventBridge rule failures
  - Threshold: >5 failures in 5 minutes
  - Purpose: Detect application issues

### 4. Log Metric Filters ✅
- **Rejected Connections Filter**: Tracks REJECT actions in Flow Logs
- **Port Scanning Filter**: Detects single-packet rejected connections
- **High Outbound Traffic Filter**: Monitors large data transfers (>10MB)
- **SSH/RDP Attempts Filter**: Tracks connections to ports 22 and 3389

## Corporate Tagging Compliance ✅

All resources created by this module include corporate tags:
- `Application` - Application name
- `Environment` - Environment (dev/qa/prod)
- `Owner` - Team responsible
- `CostCenter` - Cost center code
- `BusinessUnit` - Business unit
- `Country` - Country code
- `Criticality` - Criticality level
- `ManagedBy` - "terraform"
- `Component` - "monitoring"
- `Purpose` - Specific purpose of resource

## Configuration Options

### Feature Toggles
- `enable_vpc_flow_logs` - Enable/disable VPC Flow Logs (default: true)
- `enable_dns_query_logging` - Enable/disable DNS Query Logging (default: true)

### Retention Periods
- `vpc_flow_logs_retention_days` - VPC Flow Logs retention (default: 90 days)
- `dns_logs_retention_days` - DNS Query Logs retention (default: 90 days)

### Alerting
- `alarm_sns_topic_arn` - SNS topic for alarm notifications (optional)
- `eventbridge_rule_names` - List of EventBridge rules to monitor

## Environment-Specific Configurations

### Development
```hcl
vpc_flow_logs_retention_days = 7
dns_logs_retention_days      = 7
enable_vpc_flow_logs         = true
enable_dns_query_logging     = false  # Optional: disable to reduce costs
alarm_sns_topic_arn          = ""     # No alerts in dev
```

### Staging
```hcl
vpc_flow_logs_retention_days = 30
dns_logs_retention_days      = 30
enable_vpc_flow_logs         = true
enable_dns_query_logging     = true
alarm_sns_topic_arn          = "arn:aws:sns:us-east-1:xxx:staging-alerts"
```

### Production
```hcl
vpc_flow_logs_retention_days = 90
dns_logs_retention_days      = 90
enable_vpc_flow_logs         = true
enable_dns_query_logging     = true
alarm_sns_topic_arn          = "arn:aws:sns:us-east-1:xxx:prod-alerts"
```

## Cost Considerations

### Monthly Cost Estimates

**VPC Flow Logs**:
- Data Ingestion: ~$0.50 per GB
- Storage: ~$0.03 per GB per month
- Typical: $10-50/month depending on traffic

**DNS Query Logging**:
- Data Ingestion: ~$0.50 per GB
- Storage: ~$0.03 per GB per month
- Typical: $5-20/month depending on queries

**CloudWatch Alarms**:
- Standard Alarms: $0.10 per alarm per month
- Total: ~$1-5/month for all alarms

**Total Estimated Cost**: $16-75/month depending on traffic volume and retention

### Cost Optimization Tips
1. Reduce retention periods in non-production environments
2. Disable DNS logging in development if not needed
3. Use metric filters to focus on relevant events
4. Consider S3 export for long-term archival

## Security Benefits

### Threat Detection
- **Port Scanning**: Detects reconnaissance attempts
- **Brute Force**: Monitors SSH/RDP connection attempts
- **Data Exfiltration**: Alerts on unusual outbound traffic
- **DDoS Detection**: Tracks spikes in rejected connections

### Compliance
- **Audit Trail**: Complete network traffic logs
- **DNS Monitoring**: Tracks all DNS queries for security analysis
- **Retention Policies**: Configurable retention (7-90 days)
- **Encryption**: All logs encrypted at rest

### Incident Response
- **Real-time Alerts**: SNS notifications for critical events
- **Log Analysis**: CloudWatch Insights for pattern detection
- **Forensics**: Complete traffic logs for investigation
- **Automated Response**: Can trigger Lambda functions for remediation

## Integration Points

### With Other Modules
- **VPC Module**: Requires VPC ID and NAT Gateway ID
- **EventBridge Module**: Monitors EventBridge rule failures
- **Security Groups Module**: Flow Logs capture security group actions
- **NACLs Module**: Flow Logs capture NACL actions

### With AWS Services
- **CloudWatch**: Central logging and metrics
- **SNS**: Alert notifications
- **Route53 Resolver**: DNS query logging
- **IAM**: Service roles and policies

## Monitoring Best Practices

### Alarm Configuration
1. Set thresholds based on baseline traffic patterns
2. Avoid alert fatigue with appropriate thresholds
3. Test alarms to verify they trigger correctly
4. Document runbooks for each alarm

### Log Analysis
1. Regularly review logs for anomalies
2. Use CloudWatch Insights for pattern detection
3. Integrate with SIEM tools for advanced analysis
4. Balance compliance needs with storage costs

### Security Monitoring
1. Establish baseline traffic patterns
2. Look for deviations from baseline
3. Have incident response procedures ready
4. Update detection rules as threats evolve

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

## Documentation

- **Module README**: `terraform/modules/monitoring/README.md`
- **Main Configuration**: `terraform/modules/monitoring/main.tf`
- **Variables**: `terraform/modules/monitoring/variables.tf`
- **Outputs**: `terraform/modules/monitoring/outputs.tf`

## Testing

### Unit Tests
- VPC Flow Logs configuration validation
- DNS Query Logging setup verification
- CloudWatch Alarms threshold validation
- IAM role and policy correctness

### Integration Tests
- End-to-end Flow Logs capture
- DNS query logging verification
- Alarm triggering tests
- SNS notification delivery

## Next Steps

1. **Configure SNS Topics**: Set up SNS topics for alarm notifications
2. **Set Baselines**: Establish normal traffic patterns for threshold tuning
3. **Create Runbooks**: Document response procedures for each alarm
4. **Integrate SIEM**: Connect logs to security information and event management tools
5. **Regular Review**: Periodically review logs and adjust thresholds

## References

- [VPC Flow Logs Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html)
- [Route53 Resolver Query Logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-query-logs.html)
- [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)

---

**Module Status**: ✅ Production Ready  
**Last Updated**: January 28, 2026  
**Maintained By**: Data Engineering Team  
**Corporate Tagging**: ✅ Compliant
