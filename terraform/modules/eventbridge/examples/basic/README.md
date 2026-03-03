# Basic EventBridge Example

This example demonstrates how to configure EventBridge scheduled rules for API polling with MWAA.

## Usage

1. Set the MWAA environment ARN:

```bash
export TF_VAR_mwaa_environment_arn="arn:aws:airflow:us-east-1:123456789012:environment/janis-cencosud-mwaa"
```

2. Initialize and apply:

```bash
terraform init
terraform plan
terraform apply
```

## What This Creates

- EventBridge custom event bus for polling
- 5 scheduled rules (orders, products, stock, prices, stores)
- EventBridge targets pointing to MWAA environment
- IAM role for EventBridge to invoke MWAA
- Dead Letter Queue for failed invocations
- CloudWatch alarms for monitoring

## Polling Schedules

| Data Type | Schedule | Frequency |
|-----------|----------|-----------|
| Orders | rate(5 minutes) | Every 5 minutes |
| Products | rate(1 hour) | Every hour |
| Stock | rate(10 minutes) | Every 10 minutes |
| Prices | rate(30 minutes) | Every 30 minutes |
| Stores | rate(1 day) | Once per day |

## Testing

After deployment, you can verify the rules are created:

```bash
aws events list-rules --name-prefix janis-cencosud-poll
```

Check the targets:

```bash
aws events list-targets-by-rule --rule janis-cencosud-poll-orders-schedule
```

Monitor the Dead Letter Queue:

```bash
aws sqs get-queue-attributes \
  --queue-url $(terraform output -raw dlq_url) \
  --attribute-names ApproximateNumberOfMessages
```

## Clean Up

```bash
terraform destroy
```
