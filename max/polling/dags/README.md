# Airflow DAGs for API Polling System

This directory contains Airflow DAGs for polling Janis APIs on scheduled intervals. Each DAG is triggered by Amazon EventBridge and orchestrates the complete polling workflow with multi-tenant support for Metro and Wongio clients.

## DAG Structure

All DAGs follow the same workflow pattern defined in `base_polling_dag.py`:

1. **acquire_lock**: Acquire lock in DynamoDB to prevent concurrent executions (per client)
2. **poll_api**: Poll Janis API with incremental filters and pagination
3. **validate_data**: Validate data against JSON schemas and business rules
4. **enrich_data**: Enrich data with related entities in parallel
5. **output_data**: Add metadata and prepare for downstream processing
6. **release_lock**: Release lock (always executes via `trigger_rule='all_done'`)

## Available DAGs

The system implements 5 DAGs that handle 10 specific API endpoints across 2 clients (Metro and Wongio), resulting in 20 total API calls per complete polling cycle.

### poll_orders.py
- **Schedule**: rate(5 minutes) via EventBridge
- **Endpoint**: `/order`
- **Base URL**: `https://oms.janis.in/api`
- **Clients**: Metro, Wongio (2 calls per execution)
- **Enrichment**: Fetches order items for each order
- **Requirement**: 1.2

### poll_catalog.py (formerly poll_products.py)
- **Schedule**: rate(1 hour) via EventBridge
- **Endpoints**: `/product`, `/sku`, `/category`, `/brand` (4 endpoints)
- **Base URL**: `https://catalog.janis.in/api`
- **Clients**: Metro, Wongio (8 calls per execution: 4 endpoints × 2 clients)
- **Enrichment**: Fetches product SKUs for products
- **Requirement**: 1.3

### poll_stock.py
- **Schedule**: rate(10 minutes) via EventBridge
- **Endpoint**: `/sku-stock`
- **Base URL**: `https://wms.janis.in/api`
- **Clients**: Metro, Wongio (2 calls per execution)
- **Enrichment**: None (self-contained records)
- **Requirement**: 1.4

### poll_prices.py
- **Schedule**: rate(30 minutes) via EventBridge
- **Endpoints**: `/price`, `/price-sheet`, `/base-price` (3 endpoints)
- **Base URL**: `https://vtex.pricing.janis.in/api`
- **Clients**: Metro, Wongio (6 calls per execution: 3 endpoints × 2 clients)
- **Enrichment**: None (self-contained records)
- **Requirement**: 1.5

### poll_stores.py
- **Schedule**: rate(1 day) via EventBridge
- **Endpoint**: `/location`
- **Base URL**: `https://commerce.janis.in/api`
- **Clients**: Metro, Wongio (2 calls per execution)
- **Enrichment**: None (self-contained records)
- **Requirement**: 1.6

## Event-Driven Execution

All DAGs have `schedule_interval=None` because they are triggered by EventBridge rules, not by Airflow's internal scheduler. This approach:

- Reduces MWAA overhead (no constant scheduler polling)
- Provides more granular scheduling control
- Allows different schedules per data type
- Enables dynamic schedule adjustments without DAG changes

### Multi-Tenant Architecture

Each DAG execution processes multiple clients (Metro and Wongio) in a single run. EventBridge passes client configuration via input JSON:

**Example for poll_orders:**
```json
{
  "dag_id": "poll_orders",
  "conf": {
    "clients": ["metro", "wongio"],
    "endpoint": "/order",
    "base_url": "https://oms.janis.in/api"
  }
}
```

**Example for poll_catalog (multiple endpoints):**
```json
{
  "dag_id": "poll_catalog",
  "conf": {
    "clients": ["metro", "wongio"],
    "endpoints": ["/product", "/sku", "/category", "/brand"],
    "base_url": "https://catalog.janis.in/api"
  }
}
```

The DAG internally creates tasks for each client, ensuring proper isolation via DynamoDB locks with composite keys (`{data_type}-{client}`).

## Task Implementation Status

### ✅ Completed (Task 10)
- Base DAG factory (`base_polling_dag.py`)
- All 5 entity-specific DAGs (orders, products, stock, prices, stores)
- Task structure and dependencies
- Trigger rules for lock release

### 📋 Pending (Task 11)
The task functions in `base_polling_dag.py` are placeholders that need implementation:

- `acquire_dynamodb_lock` (Task 11.1)
- `poll_janis_api` (Task 11.2)
- `validate_data` (Task 11.3)
- `enrich_data` (Task 11.4)
- `output_data` (Task 11.5)
- `release_dynamodb_lock` (Task 11.6)

## Usage

### Deploying to MWAA

1. Upload DAGs to S3 bucket configured for MWAA:
```bash
aws s3 sync dags/ s3://your-mwaa-bucket/dags/
```

2. MWAA will automatically detect and load the DAGs

