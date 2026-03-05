"""
Airflow Task Functions for API Polling System (with Incremental Polling)

This module implements task functions for the polling DAGs with incremental filtering.
The system writes raw JSON to S3 Bronze without validation, enrichment, or deduplication,
but USES incremental filters to fetch only new/modified records.

Workflow:
- Task 1: acquire_dynamodb_lock - Acquire lock before polling
- Task 2: poll_janis_api_raw - Poll API with incremental filters (modified_since)
- Task 3: write_to_s3_bronze - Write raw JSON to S3 Bronze
- Task 4: release_dynamodb_lock - Release lock and update last_modified_date
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Import Airflow exception (may not be available in testing)
try:
    from airflow.exceptions import AirflowSkipException
except ImportError:
    # Define a placeholder for testing
    class AirflowSkipException(Exception):
        """Placeholder for Airflow skip exception when Airflow is not installed."""
        pass

# Import our polling components with fallback for different import contexts
try:
    # Try relative imports first (when imported as module)
    from .state_manager import StateManager
    from .api_client import JanisAPIClient
    from .pagination_handler import PaginationHandler
    from .s3_writer import S3Writer
except ImportError:
    # Fall back to absolute imports (when run directly or in tests)
    from state_manager import StateManager
    from api_client import JanisAPIClient
    from pagination_handler import PaginationHandler
    from s3_writer import S3Writer

logger = logging.getLogger(__name__)


# ============================================================================
# Task 1: Acquire DynamoDB Lock
# ============================================================================

def acquire_dynamodb_lock(data_type: str, client: str, **context) -> bool:
    """
    Acquire lock in DynamoDB for the specified data type and client.
    
    This function attempts to acquire a distributed lock to prevent concurrent
    executions of the same polling job. If the lock cannot be acquired (another
    execution is running), it gracefully skips the current execution.
    
    Multi-tenant support: Uses composite key "{data_type}-{client}" for DynamoDB
    to allow independent polling per client.
    
    Args:
        data_type: Type of data being polled (orders, products, etc.)
        client: Client identifier (metro, wongio, etc.)
        **context: Airflow context with execution metadata (run_id, etc.)
    
    Returns:
        True if lock was acquired successfully
    
    Raises:
        AirflowSkipException: If lock cannot be acquired (graceful skip)
    """
    # Get execution_id from Airflow context
    execution_id = context['run_id']
    
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(
        f"[{composite_key}] Attempting to acquire lock "
        f"(execution_id: {execution_id})"
    )
    
    # Get DynamoDB configuration
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'polling_control')
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    
    # Initialize StateManager
    state_manager = StateManager(
        table_name=table_name,
        endpoint_url=endpoint_url
    )
    
    # Attempt to acquire lock using composite key
    lock_acquired = state_manager.acquire_lock(composite_key, execution_id)
    
    if not lock_acquired:
        # Lock already exists - skip this execution gracefully
        logger.warning(
            f"[{composite_key}] Lock already exists, skipping execution. "
            "Another instance may be running."
        )
        raise AirflowSkipException(
            f"Lock already acquired for {composite_key}, skipping execution"
        )
    
    logger.info(
        f"[{composite_key}] Lock acquired successfully "
        f"(execution_id: {execution_id})"
    )
    
    # Store execution_id and client in XCom for downstream tasks
    context['task_instance'].xcom_push(key='execution_id', value=execution_id)
    context['task_instance'].xcom_push(key='client', value=client)
    
    return True


# ============================================================================
# Task 2: Poll Janis API (Simplified - Raw Data)
# ============================================================================

def poll_janis_api_raw(data_type: str, client: str, endpoint: str, base_url: str, **context) -> Dict[str, Any]:
    """
    Poll Janis API with INCREMENTAL filters (only new/modified records).
    
    This version:
    - USES incremental filters (modified_since parameter)
    - Does NOT deduplicate records (API handles it)
    - Does NOT validate data (writes raw JSON)
    - Fetches only records modified since last successful execution
    
    Multi-tenant support: Uses composite key "{data_type}-{client}" for state
    management and includes "janis-client" header in API requests.
    
    Args:
        data_type: Type of data to poll (orders, products, stock, prices, stores)
        client: Client identifier (metro, wongio, etc.)
        endpoint: Specific API endpoint to call (e.g., order, product)
        base_url: Base URL for the API (e.g., https://oms.janis.in/api)
        **context: Airflow context
    
    Returns:
        Dictionary with:
            - records: List of raw records from API
            - total_fetched: Total records fetched
            - last_modified_date: Latest modification date from records
    """
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(f"[{composite_key}] Starting INCREMENTAL API polling from {base_url}/{endpoint}")
    
    # Get configuration from environment
    api_key = os.environ.get('JANIS_API_KEY')
    
    if not api_key:
        raise ValueError("JANIS_API_KEY must be set in environment")
    
    # Get DynamoDB configuration to retrieve last_modified_date
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'polling_control')
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    
    state_manager = StateManager(
        table_name=table_name,
        endpoint_url=endpoint_url
    )
    
    # Get last_modified_date from DynamoDB for incremental polling
    last_modified_date = state_manager.get_last_modified_date(composite_key)
    
    if last_modified_date:
        logger.info(
            f"[{composite_key}] Using incremental filter: "
            f"modified_since={last_modified_date}"
        )
    else:
        logger.info(
            f"[{composite_key}] First execution - fetching all records "
            "(no last_modified_date found)"
        )
    
    # Initialize API client with janis-client header
    api_client = JanisAPIClient(
        base_url=base_url,
        api_key=api_key,
        rate_limit=100,
        extra_headers={'janis-client': client}
    )
    
    pagination_handler = PaginationHandler(
        client=api_client,
        max_pages=1000,
        page_size=100
    )
    
    try:
        # Build incremental filters
        filters = {}
        if last_modified_date:
            filters['modified_since'] = last_modified_date
        
        # Fetch pages with incremental filter
        all_records = pagination_handler.fetch_all_pages(
            endpoint=endpoint,
            filters=filters if filters else None
        )
        
        total_fetched = len(all_records)
        
        # Find the latest modification date from fetched records
        new_last_modified_date = None
        if all_records:
            # Assuming records have a 'dateModified' or 'date_modified' field
            date_fields = ['dateModified', 'date_modified', 'updated_at', 'modified_at']
            
            for record in all_records:
                for field in date_fields:
                    if field in record and record[field]:
                        record_date = record[field]
                        if not new_last_modified_date or record_date > new_last_modified_date:
                            new_last_modified_date = record_date
                        break
        
        logger.info(
            f"[{composite_key}] Fetched {total_fetched} records "
            f"(new_last_modified_date: {new_last_modified_date})"
        )
        
        result = {
            'records': all_records,
            'total_fetched': total_fetched,
            'last_modified_date': new_last_modified_date
        }
        
        # Push to XCom for next task
        context['task_instance'].xcom_push(key='polling_result', value=result)
        
        return result
        
    finally:
        # Always close the API client
        api_client.close()


# ============================================================================
# Task 3: Write to S3 Bronze Layer (Raw JSON)
# ============================================================================

def write_to_s3_bronze(data_type: str, client: str, **context) -> Dict[str, Any]:
    """
    Write raw JSON data to S3 Bronze layer with date partitioning.
    
    This function retrieves the raw polling data from XCom and writes it to S3
    in JSON format. The data is partitioned by date (year/month/day) for 
    efficient querying.
    
    Multi-tenant support: Data is written to separate paths per client:
    s3://{bucket}/{client}/{data_type}/year=YYYY/month=MM/day=DD/
    
    Args:
        data_type: Type of data being written
        client: Client identifier (metro, wongio, etc.)
        **context: Airflow context
    
    Returns:
        Dictionary with:
            - success: Boolean indicating write success
            - records_written: Number of records written
            - s3_path: Full S3 path where data was written
            - file_size_mb: Size of written file in MB
    """
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(f"[{composite_key}] Starting S3 write to Bronze layer")
    
    # Get polling result from XCom
    ti = context['task_instance']
    polling_result = ti.xcom_pull(
        task_ids=f'poll_api_{client}',
        key='polling_result'
    )
    
    if not polling_result:
        logger.warning(f"[{composite_key}] No polling result found in XCom")
        return {
            'success': True,
            'records_written': 0,
            'message': 'No data to write'
        }
    
    records = polling_result.get('records', [])
    
    if not records:
        logger.info(f"[{composite_key}] No records to write to S3")
        return {
            'success': True,
            'records_written': 0,
            'message': 'No records to write'
        }
    
    # Get S3 configuration from environment
    s3_bucket = os.environ.get('S3_BRONZE_BUCKET')
    
    if not s3_bucket:
        raise ValueError("S3_BRONZE_BUCKET must be set in environment")
    
    # Initialize S3 writer
    s3_writer = S3Writer(
        bucket_name=s3_bucket,
        endpoint_url=None  # AWS real (no LocalStack)
    )
    
    try:
        # Write raw JSON to S3 with current timestamp for partitioning
        write_result = s3_writer.write_to_bronze(
            data=records,
            client=client,
            data_type=data_type,
            execution_date=datetime.now(timezone.utc)
        )
        
        if write_result['success']:
            logger.info(
                f"[{composite_key}] Successfully wrote {write_result['records_written']} "
                f"records to {write_result['s3_path']} "
                f"({write_result['file_size_mb']:.2f} MB)"
            )
        else:
            logger.error(
                f"[{composite_key}] Failed to write to S3: "
                f"{write_result.get('error', 'Unknown error')}"
            )
        
        # Push result to XCom for release_lock task
        ti.xcom_push(key='s3_write_result', value=write_result)
        
        return write_result
        
    except Exception as e:
        logger.error(
            f"[{composite_key}] Unexpected error writing to S3: {str(e)}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'records_written': 0
        }


# ============================================================================
# Task 4: Release DynamoDB Lock
# ============================================================================

def release_dynamodb_lock(data_type: str, client: str, **context) -> None:
    """
    Release lock in DynamoDB and update timestamps.
    
    This function always executes (trigger_rule='all_done') to ensure the lock
    is released even if upstream tasks fail. It determines execution success
    and updates the appropriate timestamps in DynamoDB.
    
    Multi-tenant support: Uses composite key "{data_type}-{client}" for DynamoDB.
    
    Args:
        data_type: Type of data being polled
        client: Client identifier (metro, wongio, etc.)
        **context: Airflow context
    
    Returns:
        None
    """
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(f"[{composite_key}] Releasing lock")
    
    # Get DynamoDB configuration
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'polling_control')
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    
    # Initialize StateManager
    state_manager = StateManager(
        table_name=table_name,
        endpoint_url=endpoint_url
    )
    
    # Determine if execution was successful
    ti = context['task_instance']
    dag_run = context['dag_run']
    
    # Get task instances for upstream tasks
    upstream_task_ids = [f'poll_api_{client}', f'write_to_s3_{client}']
    upstream_states = []
    
    for task_id in upstream_task_ids:
        task_instance = dag_run.get_task_instance(task_id)
        if task_instance:
            upstream_states.append(task_instance.state)
    
    # Execution is successful if all upstream tasks succeeded
    success = all(state == 'success' for state in upstream_states)
    
    # Get polling result for record count
    records_fetched = 0
    error_message = None
    
    if success:
        polling_result = ti.xcom_pull(
            task_ids=f'poll_api_{client}',
            key='polling_result'
        )
        
        if polling_result:
            records_fetched = polling_result.get('total_fetched', 0)
            logger.info(
                f"[{composite_key}] Execution successful: "
                f"{records_fetched} records processed"
            )
    else:
        # Execution failed - determine error message
        failed_tasks = [
            task_id for task_id, state in zip(upstream_task_ids, upstream_states)
            if state != 'success'
        ]
        error_message = f"Tasks failed: {', '.join(failed_tasks)}"
        logger.error(f"[{composite_key}] Execution failed: {error_message}")
    
    # Get last_modified_date from polling result for incremental tracking
    last_modified_date = None
    if success:
        polling_result = ti.xcom_pull(
            task_ids=f'poll_api_{client}',
            key='polling_result'
        )
        if polling_result:
            last_modified_date = polling_result.get('last_modified_date')
    
    # Release lock with appropriate parameters using composite key
    try:
        state_manager.release_lock(
            data_type=composite_key,
            success=success,
            last_modified=last_modified_date,  # Track for incremental polling
            records_fetched=records_fetched,
            error_message=error_message
        )
        
        logger.info(
            f"[{composite_key}] Lock released successfully "
            f"(success={success})"
        )
        
    except Exception as e:
        logger.error(
            f"[{composite_key}] Error releasing lock: {e}",
            exc_info=True
        )
        # Don't raise - we want to ensure the task completes
        # even if lock release fails
    
    # Log metrics
    logger.info(
        f"[{composite_key}] Metrics: "
        f"success={success}, "
        f"records_fetched={records_fetched}, "
        f"client={client}"
    )
