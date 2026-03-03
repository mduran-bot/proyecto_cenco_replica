# EventBridge Module - Quick Start Guide

## 1. Prerequisites

- Terraform >= 1.0
- AWS CLI configured
- MWAA environment deployed (or ARN available)

## 2. Basic Usage

```hcl
module "eventbridge" {
  source = "./modules/eventbridge"

  name_prefix          = "janis-cencosud"
  environment          = "prod"
  mwaa_environment_arn = "arn:aws:airflow:us-east-1:123456789012:environment/mwaa"

  tags = {
    Environment = "prod"
    Project     = "janis-cencosud"
  }
}
```

## 3. Deploy

```bash
terraform init
terraform plan
terraform apply
```

## 4. Verify

```bash
# List rules
aws events list-rules --name-prefix janis-cencosud-poll

# Check specific rule
aws events describe-rule --name janis-cencosud-poll-orders-schedule

# View targets
aws events list-targets-by-rule --rule janis-cencosud-poll-orders-schedule
```

## 5. Monitor

```bash
# Check DLQ for failed invocations
aws sqs get-queue-attributes \
  --queue-url $(terraform output -raw dlq_url) \
  --attribute-names ApproximateNumberOfMessages

# View CloudWatch logs
aws logs tail /aws/events/janis-cencosud-polling --follow
```

## 6. Customize Polling Rates

```hcl
module "eventbridge" {
  source = "./modules/eventbridge"

  # ... other variables ...

  # Custom polling rates
  order_polling_rate   = "3 minutes"   # More frequent
  product_polling_rate = "2 hours"     # Less frequent
  stock_polling_rate   = "15 minutes"
  price_polling_rate   = "1 hour"
  store_polling_rate   = "12 hours"
}
```

## 7. Disable Rules

To disable all rules, set MWAA ARN to empty:

```hcl
module "eventbridge" {
  source = "./modules/eventbridge"

  # ... other variables ...
  mwaa_environment_arn = ""  # Disables all rules
}
```

## 8. Troubleshooting

### Rules not triggering?

```bash
# Check rule state
aws events describe-rule --name janis-cencosud-poll-orders-schedule

# Check CloudWatch alarms
aws cloudwatch describe-alarms --alarm-name-prefix janis-cencosud-eventbridge
```

### Failed invocations?

```bash
# Check DLQ messages
aws sqs receive-message --queue-url <dlq-url>

# Check CloudWatch logs
aws logs filter-log-events \
  --log-group-name /aws/events/janis-cencosud-polling \
  --filter-pattern "ERROR"
```

### IAM permission issues?

```bash
# Verify IAM role
aws iam get-role --role-name janis-cencosud-eventbridge-mwaa-role

# Check policy
aws iam get-role-policy \
  --role-name janis-cencosud-eventbridge-mwaa-role \
  --policy-name janis-cencosud-eventbridge-mwaa-policy
```

## 9. Clean Up

```bash
terraform destroy
```

## 10. Next Steps

1. Deploy MWAA environment if not already done
2. Create the 5 polling DAGs in MWAA
3. Test manual DAG trigger
4. Enable EventBridge rules
5. Monitor execution and adjust schedules as needed

## Support

For detailed documentation, see:
- [README.md](README.md) - Full module documentation
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [examples/basic/](examples/basic/) - Working example