3. Configure EventBridge rules to trigger DAGs:
```bash
# Example for orders DAG (multi-tenant)
aws events put-rule \
  --name poll-orders-schedule \
  --schedule-expression "rate(5 minutes)"

aws events put-targets \
  --rule poll-orders-schedule \
  --targets "Id"="1","Arn"="arn:aws:airflow:region:account:environment/mwaa-env","RoleArn"="arn:aws:iam::account:role/EventBridgeToMWAA","Input"='{"dag_id":"poll_orders","conf":{"clients":["metro","wongio"],"endpoint":"/order","base_url":"https://oms.janis.in/api"}}'

# Example for catalog DAG (multiple endpoints)
aws events put-rule \
  --name poll-catalog-schedule \
  --schedule-expression "rate(1 hour)"

aws events put-targets \
  --rule poll-catalog-schedule \
  --targets "Id"="1","Arn"="arn:aws:airflow:region:account:environment/mwaa-env","RoleArn"="arn:aws:iam::account:role/EventBridgeToMWAA","Input"='{"dag_id":"poll_catalog","conf":{"clients":["metro","wongio"],"endpoints":["/product","/sku","/category","/brand"],"base_url":"https://catalog.janis.in/api"}}'
```

### Testing Locally

DAGs can be tested locally using Airflow's CLI:

```bash
# Initialize Airflow database
airflow db init

# Test DAG structure
airflow dags list
airflow dags show poll_orders

# Test individual tasks
airflow tasks test poll_orders acquire_lock 2024-01-01
```

### Triggering Manually

DAGs can be triggered manually via Airflow UI or CLI with multi-tenant configuration:

```bash
# Via CLI - single client
airflow dags trigger poll_orders --conf '{"clients":["metro"],"endpoint":"/order","base_url":"https://oms.janis.in/api"}'

# Via CLI - both clients
airflow dags trigger poll_orders --conf '{"clients":["metro","wongio"],"endpoint":"/order","base_url":"https://oms.janis.in/api"}'

# Via CLI - catalog with multiple endpoints
airflow dags trigger poll_catalog --conf '{"clients":["metro","wongio"],"endpoints":["/product","/sku","/category","/brand"],"base_url":"https://catalog.janis.in/api"}'

# Via AWS CLI (through MWAA API)
aws mwaa create-cli-token --name your-mwaa-environment
# Use token in Airflow UI to trigger DAG with appropriate conf
```

## Configuration

### Environment Variables

DAGs expect the following environment variables (configured in MWAA):

- `JANIS_API_KEY_SECRET`: AWS Secrets Manager secret name for API key
- `DYNAMODB_CONTROL_TABLE`: Name of DynamoDB control table
- `S3_STAGING_BUCKET`: S3 bucket for staging data
- `SNS_ERROR_TOPIC`: SNS topic ARN for error notifications
- `LOCALSTACK_ENDPOINT`: (Optional) LocalStack endpoint for testing

**Note**: Base URLs and endpoints are now passed via EventBridge input JSON rather than environment variables, enabling dynamic configuration per DAG execution.

### MWAA Requirements

Add to `requirements.txt` for MWAA:

```
boto3>=1.28.0
requests>=2.31.0
jsonschema>=4.19.0
```

## Monitoring

### CloudWatch Logs

Each DAG execution writes structured logs to CloudWatch:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "execution_id": "manual__2024-01-15T10:30:00+00:00",
  "data_type": "orders",
  "task_id": "poll_api",
  "level": "INFO",
  "message": "Fetched 150 records"
}
```

### CloudWatch Metrics

Custom metrics emitted by DAGs:

- `RecordsFetched`: Total records fetched per execution
- `ValidationPassRate`: Percentage of valid records
- `ExecutionDuration`: Total execution time
- `LockContentionRate`: Frequency of lock acquisition failures

### Airflow UI

Monitor DAG executions in Airflow UI:

- DAG runs and task status
- Task logs and error messages
- XCom data passed between tasks
- Task duration and performance metrics

## Error Handling

### Lock Acquisition Failure

If lock cannot be acquired (another execution is running):
- Task raises `AirflowSkipException`
- DAG execution is skipped gracefully
- No error notification sent (expected behavior)

### API Errors

If API polling fails:
- Task retries with exponential backoff (handled by JanisAPIClient)
- After max retries, task fails
- Lock is released via `trigger_rule='all_done'`
- Error notification sent to SNS

### Validation Errors

If data validation fails:
- Invalid records are logged and excluded
- Valid records continue to enrichment
- Validation metrics are recorded
- If validation pass rate < 95%, alert is triggered

## Best Practices

1. **Idempotency**: All tasks are designed to be idempotent for safe retries
2. **Lock Management**: Always use `trigger_rule='all_done'` for lock release
3. **Error Logging**: Use structured logging with execution_id for correlation
4. **Metrics**: Emit custom metrics for monitoring and alerting
5. **Testing**: Test DAGs in dev environment before deploying to production

## References

- [Specification: requirements.md](../../../.kiro/specs/api-polling-system/requirements.md)
- [Specification: design.md](../../../.kiro/specs/api-polling-system/design.md)
- [Specification: tasks.md](../../../.kiro/specs/api-polling-system/tasks.md)
- [MWAA Documentation](https://docs.aws.amazon.com/mwaa/)
- [Airflow Documentation](https://airflow.apache.org/docs/)
