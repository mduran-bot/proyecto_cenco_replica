# EventBridge Module for API Polling System

This Terraform module creates EventBridge scheduled rules that trigger MWAA (Apache Airflow) DAGs for polling Janis APIs at configured intervals.

## Features

- **Scheduled Rules**: Creates 5 EventBridge rules for different data types (orders, products, stock, prices, stores)
- **MWAA Integration**: Configures targets to invoke MWAA environment with proper DAG configuration
- **Error Handling**: Includes Dead Letter Queue (SQS) for failed invocations
- **Monitoring**: CloudWatch alarms for invocation failures, DLQ messages, and throttling
- **IAM Roles**: Proper IAM role and policy for EventBridge to invoke MWAA

## Polling Schedules

According to requirements 1.1-1.6:

| Data Type | Schedule | Description |
|-----------|----------|-------------|
| Orders | rate(5 minutes) | High-frequency polling for order updates |
| Products | rate(1 hour) | Hourly product catalog synchronization |
| Stock | rate(10 minutes) | Regular inventory level updates |
| Prices | rate(30 minutes) | Price changes monitoring |
| Stores | rate(1 day) | Daily store information sync |

## Usage

```hcl
module "eventbridge" {
  source = "./modules/eventbridge"

  name_prefix           = "janis-cencosud"
  environment           = "prod"
  mwaa_environment_arn  = module.mwaa.environment_arn

  # Polling rates (default values shown)
  order_polling_rate    = "5 minutes"
  product_polling_rate  = "1 hour"
  stock_polling_rate    = "10 minutes"
  price_polling_rate    = "30 minutes"
  store_polling_rate    = "1 day"

  tags = {
    Environment = "prod"
    Project     = "janis-cencosud"
    ManagedBy   = "terraform"
  }
}
```

## Input JSON Format

Each EventBridge rule sends the following JSON to MWAA (Requirement 1.7):

```json
{
  "dag_id": "poll_{data_type}",
  "conf": {
    "data_type": "{data_type}"
  }
}
```

Example for orders:
```json
{
  "dag_id": "poll_orders",
  "conf": {
    "data_type": "orders"
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | ~> 5.0 |

## Providers

| Name | Version |
|------|---------|
| aws | ~> 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name_prefix | Prefix for resource names | `string` | n/a | yes |
| mwaa_environment_arn | ARN of MWAA environment to trigger | `string` | n/a | yes |
| environment | Environment name (dev, staging, prod) | `string` | n/a | yes |
| order_polling_rate | Polling frequency for orders | `string` | `"5 minutes"` | no |
| product_polling_rate | Polling frequency for products | `string` | `"1 hour"` | no |
| stock_polling_rate | Polling frequency for stock | `string` | `"10 minutes"` | no |
| price_polling_rate | Polling frequency for prices | `string` | `"30 minutes"` | no |
| store_polling_rate | Polling frequency for stores | `string` | `"1 day"` | no |
| tags | Common tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| event_bus_name | Name of EventBridge custom event bus |
| event_bus_arn | ARN of EventBridge custom event bus |
| rule_arns | Map of rule ARNs by data type |
| rule_names | List of all rule names |
| dlq_url | URL of Dead Letter Queue |
| dlq_arn | ARN of Dead Letter Queue |
| iam_role_arn | ARN of IAM role for EventBridge to MWAA |
| log_group_name | Name of CloudWatch Log Group |
| log_group_arn | ARN of CloudWatch Log Group |
| alarm_arns | Map of CloudWatch Alarm ARNs |

## Resources Created

- **EventBridge Event Bus**: Custom event bus for polling events
- **EventBridge Rules**: 5 scheduled rules (one per data type)
- **EventBridge Targets**: MWAA environment targets with retry and DLQ configuration
- **SQS Queue**: Dead Letter Queue for failed invocations
- **IAM Role**: Role for EventBridge to invoke MWAA
- **IAM Policy**: Policy granting necessary permissions
- **CloudWatch Log Group**: Log group for rule execution logs
- **CloudWatch Alarms**: 3 alarms for monitoring (invocation failures, DLQ messages, throttling)

## Monitoring

The module creates CloudWatch alarms for:

1. **Invocation Failures**: Triggers when more than 5 failed invocations occur in 10 minutes
2. **DLQ Messages**: Triggers when any messages appear in the Dead Letter Queue
3. **Throttled Rules**: Triggers when more than 10 throttling events occur in 10 minutes

## IAM Permissions

The EventBridge IAM role has permissions to:
- `airflow:CreateCliToken` - Create CLI tokens for MWAA API invocation
- `sqs:SendMessage` - Send failed invocations to DLQ

## Notes

- Rules are automatically disabled if `mwaa_environment_arn` is empty
- Targets are conditionally created only when MWAA ARN is provided
- All rules use the default event bus (required for schedule expressions)
- Retry policy: Maximum 2 retry attempts for failed invocations
- DLQ retention: 14 days
- Log retention: 90 days

## Compliance

This module implements:
- **Requirement 1.1**: EventBridge scheduled rules for five data types
- **Requirement 1.2**: Orders polling every 5 minutes
- **Requirement 1.3**: Products polling every 1 hour
- **Requirement 1.4**: Stock polling every 10 minutes
- **Requirement 1.5**: Prices polling every 30 minutes
- **Requirement 1.6**: Stores polling every 24 hours
- **Requirement 1.7**: MWAA invocation via API with dag_id and conf
