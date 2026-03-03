# EventBridge Module Deployment Checklist

Use this checklist to ensure proper deployment of the EventBridge module for API polling.

## Pre-Deployment

- [ ] MWAA environment is deployed and ARN is available
- [ ] AWS credentials are configured
- [ ] Terraform >= 1.0 is installed
- [ ] AWS CLI is installed and configured
- [ ] Required IAM permissions are available:
  - `events:*` for EventBridge
  - `sqs:*` for DLQ
  - `iam:*` for role creation
  - `logs:*` for CloudWatch
  - `cloudwatch:*` for alarms

## Configuration

- [ ] Set `name_prefix` variable
- [ ] Set `environment` variable
- [ ] Set `mwaa_environment_arn` variable
- [ ] Review polling rates (or use defaults):
  - [ ] Orders: 5 minutes
  - [ ] Products: 1 hour
  - [ ] Stock: 10 minutes
  - [ ] Prices: 30 minutes
  - [ ] Stores: 1 day
- [ ] Configure common tags

## Deployment

- [ ] Run `terraform init`
- [ ] Run `terraform validate`
- [ ] Run `terraform plan` and review changes
- [ ] Run `terraform apply`
- [ ] Verify no errors in output

## Post-Deployment Verification

### EventBridge Rules
- [ ] Verify 5 rules are created:
  ```bash
  aws events list-rules --name-prefix <name-prefix>-poll
  ```
- [ ] Verify each rule has correct schedule:
  - [ ] Orders: rate(5 minutes)
  - [ ] Products: rate(1 hour)
  - [ ] Stock: rate(10 minutes)
  - [ ] Prices: rate(30 minutes)
  - [ ] Stores: rate(1 day)
- [ ] Verify rules are ENABLED

### EventBridge Targets
- [ ] Verify each rule has MWAA target:
  ```bash
  aws events list-targets-by-rule --rule <rule-name>
  ```
- [ ] Verify target input format:
  ```json
  {
    "dag_id": "poll_{data_type}",
    "conf": {
      "data_type": "{data_type}"
    }
  }
  ```
- [ ] Verify retry policy is configured (max 2 attempts)
- [ ] Verify DLQ is configured

### IAM Role
- [ ] Verify IAM role exists:
  ```bash
  aws iam get-role --role-name <name-prefix>-eventbridge-mwaa-role
  ```
- [ ] Verify trust policy allows events.amazonaws.com
- [ ] Verify policy has airflow:CreateCliToken permission
- [ ] Verify policy has sqs:SendMessage permission

### Dead Letter Queue
- [ ] Verify DLQ exists:
  ```bash
  aws sqs get-queue-url --queue-name <name-prefix>-eventbridge-dlq
  ```
- [ ] Verify DLQ is empty (no failed invocations yet)
- [ ] Verify retention is 14 days

### CloudWatch
- [ ] Verify log group exists:
  ```bash
  aws logs describe-log-groups --log-group-name-prefix /aws/events/<name-prefix>-polling
  ```
- [ ] Verify log retention is 90 days
- [ ] Verify 3 alarms are created:
  - [ ] Invocation failures alarm
  - [ ] DLQ messages alarm
  - [ ] Throttled rules alarm

## Integration Testing

- [ ] MWAA DAGs are deployed (poll_orders, poll_products, etc.)
- [ ] Wait for first scheduled trigger
- [ ] Verify DAG execution in MWAA UI
- [ ] Check CloudWatch logs for rule invocations
- [ ] Verify no messages in DLQ
- [ ] Verify no CloudWatch alarms triggered

## Monitoring Setup

- [ ] Configure SNS topic for CloudWatch alarms (if not already done)
- [ ] Subscribe to alarm notifications
- [ ] Set up dashboard for EventBridge metrics
- [ ] Configure log insights queries for troubleshooting

## Documentation

- [ ] Document MWAA environment ARN
- [ ] Document DLQ URL for troubleshooting
- [ ] Document CloudWatch log group name
- [ ] Update runbook with EventBridge procedures
- [ ] Share access information with team

## Rollback Plan

In case of issues:

1. Disable rules:
   ```bash
   aws events disable-rule --name <rule-name>
   ```

2. Or destroy infrastructure:
   ```bash
   terraform destroy
   ```

3. Verify MWAA is not affected

## Common Issues

### Rules not triggering
- Check rule state (ENABLED vs DISABLED)
- Verify MWAA environment ARN is correct
- Check IAM role permissions
- Review CloudWatch logs

### Failed invocations
- Check DLQ for error messages
- Verify MWAA environment is running
- Check MWAA execution role permissions
- Review DAG code for errors

### Permission errors
- Verify IAM role trust policy
- Check IAM policy permissions
- Ensure MWAA allows EventBridge invocation

## Success Criteria

- [ ] All 5 EventBridge rules are created and enabled
- [ ] All rules have correct schedules
- [ ] All targets point to MWAA with correct input
- [ ] IAM role has necessary permissions
- [ ] DLQ is configured and empty
- [ ] CloudWatch monitoring is active
- [ ] First scheduled execution succeeds
- [ ] No alarms triggered
- [ ] Team is trained on monitoring and troubleshooting

## Sign-off

- Deployed by: _______________
- Date: _______________
- Environment: _______________
- Verified by: _______________
- Date: _______________

## Notes

Add any deployment-specific notes or issues encountered:

---
