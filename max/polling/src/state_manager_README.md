# StateManager Module

## Overview

The `StateManager` module provides DynamoDB-based state management for the API polling system. It implements distributed locking to prevent concurrent executions and tracks polling state to enable incremental data fetching.

## Features

- **Distributed Locking**: Prevents multiple polling executions from running simultaneously for the same data type
- **State Tracking**: Maintains execution history and timestamps for incremental polling
- **Error Handling**: Gracefully handles lock conflicts and DynamoDB errors
- **LocalStack Support**: Compatible with LocalStack for local development and testing

## Requirements Implemented

This module implements the following requirements from the specification:

- **3.2**: Acquire lock when DAG starts
- **3.3**: Skip execution if lock already exists
- **3.5**: Update last_successful_execution on success
- **3.6**: Release lock on success
- **3.7**: Release lock on failure, preserve timestamp
- **3.8**: Store last_modified_date for incremental queries
- **4.3**: Handle first execution (no previous state)

## DynamoDB Table Schema

The module expects a DynamoDB table with the following structure:

```python
{
    "TableName": "polling_control",
    "KeySchema": [
        {"AttributeName": "data_type", "KeyType": "HASH"}
    ],
    "AttributeDefinitions": [
        {"AttributeName": "data_type", "AttributeType": "S"}
    ],
    "BillingMode": "PAY_PER_REQUEST"
}
```

### Item Structure

```python
{
    "data_type": "orders",              # Primary key
    "lock_acquired": True,              # Lock status
    "lock_timestamp": "2024-01-15T10:30:00Z",
    "execution_id": "uuid-1234",        # Current execution ID
    "last_successful_execution": "2024-01-15T10:25:00Z",
    "last_modified_date": "2024-01-15T10:24:00Z",  # For incremental filtering
    "status": "running",                # running | completed | failed
    "records_fetched": 150,             # Metrics
    "error_message": None               # Error details if failed
}
```

## Usage

### Basic Usage

```python
from src.state_manager import StateManager
import uuid

# Initialize StateManager
state_manager = StateManager(table_name='polling_control')

# Generate unique execution ID
execution_id = str(uuid.uuid4())
data_type = 'orders'

# Try to acquire lock
if state_manager.acquire_lock(data_type, execution_id):
    try:
        # Perform polling operation
        records = fetch_data()
        latest_modified = get_latest_timestamp(records)
        
        # Release lock on success
        state_manager.release_lock(
            data_type=data_type,
            success=True,
            last_modified=latest_modified,
            records_fetched=len(records)
        )
    except Exception as e:
        # Release lock on failure
        state_manager.release_lock(
            data_type=data_type,
            success=False,
            error_message=str(e)
        )
else:
    print("Lock already held, skipping execution")
```

### LocalStack Usage

```python
import os
from src.state_manager import StateManager

# For LocalStack testing
endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
state_manager = StateManager(
    table_name='polling_control',
    endpoint_url=endpoint_url
)
```

### Querying State

```python
# Get complete state
control_item = state_manager.get_control_item('orders')
if control_item:
    print(f"Status: {control_item['status']}")
    print(f"Last execution: {control_item['last_successful_execution']}")

# Get just the last_modified_date for incremental filtering
last_modified = state_manager.get_last_modified_date('orders')
if last_modified:
    # Use for incremental query
    filter_params = {'dateModified': last_modified}
else:
    # First execution, perform full refresh
    filter_params = {}
```

## API Reference

### StateManager Class

#### `__init__(table_name: str = "polling_control", endpoint_url: Optional[str] = None)`

Initialize StateManager with DynamoDB connection.

**Parameters:**
- `table_name`: Name of the DynamoDB control table (default: "polling_control")
- `endpoint_url`: Optional endpoint URL for LocalStack testing

#### `acquire_lock(data_type: str, execution_id: str) -> bool`

Attempt to acquire a lock for the given data type.

**Parameters:**
- `data_type`: Type of data being polled (e.g., 'orders', 'products')
- `execution_id`: Unique identifier for this execution

**Returns:**
- `True` if lock was acquired successfully
- `False` if lock already exists (concurrent execution prevented)

**Raises:**
- `ClientError`: For DynamoDB errors other than ConditionalCheckFailed

#### `release_lock(data_type: str, success: bool, last_modified: Optional[str] = None, records_fetched: int = 0, error_message: Optional[str] = None) -> None`

Release the lock and update execution state.

**Parameters:**
- `data_type`: Type of data being polled
- `success`: Whether the execution was successful
- `last_modified`: Latest modification timestamp from fetched data (optional)
- `records_fetched`: Number of records fetched in this execution
- `error_message`: Error message if execution failed (optional)

**Behavior:**
- On success: Updates `last_successful_execution` and optionally `last_modified_date`
- On failure: Releases lock but preserves previous timestamps

#### `get_control_item(data_type: str) -> Optional[Dict[str, Any]]`

Retrieve the current state for a given data type.

**Parameters:**
- `data_type`: Type of data being polled

**Returns:**
- Dictionary with state information, or `None` if item doesn't exist (first execution)

#### `update_last_modified(data_type: str, last_modified: str) -> None`

Update the last_modified_date timestamp for incremental polling.

**Parameters:**
- `data_type`: Type of data being polled
- `last_modified`: Latest modification timestamp from fetched data

#### `get_last_modified_date(data_type: str) -> Optional[str]`

Get the last_modified_date for a data type.

**Parameters:**
- `data_type`: Type of data being polled

**Returns:**
- ISO format timestamp string, or `None` if not set or item doesn't exist

#### `clear_lock(data_type: str) -> None`

Clear the lock for a data type (for testing/recovery purposes).

**Parameters:**
- `data_type`: Type of data being polled

**Warning:** This method forcefully releases a lock and should only be used for testing or manual recovery scenarios.

## Error Handling

The module handles the following error scenarios:

### Lock Already Exists
When `acquire_lock()` is called and a lock already exists, it returns `False` and logs a warning. The calling code should gracefully skip execution.

### DynamoDB Errors
For DynamoDB errors other than `ConditionalCheckFailedException`, the module raises `ClientError` exceptions. The calling code should handle these appropriately.

### First Execution
When no previous state exists (first execution), `get_control_item()` and `get_last_modified_date()` return `None`. The calling code should interpret this as a signal to perform a full data refresh.

## Testing

The module includes comprehensive unit tests in `tests/test_state_manager.py`:

```bash
# Run tests
pytest tests/test_state_manager.py -v

# Run with coverage
pytest tests/test_state_manager.py --cov=src.state_manager --cov-report=term
```

## Examples

See `examples/state_manager_usage.py` for complete working examples including:

- Successful polling execution
- Concurrent execution prevention
- First execution handling
- State querying
- Error handling

## Integration with Polling System

The StateManager is designed to be used in Airflow DAGs:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from src.state_manager import StateManager
import uuid

def acquire_lock_task(**context):
    """Airflow task to acquire lock."""
    data_type = context['dag_run'].conf.get('data_type')
    execution_id = str(uuid.uuid4())
    
    state_manager = StateManager()
    if not state_manager.acquire_lock(data_type, execution_id):
        raise AirflowSkipException("Lock already held")
    
    # Store execution_id for other tasks
    context['ti'].xcom_push(key='execution_id', value=execution_id)

def release_lock_task(**context):
    """Airflow task to release lock."""
    data_type = context['dag_run'].conf.get('data_type')
    success = context['ti'].xcom_pull(key='success', default=False)
    
    state_manager = StateManager()
    state_manager.release_lock(data_type, success)

# DAG definition
dag = DAG('poll_orders', schedule_interval=None)

acquire_lock = PythonOperator(
    task_id='acquire_lock',
    python_callable=acquire_lock_task,
    dag=dag
)

release_lock = PythonOperator(
    task_id='release_lock',
    python_callable=release_lock_task,
    trigger_rule='all_done',
    dag=dag
)
```

## LocalStack Setup

To test with LocalStack:

1. **Start LocalStack:**
```bash
# From max/polling/ directory
docker-compose up -d
```

The docker-compose configuration includes:
- DynamoDB (state management)
- S3 (staging bucket)
- SNS (notifications)
- EventBridge (scheduling)
- CloudWatch Logs (logging)
- Secrets Manager (credentials)

See [LOCALSTACK_SETUP.md](../../LOCALSTACK_SETUP.md) for detailed setup instructions.

2. **Initialize DynamoDB table:**
```bash
# Using Terraform
cd ../../terraform
terraform apply -var-file="localstack.tfvars"

# Or using AWS CLI
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
  --table-name polling_control \
  --attribute-definitions AttributeName=data_type,AttributeType=S \
  --key-schema AttributeName=data_type,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

3. **Set environment variable:**
```bash
export LOCALSTACK_ENDPOINT=http://localhost:4566
```

4. **Run examples or tests:**
```bash
python examples/state_manager_usage.py
```

## Best Practices

1. **Always use try-finally**: Ensure locks are released even if errors occur
2. **Generate unique execution IDs**: Use UUID for each execution
3. **Handle lock conflicts gracefully**: Don't treat lock conflicts as errors
4. **Preserve timestamps on failure**: Use `success=False` to maintain incremental state
5. **Log appropriately**: Use structured logging with execution_id for correlation

## Troubleshooting

### Lock stuck in acquired state
If a lock gets stuck (e.g., due to process crash), use `clear_lock()` to manually release it:

```python
state_manager = StateManager()
state_manager.clear_lock('orders')
```

### First execution not working
Ensure the DynamoDB table exists and is accessible. Check AWS credentials and region configuration.

### LocalStack connection issues
Verify LocalStack is running and the endpoint URL is correct:

```bash
aws --endpoint-url=http://localhost:4566 dynamodb list-tables
```
